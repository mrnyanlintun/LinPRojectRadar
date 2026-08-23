#!/usr/bin/env bash
# Runs every server/tools/test_*.py suite, each against its OWN freshly migrated SQLite db —
# per the repo convention documented in T6_HANDOFF.md ("Build a throwaway sqlite with
# `alembic upgrade head` and copy it per suite"). A stale/shared db silently swallows failures
# (KeyError, no RESULT: line) so this never reuses one across files.
set -uo pipefail
cd "$(dirname "$0")"

VENV_PY=".venv/bin/python"
# Fall back to the interpreter on PATH when there is no project virtualenv. A checkout that
# already has the pinned dependencies installed system-wide must still be able to run the
# suites; without this the loop silently ran every file with a non-existent interpreter.
[ -x "$VENV_PY" ] || VENV_PY="$(command -v python3)"
TMPDIR="$(mktemp -d)"
TEMPLATE_DB="$TMPDIR/template.db"

export SESSION_SECRET="test-secret-do-not-use-in-prod"

echo "Building migrated template db at $TEMPLATE_DB ..."
DATABASE_URL="sqlite:///$TEMPLATE_DB" "$VENV_PY" -m alembic upgrade head >/tmp/alembic_out.log 2>&1
if [ $? -ne 0 ]; then
  echo "alembic upgrade head FAILED:"; cat /tmp/alembic_out.log; exit 1
fi

TOTAL_PASS=0
TOTAL_CHECKS=0
FAILED_SUITES=()
SUITE_COUNT=0
DIRTY_SUITES=()

# --- RUN 54, PHASE A: THE RUNNER FAILS WHEN A SUITE LEAVES THE TREE DIRTY --------------------
# Run 52 found three guards in server/app/simulation/canonical_v8.py replaced by `if False:`,
# left by a fault campaign that died between injecting and restoring. Five runs missed it
# because the NEXT campaign snapshotted the corruption from disk, faithfully restored it, and
# its own assertion then CERTIFIED it. Nothing was failing. So the runner now checks the tree
# after EVERY suite, not just after campaigns, and names the offending paths.
#
# Scope: production and client source only. code_audit/ artifacts are declared suite outputs --
# Run 52 saw 26 of them rewritten by a single pass -- and are restored by the session, not by
# the runner. Excluding them is what makes the check runnable at all; it never exempts the leak
# class, because a fault injection lands in server/app, assets or research, never in code_audit.
PROD_DIRT() { git -C .. status --porcelain -- \
    server/app assets index.html research tests.html 2>/dev/null; }
BASELINE_DIRT="$(PROD_DIRT)"

for f in tools/test_*.py; do
  SUITE_COUNT=$((SUITE_COUNT+1))
  DB="$TMPDIR/$(basename "$f").db"
  cp "$TEMPLATE_DB" "$DB"
  case "$VENV_PY" in /*) PY="$VENV_PY" ;; *) PY="../$VENV_PY" ;; esac
  OUT=$(cd tools && DATABASE_URL="sqlite:///$DB" SESSION_SECRET="$SESSION_SECRET" PYTHONIOENCODING=utf-8 "$PY" "$(basename "$f")" 2>&1)
  RC=$?
  # Canonical RESULT line only: "RESULT: <passed>/<total> checks passed". Prose summaries
  # ("34 passed, 0 failed") are NOT accepted — a suite that crashes before printing this,
  # or that prints its own wording, must fail the runner rather than look clean.
  RESULT_LINE=$(echo "$OUT" | grep -E "^RESULT: [0-9]+/[0-9]+( checks passed)?$" | tail -1)
  if [ -z "$RESULT_LINE" ]; then
    FAILED_SUITES+=("$f: NO CANONICAL RESULT LINE (exit $RC)")
    echo "FAIL  $f  (no canonical RESULT: line, exit $RC — see below)"
    echo "$OUT" | tail -20
  else
    NUMS=$(echo "$RESULT_LINE" | grep -oE "[0-9]+/[0-9]+" | tail -1)
    PASS=$(echo "$NUMS" | cut -d/ -f1)
    TOT=$(echo "$NUMS" | cut -d/ -f2)
    TOTAL_PASS=$((TOTAL_PASS+PASS))
    TOTAL_CHECKS=$((TOTAL_CHECKS+TOT))
    if [ "$PASS" != "$TOT" ]; then
      FAILED_SUITES+=("$f: $NUMS")
      echo "FAIL  $f  $NUMS"
    elif [ "$RC" -ne 0 ]; then
      # Green result line but a nonzero exit means the process died after reporting.
      FAILED_SUITES+=("$f: $NUMS but exit $RC")
      echo "FAIL  $f  $NUMS but exit $RC"
    else
      echo "ok    $f  $NUMS"
    fi
  fi

  # THE DIRTY-TREE CHECK, after this suite. A suite that leaves a fault in production or client
  # source fails the runner even when every one of its own checks passed -- which is exactly the
  # case that survived five runs.
  NOW_DIRT="$(PROD_DIRT)"
  if [ "$NOW_DIRT" != "$BASELINE_DIRT" ]; then
    DIRTY_SUITES+=("$f")
    FAILED_SUITES+=("$f: LEFT PRODUCTION/CLIENT SOURCE DIRTY")
    echo "FAIL  $f  LEFT THE TREE DIRTY -- a fault is on disk:"
    echo "$NOW_DIRT" | sed 's/^/        /'
    echo "        Restore before running anything else: the next campaign will SNAPSHOT this."
    BASELINE_DIRT="$NOW_DIRT"
  fi
done

echo ""
echo "===================================================="
echo "Suites run: $SUITE_COUNT   Total checks: $TOTAL_PASS/$TOTAL_CHECKS"
if [ ${#DIRTY_SUITES[@]} -gt 0 ]; then
  echo "SUITES THAT LEFT PRODUCTION/CLIENT SOURCE DIRTY:"
  printf '  %s\n' "${DIRTY_SUITES[@]}"
fi
if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
  echo "FAILED SUITES:"
  printf '  %s\n' "${FAILED_SUITES[@]}"
  exit 1
fi
echo "ALL SUITES GREEN"
rm -rf "$TMPDIR"
