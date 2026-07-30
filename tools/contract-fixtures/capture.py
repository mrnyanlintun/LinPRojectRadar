#!/usr/bin/env python3
"""
Contract fixture capture for the Apps Script backend.

Issues each configured GET action against the live endpoint and records the status, headers,
raw body and a SHA-256, then derives a response schema describing shape rather than values.

Safety model, enforced in code rather than by convention:

  * POST actions are never issued. Every POST in config.json carries
    capture: "DEFERRED_TO_MANUAL" because each one either mutates stored state or bills a paid
    API key. send_post() exists but refuses to run without an explicit override that is not
    reachable from the command line.
  * A capture run is opt in. Without --confirm the script prints its plan and exits.

Usage:
    python capture.py --config config.json            # dry run, prints the plan
    python capture.py --config config.json --confirm  # issues the GET requests

Standard library only. No third party dependencies.
"""

import argparse
import hashlib
import json
import os
import pathlib
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

# M0 Amendment 7: minimum 45s. Apps Script cold start has been measured above 20s.
MINIMUM_TIMEOUT_SECONDS = 45


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        cfg = json.load(handle)

    timeout = cfg.get("timeout_seconds", MINIMUM_TIMEOUT_SECONDS)
    if timeout < MINIMUM_TIMEOUT_SECONDS:
        raise SystemExit(
            "timeout_seconds is %s; the minimum is %s. Apps Script cold starts exceed 20s and a "
            "short timeout produces false failures that would be baselined as the contract."
            % (timeout, MINIMUM_TIMEOUT_SECONDS)
        )
    return cfg


def resolve_params(params, cfg):
    """Substitute {{sample_project_id}} style placeholders from the config."""
    resolved = {}
    for key, value in (params or {}).items():
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            token = value[2:-2]
            replacement = cfg.get(token, "")
            if replacement in ("", "TO_BE_RECORDED"):
                return None, "%s is not populated in config.json" % token
            resolved[key] = replacement
        else:
            resolved[key] = value
    return resolved, None


def _type_names(schema):
    """Flatten a schema's type into a set of primitive names, expanding an existing union."""
    if schema.get("type") == "mixed":
        return set(schema.get("types", []))
    return {schema.get("type", "unknown")}


def merge_schemas(left, right):
    """
    Combine two derived schemas into one that describes both.

    Merging is done on already-derived schema objects and never re-serialises them. An earlier
    version built unions by json.dumps-ing the accumulated schema on every element, which nested
    one level deeper per array element and exhausted memory on the 12 project portfolio.
    """
    if left == right:
        return left

    left_type, right_type = left.get("type"), right.get("type")

    if left_type == "object" and right_type == "object":
        left_props, right_props = left.get("properties", {}), right.get("properties", {})
        merged_props = {}
        for key in sorted(set(left_props) | set(right_props)):
            if key in left_props and key in right_props:
                merged_props[key] = merge_schemas(left_props[key], right_props[key])
            else:
                # Present in only some elements: part of the contract, so record it.
                present = left_props.get(key) or right_props[key]
                merged_props[key] = dict(present, optional=True)
        return {"type": "object", "properties": merged_props}

    if left_type == "array" and right_type == "array":
        merged = {"type": "array", "items": merge_schemas(left.get("items", {"type": "unknown"}),
                                                          right.get("items", {"type": "unknown"}))}
        return merged

    names = _type_names(left) | _type_names(right)

    # "unknown" only ever comes from an empty array, which carries no type information. It must
    # not dilute a union that has real observations.
    if "unknown" in names and len(names) > 1:
        names.discard("unknown")
        if len(names) == 1:
            return {"type": names.pop()}

    # integer and number describe the same JSON contract; widen rather than flag drift.
    if names == {"integer", "number"}:
        return {"type": "number"}

    # null combined with one concrete type means nullable, which is more useful than "mixed".
    if "null" in names and len(names) == 2:
        concrete = (names - {"null"}).pop()
        return {"type": concrete, "nullable": True}

    return {"type": "mixed", "types": sorted(names)}


def derive_schema(value):
    """
    Describe shape, not content. Arrays collapse to a single merged element schema so that a
    12 element portfolio and a 3 element portfolio compare equal.
    """
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {"type": "unknown"}, "observed_length": 0}
        merged = derive_schema(value[0])
        for element in value[1:]:
            merged = merge_schemas(merged, derive_schema(element))
        return {"type": "array", "items": merged, "observed_length": len(value)}
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {key: derive_schema(sub) for key, sub in sorted(value.items())},
        }
    return {"type": "unknown"}


