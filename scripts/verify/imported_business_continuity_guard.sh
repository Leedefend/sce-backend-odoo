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
import base64
import json
from pathlib import Path

OUT_JSON = Path("/mnt/artifacts/backend/imported_business_continuity_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/imported_business_continuity_guard.md")

Project = env["project.project"].sudo()
Contract = env["construction.contract"].sudo()
Payment = env["payment.request"].sudo()
Ledger = env["payment.ledger"].sudo()
Baseline = env["project.funding.baseline"].sudo()
Attachment = env["ir.attachment"].sudo()
Users = env["res.users"].sudo()

report = {
    "status": "PASS",
    "facts": {},
    "operability_probe": {},
    "warnings": [],
    "errors": [],
}

def count(model, domain):
    return int(model.search_count(domain))

def has_field(model, field_name):
    return field_name in model._fields

def imported_domain(model, field_name):
    if has_field(model, field_name):
        return [(field_name, "!=", False)]
    return []

def first_operable_carrier():
    project_domain = imported_domain(Project, "legacy_project_id")
    for project in Project.search(project_domain, order="id asc", limit=2000):
        if getattr(project, "lifecycle_state", "") in ("warranty", "closed"):
            continue
        if not project.is_funding_ready():
            continue
        baseline = Baseline.search(
            [
                ("project_id", "=", project.id),
                ("state", "=", "active"),
            ],
            limit=1,
        )
        if not baseline or (baseline.total_amount or 0.0) <= 1.0:
            continue
        contract = Contract.search(
            [
                ("project_id", "=", project.id),
                ("type", "=", "in"),
                ("state", "!=", "cancel"),
                ("partner_id", "!=", False),
            ],
            order="id asc",
            limit=1,
        )
        if contract:
            return project, contract
    return Project.browse(), Contract.browse()

def first_payment_operator(project, contract):
    for user in Users.search([("active", "=", True)], order="id asc"):
        if not user.has_group("smart_construction_core.group_sc_cap_finance_user"):
            continue
        if not user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            continue
        try:
            env["project.project"].with_user(user).browse(project.id).check_access_rule("read")
            env["construction.contract"].with_user(user).browse(contract.id).check_access_rule("read")
        except Exception:
            continue
        return user
    return Users.browse()

