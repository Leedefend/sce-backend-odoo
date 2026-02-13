#!/usr/bin/env bash
set -euo pipefail

CASES_FILE=${CASES_FILE:-docs/contract/cases.yml}
DB_NAME=${DB:-${DB_NAME:-}}
if [ -z "$DB_NAME" ]; then
  echo "DB not set; use DB=your_db" >&2
  exit 2
fi

python3 - <<'PY'
import json
import os
import subprocess
import sys

cases_file = os.environ.get("CASES_FILE", "docs/contract/cases.yml")
with open(cases_file, "r", encoding="utf-8") as f:
    content = f.read().strip()
try:
    cases = json.loads(content)
except Exception as exc:
    print(f"Failed to parse cases file: {exc}", file=sys.stderr)
    sys.exit(2)

if not isinstance(cases, list):
    print("cases.yml must be a JSON array", file=sys.stderr)
    sys.exit(2)

for case in cases:
    if not isinstance(case, dict):
        print("case item must be object", file=sys.stderr)
        sys.exit(2)
    cmd = [
        "scripts/contract/snapshot_export.sh",
        "--db", os.environ.get("DB") or os.environ.get("DB_NAME"),
        "--user", case.get("user", "admin"),
        "--case", case["case"],
        "--view_type", case.get("view_type", "form"),
    ]
    cfg = os.environ.get("CONTRACT_CONFIG") or os.environ.get("ODOO_CONF")
    if cfg:
        cmd += ["--config", cfg]
    if case.get("model"):
        cmd += ["--model", case["model"]]
    if case.get("id"):
        cmd += ["--id", str(case["id"])]
    if case.get("menu_id"):
        cmd += ["--menu_id", str(case["menu_id"])]
    if case.get("action_xmlid"):
        cmd += ["--action_xmlid", case["action_xmlid"]]
    if case.get("route"):
        cmd += ["--route", case["route"]]
    if case.get("project_id"):
        cmd += ["--project_id", str(case["project_id"])]
    if case.get("trace_id"):
        cmd += ["--trace_id", str(case["trace_id"])]
    if case.get("op"):
        cmd += ["--op", case["op"]]
    if case.get("execute_method"):
        cmd += ["--execute_method", case["execute_method"]]
    if case.get("intent"):
        cmd += ["--intent", case["intent"]]
    if "intent_params" in case:
        cmd += ["--intent_params", json.dumps(case.get("intent_params") or {}, ensure_ascii=False, sort_keys=True)]
    outdir = case.get("outdir") or os.environ.get("OUTDIR")
    if outdir:
        cmd += ["--outdir", outdir]
    if case.get("include_meta"):
        cmd += ["--include_meta"]
    if case.get("allow_error_response"):
        cmd += ["--allow_error_response"]

    timeout_sec = int(os.environ.get("SC_SNAPSHOT_CASE_TIMEOUT_SEC", "90"))
    try:
        subprocess.run(cmd, check=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as exc:
        case_name = case.get("case", "<unknown>")
        intent_name = case.get("intent") or ""
        op_name = case.get("op") or ""
        detail = f"intent={intent_name}" if intent_name else f"op={op_name}"
        print(
            f"[export_all] timeout case={case_name} {detail} timeout_sec={timeout_sec}",
            file=sys.stderr,
        )
        raise SystemExit(124) from exc
    except subprocess.CalledProcessError as exc:
        case_name = case.get("case", "<unknown>")
        intent_name = case.get("intent") or ""
        op_name = case.get("op") or ""
        detail = f"intent={intent_name}" if intent_name else f"op={op_name}"
        print(
            f"[export_all] failed case={case_name} {detail} exit={exc.returncode}",
            file=sys.stderr,
        )
        raise
PY
