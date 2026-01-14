#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   DB=sc_demo bash scripts/audit/pull.sh
#
# Pull /tmp audit CSVs from the Odoo service container into docs/audit/.

DB="${DB:-sc_demo}"
COMPOSE_BIN="${COMPOSE_BIN:-docker compose}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/docs/audit"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${OUT_DIR}"

if [[ -n "${ODOO_CID:-}" ]]; then
  CID="${ODOO_CID}"
else
  CID="$(docker ps -a --filter "name=sc-test-odoo-${DB}" --format "{{.ID}}" | head -n1)"
  if [[ -z "${CID}" ]]; then
    CID="$(${COMPOSE_BIN} ps -q odoo | head -n1)"
  fi
fi

if [[ -z "${CID}" ]]; then
  echo "[audit.pull] No odoo container found (service=odoo)." >&2
  echo "[audit.pull] Hint: ${COMPOSE_BIN} ps" >&2
  echo "[audit.pull] Hint: KEEP_TEST_CONTAINER=1 make test TEST_TAGS=sc_gate BD=${DB}" >&2
  exit 2
fi

echo "[audit.pull] Using container: ${CID}"
echo "[audit.pull] Export to: ${OUT_DIR}"

PATTERNS=(
  "/tmp/acl_*.csv"
  "/tmp/acl_matrix.csv"
  "/tmp/acl_p1_sources.csv"
  "/tmp/rr_*.csv"
  "/tmp/*_p1.csv"
  "/tmp/*_matrix.csv"
)

copy_from_container() {
  local container="$1"
  local copied=0
  for p in "${PATTERNS[@]}"; do
    if docker exec "${container}" sh -lc "ls -1 ${p} 2>/dev/null" >/tmp/_audit_ls.txt 2>/dev/null; then
      while IFS= read -r f; do
        [[ -z "${f}" ]] && continue
        base="$(basename "${f}")"
        target="${OUT_DIR}/${base%.csv}.${DB}.${TS}.csv"
        docker cp "${container}:${f}" "${target}"
        echo "[audit.pull] copied: ${f} -> ${target}"
        copied=$((copied+1))
      done </tmp/_audit_ls.txt
    fi
  done
  echo "${copied}"
}

COPIED="$(copy_from_container "${CID}")"
if [[ "${COPIED}" -eq 0 ]]; then
  ALT_CID="$(docker ps -a --filter "name=sc-test-odoo-${DB}" --format "{{.ID}}" | head -n1)"
  if [[ -n "${ALT_CID}" && "${ALT_CID}" != "${CID}" ]]; then
    echo "[audit.pull] Retry with test container: ${ALT_CID}"
    COPIED="$(copy_from_container "${ALT_CID}")"
  fi
fi

if [[ "${COPIED}" -eq 0 ]]; then
  echo "[audit.pull] No audit CSV found in container /tmp." >&2
  echo "[audit.pull] Tests may have run in a one-off --rm container." >&2
  exit 3
fi

echo "[audit.pull] Done. Files copied: ${COPIED}"
