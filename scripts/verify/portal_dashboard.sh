#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
CONFIG="${ODOO_CONF:-/etc/odoo/odoo.conf}"

tmp_dir="/tmp/portal_dashboard_verify"
mkdir -p "${tmp_dir}"
out="${tmp_dir}/portal_dashboard_pm.json"

SC_FORCE_DOCKER=1 scripts/contract/snapshot_export.sh \
  --db "${DB_NAME}" \
  --user pm \
  --case portal_dashboard_pm \
  --op contract.portal_dashboard \
  --config "${CONFIG}" \
  --outdir "${tmp_dir}" >/dev/null

python3 - <<'PY'
import json
import sys

path = "/tmp/portal_dashboard_verify/portal_dashboard_pm.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

entries = data.get("ui_contract_raw", {}).get("entries") or data.get("entries")
if not entries:
    raise SystemExit("[verify.portal.dashboard] entries empty")

keys = {item.get("key") for item in entries if isinstance(item, dict)}
if "capability_matrix" not in keys:
    raise SystemExit("[verify.portal.dashboard] missing capability_matrix entry")

for item in entries:
    target = item.get("target") or {}
    ttype = target.get("type")
    if ttype not in ("action", "menu", "url"):
        raise SystemExit(f"[verify.portal.dashboard] invalid target type: {ttype}")

print("[verify.portal.dashboard] PASS")
PY
