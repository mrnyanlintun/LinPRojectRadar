#!/usr/bin/env python3
"""Generator reproducibility proof for OG-SYNTH-0.2.

Builds the programme twice from the bundled v0.1 base archive, into two
different temporary output paths, and compares file sets, file bytes, the
combined ZIP and the three package ZIPs. Different output paths and a delay
between the runs are deliberate: they expose output-path and current-time
dependence. Filesystem-order dependence is exposed by comparing the two
independently walked trees.

The authoritative staged copy is never written to.

Writes code_audit/synthetic_v02_reproducibility.csv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2"
BUILDER = ROOT / "generators/build_opus_synthetic_programme_v0_2.py"
BASE = ROOT / "generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): sha256(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def build(workdir: Path, tag: str) -> dict[str, Path]:
    out = workdir / f"build_{tag}" / "Opus_Gubernatio_Synthetic_Programme_v0.2"
    zips = workdir / f"zips_{tag}"
    zips.mkdir(parents=True, exist_ok=True)
    combined = zips / "Opus_Gubernatio_Synthetic_Programme_v0.2.zip"
    result = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--base-zip",
            str(BASE),
            "--output-root",
            str(out),
            "--combined-zip",
            str(combined),
            "--separate-dir",
            str(zips),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"build {tag} failed:\n{result.stdout}\n{result.stderr}")
    return {"root": out, "combined": combined, "zips": zips}


def main() -> int:
    rows: list[dict[str, str]] = []

    def record(check: str, ok: bool, detail: str) -> None:
        rows.append({"check": check, "result": "PASS" if ok else "FAIL", "detail": detail[:400]})

    with tempfile.TemporaryDirectory(prefix="og-synth-repro-") as tmp:
        work = Path(tmp)
        first = build(work, "one")
        time.sleep(65)  # cross a minute boundary: exposes current-time dependence
        second = build(work, "two")

        tree_one, tree_two = tree(first["root"]), tree(second["root"])
        record(
            "same_file_set",
            set(tree_one) == set(tree_two),
            f"{len(tree_one)} vs {len(tree_two)} files; "
            f"only-in-first={sorted(set(tree_one) - set(tree_two))[:5]} "
            f"only-in-second={sorted(set(tree_two) - set(tree_one))[:5]}",
        )
        differing = [k for k in tree_one if tree_two.get(k) != tree_one[k]]
        record(
            "byte_identical_file_contents",
            not differing,
            f"{len(tree_one)} files compared; differing={differing[:8]}",
        )

        combined_one, combined_two = sha256(first["combined"]), sha256(second["combined"])
        record(
            "byte_identical_combined_zip",
            combined_one == combined_two,
            f"{combined_one} vs {combined_two}",
        )
        for name in (
            "Opus_Gubernatio_Package_A_Project_Structures_v0.2.zip",
            "Opus_Gubernatio_Package_B_Reference_Training_Decisions_v0.2.zip",
            "Opus_Gubernatio_Package_C_Optional_Activation_Lab_v0.2.zip",
        ):
            a, b = sha256(first["zips"] / name), sha256(second["zips"] / name)
            record(f"byte_identical_package_zip:{name}", a == b, f"{a} vs {b}")

        record(
            "no_output_path_dependence",
            not differing and combined_one == combined_two,
            "two different output roots and two different zip directories produced identical bytes",
        )
        record(
            "no_current_time_dependence",
            not differing,
            "the two builds were separated by more than a minute",
        )
        record(
            "no_filesystem_order_dependence",
            not differing,
            "each tree was walked and hashed independently and compared by relative path",
        )

        # Regenerated tree against the authoritative staged extraction.
        staged = tree(ROOT)
        common = set(staged) & set(tree_one)
        drift = [k for k in sorted(common) if staged[k] != tree_one[k]]
        record(
            "regenerated_tree_matches_staged_extraction",
            not drift and set(staged) == set(tree_one),
            f"{len(common)} common files; drift={drift[:8]}; "
            f"only-staged={sorted(set(staged) - set(tree_one))[:5]}; "
            f"only-rebuilt={sorted(set(tree_one) - set(staged))[:5]}",
        )

        supplied = Path(
            "/root/.claude/uploads/56ab0a7f-4e21-5061-8b33-396724907fe8/"
            "8b95c88e-Opus_Gubernatio_Synthetic_Programme_v0.2.zip"
        )
        if supplied.exists():
            record(
                "rebuilt_combined_zip_matches_supplied_archive",
                sha256(supplied) == combined_one,
                f"supplied={sha256(supplied)} rebuilt={combined_one}",
            )

        try:
            import lxml.etree  # noqa: F401

            lxml_present = True
        except Exception:  # noqa: BLE001
            lxml_present = False
        record(
            "note_lxml_pinned_in_requirements_lock",
            "lxml" in (ROOT / "requirements-lock.txt").read_text(encoding="utf-8"),
            "openpyxl serialises the workbook differently with and without lxml, so the "
            f"workbook is only byte-reproducible when lxml presence matches (present here: {lxml_present})",
        )

        provenance = json.loads((ROOT / "BUILD_PROVENANCE.json").read_text(encoding="utf-8"))
        record(
            "recorded_seed_20260811",
            provenance.get("random_seed") == 20260811,
            str(provenance.get("random_seed")),
        )
        record(
            "builder_checksum_matches_provenance",
            provenance.get("builder_sha256") == sha256(BUILDER),
            sha256(BUILDER),
        )
        record(
            "base_archive_checksum_matches_provenance",
            provenance.get("base_archive_sha256") == sha256(BASE),
            sha256(BASE),
        )
        record(
            "validator_checksum_matches_provenance",
            provenance.get("validator_sha256")
            == sha256(ROOT / "generators/validate_synthetic_programme_v0_2.py"),
            sha256(ROOT / "generators/validate_synthetic_programme_v0_2.py"),
        )

    out = REPO / "code_audit/synthetic_v02_reproducibility.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "result", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    failed = [r for r in rows if r["result"] == "FAIL"]
    for r in failed:
        print(f"FAIL {r['check']}: {r['detail']}")
    print(json.dumps({"checks": len(rows), "failed": len(failed)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
