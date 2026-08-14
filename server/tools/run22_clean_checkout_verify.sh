#!/usr/bin/env bash
# RUN 22 SECTION 17. CLEAN-CHECKOUT REPRODUCIBILITY.
#
# WHY THIS IS MANDATORY. Everything else in this run was measured in a long-lived developer
# working directory that has accumulated untracked files, caches and a database or two across
# twenty-two runs. A release that only passes there is not qualified: the claim is that the
# baseline is reproducible from a named commit, and the only way to know is to take one.
#
# WHAT IT DOES. Creates a git worktree at a named commit in a temporary directory -- which
# contains ONLY committed content, no untracked developer file -- reconstructs the test
# environment from committed configuration alone, and then re-runs the checks that define the
# freeze there: the production and authority tree manifests, the freeze manifest's own digest,
# and the complete suite.
#
# WHAT IT DELIBERATELY DOES NOT DO. It does not install anything from the network and it uses no
# secret and no production credential. The database is a throwaway SQLite file built by
# `alembic upgrade head`, exactly as server/run_all_suites.sh does for every suite.
#
# Usage:  tools/run22_clean_checkout_verify.sh <commit-ish> [output-csv]

set -uo pipefail

COMMIT="${1:?usage: run22_clean_checkout_verify.sh <commit-ish> [output-csv]}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${2:-$REPO/code_audit/run22_clean_checkout_reproducibility.csv}"
WT="$(mktemp -d)/worktree"

row() { printf '%s\n' "\"$1\",\"$2\",\"$3\",\"$4\"" >> "$OUT"; }

echo 'step,command,observed,verdict' > "$OUT"
echo "=== clean checkout of $COMMIT into $WT"

git -C "$REPO" worktree add --detach "$WT" "$COMMIT" >/dev/null 2>&1 || {
  row "create worktree" "git worktree add --detach $WT $COMMIT" "FAILED" "BLOCKED"; exit 1; }
RESOLVED="$(git -C "$WT" rev-parse HEAD)"
row "clean isolated checkout" "git worktree add --detach <tmp> $COMMIT" "$RESOLVED" "PASS"

# Only committed content may be present. An untracked file here would mean the worktree is not
# clean and every result below would be about the developer's directory, not the commit.
UNTRACKED="$(git -C "$WT" status --porcelain --untracked-files=all | wc -l | tr -d ' ')"
if [ "$UNTRACKED" = "0" ]; then
  row "the checkout contains only committed content" "git status --porcelain -uall" "0 entries" "PASS"
else
  row "the checkout contains only committed content" "git status --porcelain -uall" "$UNTRACKED entries" "FAIL"
fi

PY="$(command -v python3)"
row "interpreter, from PATH and not from a developer virtualenv" "command -v python3" "$PY" "PASS"

# --- the freeze manifests, recomputed in the clean checkout
PROD="$(cd "$WT/server/tools" && "$PY" -c "
import production_tree as pt, sys
d = pt.compare()
bad = d['added'] or d['removed'] or d['changed']
print(('DIFFERS ' + str(d)) if bad else ('MATCHES ' + str(len(pt.manifest_lines())) + ' files ' + pt.manifest_sha256()))
" 2>&1 | tail -1)"
case "$PROD" in MATCHES*) V=PASS ;; *) V=FAIL ;; esac
row "production tree manifest verifies in the clean checkout" "production_tree.compare()" "$PROD" "$V"

AUTH="$(cd "$WT/server/tools" && "$PY" -c "
import production_tree as pt
d = pt.compare(None, None, pt.AUTHORITY_ROOTS, pt.PINNED_AUTHORITY)
bad = d['added'] or d['removed'] or d['changed']
print(('DIFFERS ' + str(d)) if bad else ('MATCHES ' + pt.manifest_sha256(None, pt.AUTHORITY_ROOTS)))
" 2>&1 | tail -1)"
case "$AUTH" in MATCHES*) V=PASS ;; *) V=FAIL ;; esac
row "scientific authority manifest verifies in the clean checkout" "production_tree.compare(AUTHORITY_ROOTS)" "$AUTH" "$V"

# --- the freeze manifest's own digest, against the committed companion file
FZ="$WT/research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json"
if [ -f "$FZ" ]; then
  D="$("$PY" -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$FZ")"
  COMP="$WT/research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.sha256"
  if [ -f "$COMP" ]; then
    EXPECT="$(awk '{print $1}' "$COMP" | head -1)"
    [ "$D" = "$EXPECT" ] && V=PASS || V=FAIL
    row "freeze manifest digest matches its committed companion" "sha256 of the freeze json" "$D vs $EXPECT" "$V"
  else
    row "freeze manifest digest" "sha256 of the freeze json" "$D (companion file absent at this commit)" "PENDING FINALISATION"
  fi
else
  row "freeze manifest present" "ls research/freeze/" "absent at this commit" "FAIL"
fi

# --- the complete suite, in the clean checkout, from committed configuration only
echo "=== running the complete suite in the clean checkout (this takes several minutes)"
SUITE_LOG="$WT/../suite.log"
( cd "$WT/server" && ./run_all_suites.sh ) > "$SUITE_LOG" 2>&1
SUITE_RC=$?
LINE="$(grep -E '^Suites run:' "$SUITE_LOG" | tail -1)"
GREEN="$(grep -c '^ALL SUITES GREEN' "$SUITE_LOG")"
if [ "$SUITE_RC" -eq 0 ] && [ "$GREEN" -ge 1 ]; then V=PASS; else V=FAIL; fi
row "complete suite in the clean checkout" "server/run_all_suites.sh" "${LINE:-no summary line} (exit $SUITE_RC)" "$V"
grep -E '^FAIL ' "$SUITE_LOG" | head -20 | while read -r l; do
  row "suite failure detail" "run_all_suites.sh" "$l" "FAIL"
done

cp "$SUITE_LOG" "$REPO/code_audit/run22_clean_checkout_suite.log" 2>/dev/null || true
git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1
echo "=== wrote $OUT"
grep -c ',"FAIL"' "$OUT" >/dev/null && exit 0
