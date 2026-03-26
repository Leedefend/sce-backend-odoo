#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"
CHECK_MODE="${CHECK_MODE:-all}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
import os
from pathlib import Path

from odoo.addons.smart_construction_core.handlers.risk_action_execute import RiskActionExecuteHandler

OUT_JSON = Path("/mnt/artifacts/backend/evidence_exception_runtime_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/evidence_exception_runtime_guard.md")
CHECK_MODE = os.environ.get("CHECK_MODE", "all")

project = env["project.project"].create(
    {
        "name": "Evidence Exception Guard Project",
        "manager_id": env.user.id,
        "user_id": env.user.id,
        "lifecycle_state": "in_progress",
    }
)
partner = env["res.partner"].create({"name": "Evidence Exception Guard Partner"})
cost_code = env["project.cost.code"].search([], limit=1)
if not cost_code:
    cost_code = env["project.cost.code"].create({"name": "Evidence Exception Guard", "code": "EV-EX-G", "type": "other"})

env["project.cost.ledger"].create(
    {
        "project_id": project.id,
        "cost_code_id": cost_code.id,
        "amount": 100.0,
    }
)
env["payment.request"].create(
    {
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": 140.0,
        "type": "pay",
    }
)

analysis = env["sc.evidence.risk.engine"].analyze(project)
ExceptionModel = env["sc.evidence.exception"].sudo()
exception = ExceptionModel.search(
    [("project_id", "=", project.id), ("risk_code", "=", "payment_exceeds_cost")],
    limit=1,
)
handler = RiskActionExecuteHandler(env, payload={})
claim_result = {}
close_result = {}
if exception:
    claim_result = handler.handle({"action": "claim", "exception_id": int(exception.id)})
    exception.invalidate_recordset(["status", "assigned_to"])
    close_result = handler.handle({"action": "close", "exception_id": int(exception.id), "note": "已完成关闭"})
    exception.invalidate_recordset(["status", "resolution_note"])

report = {
    "status": "PASS",
    "check_mode": CHECK_MODE,
    "project_id": int(project.id),
    "risk_count": int(analysis.get("risk_count") or 0),
    "risk_codes": list(analysis.get("risk_codes") or []),
    "exception_id": int(exception.id or 0) if exception else 0,
    "exception_status": str(exception.status or "") if exception else "",
    "risk_action_id": int(exception.risk_action_id.id or 0) if exception and exception.risk_action_id else 0,
    "claim_ok": bool(claim_result.get("ok")) if claim_result else False,
    "close_ok": bool(close_result.get("ok")) if close_result else False,
    "resolution_note": str(exception.resolution_note or "") if exception else "",
    "errors": [],
}

if CHECK_MODE in ("all", "pipeline"):
    if int(analysis.get("risk_count") or 0) <= 0:
        report["errors"].append("risk_count should be > 0")
    if "payment_exceeds_cost" not in set(analysis.get("risk_codes") or []):
        report["errors"].append("payment_exceeds_cost should be present in risk_codes")
    if not report["exception_id"]:
        report["errors"].append("high severity risk should create exception")
    if not report["risk_action_id"]:
        report["errors"].append("exception should link to project.risk.action")

if CHECK_MODE in ("all", "lifecycle"):
    if not report["claim_ok"]:
        report["errors"].append("claim should succeed")
    if not report["close_ok"]:
        report["errors"].append("close should succeed")
    if report["exception_status"] != "resolved":
        report["errors"].append("exception should become resolved after close")
    if report["resolution_note"] != "已完成关闭":
        report["errors"].append("resolution_note should be updated after close")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Evidence Exception Runtime Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- check_mode: `{report['check_mode']}`\n"
    f"- project_id: `{report['project_id']}`\n"
    f"- risk_count: `{report['risk_count']}`\n"
    f"- exception_id: `{report['exception_id']}`\n"
    f"- exception_status: `{report['exception_status']}`\n"
    f"- risk_action_id: `{report['risk_action_id']}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {item}" for item in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[evidence_exception_runtime_guard] FAIL")
    for item in report["errors"]:
        print(" - %s" % item)
    raise SystemExit(1)

print("[evidence_exception_runtime_guard] PASS")
PY
