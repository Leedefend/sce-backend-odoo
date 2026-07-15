"""Read-only FE-B04 contract and permission probe for acceptance fixtures."""

import json

from odoo.exceptions import AccessError
from odoo.addons.smart_construction_core.services.financial_workspace_contract import (
    build_financial_workspace_contract,
)


RECORDS = {
    "project": ("project.project", "smart_construction_demo.fe_project_a"),
    "contract": ("construction.contract", "smart_construction_demo.fe_contract_a"),
    "settlement": ("sc.settlement.order", "smart_construction_demo.fe_settlement_a"),
    "payment_request": ("payment.request", "smart_construction_demo.fe_request_a_001"),
    "payment_execution": ("sc.payment.execution", "smart_construction_demo.fe_execution_a"),
}

FIELDS = {
    "project": ["name", "company_id", "partner_id", "currency_id", "create_uid", "create_date", "write_uid", "write_date"],
    "contract": [
        "name", "subject", "state", "project_id", "partner_id", "company_id", "currency_id",
        "amount_total", "amount_final", "paid_amount", "line_ids", "create_uid", "create_date", "write_uid", "write_date",
    ],
    "settlement": [
        "name", "title", "state", "project_id", "contract_id", "partner_id", "company_id", "currency_id",
        "amount_total", "settlement_amount", "deduction_amount", "amount_after_adjustment", "paid_amount",
        "remaining_amount", "actual_paid_amount", "remaining_reservable_amount", "payment_request_ids", "line_ids",
        "create_uid", "create_date", "write_uid", "write_date",
    ],
    "payment_request": [
        "name", "state", "project_id", "contract_id", "settlement_id", "partner_id", "company_id", "currency_id",
        "amount", "paid_amount_total", "settlement_reserved_amount", "settlement_remaining_amount",
        "ledger_line_ids", "create_uid", "create_date", "write_uid", "write_date",
    ],
    "payment_execution": [
        "name", "state", "project_id", "contract_id", "payment_request_id", "partner_id", "company_id", "currency_id",
        "planned_amount", "paid_amount", "date_payment", "create_uid", "create_date", "write_uid", "write_date",
    ],
}

USERS = {
    "finance": "demo_role_finance",
    "project_member": "demo_role_project_a_member",
    "pm": "demo_role_pm",
    "owner": "demo_role_owner",
}


