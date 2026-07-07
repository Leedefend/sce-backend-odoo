# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from odoo import fields


ROOT = Path("/mnt") if Path("/mnt/artifacts").exists() else Path.cwd()
REPORT_JSON = ROOT / "artifacts" / "backend" / "material_cross_document_progress_audit.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "material_cross_document_progress_audit.md"


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_action(label, action, model, res_id, failures):
    _expect(action.get("res_model") == model, "%s: expected res_model=%s, got %s" % (label, model, action.get("res_model")), failures)
    _expect(action.get("res_id") == res_id, "%s: expected res_id=%s, got %s" % (label, res_id, action.get("res_id")), failures)


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _set_validated(record, table):
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))  # noqa: F821
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _approve_submitted(record, table):
    _set_validated(record, table)
    record.action_on_tier_approved()
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        _set_validated(record, table)


def _attachment(record, name):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"material settlement payment traceability").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    record.invalidate_recordset()
    return attachment


def _audit_count(record, event_code, action=False):
    domain = [("model", "=", record._name), ("res_id", "=", record.id), ("event_code", "=", event_code)]
    if action:
        domain.append(("action", "=", action))
    return env["sc.audit.log"].sudo().search_count(domain)  # noqa: F821


def _progress_chain(evidence, failures):
    ok = not failures
    return [
        {
            "kind": "document_state",
            "document": "sc.material.settlement",
            "record_id": evidence.get("settlement") or 0,
            "from_state": "draft",
            "to_state": "submitted",
            "action": "action_submit",
            "ok": ok and bool(evidence.get("settlement")),
        },
        {
            "kind": "document_state",
            "document": "sc.material.settlement",
            "record_id": evidence.get("settlement") or 0,
            "from_state": "submitted",
            "to_state": "confirmed",
            "action": "action_confirm",
            "ok": ok and bool(evidence.get("settlement")),
        },
        {
            "kind": "downstream_link",
            "document": "payment.request",
            "record_id": evidence.get("payment_request") or 0,
            "source_document": "sc.material.settlement",
            "source_record_id": evidence.get("settlement") or 0,
            "action": "material_settlement_confirmed",
            "ok": ok and bool(evidence.get("payment_request")),
        },
        {
            "kind": "document_state",
            "document": "payment.request",
            "record_id": evidence.get("payment_request") or 0,
            "from_state": "draft",
            "to_state": "approved",
            "action": "action_submit/action_on_tier_approved",
            "ok": ok and bool(evidence.get("payment_request")),
        },
        {
            "kind": "downstream_link",
            "document": "sc.payment.execution",
            "record_id": evidence.get("payment_execution") or 0,
            "source_document": "payment.request",
            "source_record_id": evidence.get("payment_request") or 0,
            "action": "action_create_payment_execution",
            "ok": ok and bool(evidence.get("payment_execution")),
        },
        {
            "kind": "document_state",
            "document": "sc.payment.execution",
            "record_id": evidence.get("payment_execution") or 0,
            "from_state": "draft",
            "to_state": "paid",
            "action": "action_confirm/action_paid",
            "ok": ok and bool(evidence.get("payment_execution")),
        },
        {
            "kind": "downstream_link",
            "document": "payment.ledger",
            "record_id": evidence.get("payment_ledger") or 0,
            "source_document": "payment.request",
            "source_record_id": evidence.get("payment_request") or 0,
            "action": "payment_execution_paid",
            "ok": ok and bool(evidence.get("payment_ledger")),
        },
    ]


def _to_markdown(result):
    lines = [
        "# Material Cross-Document Progress Audit",
        "",
        f"- generated_at_utc: {result.get('generated_at_utc', '')}",
        f"- ok: {result.get('ok')}",
        f"- status: {result.get('status', '')}",
        "",
        "## Progress Chain",
        "",
        "| kind | document | record_id | action | ok |",
        "|---|---|---|---|---|",
    ]
    for row in result.get("progress_chain") or []:
        lines.append(
            "| {kind} | `{document}` | `{record_id}` | `{action}` | {ok} |".format(
                kind=row.get("kind", ""),
                document=row.get("document", ""),
                record_id=row.get("record_id", ""),
                action=row.get("action", ""),
                ok=bool(row.get("ok")),
            )
        )
    failures = result.get("failures") or []
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend("- %s" % failure for failure in failures)
    return "\n".join(lines) + "\n"


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MSPET Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MSPET Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    product = env["product.product"].sudo().search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)  # noqa: F821
    if product:
        return product
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "系统默认材料（技术兜底）",
            "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
            "type": "product",
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MSPET Material %s" % token,
            "code": "MSPET-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MSPET-SPEC",
            "uom_text": "件",
        }
    )


