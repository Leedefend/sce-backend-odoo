#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   DB=sc_demo bash scripts/audit/pull.sh
#
# Pull /tmp audit CSVs from a running Odoo container into docs/audit/.

DB="${DB:-sc_demo}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/docs/audit"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${OUT_DIR}"

CID="$(
  docker ps --format '{{.Names}}' \
    | awk '
        $0 ~ /sc-backend-odoo.*odoo/ {print; exit}
        $0 ~ /odoo/ {print; exit}
      '
)"

if [[ -z "${CID}" ]]; then
  echo "[audit.pull] No running odoo container found. Run make test first." >&2
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

COPIED=0
for p in "${PATTERNS[@]}"; do
  if docker exec "${CID}" sh -lc "ls -1 ${p} 2>/dev/null" >/tmp/_audit_ls.txt 2>/dev/null; then
    while IFS= read -r f; do
      [[ -z "${f}" ]] && continue
      base="$(basename "${f}")"
      target="${OUT_DIR}/${base%.csv}.${DB}.${TS}.csv"
      docker cp "${CID}:${f}" "${target}"
      echo "[audit.pull] copied: ${f} -> ${target}"
      COPIED=$((COPIED+1))
    done </tmp/_audit_ls.txt
  fi
done

if [[ "${COPIED}" -eq 0 ]]; then
  echo "[audit.pull] No audit CSV found in container /tmp. Did tests run?" >&2
  exit 3
fi

echo "[audit.pull] Done. Files copied: ${COPIED}"