def _json_value(value):
    if hasattr(value, "ids"):
        if len(value) == 1:
            return {"id": value.id, "display_name": value.display_name}
        return [{"id": item.id, "display_name": item.display_name} for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _record_values(key, record):
    output = {}
    for field_name in FIELDS[key]:
        if field_name not in record._fields:
            output[field_name] = {"missing": True}
            continue
        field = record._fields[field_name]
        value = record[field_name]
        output[field_name] = {
            "label": field.string,
            "type": field.type,
            "currency_field": getattr(field, "currency_field", None),
            "value": _json_value(value),
        }
        if field.type == "selection":
            selection = field._description_selection(env)
            output[field_name]["display"] = dict(selection).get(value, value)
    return output


def _role_access(user, model_name, record_id):
    model = env[model_name].with_user(user).with_company(user.company_id).with_context(
        allowed_company_ids=user.company_ids.ids,
    )
    model_read = bool(model.check_access_rights("read", raise_exception=False))
    record_read = False
    if model_read:
        record = model.browse(record_id).exists()
        if record:
            try:
                record.check_access_rule("read")
                record_read = True
            except AccessError:
                record_read = False
    return {"model_read": model_read, "record_read": record_read}


payload = {"records": {}, "roles": {}, "relations": {}}
resolved = {}
for key, (model_name, xmlid) in RECORDS.items():
    record = env.ref(xmlid)
    resolved[key] = record
    payload["records"][key] = {
        "model": model_name,
        "model_label": env[model_name]._description,
        "xmlid": xmlid,
        "id": record.id,
        "display_name": record.display_name,
        "fields": _record_values(key, record),
    }

ledgers = env["payment.ledger"].search([("payment_request_id", "=", resolved["payment_request"].id)])
payload["records"]["ledger"] = {
    "model": "payment.ledger",
    "model_label": env["payment.ledger"]._description,
    "count": len(ledgers),
    "rows": [
        {
            "id": row.id,
            "display_name": row.display_name,
            "payment_request_id": _json_value(row.payment_request_id),
            "project_id": _json_value(row.project_id),
            "partner_id": _json_value(row.partner_id),
            "currency_id": _json_value(row.currency_id),
            "amount": row.amount,
            "paid_at": _json_value(row.paid_at),
            "ref": row.ref,
        }
        for row in ledgers
    ],
}

payload["relations"] = {
    "project_to_contracts": [
        {"id": row.id, "display_name": row.display_name}
        for row in env["construction.contract"].search([("project_id", "=", resolved["project"].id)])
    ],
    "contract_to_settlements": [
        {"id": row.id, "display_name": row.display_name}
        for row in env["sc.settlement.order"].search([("contract_id", "=", resolved["contract"].id)])
    ],
    "settlement_to_requests": [
        {"id": row.id, "display_name": row.display_name}
        for row in resolved["settlement"].payment_request_ids
    ],
    "request_to_executions": [
        {"id": row.id, "display_name": row.display_name}
        for row in env["sc.payment.execution"].search([("payment_request_id", "=", resolved["payment_request"].id)])
    ],
    "request_to_ledgers": [
        {"id": row.id, "display_name": row.display_name}
        for row in ledgers
    ],
}

for role, login in USERS.items():
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    row = {
        "login": login,
        "company": user.company_id.display_name,
        "companies": user.company_ids.mapped("display_name"),
        "access": {},
        "workspaces": {},
    }
    for key, record in resolved.items():
        row["access"][key] = _role_access(user, RECORDS[key][0], record.id)
        user_env = env(user=user.id, context={
            **env.context,
            "allowed_company_ids": user.company_ids.ids,
        })
        row["workspaces"][key] = build_financial_workspace_contract(
            user_env,
            RECORDS[key][0],
            record.id,
        )
    row["access"]["ledger"] = _role_access(user, "payment.ledger", ledgers[:1].id) if ledgers else {
        "model_read": bool(env["payment.ledger"].with_user(user).check_access_rights("read", raise_exception=False)),
        "record_read": False,
    }
    request = env["payment.request"].with_user(user).with_company(user.company_id).with_context(
        allowed_company_ids=user.company_ids.ids,
    ).browse(resolved["payment_request"].id)
    try:
        action_result = env["sc.workflow.contract.service"].with_user(user).describe_record(request)
    except Exception as exc:
        action_result = {"error": type(exc).__name__, "message": str(exc)}
    row["payment_request_workflow"] = action_result
    payload["roles"][role] = row


def _fact_value(workspace, key):
    return next((item.get("value") for item in (workspace or {}).get("facts", []) if item.get("key") == key), None)


def _relation_rows(workspace, key):
    return next((item.get("records") or [] for item in (workspace or {}).get("relationships", []) if item.get("key") == key), [])


finance = payload["roles"]["finance"]["workspaces"]
member = payload["roles"]["project_member"]["workspaces"]
pm = payload["roles"]["pm"]["workspaces"]
owner = payload["roles"]["owner"]["workspaces"]
assert finance["project"] is None
assert finance["contract"] and finance["settlement"] and finance["payment_request"] and finance["payment_execution"]
assert _fact_value(finance["contract"], "amount_total") == 1130.0
assert _fact_value(finance["contract"], "paid_amount") == 1000.0
assert _fact_value(finance["settlement"], "settlement_reserved") == 1000.0
assert _fact_value(finance["settlement"], "settlement_actual_paid") == 0.0
assert _fact_value(finance["settlement"], "settlement_remaining") == 0.0
assert [row["label"] for row in _relation_rows(finance["payment_request"], "executions")] == ["FE-A-PE-001"]
assert _relation_rows(finance["payment_request"], "ledgers") == []
assert member["project"] and member["contract"] is None and member["settlement"] is None
assert _relation_rows(member["project"], "contracts") == []
assert pm["project"] and pm["contract"] and pm["settlement"] and pm["payment_request"] is None
assert owner["contract"] and owner["settlement"] is None and owner["payment_request"] is None
for role_row in (member, owner):
    assert "FE-A-PR-001" not in json.dumps(role_row, ensure_ascii=False)

print("[verify.frontend.financial_workspace.runtime] PASS")
print("FRONTEND_FINANCIAL_WORKSPACE_RUNTIME_JSON=%s" % json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str))
