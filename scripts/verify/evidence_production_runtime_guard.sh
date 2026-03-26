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

from odoo.exceptions import UserError

from odoo.addons.smart_construction_core.services.project_decision_engine_service import (
    ProjectDecisionEngineService,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)

OUT_JSON = Path("/mnt/artifacts/backend/evidence_production_runtime_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/evidence_production_runtime_guard.md")
CHECK_MODE = os.environ.get("CHECK_MODE", "all")

project = env["project.project"].create(
    {
        "name": "Evidence Runtime Guard Project",
        "manager_id": env.user.id,
        "user_id": env.user.id,
        "lifecycle_state": "in_progress",
    }
)
partner = env["res.partner"].create({"name": "Evidence Runtime Guard Partner"})
cost_code = env["project.cost.code"].search([], limit=1)
if not cost_code:
    cost_code = env["project.cost.code"].create({"name": "Evidence Guard Code", "code": "EV-GUARD", "type": "other"})

cost = env["project.cost.ledger"].create(
    {
        "project_id": project.id,
        "cost_code_id": cost_code.id,
        "amount": 120.0,
    }
)
payment = env["payment.request"].create(
    {
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": 60.0,
        "type": "pay",
    }
)

Evidence = env["sc.business.evidence"].sudo()
payment_evidence = Evidence.search(
    [("source_model", "=", "payment.request"), ("source_id", "=", payment.id), ("evidence_type", "=", "payment")],
    limit=1,
)
cost_evidence = Evidence.search(
    [("source_model", "=", "project.cost.ledger"), ("source_id", "=", cost.id), ("evidence_type", "=", "cost")],
    limit=1,
)

decision_service = ProjectDecisionEngineService(env)
dashboard_service = ProjectDashboardService(env)
before = decision_service.decide(project)
dashboard_before = dashboard_service.project_payload(project)

immutability = {"write_blocked": False, "unlink_blocked": False}
try:
    payment_evidence.write({"name": "tampered"})
except UserError:
    immutability["write_blocked"] = True
try:
    payment_evidence.unlink()
except UserError:
    immutability["unlink_blocked"] = True

payment_evidence.with_context(allow_evidence_mutation=True).unlink()
after_delete = decision_service.decide(project)
dashboard_after_delete = dashboard_service.project_payload(project)
risk_after_delete = (after_delete.get("facts") or {}).get("signals") or {}

env["sc.evidence.builder"].build(payment, event_code="guard_rebuild_payment")
rebuilt = Evidence.search(
    [("source_model", "=", "payment.request"), ("source_id", "=", payment.id), ("evidence_type", "=", "payment")],
    limit=1,
)
after_rebuild = decision_service.decide(project)

report = {
    "status": "PASS",
    "check_mode": CHECK_MODE,
    "before_primary_action": before.get("primary_action_key"),
    "after_delete_primary_action": after_delete.get("primary_action_key"),
    "after_rebuild_primary_action": after_rebuild.get("primary_action_key"),
    "cost_evidence_created": bool(cost_evidence),
    "payment_evidence_created": bool(payment_evidence),
    "payment_evidence_rebuilt": bool(rebuilt),
    "dashboard_payment_total_before": dashboard_before.get("payment_total"),
    "dashboard_payment_total_after_delete": dashboard_after_delete.get("payment_total"),
    "risk_no_payment_after_delete": bool(risk_after_delete.get("no_payment")),
    "immutability": immutability,
    "errors": [],
}

if not report["cost_evidence_created"]:
    report["errors"].append("cost evidence was not created automatically")
if not report["payment_evidence_created"]:
    report["errors"].append("payment evidence was not created automatically")
if report["before_primary_action"] != "settlement_enter":
    report["errors"].append("before delete primary action should be settlement_enter")
if report["dashboard_payment_total_before"] in (0, "0", "0.0", None):
    report["errors"].append("dashboard payment total should be populated before deleting payment evidence")
if report["after_delete_primary_action"] != "payment_enter":
    report["errors"].append("after delete primary action should fall back to payment_enter")
if report["dashboard_payment_total_after_delete"] not in (0, "0", "0.0", None):
    report["errors"].append("dashboard payment total should drop to 0 after deleting payment evidence")
if not report["risk_no_payment_after_delete"]:
    report["errors"].append("risk engine should flag no_payment after deleting payment evidence")
if report["after_rebuild_primary_action"] != "settlement_enter":
    report["errors"].append("after rebuild primary action should recover to settlement_enter")
if not report["payment_evidence_rebuilt"]:
    report["errors"].append("payment evidence should be rebuilt by builder")
if not report["immutability"]["write_blocked"]:
    report["errors"].append("evidence write should be blocked")
if not report["immutability"]["unlink_blocked"]:
    report["errors"].append("evidence unlink should be blocked")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Evidence Production Runtime Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- before_primary_action: `{report['before_primary_action']}`\n"
    f"- after_delete_primary_action: `{report['after_delete_primary_action']}`\n"
    f"- after_rebuild_primary_action: `{report['after_rebuild_primary_action']}`\n"
    f"- dashboard_payment_total_before: `{report['dashboard_payment_total_before']}`\n"
    f"- dashboard_payment_total_after_delete: `{report['dashboard_payment_total_after_delete']}`\n"
    f"- risk_no_payment_after_delete: `{report['risk_no_payment_after_delete']}`\n"
    f"- immutability.write_blocked: `{report['immutability']['write_blocked']}`\n"
    f"- immutability.unlink_blocked: `{report['immutability']['unlink_blocked']}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {item}" for item in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[evidence_production_runtime_guard] FAIL")
    for item in report["errors"]:
        print(" - %s" % item)
    raise SystemExit(1)

print("[evidence_production_runtime_guard] PASS")
PY
