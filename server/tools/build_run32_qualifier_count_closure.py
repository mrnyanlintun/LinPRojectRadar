"""Run 32 accounting closure: the authoritative pre-change client qualifier population.

The population is extracted MECHANICALLY from the pinned pre-change git object, never
from the current tree and never from the reconciliation CSV that is under audit.

Two artefacts are emitted:
  code_audit/run32_prechange_qualifier_population.csv  - every raw entry, every unique key
  code_audit/run32_qualifier_count_closure.csv         - unique key vs the reconciliation

Neither count is forced. Raw entries and unique keys are counted separately so that a
duplicated key would show as a raw/unique split rather than being silently collapsed.
"""
import csv, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRECHANGE_OBJECT = "19a70556fe1b6ee8d17706cfbbc5d72e12051086"
SOURCE_FILE = "assets/js/knowledge.js"
MAP_NAME = "RUN1_PROXY_QUALIFIER"
RECON = os.path.join(ROOT, "code_audit", "run32_proxy_qualifier_reconciliation.csv")
POP_CSV = os.path.join(ROOT, "code_audit", "run32_prechange_qualifier_population.csv")
CLOSURE_CSV = os.path.join(ROOT, "code_audit", "run32_qualifier_count_closure.csv")

ENTRY = re.compile(r'^\s{4}([A-Za-z0-9_]+):\s*"')


def prechange_source(obj=PRECHANGE_OBJECT, path=SOURCE_FILE):
    out = subprocess.run(["git", "show", "%s:%s" % (obj, path)], cwd=ROOT,
                         capture_output=True, check=True)
    return out.stdout.decode("utf-8").splitlines()


def extract_raw_entries(lines):
    """Every raw `key: "value"` line inside the map literal, in file order.

    The map body is delimited by its own opening and its closing brace at the literal's
    indentation, so a following object literal cannot leak entries into the population.
    """
    entries = []
    inside = False
    for n, line in enumerate(lines, 1):
        if not inside:
            if re.search(r'\b%s\s*=\s*\{' % MAP_NAME, line):
                inside = True
            continue
        if re.match(r'^\s{0,2}\};?\s*$', line):
            break
        m = ENTRY.match(line)
        if m:
            value = line.split(":", 1)[1].strip()
            value = value.rstrip(",").strip()
            if value.startswith('"'):
                value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
            entries.append({"key": m.group(1), "value": value, "line": n})
    if not inside:
        raise SystemExit("FATAL: %s not found in %s@%s" % (MAP_NAME, SOURCE_FILE, PRECHANGE_OBJECT))
    if not entries:
        raise SystemExit("FATAL: %s in %s@%s yielded no entries" % (MAP_NAME, SOURCE_FILE, PRECHANGE_OBJECT))
    return entries


def module_ids_by_method_class(lines):
    """Pre-change module id for each method_class, read from the same object's handbook rows."""
    out = {}
    for line in lines:
        m = re.search(r'id:\s*"([A-Z]\d+\.\d+)"', line)
        c = re.search(r'\bmc:\s*"([A-Za-z0-9_]+)"', line)
        if m and c:
            out.setdefault(c.group(1), m.group(1))
    return out


def historical_aliases():
    """Method classes the CURRENT tree records as historical aliases, not current identities."""
    p = os.path.join(ROOT, "assets", "js", "taxonomy.js")
    text = open(p, encoding="utf-8").read()
    block = re.search(r'LIN_HISTORICAL_METHOD_CLASS\s*=\s*\{(.*?)\n\s*\};', text, re.S)
    if not block:
        return set()
    return set(re.findall(r'"([A-Za-z0-9_]+)"', block.group(1)))


def read_reconciliation():
    with open(RECON, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def build():
    lines = prechange_source()
    entries = extract_raw_entries(lines)
    mods = module_ids_by_method_class(lines)
    aliases = historical_aliases()

    counts = {}
    for e in entries:
        counts[e["key"]] = counts.get(e["key"], 0) + 1

    pop_rows = []
    for e in entries:
        dup = counts[e["key"]] > 1
        pop_rows.append({
            "key": e["key"],
            "value": e["value"],
            "source_file": SOURCE_FILE,
            "source_location": "%s@%s line %d (%s literal)" % (SOURCE_FILE, PRECHANGE_OBJECT[:7], e["line"], MAP_NAME),
            "module_id": mods.get(e["key"], "NONE - no handbook row carries this method_class"),
            "occurrence_count": counts[e["key"]],
            "duplicate": "YES" if dup else "NO",
            "alias_or_historical": "YES" if e["key"] in aliases else "NO",
            "evidence": "extracted from the pinned pre-change git object, not from the current tree",
            "result": "PASS" if not dup else "FAIL - duplicate key in the source literal",
        })

    unique_keys = sorted(counts)
    recon = read_reconciliation()
    recon_keys = [r["client qualifier key"] for r in recon]
    recon_counts = {}
    for k in recon_keys:
        recon_counts[k] = recon_counts.get(k, 0) + 1
    by_key = {r["client qualifier key"]: r for r in recon}

    closure_rows = []
    for k in unique_keys:
        r = by_key.get(k)
        present = r is not None
        cls = r["classification"] if present else "NONE"
        act = r["required action"] if present else "NONE"
        ok = present and cls in {
            "CURRENT_REQUIRED", "WITHDRAWN", "HISTORICAL_ONLY",
            "CURRENT_SERVER_QUALIFIER_MISSING", "BACKWARD_ALIAS_ONLY"} and recon_counts.get(k, 0) == 1
        closure_rows.append({
            "key": k,
            "present_in_reconciliation": "YES" if present else "NO",
            "classification": cls,
            "current_action": act,
            "evidence": "pre-change occurrence count %d; reconciliation row count %d"
                        % (counts[k], recon_counts.get(k, 0)),
            "result": "PASS" if ok else "FAIL",
        })
    for k in sorted(set(recon_keys) - set(unique_keys)):
        closure_rows.append({
            "key": k,
            "present_in_reconciliation": "YES",
            "classification": by_key[k]["classification"],
            "current_action": by_key[k]["required action"],
            "evidence": "EXTRA - not present in the authoritative pre-change population",
            "result": "FAIL",
        })

    def write(path, rows, cols):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    write(POP_CSV, pop_rows, ["key", "value", "source_file", "source_location", "module_id",
                              "occurrence_count", "duplicate", "alias_or_historical",
                              "evidence", "result"])
    write(CLOSURE_CSV, closure_rows, ["key", "present_in_reconciliation", "classification",
                                      "current_action", "evidence", "result"])

    return {
        "raw_entries": len(entries),
        "unique_keys": len(unique_keys),
        "duplicate_keys": sum(1 for k in counts if counts[k] > 1),
        "reconciliation_rows": len(recon),
        "duplicate_reconciliation_rows": sum(1 for k in recon_counts if recon_counts[k] > 1),
        "omitted_keys": sorted(set(unique_keys) - set(recon_keys)),
        "extra_keys": sorted(set(recon_keys) - set(unique_keys)),
        "unclassified": [r["key"] for r in closure_rows if r["classification"] == "NONE"],
        "distribution": {c: recon_keys.count(c) for c in []},
    }


if __name__ == "__main__":
    s = build()
    for k, v in s.items():
        if k == "distribution":
            continue
        print("%-32s %s" % (k, v))
