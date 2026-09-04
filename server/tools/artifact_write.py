"""
RUN 135C, M14. WHERE A GENERATOR WRITES, AND WHY IT IS NO LONGER THE COMMITTED FILE.

THE DEFECT. Executing a generator rewrote its committed artefact in place. Twenty-one
`code_audit/*.csv`, one `research/freeze/*.csv` and the two study manifests went dirty simply by
being run, and four values changed while a read-only hunt was merely LOOKING at them. The Run 135
hunt dirtied the tree three times without meaning to change anything, and the two study manifests
regenerate at v68 / v26 against a committed v25 / v13 -- so a casual run silently proposes a new
launch identity. Sealed evidence that rewrites itself when observed is not sealed.

THE RULE. A generator writes to a scratch path by DEFAULT. Overwriting the committed artefact is a
deliberate act and must be asked for:

    python tools/<generator>.py                     -> writes under the scratch root, prints both
                                                       paths and whether the bytes differ
    python tools/<generator>.py --write-artifact    -> overwrites the committed artefact

This keeps deliberate re-baselining -- which this programme does often and should -- and removes
the accidental rewrite, which nobody ever wanted. The environment variable RUN135_WRITE_ARTIFACT=1
is honoured as well, for a shell loop that means it.

THE SCRATCH ROOT is $RUN135_ARTIFACT_SCRATCH if set, else <repo>/.artifact_scratch, and the
artefact's path below the repository root is preserved inside it, so a generator that writes
code_audit/x.csv writes .artifact_scratch/code_audit/x.csv and nothing collides.
"""
from __future__ import annotations

import os
import pathlib
import sys

__all__ = ["writing_committed_artifact", "artifact_target", "report_artifact_write",
           "repo_root", "artifact_out"]


def writing_committed_artifact(argv: list[str] | None = None) -> bool:
    """True when the caller has explicitly asked to overwrite the committed artefact."""
    argv = sys.argv if argv is None else argv
    if "--write-artifact" in argv:
        return True
    return os.environ.get("RUN135_WRITE_ARTIFACT", "").strip() in ("1", "true", "TRUE", "yes")


def scratch_root(repo_root: pathlib.Path) -> pathlib.Path:
    env = os.environ.get("RUN135_ARTIFACT_SCRATCH", "").strip()
    return pathlib.Path(env) if env else (repo_root / ".artifact_scratch")


def artifact_target(committed: pathlib.Path, repo_root: pathlib.Path,
                    argv: list[str] | None = None) -> pathlib.Path:
    """
    The path this run should write to.

    `committed` is where the artefact lives in the repository. Returns `committed` itself only
    when --write-artifact (or RUN135_WRITE_ARTIFACT=1) was given; otherwise the mirrored path
    under the scratch root, whose parent directories are created.
    """
    committed = pathlib.Path(committed)
    if writing_committed_artifact(argv):
        committed.parent.mkdir(parents=True, exist_ok=True)
        return committed
    try:
        rel = committed.resolve().relative_to(pathlib.Path(repo_root).resolve())
    except ValueError:
        rel = pathlib.Path(committed.name)
    target = scratch_root(pathlib.Path(repo_root)) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def report_artifact_write(committed: pathlib.Path, written: pathlib.Path) -> None:
    """Say where the bytes went and, when they went to scratch, whether they differ."""
    committed, written = pathlib.Path(committed), pathlib.Path(written)
    if committed == written:
        print(f"  WROTE THE COMMITTED ARTEFACT (--write-artifact): {committed}")
        return
    same = (committed.exists()
            and committed.read_bytes() == written.read_bytes())
    print(f"  wrote {written}")
    print(f"  the committed artefact {committed} was NOT touched; "
          + ("it is byte-identical to what this run produced"
             if same else
             "IT DIFFERS from what this run produced -- re-run with --write-artifact to "
             "re-baseline it deliberately"))


# -------------------------------------------------------------------------------------------------
# RUN 136, F10. THE ZERO-CONFIGURATION FORM.
#
# `artifact_target` needs the repository root passed in, which suited the two Run 135C generators
# that already had one to hand. Routing the REST of the fleet meant threading a root through
# scripts that compute their paths a dozen different ways, and every thread is a chance to point
# one at the wrong place. `artifact_out` finds the root itself, so routing a write site is a
# one-token wrap at the point of the write:
#
#     out = ROOT / "code_audit" / "x.csv"        ->   out = artifact_out(ROOT / "code_audit" / "x.csv")
#
# THIS IS NOT A SECOND MECHANISM. It is the same flag (--write-artifact), the same environment
# variables (RUN135_WRITE_ARTIFACT, RUN135_ARTIFACT_SCRATCH), the same scratch root and the same
# mirrored layout; `artifact_out` is a thin call through `artifact_target`.
# -------------------------------------------------------------------------------------------------


def repo_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """The repository root: the nearest ancestor holding a `.git` entry.

    Falls back to two levels above this file (`server/tools/..` -> repo root), which is where
    this module has always lived, so a checkout without `.git` -- an export, a tarball -- still
    routes to the right place instead of raising.
    """
    here = pathlib.Path(start or __file__).resolve()
    for d in (here, *here.parents):
        if (d / ".git").exists():
            return d
    return pathlib.Path(__file__).resolve().parent.parent.parent


def artifact_out(committed, argv: list[str] | None = None) -> pathlib.Path:
    """Where THIS run should write `committed`: scratch by default, the file itself on request."""
    committed = pathlib.Path(committed)
    return artifact_target(committed, repo_root(committed), argv)