def write_fixture(out_dir, method, action, status, headers, body):
    target = pathlib.Path(out_dir) / method.lower()
    target.mkdir(parents=True, exist_ok=True)

    body_path = target / ("%s.json" % action)
    body_path.write_bytes(body)

    header_lines = ["HTTP status: %s" % status]
    header_lines += ["%s: %s" % (k, v) for k, v in headers]
    (target / ("%s.headers.txt" % action)).write_text("\n".join(header_lines) + "\n", encoding="utf-8")

    digest = hashlib.sha256(body).hexdigest().upper()
    (target / ("%s.sha256.txt" % action)).write_text("%s  %s.json\n" % (digest, action), encoding="utf-8")

    return body_path, digest


def write_schema(out_dir, action, body):
    schema_dir = pathlib.Path(out_dir) / "response-schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        schema = {"action": action, "error": "response was not decodable JSON: %s" % exc}
    else:
        schema = {"action": action, "schema": derive_schema(parsed)}
    path = schema_dir / ("%s.schema.json" % action)
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def send_get(base_url, action, params, timeout):
    query = {"action": action}
    query.update(params or {})
    url = base_url + ("&" if "?" in base_url else "?") + urllib.parse.urlencode(query)

    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "contract-fixtures/1.0"})
    context = ssl.create_default_context()
    # Apps Script answers with a 302 to script.googleusercontent.com. urllib follows it by
    # default; without following, the recorded body would be the redirect page, not the payload.
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.status, list(response.headers.items()), response.read()


def send_post(*_args, **_kwargs):
    raise RuntimeError(
        "POST capture is disabled. Every POST action is DEFERRED_TO_MANUAL because it mutates "
        "stored state or bills a paid API key. Capturing them requires a disposable project and "
        "explicit researcher approval."
    )


def main():
    parser = argparse.ArgumentParser(description="Capture Apps Script contract fixtures.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--confirm", action="store_true",
                        help="Actually issue the requests. Without this the script prints its plan and exits.")
    parser.add_argument("--repo-root", default=None,
                        help="Repository root. Defaults to two levels above this file.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    repo_root = pathlib.Path(args.repo_root) if args.repo_root else pathlib.Path(__file__).resolve().parents[2]
    out_dir = repo_root / cfg.get("output_dir", "p0-baseline/contracts")
    timeout = cfg.get("timeout_seconds", MINIMUM_TIMEOUT_SECONDS)

    planned, skipped = [], []
    for entry in cfg.get("get_actions", []):
        if not entry.get("capture", False):
            skipped.append((entry["action"], "capture is false"))
            continue
        params, problem = resolve_params(entry.get("params"), cfg)
        if problem:
            skipped.append((entry["action"], problem))
            continue
        planned.append((entry["action"], params))

    deferred = [e["action"] for e in cfg.get("post_actions", [])]

    print("Endpoint : %s" % cfg["base_url"])
    print("Timeout  : %ss" % timeout)
    print("Output   : %s" % out_dir)
    print()
    print("GET actions to capture (%d): %s" % (len(planned), ", ".join(a for a, _ in planned) or "none"))
    if skipped:
        print("GET actions skipped (%d):" % len(skipped))
        for action, why in skipped:
            print("  %-20s %s" % (action, why))
    print("POST actions DEFERRED_TO_MANUAL (%d): %s" % (len(deferred), ", ".join(deferred)))
    print()

    if not args.confirm:
        print("Dry run. No request was issued. Re-run with --confirm to capture.")
        return 0

    failures = 0
    for action, params in planned:
        try:
            status, headers, body = send_get(cfg["base_url"], action, params, timeout)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            status, headers = exc.code, list(exc.headers.items())
            print("  %-20s HTTP %s (recorded)" % (action, status))
        except Exception as exc:  # noqa: BLE001 - a failed capture must be visible, never silent
            failures += 1
            print("  %-20s FAILED: %s: %s" % (action, type(exc).__name__, exc))
            continue
        else:
            print("  %-20s HTTP %s" % (action, status))

        _, digest = write_fixture(out_dir, "GET", action, status, headers, body)
        write_schema(out_dir, action, body)
        print("  %-20s sha256 %s" % ("", digest[:16] + "..."))

    print()
    print("Captured %d of %d. Failures: %d" % (len(planned) - failures, len(planned), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