try:
    project_domain = imported_domain(Project, "legacy_project_id")
    contract_domain = imported_domain(Contract, "legacy_contract_id")

    done_validated_domain = [("state", "=", "done"), ("validation_status", "=", "validated")]
    linked_ledger_request_ids = set(Ledger.search([]).mapped("payment_request_id").ids)

    report["facts"] = {
        "imported_project_count": count(Project, project_domain),
        "funding_ready_imported_project_count": sum(1 for item in Project.search(project_domain) if item.is_funding_ready()),
        "active_funding_baseline_project_count": len(set(Baseline.search([("state", "=", "active")]).mapped("project_id").ids)),
        "imported_contract_count": count(Contract, contract_domain),
        "payment_request_count": count(Payment, []),
        "payment_done_validated_count": count(Payment, done_validated_domain),
        "payment_ledger_count": count(Ledger, []),
        "ledger_linked_payment_request_count": len(linked_ledger_request_ids),
        "payment_missing_project_count": count(Payment, [("project_id", "=", False)]),
        "payment_missing_partner_count": count(Payment, [("partner_id", "=", False)]),
        "payment_missing_contract_count": count(Payment, [("contract_id", "=", False)]),
        "payment_missing_settlement_count": count(Payment, [("settlement_id", "=", False)]),
    }

    if report["facts"]["imported_project_count"] <= 0:
        report["errors"].append("no imported project carrier found")
    if report["facts"]["imported_contract_count"] <= 0:
        report["errors"].append("no imported contract carrier found")
    if report["facts"]["payment_request_count"] <= 0:
        report["errors"].append("no payment request facts found")
    if report["facts"]["payment_done_validated_count"] <= 0:
        report["errors"].append("no completed validated payment facts found")
    if report["facts"]["payment_ledger_count"] != report["facts"]["ledger_linked_payment_request_count"]:
        report["errors"].append("payment ledger rows are not uniquely linked to payment requests")
    if report["facts"]["payment_missing_project_count"] > 0:
        report["errors"].append("payment requests missing project carrier")
    if report["facts"]["payment_missing_partner_count"] > 0:
        report["errors"].append("payment requests missing partner carrier")
    if report["facts"]["payment_missing_contract_count"] > 0:
        report["warnings"].append("some imported payment requests still lack deterministic contract linkage")
    if report["facts"]["payment_missing_settlement_count"] > 0:
        report["warnings"].append("payment requests without settlement are accepted by current optional-settlement semantics")

    project, contract = first_operable_carrier()
    if not project or not contract:
        report["errors"].append("no imported project/contract carrier can run rollback payment operability probe")
    else:
        operator = first_payment_operator(project, contract)
        if not operator:
            report["errors"].append("no finance operator can read the imported project/contract carrier")
        else:
            request = env["payment.request"].with_user(operator).create(
            {
                "name": "New",
                "type": "pay",
                "project_id": project.id,
                "contract_id": contract.id,
                "partner_id": contract.partner_id.id,
                "currency_id": contract.currency_id.id or project.company_currency_id.id or env.company.currency_id.id,
                "amount": 1.0,
                "note": "rollback-only imported business continuity guard",
            }
            )
            Attachment.create(
                {
                    "name": "imported_business_continuity_guard.txt",
                    "datas": base64.b64encode(b"rollback-only imported business continuity guard"),
                    "res_model": "payment.request",
                    "res_id": request.id,
                    "type": "binary",
                    "mimetype": "text/plain",
                }
            )
            request.action_submit()
            request.write({"validation_status": "validated"})
            request.action_on_tier_approved()
            ledger = request._ensure_payment_ledger(amount=request.amount, ref="imported-business-continuity-guard")
            request.action_done()
            report["operability_probe"] = {
                "project_id": int(project.id),
                "contract_id": int(contract.id),
                "payment_request_id": int(request.id),
                "ledger_id": int(ledger.id),
                "operator_id": int(operator.id),
                "operator_login": operator.login,
                "final_state": request.state,
                "validation_status": request.validation_status,
                "settlement_selected": bool(request.settlement_id),
            }
            if request.state != "done" or request.validation_status != "validated":
                report["errors"].append("rollback payment operability probe did not reach done/validated")
finally:
    env.cr.rollback()

env.invalidate_all()
probe = report.get("operability_probe") or {}
persisted = {}
if probe.get("payment_request_id"):
    persisted["payment_request"] = bool(Payment.browse(probe["payment_request_id"]).exists())
if probe.get("ledger_id"):
    persisted["payment_ledger"] = bool(Ledger.browse(probe["ledger_id"]).exists())
if probe.get("payment_request_id"):
    persisted["attachment_count"] = int(
        Attachment.search_count(
            [
                ("res_model", "=", "payment.request"),
                ("res_id", "=", probe["payment_request_id"]),
                ("name", "=", "imported_business_continuity_guard.txt"),
            ]
        )
    )
report["rollback_check"] = persisted
if persisted.get("payment_request") or persisted.get("payment_ledger") or persisted.get("attachment_count", 0) > 0:
    report["errors"].append("rollback-only operability probe left persistent records")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Imported Business Continuity Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- imported projects: `{report['facts'].get('imported_project_count', 0)}`\n"
    f"- imported contracts: `{report['facts'].get('imported_contract_count', 0)}`\n"
    f"- payment requests: `{report['facts'].get('payment_request_count', 0)}`\n"
    f"- done validated payments: `{report['facts'].get('payment_done_validated_count', 0)}`\n"
    f"- ledgers: `{report['facts'].get('payment_ledger_count', 0)}`\n"
    f"- operability final state: `{report['operability_probe'].get('final_state', '')}`\n"
    + ("\n- warnings:\n" + "\n".join(f"  - {line}" for line in report["warnings"]) if report["warnings"] else "")
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[imported_business_continuity_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[imported_business_continuity_guard] PASS")
for line in report["warnings"]:
    print(f" - warning: {line}")
PY
