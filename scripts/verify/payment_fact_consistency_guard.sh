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

from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.payment_slice_service import PaymentSliceService
from odoo.addons.smart_construction_core.services.project_dashboard_service import ProjectDashboardService
from odoo.addons.smart_construction_core.services.project_decision_engine_service import ProjectDecisionEngineService
from odoo.addons.smart_construction_core.services.settlement_slice_service import SettlementSliceService

OUT_JSON = Path("/mnt/artifacts/backend/payment_fact_consistency_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/payment_fact_consistency_guard.md")

PROJECT_NAMES = [
    "展厅-智慧园区运营中心",
    "展厅-装配式住宅试点",
    "展厅-产线升级改造工程",
]

Project = env["project.project"].sudo()
PaymentRequest = env["payment.request"].sudo()
PaymentLedger = env["payment.ledger"].sudo()
dashboard = ProjectDashboardService(env)
decision_service = ProjectDecisionEngineService(env)
payment_service = PaymentSliceService(env)
settlement_service = SettlementSliceService(env)
payment_adapter = PaymentSliceNativeAdapter(env)

report = {"status": "PASS", "projects": {}, "missing_projects": [], "errors": []}

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
        report["missing_projects"].append(name)
        continue

    request_domain = [("project_id", "=", int(project.id)), ("type", "=", "pay")]
    request_count = PaymentRequest.search_count(request_domain)
    request_total = 0.0
    for row in PaymentRequest.search(request_domain):
        request_total += float(getattr(row, "amount", 0.0) or 0.0)

    ledger_domain = [("project_id", "=", int(project.id))]
    ledger_count = PaymentLedger.search_count(ledger_domain)
    ledger_total = 0.0
    for row in PaymentLedger.search(ledger_domain):
        ledger_total += float(getattr(row, "amount", 0.0) or 0.0)

    adapter_summary = payment_adapter.summary(project)
    payment_payload = payment_service.project_payload(project)
    dashboard_payload = dashboard.project_payload(project)
    decision = decision_service.decide(project)
    settlement_summary = settlement_service.summary(project)

    row = {
        "project_id": int(project.id),
        "request_count": int(request_count),
        "request_total": round(request_total, 2),
        "ledger_count": int(ledger_count),
        "ledger_total": round(ledger_total, 2),
        "adapter_request_count": intval(adapter_summary.get("request_count")),
        "adapter_total_payment_amount": num(adapter_summary.get("total_payment_amount")),
        "payment_payload_record_count": intval(payment_payload.get("payment_record_count")),
        "payment_payload_total": num(payment_payload.get("payment_total_amount")),
        "payment_payload_executed_count": intval(payment_payload.get("executed_payment_record_count")),
        "payment_payload_executed_total": num(payment_payload.get("executed_payment_amount")),
        "dashboard_payment_total": num(dashboard_payload.get("payment_total")),
        "dashboard_payment_executed_total": num(dashboard_payload.get("payment_executed_total")),
        "dashboard_payment_executed_count": intval(dashboard_payload.get("payment_executed_record_count")),
        "settlement_total_payment": num(settlement_summary.get("total_payment")),
        "settlement_executed_payment": num(settlement_summary.get("executed_payment_amount")),
        "settlement_payment_record_count": intval(settlement_summary.get("payment_record_count")),
        "settlement_executed_payment_record_count": intval(settlement_summary.get("executed_payment_record_count")),
        "decision_payment_count": intval((decision.get("facts") or {}).get("payment_count")),
        "decision_payment_total": num((decision.get("facts") or {}).get("payment_total")),
    }
    report["projects"][name] = row

    if row["adapter_request_count"] != row["request_count"]:
        report["errors"].append(f"{name}: adapter_request_count {row['adapter_request_count']} != request_count {row['request_count']}")
    if row["adapter_total_payment_amount"] != row["request_total"]:
        report["errors"].append(f"{name}: adapter_total_payment_amount {row['adapter_total_payment_amount']} != request_total {row['request_total']}")
    if row["payment_payload_record_count"] != row["request_count"]:
        report["errors"].append(f"{name}: payment_payload_record_count {row['payment_payload_record_count']} != request_count {row['request_count']}")
    if row["payment_payload_total"] != row["request_total"]:
        report["errors"].append(f"{name}: payment_payload_total {row['payment_payload_total']} != request_total {row['request_total']}")
    if row["dashboard_payment_total"] != row["request_total"]:
        report["errors"].append(f"{name}: dashboard_payment_total {row['dashboard_payment_total']} != request_total {row['request_total']}")
    if row["settlement_total_payment"] != row["request_total"]:
        report["errors"].append(f"{name}: settlement_total_payment {row['settlement_total_payment']} != request_total {row['request_total']}")
    if row["settlement_payment_record_count"] != row["request_count"]:
        report["errors"].append(f"{name}: settlement_payment_record_count {row['settlement_payment_record_count']} != request_count {row['request_count']}")
    if row["decision_payment_count"] != row["request_count"]:
        report["errors"].append(f"{name}: decision_payment_count {row['decision_payment_count']} != request_count {row['request_count']}")
    if row["decision_payment_total"] != row["request_total"]:
        report["errors"].append(f"{name}: decision_payment_total {row['decision_payment_total']} != request_total {row['request_total']}")
    if row["payment_payload_executed_count"] != row["ledger_count"]:
        report["errors"].append(f"{name}: payment_payload_executed_count {row['payment_payload_executed_count']} != ledger_count {row['ledger_count']}")
    if row["payment_payload_executed_total"] != row["ledger_total"]:
        report["errors"].append(f"{name}: payment_payload_executed_total {row['payment_payload_executed_total']} != ledger_total {row['ledger_total']}")
    if row["dashboard_payment_executed_total"] != row["ledger_total"]:
        report["errors"].append(f"{name}: dashboard_payment_executed_total {row['dashboard_payment_executed_total']} != ledger_total {row['ledger_total']}")
    if row["dashboard_payment_executed_count"] != row["ledger_count"]:
        report["errors"].append(f"{name}: dashboard_payment_executed_count {row['dashboard_payment_executed_count']} != ledger_count {row['ledger_count']}")
    if row["settlement_executed_payment"] != row["ledger_total"]:
        report["errors"].append(f"{name}: settlement_executed_payment {row['settlement_executed_payment']} != ledger_total {row['ledger_total']}")
    if row["settlement_executed_payment_record_count"] != row["ledger_count"]:
        report["errors"].append(f"{name}: settlement_executed_payment_record_count {row['settlement_executed_payment_record_count']} != ledger_count {row['ledger_count']}")

if report["errors"]:
    report["status"] = "FAIL"
elif report["missing_projects"]:
    report["status"] = "SKIP_ENV"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Payment Fact Consistency Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {name}: request_total={row['request_total']} / ledger_total={row['ledger_total']} / dashboard={row['dashboard_payment_total']} / settlement={row['settlement_total_payment']}"
        for name, row in report["projects"].items()
    )
    + ("\n- missing demo projects:\n" + "\n".join(f"  - {line}" for line in report["missing_projects"]) if report["missing_projects"] else "")
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[payment_fact_consistency_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

if report["status"] == "SKIP_ENV":
    print("[payment_fact_consistency_guard] SKIP_ENV")
    for line in report["missing_projects"]:
        print(f" - missing demo project: {line}")
    raise SystemExit(0)

print("[payment_fact_consistency_guard] PASS")
PY
