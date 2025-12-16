# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    project_id = fields.Many2one(
        "project.project",
        string="关联项目",
        help="用于将发票/凭证成本写入项目台账。",
    )

    def action_post(self):
        res = super().action_post()
        if self._is_cost_enabled("smart_construction_core.sc_cost_from_account_move"):
            self._create_cost_ledger_entries()
        return res

    def button_draft(self):
        res = super().button_draft()
        # 清理当前凭证生成的成本台账，确保过账/反过账一一对应
        ledger_obj = self.env["project.cost.ledger"]
        for move in self:
            ledger_obj.search(
                [
                    ("source_model", "=", "account.move.line"),
                    ("source_line_id", "in", move.line_ids.ids),
                ]
            ).unlink()
        return res

    def _is_cost_enabled(self, param_key):
        icp = self.env["ir.config_parameter"].sudo().with_company(self.env.company)
        val = icp.get_param(param_key, default="False")
        return str(val).lower() in ("1", "true", "yes")

    def _create_cost_ledger_entries(self):
        ledger_obj = self.env["project.cost.ledger"]
        for move in self.filtered(lambda m: m.move_type in ("in_invoice", "entry")):
            for line in move.line_ids.filtered(lambda l: not l.display_type):
                vals = line._prepare_cost_ledger_vals()
                if not vals:
                    continue
                existing = ledger_obj.search(
                    [
                        ("source_model", "=", "account.move.line"),
                        ("source_line_id", "=", line.id),
                    ],
                    limit=1,
                )
                if existing:
                    existing.write(vals)
                else:
                    ledger_obj.create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="move_id.project_id",
        store=True,
        readonly=False,
    )
    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        domain="[('project_id', '=', project_id)]",
    )
    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
    )

    def _prepare_cost_ledger_vals(self):
        self.ensure_one()
        project = self.project_id
        if not project or not self.cost_code_id:
            return False
        internal_group = self.account_id.internal_group
        if internal_group not in ("expense", "asset"):
            return False
        amount = self.debit
        if amount <= 0:
            return False
        return {
            "project_id": project.id,
            "wbs_id": self.wbs_id.id,
            "cost_code_id": self.cost_code_id.id,
            "date": self.date or fields.Date.context_today(self),
            "qty": self.quantity,
            "uom_id": self.product_uom_id.id,
            "amount": amount,
            "partner_id": self.partner_id.id,
            "source_model": "account.move.line",
            "source_id": self.move_id.id,
            "source_line_id": self.id,
            "note": f"{self.move_id.name or self.move_id.ref} - {self.name}",
        }
