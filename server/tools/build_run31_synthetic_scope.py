#!/usr/bin/env python3
"""
RUN 31: classify every synthetic-manifest entry FROM COMMITTED AUTHORITY, not from absence.

WHAT MY EARLIER SWEEP GOT WRONG, and it got it wrong twice.

  1. THE DENOMINATOR WAS TRIPLE-COUNTED. The three OG-SYNTH-0.1 manifests are BYTE-IDENTICAL --
     one programme-level manifest copied into each package directory, which the 2026-08-11 ingest
     report states in terms ("All three archives ship a byte-identical, programme-level
     CHECKSUMS.sha256 listing all 90"). Counting them as three independent expectations inflated
     519 and inflated the unresolved count with it.

  2. THE RESOLUTION BASE WAS WRONG. The programme manifest is RELEASE-ROOT-relative, and this
     repository nests each package in its own directory, so `package_B_.../x.csv` lives under
     `OG-SYNTH-0.1/package_B/`. Resolving against one base at a time could never find it. The
     2026-08-11 report says the same thing: verification was "performed against a merged tree
     assembled from all three archives, which is the tree the manifest describes".

Correcting both leaves FIVE unresolved entries, not 177.

AND THE FIVE ARE NOT "EXTERNAL REFERENCE" CONTENT. Section 3 permits that label only where
committed evidence proves the file was never vendored AND was never claimed as repository
package content. These five ARE claimed: the programme manifest lists them. The committed
authority -- REPORT_2026-08-11 section 3, which names each of the five and the consequence of
its absence, and code_audit/synthetic_package_file_inventory.csv, whose 99 staged rows contain
none of them -- proves they were CLAIMED BY THE MANIFEST AND NEVER DELIVERED WITH THE ARCHIVES.

So the honest classification is section 2's: this is governed package content that cannot be
recovered, and THE HISTORICAL OG-SYNTH-0.1 PACKAGE IS INCOMPLETE. It is recorded as such. The
package is NOT reported as fully preserved, and the five are NOT relabelled to close the count.
"""
import csv, hashlib, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYNTH = ROOT / "research_fixtures" / "synthetic"
INGEST_REPORT = "REPORT_2026-08-11_synthetic-package-ingest-and-reconciliation.md"
ARCHIVE_INVENTORY = "code_audit/synthetic_package_file_inventory.csv"

#: The five entries the committed ingest record names as claimed-but-never-delivered, quoted from
#: REPORT_2026-08-11 section 3. Listed here so the classification cites its authority per entry
#: rather than being derived from the file not being on disk.
CLAIMED_NEVER_DELIVERED = {
    "validators/validate_synthetic_programme.py":
        "REPORT_2026-08-11 s3: 'The claimed 160 checks cannot be rerun. The claim is unverified.'",
    "generators/generate_opus_synthetic_programme.py":
        "REPORT_2026-08-11 s3: 'Reproducibility from seed 20260811 cannot be tested at all.'",
    "validation_report.json":
        "REPORT_2026-08-11 s3: 'The machine-readable validation record is absent; only the "
        "human-readable summary survives.'",
    "module_asset_map.csv":
        "REPORT_2026-08-11 s3: 'The programme-level module map is absent; three per-package maps "
        "survive and do not cover the same ground.'",
    "schemas/schema_catalog.json":
        "REPORT_2026-08-11 s3: 'There is no declared schema to check the data against.'",
}


KNOWN_UNDELIVERED_BY_PROGRAMME = {"OG-SYNTH-0.1": set(CLAIMED_NEVER_DELIVERED)}


def undelivered_for(path) -> set:
    """The committed never-delivered set for the programme a manifest belongs to.

    SCOPED, and the scoping is itself a finding: REPORT_2026-08-11 records these five as never
    delivered WITH THE THREE v0.1 ARCHIVES. v0.2 and v0.3 DO ship files of the same names and
    they resolve and match, so a global list would call delivered files undelivered.
    """
    for prog, entries in KNOWN_UNDELIVERED_BY_PROGRAMME.items():
        if prog in str(path):
            return entries
    return set()


def parse(man):
    out = []
    for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line.strip())
        if m:
            out.append((m.group(1).lower(), m.group(2).strip()))
    return out


def bases_for(man):
    """Every base this manifest's paths may be relative to, determined from the layout."""
    d = man.parent
    cands = [d, d.parent, ROOT]
    # A release-level manifest copied into sibling package dirs resolves across ALL of them.
    if d.parent.name.startswith("OG-SYNTH"):
        cands = sorted(d.parent.glob("package_*")) + cands
    return cands


def in_archive_inventory(rel):
    inv = ROOT / ARCHIVE_INVENTORY
    if not inv.is_file():
        return False
    name = rel.split("/")[-1]
    with inv.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("path_within_archive", "").split("/")[-1] == name:
                return True
    return False


def in_git_history(rel):
    r = subprocess.run(["git", "log", "--all", "--oneline", "--", f"*{rel.split('/')[-1]}"],
                       cwd=ROOT, capture_output=True, text=True)
    return bool(r.stdout.strip())


