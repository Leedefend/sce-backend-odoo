#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
from pathlib import Path

from odoo.addons.smart_construction_core.services.cost_tracking_service import CostTrackingService
from odoo.addons.smart_construction_core.services.project_dashboard_service import ProjectDashboardService
from odoo.addons.smart_construction_core.services.project_decision_engine_service import ProjectDecisionEngineService
from odoo.addons.smart_construction_core.services.settlement_slice_service import SettlementSliceService

OUT_JSON = Path("/mnt/artifacts/backend/business_fact_consistency_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/business_fact_consistency_guard.md")

PROJECT_NAMES = [
    "展厅-智慧园区运营中心",
    "展厅-装配式住宅试点",
    "展厅-产线升级改造工程",
]

Project = env["project.project"].sudo()
dashboard = ProjectDashboardService(env)
decision_service = ProjectDecisionEngineService(env)
cost_service = CostTrackingService(env)
settlement_service = SettlementSliceService(env)

report = {"status": "PASS", "projects": {}, "errors": []}

def num(value):
    try:
        return round(float(value or 0.0), 2)
    except Exception:
        return 0.0

def intval(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0

for name in PROJECT_NAMES:
    project = Project.search([("name", "=", name)], limit=1)
    if not project:
        report["errors"].append(f"missing project: {name}")
        continue

    dashboard_payload = dashboard.project_payload(project)
    completion = dashboard.build_completion(project)
    flow_map = dashboard.build_flow_map(project)
    decision = decision_service.decide(project)
    cost_payload = cost_service.project_payload(project)
    settlement_summary = settlement_service.summary(project)

    row = {
        "project_id": int(project.id),
        "lifecycle_state": str(getattr(project, "lifecycle_state", "") or ""),
        "dashboard_cost_total": num(dashboard_payload.get("cost_total")),
        "dashboard_payment_total": num(dashboard_payload.get("payment_total")),
        "dashboard_progress_percent": num(dashboard_payload.get("progress_percent")),
        "cost_total_amount": num(cost_payload.get("cost_total_amount")),
        "cost_record_count": intval(cost_payload.get("cost_record_count")),
        "settlement_total_cost": num(settlement_summary.get("total_cost")),
        "settlement_total_payment": num(settlement_summary.get("total_payment")),
        "settlement_cost_record_count": intval(settlement_summary.get("cost_record_count")),
        "decision_progress_percent": num((decision.get("facts") or {}).get("progress_percent")),
        "decision_cost_count": intval((decision.get("facts") or {}).get("cost_count")),
        "decision_payment_count": intval((decision.get("facts") or {}).get("payment_count")),
        "completion_percent": intval(completion.get("percent")),
        "flow_map_current_stage": str(flow_map.get("current_stage") or ""),
    }
    report["projects"][name] = row

    if row["dashboard_cost_total"] != row["cost_total_amount"]:
        report["errors"].append(
            f"{name}: dashboard_cost_total {row['dashboard_cost_total']} != cost_total_amount {row['cost_total_amount']}"
        )
    if row["settlement_total_cost"] != row["cost_total_amount"]:
        report["errors"].append(
            f"{name}: settlement_total_cost {row['settlement_total_cost']} != cost_total_amount {row['cost_total_amount']}"
        )
    if row["dashboard_payment_total"] != row["settlement_total_payment"]:
        report["errors"].append(
            f"{name}: dashboard_payment_total {row['dashboard_payment_total']} != settlement_total_payment {row['settlement_total_payment']}"
        )
    if row["cost_record_count"] != row["settlement_cost_record_count"]:
        report["errors"].append(
            f"{name}: cost_record_count {row['cost_record_count']} != settlement_cost_record_count {row['settlement_cost_record_count']}"
        )
    if row["dashboard_progress_percent"] != row["decision_progress_percent"]:
        report["errors"].append(
            f"{name}: dashboard_progress_percent {row['dashboard_progress_percent']} != decision_progress_percent {row['decision_progress_percent']}"
        )
    if row["decision_cost_count"] == 0 and row["flow_map_current_stage"] in {"cost", "payment", "settlement"}:
        report["errors"].append(
            f"{name}: flow_map_current_stage={row['flow_map_current_stage']} but decision_cost_count=0"
        )
    if row["decision_payment_count"] == 0 and row["flow_map_current_stage"] in {"payment", "settlement"}:
        report["errors"].append(
            f"{name}: flow_map_current_stage={row['flow_map_current_stage']} but decision_payment_count=0"
        )
    if row["completion_percent"] == 100 and row["flow_map_current_stage"] != "settlement":
        report["errors"].append(
            f"{name}: completion_percent=100 but flow_map_current_stage={row['flow_map_current_stage']}"
        )

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Business Fact Consistency Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {name}: cost={row['cost_total_amount']} / payment={row['dashboard_payment_total']} / progress={row['dashboard_progress_percent']} / flow={row['flow_map_current_stage']}"
        for name, row in report["projects"].items()
    )
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[business_fact_consistency_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[business_fact_consistency_guard] PASS")
PY
