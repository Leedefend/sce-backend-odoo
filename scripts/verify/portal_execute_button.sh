#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
CONFIG="${ODOO_CONF:-/etc/odoo/odoo.conf}"

OUTDIR="tmp/portal_execute_button_verify"
TMPDIR="${OUTDIR}/.tmp"
mkdir -p "${OUTDIR}" "${TMPDIR}"

env SC_FORCE_DOCKER=1 timeout 30 scripts/contract/snapshot_export.sh \
  --db "${DB_NAME}" \
  --user pm \
  --case portal_execute_button_pm \
  --op contract.portal_execute_button \
  --config "${CONFIG}" \
  --outdir "${OUTDIR}" >/dev/null

env SC_FORCE_DOCKER=1 timeout 30 scripts/contract/snapshot_export.sh \
  --db "${DB_NAME}" \
  --user pm \
  --case portal_execute_button_pm \
  --op contract.portal_execute_button \
  --config "${CONFIG}" \
  --outdir "${TMPDIR}" >/dev/null

OUTDIR="${OUTDIR}" TMPDIR="${TMPDIR}" python3 - <<'PY'
import json
import os

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(payload):
    if not isinstance(payload, dict):
        return payload
    payload = dict(payload)
    for key in ("exported_at", "trace_id"):
        payload.pop(key, None)
    return payload

outdir = os.environ["OUTDIR"]
tmpdir = os.environ["TMPDIR"]
left = normalize(load(os.path.join(outdir, "portal_execute_button_pm.json")))
right = normalize(load(os.path.join(tmpdir, "portal_execute_button_pm.json")))
if left != right:
    raise SystemExit("[verify.portal.execute_button] snapshot drift detected")

payload = left.get("ui_contract_raw") or {}
allowed = payload.get("allowed")
if allowed is not True:
    raise SystemExit("[verify.portal.execute_button] expected allowed=true")

print("[verify.portal.execute_button] snapshot stable + allowed OK")
PY

env SC_FORCE_DOCKER=1 timeout 30 scripts/contract/snapshot_export.sh \
  --db "${DB_NAME}" \
  --user pm \
  --case portal_execute_button_not_allowed \
  --op contract.portal_execute_button \
  --model project.project \
  --execute_method action_sc_project_manage \
  --config "${CONFIG}" \
  --outdir "${OUTDIR}" >/dev/null

OUTDIR="${OUTDIR}" python3 - <<'PY'
import json
import os

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

payload = load(os.path.join(os.environ["OUTDIR"], "portal_execute_button_not_allowed.json"))
data = payload.get("ui_contract_raw") or {}
allowed = data.get("allowed")
error = data.get("error") or {}
if allowed is not False:
    raise SystemExit("[verify.portal.execute_button] expected allowed=false")
if error.get("code") != "not_allowed":
    raise SystemExit("[verify.portal.execute_button] expected error.code=not_allowed")

print("[verify.portal.execute_button] not_allowed OK")
PY

echo "[verify.portal.execute_button] PASS outdir=${OUTDIR}"
