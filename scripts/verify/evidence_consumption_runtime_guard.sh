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

from odoo import api, SUPERUSER_ID

from odoo.addons.smart_construction_core.handlers.business_evidence_trace import BusinessEvidenceTraceHandler
from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import ProjectDashboardEnterHandler

OUT_JSON = Path("/mnt/artifacts/backend/evidence_consumption_runtime_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/evidence_consumption_runtime_guard.md")
CHECK_MODE = os.environ.get("CHECK_MODE", "all")

project = env["project.project"].create(
    {
        "name": "Evidence Consumption Guard Project",
        "manager_id": env.user.id,
        "user_id": env.user.id,
        "lifecycle_state": "in_progress",
    }
)
partner = env["res.partner"].create({"name": "Evidence Consumption Guard Partner"})
cost_code = env["project.cost.code"].search([], limit=1)
if not cost_code:
    cost_code = env["project.cost.code"].create({"name": "Evidence Consume Guard", "code": "EV-CONSUME", "type": "other"})

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

su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
dashboard_handler = ProjectDashboardEnterHandler(
    env,
    su_env=su_env,
    context={"trace_id": "guard-evidence-consumption-dashboard"},
    payload={"params": {"project_id": int(project.id)}},
)
dashboard_result = dashboard_handler.run()
dashboard_data = dashboard_result.get("data") or {}
fact_metrics = dashboard_data.get("fact_metrics") or []
fact_metric_keys = {str(item.get("key") or "") for item in fact_metrics if isinstance(item, dict)}

trace_handler = BusinessEvidenceTraceHandler(
    env,
    su_env=su_env,
    context={"trace_id": "guard-evidence-consumption-trace"},
    payload={"params": {"business_model": "project.project", "business_id": int(project.id), "evidence_type": "payment"}},
)
trace_result = trace_handler.run()
trace_data = trace_result.get("data") or {}
timeline = (trace_data.get("timeline") or {}).get("items") or []

risk_result = env["sc.evidence.risk.engine"].analyze(project)
risks = risk_result.get("risks") or []
action_result = env["sc.evidence.action.engine"].decide(project)
primary_action = action_result.get("primary_action") or {}

report = {
    "status": "PASS",
    "check_mode": CHECK_MODE,
    "project_id": int(project.id),
    "fact_metric_keys": sorted(fact_metric_keys),
    "fact_metrics": fact_metrics,
    "trace_entry": trace_data.get("trace_entry") or {},
    "timeline_count": len(timeline),
    "timeline_first_item": timeline[0] if timeline else {},
    "risk_count": int(risk_result.get("risk_count") or 0),
    "risks": risks,
    "primary_action": primary_action,
    "errors": [],
}

required_fact_keys = {"payment_total", "cost_total", "settlement_total", "risk_count"}
if CHECK_MODE in ("all", "trace_entry"):
    if not dashboard_result.get("ok"):
        report["errors"].append("project.dashboard.enter returned ok=false")
    if not required_fact_keys.issubset(fact_metric_keys):
        report["errors"].append("dashboard fact_metrics missing required keys")
    for item in fact_metrics:
        key = str(item.get("key") or "")
        if key not in required_fact_keys:
            continue
        trace_action = item.get("trace_action") or {}
        payload = trace_action.get("payload") or {}
        if str(trace_action.get("intent") or "") != "business.evidence.trace":
            report["errors"].append("fact metric missing business.evidence.trace intent: %s" % key)
        if int(payload.get("business_id") or 0) != int(project.id):
            report["errors"].append("fact metric trace payload business_id mismatch: %s" % key)

if CHECK_MODE in ("all", "timeline"):
    if not trace_result.get("ok"):
        report["errors"].append("business.evidence.trace returned ok=false")
    if not trace_data.get("trace_entry"):
        report["errors"].append("trace_entry missing from business.evidence.trace payload")
    if len(timeline) <= 0:
        report["errors"].append("timeline.items should not be empty")
    else:
        first = timeline[0]
        for key in ("time", "type", "title", "amount", "source_ref", "risk_codes", "checksum"):
            if key not in first:
                report["errors"].append("timeline item missing key: %s" % key)

if CHECK_MODE in ("all", "risk"):
    if int(risk_result.get("risk_count") or 0) <= 0:
        report["errors"].append("risk_count should be > 0")
    if not risks:
        report["errors"].append("risks should not be empty")
    for risk in risks:
        if not str(risk.get("risk_code") or ""):
            report["errors"].append("risk missing risk_code")
        if not str(risk.get("severity") or ""):
            report["errors"].append("risk missing severity")
        if not str(risk.get("reason") or ""):
            report["errors"].append("risk missing reason")
        if not isinstance(risk.get("evidence_refs"), list) or not risk.get("evidence_refs"):
            report["errors"].append("risk missing evidence_refs")

if CHECK_MODE in ("all", "action"):
    if str(primary_action.get("action_key") or "") != "settlement_enter":
        report["errors"].append("primary_action.action_key should be settlement_enter")
    for key in ("label", "reason"):
        if not str(primary_action.get(key) or ""):
            report["errors"].append("primary_action missing %s" % key)
    if not isinstance(primary_action.get("risk_codes"), list) or not primary_action.get("risk_codes"):
        report["errors"].append("primary_action missing risk_codes")
    if not isinstance(primary_action.get("evidence_refs"), list) or not primary_action.get("evidence_refs"):
        report["errors"].append("primary_action missing evidence_refs")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Evidence Consumption Runtime Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- check_mode: `{report['check_mode']}`\n"
    f"- project_id: `{report['project_id']}`\n"
    f"- fact_metric_keys: `{', '.join(report['fact_metric_keys'])}`\n"
    f"- timeline_count: `{report['timeline_count']}`\n"
    f"- risk_count: `{report['risk_count']}`\n"
    f"- primary_action: `{str((report['primary_action'] or {}).get('action_key') or '')}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {item}" for item in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[evidence_consumption_runtime_guard] FAIL")
    for item in report["errors"]:
        print(" - %s" % item)
    raise SystemExit(1)

print("[evidence_consumption_runtime_guard] PASS")
PY
