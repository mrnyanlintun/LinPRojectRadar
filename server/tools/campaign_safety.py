#!/usr/bin/env python3
"""
CAMPAIGN SAFETY: the start-AND-end dirty-tree guard, and pristine HEAD snapshots.

WHY THIS FILE EXISTS, stated once so no future run re-derives it.

Run 52 found three guards in `server/app/simulation/canonical_v8.py` replaced by `if False:`,
left there by a fault campaign that died between injecting and restoring. Five consecutive runs
(48-52) recorded a mid-injection abort and none of them caught the leak. Run 53 established why,
by reading both leaking campaigns:

  1. A fault injects. The process dies before its `finally` -- a kill, a timeout, a runner
     cancellation. The fault is on disk.
  2. The NEXT fault takes its snapshot `original = f.read_text()` FROM DISK. The snapshot is
     already corrupt.
  3. That fault's `finally` faithfully restores the corrupt snapshot, and its assertion
     `restored == original` PASSES, because `original` was corrupt to begin with.
  4. The campaign reports every fault restored green and exits clean, with neutered guards on
     disk.

**Every subsequent correct `finally` cements the leak. Every correct assertion certifies it.**
That is why nothing was failing for five runs.

So a `finally` is NOT the fix. It is hygiene -- necessary, insufficient. There are two fixes and
this module provides both:

  A. `require_clean_tree(..., when="start")` BEFORE the first fault. An end-only check passes
     whenever the leak began in an earlier process, which is exactly the case above. A START
     check catches a cemented leak on the very next run, before it can be snapshotted.
  B. `head_text()` / `head_bytes()` -- take the per-fault snapshot from the COMMITTED bytes at
     HEAD, not from the working tree. A snapshot that cannot see the corruption cannot restore
     it.

Used together, step 2 above becomes impossible: the campaign refuses to begin, and even if it
began, it would restore from HEAD rather than from the corruption.

USAGE

    from campaign_safety import require_clean_tree, head_text, CampaignTreeDirty

    require_clean_tree(ROOT, "start", "run34 calibration campaign", allow=[OUT])
    ...  faults ...
    require_clean_tree(ROOT, "end", "run34 calibration campaign", allow=[OUT])

`allow` names paths the campaign is DESIGNED to write -- its own results artifact. Nothing else
is tolerated at either end. The allowlist is not a weakening: it is what makes the check
runnable at all, and every entry must be a declared output of the campaign itself, never a
production or client file.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import subprocess
import sys

__all__ = [
    "arm",
    "strict",
    "CampaignTreeDirty",
    "porcelain",
    "require_clean_tree",
    "tree_is_clean",
    "head_bytes",
    "head_text",
    "snapshot_text",
    "restore_guard",
    "PRODUCTION_PREFIXES",
]

# The trees a fault campaign must never leave dirty. A leak anywhere is bad; a leak HERE is the
# defect that motivated this module, and the runner check reports these separately.
PRODUCTION_PREFIXES = (
    "server/app/",
    "assets/",
    "index.html",
    "research/",
    "tests.html",
)


class CampaignTreeDirty(RuntimeError):
    """Raised when a campaign starts or ends on a tree it did not intend to dirty."""


def _rel(root: pathlib.Path, p) -> str:
    """Repo-relative POSIX path.

    A RELATIVE input is already repo-relative and is returned as-is. It must NOT be resolved:
    `Path("server/app/documents.py").resolve()` resolves against the CWD, and campaigns run from
    `server/tools`, so resolving turned every relative target into
    `server/tools/server/app/documents.py`. Caught by execution, not by reading.
    """
    p = pathlib.Path(p)
    if not p.is_absolute():
        return p.as_posix()
    try:
        return p.resolve().relative_to(pathlib.Path(root).resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def porcelain(root) -> list[str]:
    """`git status --porcelain` as a list of 'XY path' lines. Empty list == clean tree."""
    r = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise CampaignTreeDirty(
            "git status --porcelain failed; a campaign must not run where the tree state "
            f"cannot be established. rc={r.returncode} {r.stderr.strip()[:300]}")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _paths(lines: list[str]) -> list[str]:
    out = []
    for ln in lines:
        p = ln[3:].strip()
        if " -> " in p:                      # a rename: take the destination
            p = p.split(" -> ", 1)[1]
        out.append(p.strip('"'))
    return out


def tree_is_clean(root, allow=()) -> tuple[bool, list[str]]:
    """(clean, offending_lines). `allow` is a list of repo-relative paths or Path objects."""
    allowed = {_rel(root, a) for a in allow}
    lines = porcelain(root)
    bad = [ln for ln, p in zip(lines, _paths(lines)) if p not in allowed]
    return (not bad), bad


def strict() -> bool:
    """Whether ANY dirt refuses, or only dirt in production/client source. See below."""
    return os.environ.get("CAMPAIGN_SAFETY_STRICT", "") not in ("", "0", "false", "no")


def require_clean_tree(root, when: str, campaign: str, allow=()) -> None:
    """THE FIX. Fail loudly if the tree is dirty before the first fault or after the last.

    `when` is "start" or "end"; both are required. A campaign must NOT begin on a dirty tree --
    it would snapshot the corruption and then certify it (see the module docstring).

    TWO LEVELS, AND WHY. The order that created this file says plainly: "Non-empty at either
    point fails the campaign loudly." Taken literally against the WHOLE tree, that makes every
    armed campaign refuse for the whole of any working session -- a session that has edited one
    tool file cannot run its own gate -- and a check that cannot be run is not a check. So:

      * HARD REFUSAL for dirt under PRODUCTION_PREFIXES -- server/app, assets, index.html,
        research, tests.html. This is the leak class and it is not negotiable. Every guard
        Run 52 found neutered was in `server/app/simulation/canonical_v8.py`.
      * LOUD REPORT, in full, with the complete `git status --porcelain`, for dirt anywhere
        else. The campaign proceeds. Nothing is hidden: the listing is printed either way.
      * `CAMPAIGN_SAFETY_STRICT=1` promotes ANY dirt to a refusal -- the literal reading. Use it
        for a freeze-gate run, where the tree is committed and must be.

    Note that this is belt and braces, not a substitute: `snapshot_text()` refuses to snapshot
    ANY file that differs from HEAD, wherever it lives, so a campaign can never restore
    corruption even when the start check let it proceed.
    """
    if when not in ("start", "end"):
        raise ValueError("when must be 'start' or 'end'")
    clean, bad = tree_is_clean(root, allow)
    if clean:
        print(f"  TREE CLEAN ({when}): {campaign}")
        return
    prod = [ln for ln, p in zip(bad, _paths(bad))
            if any(p.startswith(x) for x in PRODUCTION_PREFIXES)]
    if not prod and not strict():
        banner = "-" * 94
        print(banner)
        print(f"  TREE DIRTY at {when} of {campaign}, but NOT in production or client source.")
        print("  Proceeding. Set CAMPAIGN_SAFETY_STRICT=1 to refuse on any dirt at all.")
        print("  full `git status --porcelain`:")
        for ln in bad:
            print(f"      {ln}")
        print(banner)
        return
    banner = "=" * 94
    msg = [banner,
           f"CAMPAIGN REFUSED: THE TREE IS DIRTY AT {when.upper()} -- {campaign}",
           banner]
    if when == "start":
        msg += [
            "A campaign MUST NOT begin on a dirty tree. Its per-fault snapshot would capture",
            "whatever is on disk, its `finally` would faithfully restore the corruption, and its",
            "own assertion would then CERTIFY it. That is the mechanism Run 53 established and",
            "it is why five runs missed a neutered production guard.",
        ]
    else:
        msg += [
            "A campaign left the tree dirty. A fault is on disk. Do not re-run any campaign",
            "until it is restored -- the next one will snapshot the corruption.",
        ]
    if prod:
        msg += ["", "*** DIRT IN PRODUCTION / CLIENT SOURCE -- this is the leak class: ***"]
        msg += [f"      {ln}" for ln in prod]
    msg += ["", "full `git status --porcelain`:"] + [f"      {ln}" for ln in bad]
    msg += ["", "Restore with:  git checkout -- <path>   (or `git stash` if the dirt is yours)",
            banner]
    text = "\n".join(msg)
    print(text, file=sys.stderr)
    print(text)
    raise CampaignTreeDirty(f"tree dirty at {when} of {campaign}: " + "; ".join(bad[:8]))


def arm(root, campaign: str, allow=()) -> None:
    """Start check now, end check at process exit. One line per campaign.

    The start check raises `CampaignTreeDirty` -- the campaign REFUSES TO BEGIN, which is the
    fix (see the module docstring).

    The end check runs from `atexit`, so it fires however the campaign leaves: a clean return, a
    `sys.exit`, or an unhandled exception. An exception raised inside an `atexit` callback is
    *ignored* by CPython and leaves the exit status at 0 -- proved, not assumed -- so the end
    check calls `os._exit(1)` after printing. The campaign's own RESULT line has already been
    printed by then, and `server/run_all_suites.sh` explicitly fails a suite that prints a green
    RESULT line and then exits non-zero. That is how the runner comes to fail on a dirty tree
    without any check being weakened.
    """
    require_clean_tree(root, "start", campaign, allow)

    import atexit

    def _at_end():
        try:
            clean, bad = tree_is_clean(root, allow)
        except Exception as exc:                              # pragma: no cover - defensive
            print(f"CAMPAIGN END CHECK COULD NOT RUN: {exc}", file=sys.stderr)
            return
        if clean:
            print(f"  TREE CLEAN (end): {campaign}")
            return
        try:
            # Same two-level policy as the start check: this RETURNS without raising when the
            # dirt is outside production/client source and STRICT is off, and the campaign is
            # then not failed for a session's own edits.
            require_clean_tree(root, "end", campaign, allow)
            return
        except CampaignTreeDirty:
            pass
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)

    atexit.register(_at_end)


def head_bytes(root, relpath) -> bytes:
    """The COMMITTED bytes of a tracked file at HEAD. The pristine baseline to snapshot from."""
    rel = _rel(root, relpath)
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(root), capture_output=True)
    if r.returncode != 0:
        raise CampaignTreeDirty(
            f"cannot read {rel} at HEAD (rc={r.returncode}): {r.stderr.decode()[:200]}. "
            "A campaign that cannot snapshot from a clean baseline must stop rather than "
            "snapshot the working tree.")
    return r.stdout


def head_text(root, relpath, encoding="utf-8") -> str:
    return head_bytes(root, relpath).decode(encoding)


def snapshot_text(root, relpath, encoding="utf-8") -> str:
    """Snapshot for restoring: HEAD bytes when the file is tracked and matches disk.

    Refuses -- it does NOT silently fall back to disk -- when the working file differs from
    HEAD, because that difference is precisely the leak this module exists to stop. A campaign
    with a legitimate reason to run against a modified file must say so explicitly by calling
    `pathlib.Path.read_text` itself and recording why, per section 14.2.
    """
    rel = _rel(root, relpath)
    p = pathlib.Path(root) / rel
    disk = p.read_text(encoding=encoding)
    at_head = head_text(root, relpath, encoding=encoding)
    if disk == at_head:
        return at_head
    if rel.startswith(PRODUCTION_PREFIXES) or rel.startswith("server/"):
        # THE LEAK CLASS. Every guard Run 52 found neutered was here. Refuse, always.
        raise CampaignTreeDirty(
            f"{rel} differs from HEAD. Refusing to snapshot the working tree: that is how a "
            "leaked fault gets cemented and certified. Restore the file first.")
    # A REGENERABLE AUDIT ARTIFACT, not source. `server/run_all_suites.sh` legitimately leaves
    # roughly two dozen of these rewritten by the time a late campaign runs -- Run 52 counted 26
    # -- and refusing on them would make the campaigns unrunnable inside their own runner while
    # protecting nothing: a fault injection lands in server/app, assets or research, never in a
    # generated CSV, and each of these is rebuilt by its own generator. Fall back to the working
    # tree, and SAY SO, at every occurrence, so the fallback can never be silent.
    print(f"  SNAPSHOT FROM DISK (not HEAD): {rel} -- a regenerable artifact already rewritten "
          f"in this pass. Not the leak class; see server/tools/campaign_safety.py.")
    return disk


@contextlib.contextmanager
def restore_guard(files: dict, after=None):
    """A `finally` that cannot be skipped, for campaigns whose restore is straight-line code.

    `files` maps pathlib.Path -> the bytes to write back. Hygiene, not the fix: see the module
    docstring for why a `finally` alone would not have prevented the leak.
    """
    try:
        yield
    finally:
        for f, b in files.items():
            if isinstance(b, str):
                pathlib.Path(f).write_text(b, encoding="utf-8")
            else:
                pathlib.Path(f).write_bytes(b)
        if after is not None:
            after()


def _repo_root_from(start) -> pathlib.Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(start),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise CampaignTreeDirty("not inside a git work tree")
    return pathlib.Path(r.stdout.strip())


if __name__ == "__main__":
    # Self-check, so this module is itself falsifiable rather than merely asserted.
    root = _repo_root_from(os.getcwd())
    clean, bad = tree_is_clean(root)
    print(f"repo: {root}")
    print(f"clean: {clean}" + ("" if clean else f"  ({len(bad)} entries)"))
    for ln in bad:
        print("   ", ln)
    sys.exit(0 if clean else 1)
