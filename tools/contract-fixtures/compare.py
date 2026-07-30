#!/usr/bin/env python3
"""
D2 gate tool. Diffs two fixture directories and reports contract drift.

Compares, per action:
  * status differences
  * key set differences   (keys present in one side and absent in the other, at every depth)
  * type differences      (same key, different JSON type)
  * null handling         (a key null on one side and non null on the other)

Array contents are not compared. Only the merged element shape is, so a portfolio of 12 and a
portfolio of 3 compare equal provided their element shapes match.

Usage:
    python compare.py --baseline p0-baseline/contracts --candidate render-fixtures/contracts
    python compare.py --baseline A --candidate B --json report.json

Exit codes:
    0  no differences
    1  differences found
    2  could not run (missing directory, unreadable fixture)

Standard library only.
"""

import argparse
import json
import pathlib
import sys


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "missing"
    except (ValueError, UnicodeDecodeError) as exc:
        return None, "unreadable: %s" % exc


def read_status(headers_path):
    if not headers_path.exists():
        return None
    for line in headers_path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("http status:"):
            return line.split(":", 1)[1].strip()
    return None


def json_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def flatten(value, prefix=""):
    """
    Map every path to its JSON type. Arrays are represented by merging their elements under
    `path[]` so that length differences do not register as contract drift.
    """
    out = {}
    if isinstance(value, dict):
        for key, sub in value.items():
            path = "%s.%s" % (prefix, key) if prefix else key
            out[path] = json_type(sub)
            out.update(flatten(sub, path))
    elif isinstance(value, list):
        path = "%s[]" % prefix
        for element in value:
            observed = json_type(element)
            if path in out and out[path] != observed:
                out[path] = "mixed"
            else:
                out[path] = observed
            out.update(flatten(element, path))
    return out


def compare_action(action, baseline_dir, candidate_dir, method):
    result = {"action": action, "method": method,
              "status": [], "missing_keys": [], "extra_keys": [],
              "type_differences": [], "null_differences": [], "errors": []}

    base_body = baseline_dir / method.lower() / ("%s.json" % action)
    cand_body = candidate_dir / method.lower() / ("%s.json" % action)

    base_status = read_status(baseline_dir / method.lower() / ("%s.headers.txt" % action))
    cand_status = read_status(candidate_dir / method.lower() / ("%s.headers.txt" % action))
    if base_status != cand_status:
        result["status"].append({"baseline": base_status, "candidate": cand_status})

    base_json, base_err = load_json(base_body)
    cand_json, cand_err = load_json(cand_body)
    if base_err:
        result["errors"].append("baseline %s" % base_err)
    if cand_err:
        result["errors"].append("candidate %s" % cand_err)
    if base_err or cand_err:
        return result

    base_flat = flatten(base_json)
    cand_flat = flatten(cand_json)

    for path in sorted(set(base_flat) - set(cand_flat)):
        result["missing_keys"].append({"path": path, "baseline_type": base_flat[path]})
    for path in sorted(set(cand_flat) - set(base_flat)):
        result["extra_keys"].append({"path": path, "candidate_type": cand_flat[path]})

    for path in sorted(set(base_flat) & set(cand_flat)):
        b, c = base_flat[path], cand_flat[path]
        if b == c:
            continue
        if "null" in (b, c):
            result["null_differences"].append({"path": path, "baseline": b, "candidate": c})
        else:
            result["type_differences"].append({"path": path, "baseline": b, "candidate": c})

    return result


def has_differences(entry):
    return any(entry[k] for k in
               ("status", "missing_keys", "extra_keys", "type_differences", "null_differences", "errors"))


def main():
    parser = argparse.ArgumentParser(description="Diff two contract fixture directories (D2 gate).")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--json", default=None, help="Write the full report to this path.")
    args = parser.parse_args()

    baseline_dir = pathlib.Path(args.baseline)
    candidate_dir = pathlib.Path(args.candidate)
    for label, path in (("baseline", baseline_dir), ("candidate", candidate_dir)):
        if not path.is_dir():
            print("%s directory not found: %s" % (label, path))
            return 2

    report, drift = [], False
    for method in ("GET", "POST"):
        base_method_dir = baseline_dir / method.lower()
        if not base_method_dir.is_dir():
            continue
        for body in sorted(base_method_dir.glob("*.json")):
            entry = compare_action(body.stem, baseline_dir, candidate_dir, method)
            report.append(entry)
            if has_differences(entry):
                drift = True

    print("Baseline : %s" % baseline_dir)
    print("Candidate: %s" % candidate_dir)
    print("Actions compared: %d" % len(report))
    print()

    for entry in report:
        if not has_differences(entry):
            print("  OK    %s %s" % (entry["method"], entry["action"]))
            continue
        print("  DRIFT %s %s" % (entry["method"], entry["action"]))
        for item in entry["errors"]:
            print("        error: %s" % item)
        for item in entry["status"]:
            print("        status: baseline=%s candidate=%s" % (item["baseline"], item["candidate"]))
        for item in entry["missing_keys"]:
            print("        missing in candidate: %s (%s)" % (item["path"], item["baseline_type"]))
        for item in entry["extra_keys"]:
            print("        extra in candidate:   %s (%s)" % (item["path"], item["candidate_type"]))
        for item in entry["type_differences"]:
            print("        type: %s baseline=%s candidate=%s" % (item["path"], item["baseline"], item["candidate"]))
        for item in entry["null_differences"]:
            print("        null: %s baseline=%s candidate=%s" % (item["path"], item["baseline"], item["candidate"]))

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print()
        print("Report written to %s" % args.json)

    print()
    print("RESULT: %s" % ("DRIFT DETECTED" if drift else "no differences"))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
