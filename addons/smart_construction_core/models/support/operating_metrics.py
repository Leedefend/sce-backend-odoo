# -*- coding: utf-8 -*-
from typing import Dict, Iterable, Optional, Sequence

from odoo import _
from odoo.exceptions import ValidationError


RESERVED_STATES: Sequence[str] = ("submit", "approve", "approved", "done")
# Compatibility aliases: existing callers and public fields historically call
# the reservation amount "paid". New code must use the explicit reserved name.
PAID_STATES: Sequence[str] = RESERVED_STATES
PAYMENT_EXECUTION_ACTUAL_PAID_STATES: Sequence[str] = ("paid",)


def get_reserved_states() -> Sequence[str]:
    """Payment-request states that reserve settlement capacity."""
    return RESERVED_STATES


def get_paid_states() -> Sequence[str]:
    """Compatibility alias for the historical reservation-state API."""
    return get_reserved_states()


def settlement_reserved_amount_map(
    env,
    settlement_ids: Iterable[int],
    reserved_states: Optional[Sequence[str]] = None,
) -> Dict[int, float]:
    """Aggregate valid payment-request reservations by settlement.

    主表关联按付款申请金额统计；历史多结算单付款申请没有主表结算单，
    需按明细上的本次申请金额分摊到各结算单。
    """
    ids = list(settlement_ids)
    if not ids:
        return {}
    states = tuple(reserved_states or RESERVED_STATES)
    Payment = env["payment.request"].sudo()
    rows = Payment.read_group(
        [
            ("settlement_id", "in", ids),
            ("type", "=", "pay"),
            ("state", "in", states),
        ],
        ["amount:sum"],
        ["settlement_id"],
    )
    res: Dict[int, float] = {}
    for r in rows:
        sid = r.get("settlement_id")
        if sid and isinstance(sid, (list, tuple)) and sid[0]:
            # read_group returns the aggregated field as "amount" (17.0) but some
            # addons expect "amount_sum" style; keep both for compatibility.
            res[sid[0]] = (r.get("amount_sum") or r.get("amount") or 0.0)
    Line = env["payment.request.line"].sudo()
    line_rows = Line.read_group(
        [
            ("settlement_id", "in", ids),
            ("request_id.settlement_id", "=", False),
            ("request_id.type", "=", "pay"),
            ("request_id.state", "in", states),
            ("current_pay_amount", "!=", 0),
        ],
        ["current_pay_amount:sum"],
        ["settlement_id"],
    )
    for r in line_rows:
        sid = r.get("settlement_id")
        if sid and isinstance(sid, (list, tuple)) and sid[0]:
            res[sid[0]] = res.get(sid[0], 0.0) + (
                r.get("current_pay_amount_sum") or r.get("current_pay_amount") or 0.0
            )
    return res


def settlement_paid_map(
    env,
    settlement_ids: Iterable[int],
    paid_states: Optional[Sequence[str]] = None,
) -> Dict[int, float]:
    """Compatibility alias: historical "paid" fields represent reservation."""
    return settlement_reserved_amount_map(env, settlement_ids, reserved_states=paid_states)


def _currency_rounding(currency) -> float:
    precision = currency.rounding if currency else 0.01
    return precision if precision and precision > 0 else 0.01


def _currency_round(currency, amount: float) -> float:
    return currency.round(amount) if currency else amount


def ensure_payment_settlement_currency_consistency(payment_rec, settlement) -> None:
    """Reject capacity checks when no explicit same-currency fact exists."""
    if not settlement:
        return
    settlement_currency = settlement.currency_id
    payment_currency = payment_rec.currency_id
    if not settlement_currency or not payment_currency or payment_currency != settlement_currency:
        raise ValidationError(_("付款申请币种必须与结算单币种一致；当前流程不提供自动汇率换算。"))

    contracts = payment_rec.contract_id | settlement.contract_id
    mismatched = contracts.filtered(lambda contract: contract.currency_id != settlement_currency)
    if mismatched:
        raise ValidationError(_("合同币种必须与结算单币种一致；当前流程不提供自动汇率换算。"))

    if payment_rec.company_id and settlement.company_id and payment_rec.company_id != settlement.company_id:
        raise ValidationError(_("付款申请公司必须与结算单公司一致。"))


def settlement_payable_base(settlement) -> float:
    """Confirmed-adjustment payment ceiling, rounded in settlement currency."""
    amount = (
        settlement.amount_after_adjustment
        if "amount_after_adjustment" in settlement._fields
        else settlement.amount_total
    )
    return max(_currency_round(settlement.currency_id, amount or 0.0), 0.0)


