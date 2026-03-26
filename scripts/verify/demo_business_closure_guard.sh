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

from odoo.addons.smart_construction_core.services.project_dashboard_service import ProjectDashboardService
from odoo.addons.smart_construction_core.services.project_decision_engine_service import ProjectDecisionEngineService

OUT_JSON = Path("/mnt/artifacts/audit/demo_business_closure_audit.json")
OUT_MD = Path("/mnt/artifacts/backend/demo_business_closure_guard.md")

PROJECT_SPECS = {
    "展厅-智慧园区运营中心": {
        "profile": "execution",
        "lifecycle": "in_progress",
        "cost_expected": 0,
        "payment_expected": 0,
        "settlement_expected": 0,
        "decision_action": "cost_tracking_enter",
    },
    "展厅-装配式住宅试点": {
        "profile": "payment",
        "lifecycle": "in_progress",
        "cost_min": 1,
        "payment_expected": 0,
        "settlement_expected": 0,
        "decision_action": "payment_enter",
    },
    "展厅-产线升级改造工程": {
        "profile": "settlement_complete",
        "lifecycle": "done",
        "cost_min": 1,
        "payment_min": 1,
        "settlement_min": 1,
        "decision_action": "settlement_enter",
        "completion_percent": 100,
    },
}

Project = env["project.project"].sudo()
Task = env["project.task"].sudo()
Cost = env["project.cost.ledger"].sudo()
Payment = env["payment.request"].sudo()
Ledger = env["payment.ledger"].sudo()
Settlement = env["sc.settlement.order"].sudo()
dashboard = ProjectDashboardService(env)
decision_service = ProjectDecisionEngineService(env)

report = {"status": "PASS", "projects": {}, "errors": []}

for name, spec in PROJECT_SPECS.items():
    project = Project.search([("name", "=", name)], limit=1)
    if not project:
        report["errors"].append(f"missing project: {name}")
        continue
    payload = {
        "profile": spec["profile"],
        "project_id": project.id,
        "lifecycle_state": project.lifecycle_state,
        "stage": getattr(project.stage_id, "display_name", ""),
        "showcase": bool(getattr(project, "sc_demo_showcase", False)),
        "showcase_ready": bool(getattr(project, "sc_demo_showcase_ready", False)),
        "task_count": Task.search_count([("project_id", "=", project.id)]),
        "task_done_count": Task.search_count([("project_id", "=", project.id), ("sc_state", "=", "done")]),
        "cost_count": Cost.search_count([("project_id", "=", project.id)]),
        "payment_count": Payment.search_count([("project_id", "=", project.id)]),
        "payment_linked_count": Payment.search_count([("project_id", "=", project.id), ("settlement_id", "!=", False)]),
        "payment_done_count": Payment.search_count([("project_id", "=", project.id), ("type", "=", "pay"), ("state", "=", "done")]),
        "ledger_count": Ledger.search_count([("project_id", "=", project.id)]),
        "settlement_count": Settlement.search_count([("project_id", "=", project.id)]),
        "settlement_done_count": Settlement.search_count([("project_id", "=", project.id), ("state", "=", "done")]),
    }
    decision = decision_service.decide(project)
    completion = dashboard.build_completion(project)
    payload["decision_action"] = decision.get("primary_action_key")
    payload["completion_percent"] = completion.get("percent")
    report["projects"][name] = payload

    if payload["lifecycle_state"] != spec["lifecycle"]:
        report["errors"].append(f"{name}: lifecycle expected {spec['lifecycle']} got {payload['lifecycle_state']}")
    if not payload["showcase"] or not payload["showcase_ready"]:
        report["errors"].append(f"{name}: showcase flags not ready")
    if payload["task_count"] < 1:
        report["errors"].append(f"{name}: task_count < 1")
    if spec["profile"] == "full_journey" and payload["task_done_count"] < payload["task_count"]:
        report["errors"].append(f"{name}: task_done_count expected full completion got {payload['task_done_count']}/{payload['task_count']}")

    if "cost_expected" in spec and payload["cost_count"] != spec["cost_expected"]:
        report["errors"].append(f"{name}: cost_count expected {spec['cost_expected']} got {payload['cost_count']}")
    if "cost_min" in spec and payload["cost_count"] < spec["cost_min"]:
        report["errors"].append(f"{name}: cost_count < {spec['cost_min']}")

    if "payment_expected" in spec and payload["payment_count"] != spec["payment_expected"]:
        report["errors"].append(f"{name}: payment_count expected {spec['payment_expected']} got {payload['payment_count']}")
    if "payment_min" in spec and payload["payment_count"] < spec["payment_min"]:
        report["errors"].append(f"{name}: payment_count < {spec['payment_min']}")
    if spec["profile"] == "full_journey" and payload["payment_linked_count"] < 1:
        report["errors"].append(f"{name}: payment_linked_count < 1")
    if spec["profile"] == "full_journey" and payload["payment_done_count"] < 1:
        report["errors"].append(f"{name}: payment_done_count < 1")
    if spec["profile"] == "full_journey" and payload["ledger_count"] < 1:
        report["errors"].append(f"{name}: ledger_count < 1")

    if "settlement_expected" in spec and payload["settlement_count"] != spec["settlement_expected"]:
        report["errors"].append(f"{name}: settlement_count expected {spec['settlement_expected']} got {payload['settlement_count']}")
    if "settlement_min" in spec and payload["settlement_done_count"] < spec["settlement_min"]:
        report["errors"].append(f"{name}: settlement_done_count < {spec['settlement_min']}")
    if payload["decision_action"] != spec["decision_action"]:
        report["errors"].append(f"{name}: decision_action expected {spec['decision_action']} got {payload['decision_action']}")
    if "completion_percent" in spec and int(payload["completion_percent"] or 0) != int(spec["completion_percent"]):
        report["errors"].append(f"{name}: completion_percent expected {spec['completion_percent']} got {payload['completion_percent']}")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Demo Business Closure Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(f"- {name}: {payload['profile']} / lifecycle={payload['lifecycle_state']} / cost={payload['cost_count']} / payment={payload['payment_count']} / settlement={payload['settlement_count']}" for name, payload in report["projects"].items())
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[demo_business_closure_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[demo_business_closure_guard] PASS")
PY
