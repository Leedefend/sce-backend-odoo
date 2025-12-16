# -*- coding: utf-8 -*-
from typing import Dict, Iterable, Optional, Sequence

PAID_STATES: Sequence[str] = ("submit", "approve", "approved", "done")


def get_paid_states() -> Sequence[str]:
    """唯一“已付”状态口径。"""
    return PAID_STATES


def settlement_paid_map(env, settlement_ids: Iterable[int], paid_states: Optional[Sequence[str]] = None) -> Dict[int, float]:
    """按结算单聚合付款金额。"""
    ids = list(settlement_ids)
    if not ids:
        return {}
    states = tuple(paid_states or PAID_STATES)
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
    return res


def settlement_paid_payable_map(env, settlement_ids: Iterable[int], amount_total_map: Optional[Dict[int, float]] = None, paid_states: Optional[Sequence[str]] = None) -> Dict[int, Dict[str, float]]:
    """返回 {settlement_id: {'paid': x, 'payable': y}}。"""
    ids = list(settlement_ids)
    if not ids:
        return {}
    paid_map = settlement_paid_map(env, ids, paid_states=paid_states)
    amount_total_map = amount_total_map or {}
    if not amount_total_map:
        totals = env["sc.settlement.order"].sudo().browse(ids)
        amount_total_map = {rec.id: rec.amount_total for rec in totals}

    res: Dict[int, Dict[str, float]] = {}
    for sid in ids:
        paid = paid_map.get(sid, 0.0)
        total = amount_total_map.get(sid, 0.0) or 0.0
        res[sid] = {"paid": paid, "payable": total - paid}
    return res


def compute_payment_payable_excluding_self(payment_rec):
    """
    计算当前付款申请所在结算单的已付/可付口径，排除自身，避免自我误伤。
    返回 {'paid': x, 'payable': y, 'precision': rounding}
    """
    settle = payment_rec.settlement_id.sudo()
    if not settle:
        return {"paid": 0.0, "payable": 0.0, "precision": (payment_rec.company_id.currency_id.rounding or 0.01)}

    paid_states = get_paid_states()
    paid_map = settlement_paid_map(payment_rec.env, [settle.id], paid_states=paid_states)
    paid = paid_map.get(settle.id, 0.0)
    # 排除当前记录自身
    if payment_rec.state in paid_states:
        paid -= payment_rec.amount or 0.0
    payable = (settle.amount_total or 0.0) - paid
    currency = payment_rec.company_id.currency_id
    precision = currency.rounding or 0.01
    if precision <= 0:
        precision = 0.01
    return {"paid": paid, "payable": payable, "precision": precision}
