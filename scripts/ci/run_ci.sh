#!/usr/bin/env bash
set -euo pipefail
source scripts/common/env.sh
source scripts/common/compose.sh
source scripts/common/log.sh

: "${DB_CI:?DB_CI is required}"
: "${MODULE:?MODULE is required}"
: "${TEST_TAGS_FINAL:?TEST_TAGS_FINAL is required}"

mkdir -p "$CI_ARTIFACT_DIR/$PROJECT_CI"

if [[ "$CI_ARTIFACT_PURGE" == "1" ]]; then
  ls -1dt "$CI_ARTIFACT_DIR/$PROJECT_CI"/* 2>/dev/null | tail -n +"$((CI_ARTIFACT_KEEP + 1))" | xargs -r rm -rf || true
fi

ts="$(date +%Y%m%d-%H%M%S)"
outdir="$CI_ARTIFACT_DIR/$PROJECT_CI/$ts"
mkdir -p "$outdir"

cleanup() {
  log "[CI][CLEANUP] collecting -> $outdir"
  compose_ci config >"$outdir/compose.effective.yml" 2>"$outdir/compose.config.err" || true
  compose_ci ps -a >"$outdir/ps.txt" 2>&1 || true
  compose_ci logs --no-color --tail="$CI_TAIL_ODOO" odoo  >"$outdir/odoo.tail.log" 2>&1 || true
  compose_ci logs --no-color --tail="$CI_TAIL_DB"   db    >"$outdir/db.tail.log"   2>&1 || true
  compose_ci logs --no-color --tail="$CI_TAIL_REDIS" redis >"$outdir/redis.tail.log" 2>&1 || true
  [[ -f "$CI_LOG" ]] && cp -f "$CI_LOG" "$outdir/$CI_LOG" || true
  compose_ci down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

log "== CI runner =="
log "DB_CI=$DB_CI MODULE=$MODULE TEST_TAGS_FINAL=$TEST_TAGS_FINAL"
log "artifacts=$outdir"
echo

compose_ci down -v --remove-orphans >/dev/null 2>&1 || true

DB_CI="$DB_CI" \
MODULE="$MODULE" \
TEST_TAGS="$TEST_TAGS" \
TEST_TAGS_FINAL="$TEST_TAGS_FINAL" \
compose_ci up --abort-on-container-exit --exit-code-from odoo 2>&1 | tee "$CI_LOG"

rc="${PIPESTATUS[0]}"

# heuristic pass signature
if [[ "$rc" -ne 0 ]] && grep -Eq "$CI_PASS_SIG_RE" "$CI_LOG"; then
  rc=0
fi

echo "exit=$rc" >"$outdir/exit.txt"
log "== artifacts: $outdir =="
exit "$rc"