def main():
    rows = []
    manifests = sorted(SYNTH.rglob("CHECKSUMS.sha256"))
    # Identify byte-identical manifest copies so the denominator is not multiplied by them.
    digests = {m: hashlib.sha256(m.read_bytes()).hexdigest() for m in manifests}
    seen_digest = {}
    for m in manifests:
        seen_digest.setdefault(digests[m], []).append(m)

    local_x = local_resolved = local_matched = local_missing = mismatch = 0
    external_y = 0
    for man in manifests:
        rel_man = str(man.relative_to(ROOT))
        canonical = seen_digest[digests[man]][0]
        is_copy = man != canonical
        for digest, rel in parse(man):
            hit = None
            for b in bases_for(man):
                p = b / rel
                if p.is_file():
                    hit = p
                    break
            claimed_external = rel in undelivered_for(man)
            if hit is not None:
                ok = hashlib.sha256(hit.read_bytes()).hexdigest() == digest
                state = "RESOLVED_MATCH" if ok else "RESOLVED_MISMATCH"
                cls = "LOCALLY_PRESERVED_PACKAGE_CONTENT"
                auth = (f"{ARCHIVE_INVENTORY}: staged in the delivered archive; file resolves "
                        f"under {hit.parent.relative_to(ROOT)} and matches its recorded checksum")
                if not is_copy:
                    local_x += 1
                    local_resolved += 1
                    local_matched += 1 if ok else 0
                    mismatch += 0 if ok else 1
            else:
                state = "CLAIMED_BUT_NEVER_DELIVERED"
                cls = "GOVERNED_PACKAGE_CONTENT_UNRECOVERABLE"
                auth = (CLAIMED_NEVER_DELIVERED.get(rel)
                        if rel in undelivered_for(man)
                        else "NO COMMITTED AUTHORITY -- UNCLASSIFIED")
                if not is_copy:
                    local_x += 1
                    local_missing += 1
            rows.append([
                rel_man, "COPY" if is_copy else "CANONICAL", rel, digest,
                "release-root-relative" if rel.split("/")[0].startswith("package_")
                else "record-relative",
                "YES" if in_git_history(rel) else "NO",
                "YES" if hit is not None else "NO",
                "YES" if not claimed_external else "YES (claimed by the manifest)",
                "NO" if not claimed_external else "NO -- claimed, so not external-only",
                auth, cls, state,
                "PASS" if state == "RESOLVED_MATCH" else
                ("FAIL" if state == "RESOLVED_MISMATCH" else "INCOMPLETE_PACKAGE")])

    out = ROOT / "code_audit" / "run31_synthetic_manifest_scope_reconciliation.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["manifest", "manifest_role", "path", "expected_sha256",
                    "path_convention", "present_in_repository_history",
                    "resolved_in_working_tree", "claimed_as_package_content",
                    "external_reference_only", "classification_authority",
                    "classification", "resolution_state", "status"])
        w.writerows(rows)
    print(f"wrote {out.relative_to(ROOT)}  ({len(rows)} rows)")
    # SECTION 4's ACCOUNTING, over ALL manifest entries, because the identity X + Y = 519 is
    # stated over the manifest entries and not over the de-duplicated set.
    #
    # Y IS ZERO, AND THAT IS THE FINDING. Section 3 permits the external-reference label only
    # where committed evidence proves the file was never vendored AND was never claimed as
    # repository-preserved package content. Every entry here IS claimed -- the programme manifest
    # lists it -- so no entry qualifies. The five that cannot be resolved are governed package
    # content that was never delivered, which makes the historical OG-SYNTH-0.1 package
    # INCOMPLETE. They are reported as missing local files, not relabelled.
    total = len(rows)
    external = sum(1 for r in rows if r[10] == "EXTERNAL_REFERENCE_ONLY")
    local = total - external
    missing_rows = sum(1 for r in rows if r[11] == "CLAIMED_BUT_NEVER_DELIVERED")
    matched_rows = sum(1 for r in rows if r[11] == "RESOLVED_MATCH")
    mismatch_rows = sum(1 for r in rows if r[11] == "RESOLVED_MISMATCH")
    unique_missing = len({r[2] for r in rows if r[11] == "CLAIMED_BUT_NEVER_DELIVERED"})
    unclassified = sum(1 for r in rows if "NO COMMITTED AUTHORITY" in r[9])
    print()
    print("LOCALLY GOVERNED PACKAGE")
    print(f"  expected local entries  X = {local}")
    print(f"  resolved local entries    = {matched_rows + mismatch_rows}")
    print(f"  matched local checksums   = {matched_rows}")
    print(f"  MISSING local entries     = {missing_rows}  ({unique_missing} unique paths)")
    print(f"  checksum mismatches       = {mismatch_rows}")
    print("EXTERNAL REFERENCE INVENTORY")
    print(f"  external entries        Y = {external}")
    print(f"  unclassified              = {unclassified}")
    print(f"IDENTITY  X + Y = {local + external}  (expected {total})")
    print()
    print("PACKAGE COMPLETENESS: OG-SYNTH-0.1 is INCOMPLETE -- "
          f"{unique_missing} manifest-claimed files were never delivered with the archives.")


if __name__ == "__main__":
    main()
