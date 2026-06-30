# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy

from odoo import api, fields, models


SETTLEMENT_ACTION_XMLIDS = (
    "smart_construction_core.action_sc_settlement_order_income",
    "smart_construction_core.action_sc_settlement_order_expense",
)

SETTLEMENT_ACCEPTANCE_FIELD_MAP = {
    "user_acceptance_document_state": ("settlement_acceptance_document_state", "单据状态"),
    "user_acceptance_document_no": ("settlement_acceptance_document_no", "单据编号"),
    "user_acceptance_project_name": ("settlement_acceptance_project_name", "项目名称"),
    "user_acceptance_document_date": ("settlement_acceptance_document_date", "单据日期"),
    "user_acceptance_title": ("settlement_acceptance_title", "标题/结算内容"),
    "user_acceptance_partner_name": ("settlement_acceptance_partner_name", "结算单位"),
    "user_acceptance_amount": ("settlement_acceptance_amount", "结算金额"),
    "user_acceptance_payment_state": ("settlement_acceptance_payment_state", "付款状态"),
    "user_acceptance_paid_amount": ("settlement_acceptance_paid_amount", "已付款金额"),
    "user_acceptance_unpaid_amount": ("settlement_acceptance_unpaid_amount", "未付款金额"),
    "user_acceptance_request_state": ("settlement_acceptance_request_state", "支付申请状态"),
    "user_acceptance_requested_amount": ("settlement_acceptance_requested_amount", "已申请金额"),
    "user_acceptance_unrequested_amount": ("settlement_acceptance_unrequested_amount", "未申请金额"),
    "user_acceptance_note": ("settlement_acceptance_note", "结算说明/备注"),
    "user_acceptance_attachment": ("settlement_acceptance_attachment", "附件"),
    "user_acceptance_creator": ("settlement_acceptance_creator", "录入人"),
    "user_acceptance_created_at": ("settlement_acceptance_created_at", "录入时间"),
}


class UIBusinessConfigContractSettlementFormalSync(models.Model):
    _inherit = "ui.business.config.contract"

    @api.model
    def sc_sync_settlement_formal_list_contracts(self):
        Contract = self.sudo()
        changed = 0
        for action_xmlid in SETTLEMENT_ACTION_XMLIDS:
            action = self.env.ref(action_xmlid, raise_if_not_found=False)
            if not action:
                continue
            contracts = Contract.search(
                [
                    ("model", "=", "sc.settlement.order"),
                    ("action_id", "=", action.id),
                    ("status", "=", "published"),
                    ("view_type", "in", ["tree", "list"]),
                ],
                order="id",
            )
            for contract in contracts:
                payload = deepcopy(contract.contract_json or {})
                if not isinstance(payload, dict):
                    continue
                next_payload = self._sc_settlement_formalize_contract_payload(payload)
                if next_payload == payload:
                    continue
                contract.write(
                    {
                        "contract_json": next_payload,
                        "version_no": int(contract.version_no or 1) + 1,
                        "published_at": fields.Datetime.now(),
                    }
                )
                changed += 1
        return changed

    @api.model
    def _sc_settlement_formalize_contract_payload(self, payload):
        def replace_value(value):
            mapped = SETTLEMENT_ACCEPTANCE_FIELD_MAP.get(str(value or "").strip())
            return mapped[0] if mapped else value

        def replace_label(field_name, label):
            for _legacy, (formal_name, formal_label) in SETTLEMENT_ACCEPTANCE_FIELD_MAP.items():
                if field_name == formal_name:
                    return formal_label
            return label

        def visit(value):
            if isinstance(value, list):
                return [visit(item) for item in value]
            if isinstance(value, dict):
                row = {key: visit(item) for key, item in value.items()}
                for key in ("name", "field", "field_name"):
                    if key in row:
                        row[key] = replace_value(row[key])
                field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
                if field_name:
                    if "label" in row:
                        row["label"] = replace_label(field_name, row.get("label"))
                    if "string" in row:
                        row["string"] = replace_label(field_name, row.get("string"))
                return row
            if isinstance(value, str):
                return replace_value(value)
            return value

        next_payload = visit(payload)
        if not isinstance(next_payload, dict):
            return payload
        orchestration = next_payload.get("view_orchestration")
        if isinstance(orchestration, dict):
            context = dict(orchestration.get("context") or {})
            context["source"] = "smart_construction_core.formal_settlement_list_contract_sync"
            orchestration["context"] = context
        return next_payload