def _create_settlement(shared):
    settlement = env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "settlement_date": fields.Date.context_today(env["sc.material.settlement"]),  # noqa: F821
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": shared["product"].id,
                        "material_catalog_id": shared["material"].id,
                        "material_spec": "MSPET-SPEC",
                        "product_uom_id": shared["product"].uom_id.id,
                        "qty": 3.0,
                        "unit_price": 25.0,
                        "tax_rate": 3.0,
                        "note": "MSPET材料结算行",
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    settlement.action_confirm()
    settlement.invalidate_recordset()
    return settlement


failures = []
evidence = {}

try:
    _ensure_groups()
    shared = {
        "project": _project(),
        "supplier": _supplier(),
        "product": _product(),
    }
    shared["material"] = _material(shared["project"])
    settlement = _create_settlement(shared)
    request = settlement.payment_request_id
    _expect(bool(request), "payment_request: expected material settlement payment request", failures)
    if request:
        _expect(request.material_settlement_id == settlement, "payment_request.material_settlement_id: expected settlement link", failures)
        _expect(request.project_id == settlement.project_id, "payment_request.project_id: expected settlement project", failures)
        _expect(request.partner_id == settlement.supplier_id, "payment_request.partner_id: expected settlement supplier", failures)
        _expect(request.amount == settlement.amount_total, "payment_request.amount: expected settlement total", failures)
        _expect(not request.contract_id, "payment_request.contract_id: expected material settlement can proceed without contract", failures)
        _attachment(request, "material-settlement-payment-request")
        request.action_submit()
        request.invalidate_recordset()
        _expect(request.state == "submit", "payment_request.state: expected submit after action_submit", failures)
        _approve_submitted(request, "payment_request")
        request.invalidate_recordset()
        _expect(request.state == "approved", "payment_request.state: expected approved after tier approval", failures)
        _expect(_audit_count(request, "payment_submitted", "action_submit") >= 1, "payment_request.audit_submit missing", failures)
        _expect(_audit_count(request, "payment_approved", "action_on_tier_approved") >= 1, "payment_request.audit_approved missing", failures)

        action = request.action_create_payment_execution()
        _expect(action.get("res_model") == "sc.payment.execution", "payment_execution.action: expected execution action", failures)
        execution = env["sc.payment.execution"].sudo().create(  # noqa: F821
            {
                "payment_request_id": request.id,
                "payment_account_name": "MSPET付款户名",
                "payment_account_no": "MSPET-PAYER-001",
                "receipt_account_name": "MSPET收款户名",
                "receipt_account_no": "MSPET-PAYEE-001",
            }
        )
        _attachment(execution, "material-settlement-payment-execution")
        execution.action_confirm()
        execution.action_paid()
        execution.invalidate_recordset()
        request.invalidate_recordset()
        _expect(execution.state == "paid", "payment_execution.state: expected paid", failures)
        _expect(execution.payment_request_id == request, "payment_execution.payment_request_id: expected request link", failures)
        _expect(execution.project_id == request.project_id, "payment_execution.project_id: expected request project", failures)
        _expect(execution.partner_id == request.partner_id, "payment_execution.partner_id: expected request partner", failures)
        _expect(not execution.contract_id, "payment_execution.contract_id: expected material settlement can proceed without contract", failures)
        _expect(request.state == "done", "payment_request.state: expected done after execution paid", failures)
        _expect(_audit_count(request, "payment_paid", "payment_execution_paid") >= 1, "payment_request.audit_paid missing", failures)

        ledger = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)  # noqa: F821
        _expect(bool(ledger), "payment_ledger: expected ledger from execution", failures)
        if ledger:
            _expect(ledger.amount == request.amount, "payment_ledger.amount: expected request amount", failures)
            _expect_action("payment_ledger.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
            _expect_action("payment_ledger.open_material_settlement", ledger.action_open_settlement(), "sc.material.settlement", settlement.id, failures)
    else:
        execution = False
        ledger = False

    evidence = {
        "project": shared["project"].id,
        "supplier": shared["supplier"].id,
        "material": shared["material"].id,
        "settlement": settlement.id,
        "payment_request": request.id if request else False,
        "payment_execution": execution.id if execution else False,
        "payment_ledger": ledger.id if ledger else False,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "generated_at_utc": _utc_now(),
    "audit": "material_settlement_payment_execution_traceability_audit",
    "ok": not failures,
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "progress_chain": _progress_chain(evidence, failures),
    "reports": {
        "json": str(REPORT_JSON.relative_to(ROOT)),
        "md": str(REPORT_MD.relative_to(ROOT)),
    },
    "failures": failures,
}
_write(REPORT_JSON, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
_write(REPORT_MD, _to_markdown(result))
print(REPORT_JSON)
print(REPORT_MD)
print("MATERIAL_SETTLEMENT_PAYMENT_EXECUTION_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
