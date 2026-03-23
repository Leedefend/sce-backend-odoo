# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.exceptions import AccessError, UserError


class PaymentSliceEntryService:
    """Create the minimum project-linked draft payment.request."""

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _required_text(self, values, key):
        return str((values or {}).get(key) or "").strip()

    def _required_amount(self, values):
        raw = (values or {}).get("amount")
        try:
            amount = round(float(raw or 0.0), 2)
        except Exception as exc:
            raise UserError("金额必须为有效数字。") from exc
        if amount <= 0:
            raise UserError("金额必须大于 0。")
        return amount

    def _resolve_date(self, values):
        raw = self._required_text(values, "date")
        return raw or str(fields.Date.today())

    def _resolve_partner(self, project):
        partner = getattr(project, "partner_id", None)
        if partner:
            return partner
        user_partner = getattr(self.env.user, "partner_id", None)
        if user_partner:
            return user_partner
        company_partner = getattr(getattr(project, "company_id", None), "partner_id", None) or getattr(self.env.company, "partner_id", None)
        if company_partner:
            return company_partner
        Partner = self._model("res.partner")
        if Partner is None:
            raise UserError("缺少可用往来单位，无法创建付款记录。")
        try:
            partner = Partner.sudo().search([("active", "=", True)], order="id asc", limit=1)
        except Exception:
            partner = None
        if partner:
            return partner
        raise UserError("缺少可用往来单位，无法创建付款记录。")

    def create(self, project=None, values=None, context=None):
        del context
        if not project:
            raise UserError("缺少项目上下文，无法创建付款记录。")
        PaymentRequest = self._model("payment.request")
        if PaymentRequest is None:
            raise UserError("缺少 payment.request，无法创建付款记录。")
        amount = self._required_amount(values)
        description = self._required_text(values, "description") or "项目付款记录"
        entry_date = self._resolve_date(values)
        partner = self._resolve_partner(project)
        currency = getattr(project, "company_id", None) and getattr(project.company_id, "currency_id", None) or getattr(self.env.company, "currency_id", None)
        request_vals = {
            "type": "pay",
            "project_id": int(project.id),
            "partner_id": int(partner.id),
            "currency_id": int(getattr(currency, "id", 0) or 0),
            "amount": amount,
            "date_request": entry_date,
            "note": description,
            "state": "draft",
        }
        try:
            request = PaymentRequest.sudo().create(request_vals)
        except AccessError as exc:
            raise UserError("当前账号无权限创建付款记录。") from exc
        except Exception as exc:
            raise UserError(f"创建付款记录失败：{exc}") from exc
        return {
            "project_id": int(project.id),
            "payment_request_id": int(request.id),
            "payment_request_name": str(getattr(request, "name", "") or ""),
            "state": str(getattr(request, "state", "") or ""),
            "amount": amount,
            "date": str(getattr(request, "date_request", "") or entry_date),
            "description": description,
            "partner_name": str(getattr(partner, "display_name", "") or ""),
            "summary_hint": "已创建 draft payment.request 付款记录，可继续查看付款记录与付款汇总。",
        }
