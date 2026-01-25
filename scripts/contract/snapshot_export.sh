#!/usr/bin/env bash
set -euo pipefail

outdir=""
case_name=""
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [ "${args[$i]}" = "--outdir" ]; then
    outdir="${args[$((i+1))]}"
  fi
  if [ "${args[$i]}" = "--case" ]; then
    case_name="${args[$((i+1))]}"
  fi
done

if python3 - <<'PY' >/dev/null 2>&1
import odoo  # noqa: F401
PY
then
  exec python3 scripts/contract/snapshot_export.py "$@"
fi

if [ -z "$outdir" ]; then
  outdir="docs/contract/snapshots"
fi
if [ -z "$case_name" ]; then
  echo "missing --case" >&2
  exit 2
fi
mkdir -p "$outdir"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose exec -T odoo python3 - --stdout "$@" < scripts/contract/snapshot_export.py > "${outdir}/${case_name}.json"
  echo "${outdir}/${case_name}.json"
  exit 0
fi

if command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
  docker-compose exec -T odoo python3 - --stdout "$@" < scripts/contract/snapshot_export.py > "${outdir}/${case_name}.json"
  echo "${outdir}/${case_name}.json"
  exit 0
fi

echo "No local odoo module and no docker compose available" >&2
exit 2
