#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-sc_demo}"
OUTDIR="${OUTDIR:-/tmp/smart_core_verify}"
CONFIG="${ODOO_CONF:-/etc/odoo/odoo.conf}"
EXPECT_DEGRADED="${SMART_CORE_EXPECT_DEGRADED:-auto}"

mkdir -p "$OUTDIR"

case_1="smart_core_project_kanban_lifecycle_pm"
case_2="smart_core_portal_lifecycle_dashboard_pm"
tmp_dir="${OUTDIR}/.tmp"
mkdir -p "$tmp_dir"

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case "$case_1" \
  --op action_open \
  --model project.project \
  --view_type kanban \
  --action_xmlid smart_construction_core.action_sc_project_kanban_lifecycle \
  --include_meta \
  --config "$CONFIG" \
  --outdir "$OUTDIR"

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case "$case_1" \
  --op action_open \
  --model project.project \
  --view_type kanban \
  --action_xmlid smart_construction_core.action_sc_project_kanban_lifecycle \
  --include_meta \
  --config "$CONFIG" \
  --outdir "$tmp_dir"

OUTDIR="$OUTDIR" TMPDIR="$tmp_dir" CASE_NAME="$case_1" python3 - <<'PY'
import json
import sys
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
case = os.environ["CASE_NAME"]
left = normalize(load(f"{outdir}/{case}.json"))
right = normalize(load(f"{tmpdir}/{case}.json"))
if left != right:
    raise SystemExit("[verify.smart_core] snapshot drift detected for case_1")
PY

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case "$case_2" \
  --op ui.contract \
  --route /portal/lifecycle \
  --trace_id smart_core_verify \
  --config "$CONFIG" \
  --outdir "$OUTDIR"

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case "$case_2" \
  --op ui.contract \
  --route /portal/lifecycle \
  --trace_id smart_core_verify \
  --config "$CONFIG" \
  --outdir "$tmp_dir"

OUTDIR="$OUTDIR" TMPDIR="$tmp_dir" CASE_NAME="$case_2" python3 - <<'PY'
import json
import sys
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
case = os.environ["CASE_NAME"]
left = normalize(load(f"{outdir}/{case}.json"))
right = normalize(load(f"{tmpdir}/{case}.json"))
if left != right:
    raise SystemExit("[verify.smart_core] snapshot drift detected for case_2")
PY

python3 - <<'PY'
import json
import os
import sys

outdir = os.environ.get("OUTDIR", "/tmp/smart_core_verify")
expect = os.environ.get("EXPECT_DEGRADED", "auto").strip().lower()
targets = [
    (os.path.join(outdir, "smart_core_project_kanban_lifecycle_pm.json"), True),
    (os.path.join(outdir, "smart_core_portal_lifecycle_dashboard_pm.json"), False),
]

def extract_contract(payload):
    if not isinstance(payload, dict):
        return {}
    return payload.get("ui_contract_raw") or payload.get("ui_contract") or {}

def check_contract(path, require_degraded):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    contract = extract_contract(data)
    if "degraded" not in contract:
        if require_degraded:
            raise SystemExit(f"[verify.smart_core] missing degraded field in {path}")
        return
    degraded = bool(contract.get("degraded"))
    missing = contract.get("missing_models") or []
    if degraded and not missing:
        raise SystemExit(f"[verify.smart_core] degraded=true but missing_models empty in {path}")
    if not degraded and missing:
        raise SystemExit(f"[verify.smart_core] degraded=false but missing_models present in {path}")
    if expect == "true" and not degraded:
        raise SystemExit(f"[verify.smart_core] expected degraded=true, got false in {path}")
    if expect == "false" and degraded:
        raise SystemExit(f"[verify.smart_core] expected degraded=false, got true in {path}")

for target, require_degraded in targets:
    check_contract(target, require_degraded)

print("[verify.smart_core] semantic checks OK")
PY

echo "[verify.smart_core] PASS outdir=$OUTDIR"
