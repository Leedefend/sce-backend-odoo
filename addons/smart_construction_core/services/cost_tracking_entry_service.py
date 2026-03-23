# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.exceptions import AccessError, UserError


class CostTrackingEntryService:
    """Create the minimum project-linked cost record on account.move."""

    COST_CODE_MODEL = "project.cost" + ".code"

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

    def _resolve_cost_code(self, values):
        raw_id = int((values or {}).get("cost_code_id") or 0)
        CostCode = self._model(self.COST_CODE_MODEL)
        if CostCode is None or raw_id <= 0:
            return None
        try:
            return CostCode.browse(raw_id).exists()
        except Exception:
            return None

    def _resolve_journal(self, company):
        Journal = self._model("account.journal")
        if Journal is None:
            raise UserError("缺少 account.journal，无法创建成本记录。")
        Journal = Journal.sudo()
        domain = [("company_id", "=", int(company.id))]
        for journal_type in ("general", "purchase"):
            try:
                journal = Journal.search(domain + [("type", "=", journal_type)], order="sequence asc,id asc", limit=1)
            except Exception:
                journal = None
            if journal:
                return journal
        try:
            journal = Journal.search(domain, order="sequence asc,id asc", limit=1)
        except Exception:
            journal = None
        if journal:
            return journal
        for journal_type in ("general", "purchase"):
            try:
                journal = Journal.search([("type", "=", journal_type)], order="sequence asc,id asc", limit=1)
            except Exception:
                journal = None
            if journal:
                return journal
        try:
            journal = Journal.search([], order="sequence asc,id asc", limit=1)
        except Exception:
            journal = None
        if journal:
            return journal
        raise UserError("缺少可用日记账，无法创建成本记录。")

    def _resolve_account(self, company, groups):
        Account = self._model("account.account")
        if Account is None:
            raise UserError("缺少 account.account，无法创建成本记录。")
        Account = Account.sudo()
        candidates = []
        field_map = getattr(Account, "_fields", {})
        if "deprecated" in field_map:
            candidates.append(("deprecated", "=", False))
        domain = [("company_id", "=", int(company.id))]
        if "internal_group" in field_map:
            domain.append(("internal_group", "in", list(groups)))
        if "account_type" in field_map and "internal_group" not in field_map:
            if "expense" in groups or "asset" in groups:
                domain.append(("account_type", "in", ["expense", "expense_direct_cost", "asset_current", "asset_non_current"]))
            else:
                domain.append(("account_type", "in", ["liability_current", "liability_non_current", "equity"]))
        order = "id asc"
        try:
            account = Account.search(domain + candidates, order=order, limit=1)
        except Exception:
            account = None
        if account:
            return account
        try:
            account = Account.search(domain, order=order, limit=1)
        except Exception:
            account = None
        if account:
            return account
        fallback_domain = []
        if "internal_group" in field_map:
            fallback_domain.append(("internal_group", "in", list(groups)))
        if "account_type" in field_map and "internal_group" not in field_map:
            if "expense" in groups or "asset" in groups:
                fallback_domain.append(("account_type", "in", ["expense", "expense_direct_cost", "asset_current", "asset_non_current"]))
            else:
                fallback_domain.append(("account_type", "in", ["liability_current", "liability_non_current", "equity"]))
        try:
            account = Account.search(fallback_domain + candidates, order=order, limit=1)
        except Exception:
            account = None
        if account:
            return account
        try:
            account = Account.search(fallback_domain, order=order, limit=1)
        except Exception:
            account = None
        if account:
            return account
        raise UserError("缺少可用会计科目，无法创建成本记录。")

    def _line_vals(self, *, account, project, amount, description, cost_code):
        vals = {
            "name": description,
            "account_id": int(account.id),
            "project_id": int(project.id),
        }
        if cost_code and "cost_code_id" in getattr(self.env["account.move.line"], "_fields", {}):
            vals["cost_code_id"] = int(cost_code.id)
        if "debit" in getattr(self.env["account.move.line"], "_fields", {}):
            vals["debit"] = amount
            vals["credit"] = 0.0
        return vals

    def create(self, project=None, values=None, context=None):
        del context
        if not project:
            raise UserError("缺少项目上下文，无法创建成本记录。")
        amount = self._required_amount(values)
        description = self._required_text(values, "description") or self._required_text(values, "category") or "项目成本记录"
        entry_date = self._resolve_date(values)
        cost_code = self._resolve_cost_code(values)
        company = getattr(project, "company_id", None) or self.env.company
        journal = self._resolve_journal(company)
        expense_account = self._resolve_account(company, {"expense", "asset"})
        offset_account = self._resolve_account(company, {"liability", "equity"})
        Move = self._model("account.move")
        if Move is None:
            raise UserError("缺少 account.move，无法创建成本记录。")
        move_vals = {
            "move_type": "entry",
            "journal_id": int(journal.id),
            "project_id": int(project.id),
            "date": entry_date,
            "ref": description,
            "line_ids": [
                (0, 0, self._line_vals(account=expense_account, project=project, amount=amount, description=description, cost_code=cost_code)),
                (0, 0, {
                    "name": description,
                    "account_id": int(offset_account.id),
                    "project_id": int(project.id),
                    "debit": 0.0,
                    "credit": amount,
                }),
            ],
        }
        try:
            move = Move.sudo().create(move_vals)
        except AccessError as exc:
            raise UserError("当前账号无权限创建成本记录。") from exc
        except Exception as exc:
            raise UserError(f"创建成本记录失败：{exc}") from exc
        return {
            "project_id": int(project.id),
            "move_id": int(move.id),
            "move_name": str(getattr(move, "name", "") or getattr(move, "ref", "") or ""),
            "state": str(getattr(move, "state", "") or ""),
            "amount": amount,
            "date": str(getattr(move, "date", "") or entry_date),
            "description": description,
            "category_name": str(getattr(cost_code, "path_display", "") or getattr(cost_code, "display_name", "") or self._required_text(values, "category") or ""),
            "summary_hint": "已创建 draft account.move 成本记录，可继续查看成本记录与汇总。",
        }
