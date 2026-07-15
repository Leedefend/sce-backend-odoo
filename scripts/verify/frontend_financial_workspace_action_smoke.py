"""Transactional proof for the FE-B04 permitted and rejected action paths."""

import json

from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
    PaymentRequestAvailableActionsHandler,
)
from odoo.addons.smart_construction_core.handlers.payment_request_execute import (
    PaymentRequestExecuteHandler,
)
from odoo.addons.smart_construction_core.models.support import operating_metrics as opm
from odoo.exceptions import AccessError


def fail(message):
    raise RuntimeError("[verify.frontend.financial_workspace.action] %s" % message)


def user_env(login):
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    if not user:
        fail("missing user %s" % login)
    return env(user=user.id, context={
        **env.context,
        "allowed_company_ids": user.company_ids.ids,
    })


journey = env.ref("smart_construction_demo.fe_journey_payment_request_a")
settlement = env.ref("smart_construction_demo.fe_journey_settlement_a")
draft = env.ref("smart_construction_demo.fe_request_a_002")
finance_env = user_env("demo_role_finance")
member_env = user_env("demo_role_project_a_member")

savepoint = env.cr.savepoint()
savepoint.__enter__()
try:
    finance_request = finance_env["payment.request"].browse(journey.id)
    before = {
        "state": finance_request.state,
        "ledger_count": len(finance_request.ledger_line_ids),
        "actual_paid": opm.settlement_actual_paid_amount_map(finance_env, [settlement.id]).get(settlement.id, 0.0),
        "reserved": opm.settlement_reserved_amount_map(finance_env, [settlement.id]).get(settlement.id, 0.0),
        "remaining": opm.settlement_remaining_reservable_amount(settlement),
    }
    available = PaymentRequestAvailableActionsHandler(
        finance_env,
        payload={"id": journey.id},
    ).run(payload={"id": journey.id})
    rows = (available.get("data") or {}).get("actions") or []
    submit = next((row for row in rows if row.get("key") == "submit"), None)
    if not submit or not submit.get("allowed") or not submit.get("actor_matches_required_role"):
        fail("finance submit action is not authoritatively available: %s" % submit)

    unauthorized_before = (journey.state, len(journey.ledger_line_ids))
    try:
        PaymentRequestExecuteHandler(member_env, payload={
            "id": journey.id,
            "action": "submit",
            "request_id": "fe_b04_member_denied",
        }).run(payload={
            "id": journey.id,
            "action": "submit",
            "request_id": "fe_b04_member_denied",
        })
    except AccessError:
        pass
    else:
        fail("project member execution did not raise AccessError")
    journey.invalidate_recordset()
    if (journey.state, len(journey.ledger_line_ids)) != unauthorized_before:
        fail("unauthorized action changed business data")

    success = PaymentRequestExecuteHandler(finance_env, payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_once",
    }).run(payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_once",
    })
    finance_request.invalidate_recordset()
    ledger = finance_env["payment.ledger"].search([("payment_request_id", "=", journey.id)])
    after = {
        "state": finance_request.state,
        "ledger_count": len(ledger),
        "ledger_amount": ledger.amount if len(ledger) == 1 else None,
        "actual_paid": opm.settlement_actual_paid_amount_map(finance_env, [settlement.id]).get(settlement.id, 0.0),
        "reserved": opm.settlement_reserved_amount_map(finance_env, [settlement.id]).get(settlement.id, 0.0),
        "remaining": opm.settlement_remaining_reservable_amount(settlement),
    }
    if not success.get("ok") or after != {
        "state": "submit",
        "ledger_count": 0,
        "ledger_amount": None,
        "actual_paid": 0.0,
        "reserved": 100.0,
        "remaining": 0.0,
    }:
        fail("successful action did not close the authoritative loop: %s" % after)

    replay = PaymentRequestExecuteHandler(finance_env, payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_once",
    }).run(payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_once",
    })
    if not replay.get("ok"):
        fail("same request id replay failed unexpectedly: %s" % replay)
    finance_request.invalidate_recordset()
    replay_snapshot = {
        "state": finance_request.state,
        "ledger_count": finance_env["payment.ledger"].search_count([("payment_request_id", "=", journey.id)]),
        "reserved": opm.settlement_reserved_amount_map(finance_env, [settlement.id]).get(settlement.id, 0.0),
    }
    if replay_snapshot != {"state": "submit", "ledger_count": 0, "reserved": 100.0}:
        fail("same request id replay changed authoritative data: %s" % replay_snapshot)
    if finance_env["payment.ledger"].search_count([("payment_request_id", "=", journey.id)]) != 0:
        fail("idempotent replay duplicated the ledger")

    duplicate = PaymentRequestExecuteHandler(finance_env, payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_again",
    }).run(payload={
        "id": journey.id,
        "action": "submit",
        "request_id": "fe_b04_done_again",
    })
    if not duplicate.get("ok"):
        fail("new duplicate submission failed unexpectedly: %s" % duplicate)
    if finance_env["payment.ledger"].search_count([("payment_request_id", "=", journey.id)]) != 0:
        fail("duplicate business error changed ledger data")

    draft_before = (draft.state, len(draft.ledger_line_ids), draft.amount)
    invalid = PaymentRequestExecuteHandler(finance_env, payload={
        "id": draft.id,
        "action": "done",
        "request_id": "fe_b04_invalid_state",
    }).run(payload={
        "id": draft.id,
        "action": "done",
        "request_id": "fe_b04_invalid_state",
    })
    draft.invalidate_recordset()
    if invalid.get("ok") or (draft.state, len(draft.ledger_line_ids), draft.amount) != draft_before:
        fail("invalid-state failure changed business data")

    print("[verify.frontend.financial_workspace.action] PASS")
    print(json.dumps({
        "before": before,
        "after": after,
        "available_actions_before": [{"key": row.get("key"), "label": row.get("label"), "allowed": row.get("allowed")} for row in rows],
        "unauthorized_unchanged": True,
        "invalid_state_unchanged": True,
        "same_request_id_replayed_without_mutation": True,
        "new_request_id_replayed_without_mutation": True,
        "duplicate_ledger_count": 0,
    }, ensure_ascii=False, indent=2))
finally:
    savepoint.__exit__(Exception, Exception("rollback FE-B04 action smoke"), None)
