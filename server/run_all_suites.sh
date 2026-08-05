#!/usr/bin/env bash
# Runs every server/tools/test_*.py suite, each against its OWN freshly migrated SQLite db —
# per the repo convention documented in T6_HANDOFF.md ("Build a throwaway sqlite with
# `alembic upgrade head` and copy it per suite"). A stale/shared db silently swallows failures
# (KeyError, no RESULT: line) so this never reuses one across files.
set -uo pipefail
cd "$(dirname "$0")"

VENV_PY=".venv/bin/python"
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

for f in tools/test_*.py; do
  SUITE_COUNT=$((SUITE_COUNT+1))
  DB="$TMPDIR/$(basename "$f").db"
  cp "$TEMPLATE_DB" "$DB"
  OUT=$(cd tools && DATABASE_URL="sqlite:///$DB" SESSION_SECRET="$SESSION_SECRET" ../"$VENV_PY" "$(basename "$f")" 2>&1)
  RESULT_LINE=$(echo "$OUT" | grep -E "RESULT:|^[0-9]+/[0-9]+" | tail -1)
  if echo "$OUT" | grep -qE "RESULT:.*[0-9]+/[0-9]+"; then
    NUMS=$(echo "$OUT" | grep -oE "RESULT:.*" | tail -1 | grep -oE "[0-9]+/[0-9]+" | tail -1)
    PASS=$(echo "$NUMS" | cut -d/ -f1)
    TOT=$(echo "$NUMS" | cut -d/ -f2)
    TOTAL_PASS=$((TOTAL_PASS+PASS))
    TOTAL_CHECKS=$((TOTAL_CHECKS+TOT))
    if [ "$PASS" != "$TOT" ]; then
      FAILED_SUITES+=("$f: $NUMS")
      echo "FAIL  $f  $NUMS"
    else
      echo "ok    $f  $NUMS"
    fi
  else
    FAILED_SUITES+=("$f: NO RESULT LINE")
    echo "FAIL  $f  (no RESULT: line — see below)"
    echo "$OUT" | tail -20
  fi
done

echo ""
echo "===================================================="
echo "Suites run: $SUITE_COUNT   Total checks: $TOTAL_PASS/$TOTAL_CHECKS"
if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
  echo "FAILED SUITES:"
  printf '  %s\n' "${FAILED_SUITES[@]}"
  exit 1
fi
echo "ALL SUITES GREEN"
rm -rf "$TMPDIR"