def settlement_remaining_reservable_amount(settlement, reserved_amount: Optional[float] = None) -> float:
    """Remaining request capacity, never negative, in settlement currency."""
    if reserved_amount is None:
        reserved_amount = settlement_reserved_amount_map(settlement.env, settlement.ids).get(settlement.id, 0.0)
    remaining = settlement_payable_base(settlement) - (reserved_amount or 0.0)
    return max(_currency_round(settlement.currency_id, remaining), 0.0)


def compute_settlement_reservable_excluding_request(payment_rec, settlement, current_amount: float):
    """Return reservation metrics while excluding the request being edited."""
    ensure_payment_settlement_currency_consistency(payment_rec, settlement)
    reserved_states = get_reserved_states()
    reserved = settlement_reserved_amount_map(
        payment_rec.env,
        [settlement.id],
        reserved_states=reserved_states,
    ).get(settlement.id, 0.0)
    if payment_rec.state in reserved_states:
        reserved -= current_amount or 0.0
    reserved = max(_currency_round(settlement.currency_id, reserved), 0.0)
    return {
        "reserved": reserved,
        "payable_base": settlement_payable_base(settlement),
        "payable": settlement_remaining_reservable_amount(settlement, reserved),
        "precision": _currency_rounding(settlement.currency_id),
    }


def settlement_actual_paid_amount_map(env, settlement_ids: Iterable[int]) -> Dict[int, float]:
    """Aggregate actual paid amounts using payment.ledger as the only fact."""
    ids = list(settlement_ids)
    if not ids:
        return {}
    ledgers = env["payment.ledger"].sudo().search(
        [
            "|",
            ("payment_request_id.settlement_id", "in", ids),
            ("payment_request_id.outflow_line_ids.settlement_id", "in", ids),
        ]
    )
    result: Dict[int, float] = {}
    for ledger in ledgers:
        request = ledger.payment_request_id
        if request.settlement_id and request.settlement_id.id in ids:
            ensure_payment_settlement_currency_consistency(request, request.settlement_id)
            sid = request.settlement_id.id
            result[sid] = result.get(sid, 0.0) + (ledger.amount or 0.0)
            continue
        lines = request.outflow_line_ids.filtered(lambda line: line.settlement_id and line.settlement_id.id in ids)
        allocation_total = sum(request.outflow_line_ids.mapped("current_pay_amount"))
        if not allocation_total:
            continue
        for line in lines:
            ensure_payment_settlement_currency_consistency(request, line.settlement_id)
            sid = line.settlement_id.id
            allocated = (ledger.amount or 0.0) * (line.current_pay_amount or 0.0) / allocation_total
            result[sid] = result.get(sid, 0.0) + allocated
    return result


def contract_actual_paid_amount_map(env, contract_ids: Iterable[int]) -> Dict[int, float]:
    """Aggregate only executions whose state is proven to mean payment done."""
    ids = list(contract_ids)
    if not ids:
        return {}
    rows = env["sc.payment.execution"].sudo().read_group(
        [
            ("contract_id", "in", ids),
            ("state", "in", list(PAYMENT_EXECUTION_ACTUAL_PAID_STATES)),
        ],
        ["paid_amount:sum"],
        ["contract_id"],
    )
    return {
        row["contract_id"][0]: row.get("paid_amount_sum", row.get("paid_amount", 0.0)) or 0.0
        for row in rows
        if row.get("contract_id")
    }


def settlement_paid_payable_map(env, settlement_ids: Iterable[int], amount_total_map: Optional[Dict[int, float]] = None, paid_states: Optional[Sequence[str]] = None) -> Dict[int, Dict[str, float]]:
    """Compatibility response: ``paid`` is reserved payment-request amount."""
    ids = list(settlement_ids)
    if not ids:
        return {}
    paid_map = settlement_reserved_amount_map(env, ids, reserved_states=paid_states)
    amount_total_map = amount_total_map or {}
    if not amount_total_map:
        totals = env["sc.settlement.order"].sudo().browse(ids)
        amount_total_map = {rec.id: settlement_payable_base(rec) for rec in totals}

    res: Dict[int, Dict[str, float]] = {}
    for sid in ids:
        paid = paid_map.get(sid, 0.0)
        total = amount_total_map.get(sid, 0.0) or 0.0
        res[sid] = {"paid": paid, "payable": max(total - paid, 0.0)}
    return res


def compute_payment_payable_excluding_self(payment_rec):
    """
    计算当前付款申请所在结算单的已付/可付口径，排除自身，避免自我误伤。
    返回 {'paid': x, 'payable': y, 'precision': rounding}
    """
    settle = payment_rec.settlement_id.sudo()
    if not settle:
        return {"paid": 0.0, "reserved": 0.0, "payable": 0.0, "precision": 0.01}

    metrics = compute_settlement_reservable_excluding_request(
        payment_rec,
        settle,
        payment_rec.amount or 0.0,
    )
    metrics["paid"] = metrics["reserved"]
    return metrics
