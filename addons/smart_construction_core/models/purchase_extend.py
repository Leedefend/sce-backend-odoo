# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    project_id = fields.Many2one(
        "project.project",
        string="关联项目",
        help="该采购订单关联的施工项目，默认同步到订单行。",
    )
    plan_id = fields.Many2one(
        "project.material.plan",
        string="物资计划",
        help="来源物资计划，便于追溯生成关系。",
    )

    def button_confirm(self):
        for order in self:
            if order.project_id:
                order.project_id._ensure_operation_allowed(
                    operation_label="确认采购订单",
                    blocked_states=("paused", "closed"),
                )
        res = super().button_confirm()
        if self._is_cost_enabled("smart_construction_core.sc_cost_from_purchase"):
            self._create_cost_ledger_entries()
        return res

    def _is_cost_enabled(self, param_key):
        icp = self.env["ir.config_parameter"].sudo().with_company(self.env.company)
        val = icp.get_param(param_key, default="False")
        return str(val).lower() in ("1", "true", "yes")

    def _create_cost_ledger_entries(self):
        ledger_obj = self.env["project.cost.ledger"]
        for order in self:
            for line in order.order_line:
                vals = line._prepare_cost_ledger_vals()
                if not vals:
                    continue
                existing = ledger_obj.search(
                    [
                        ("source_model", "=", "purchase.order.line"),
                        ("source_line_id", "=", line.id),
                    ],
                    limit=1,
                )
                if existing:
                    existing.write(vals)
                else:
                    ledger_obj.create(vals)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        default=lambda self: self.order_id.project_id,
        help="可单独指定采购行对应的项目，默认继承订单。",
    )
    plan_id = fields.Many2one(
        related="order_id.plan_id",
        string="物资计划",
        store=True,
        readonly=True,
    )
    plan_line_id = fields.Many2one(
        "project.material.plan.line",
        string="计划明细",
        help="记录采购行对应的物资计划行，便于追溯。",
    )
    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        domain="[('project_id', '=', project_id)]",
    )
    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
        help="填写后可自动写入成本台账。",
    )

    @api.model
    def create(self, vals):
        if not vals.get("project_id") and vals.get("order_id"):
            order = self.env["purchase.order"].browse(vals["order_id"])
            vals["project_id"] = order.project_id.id
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        if "project_id" in vals and not vals.get("project_id"):
            for line in self:
                if line.order_id.project_id:
                    line.project_id = line.order_id.project_id
        return res

    def _prepare_cost_ledger_vals(self):
        self.ensure_one()
        project = self.project_id or self.order_id.project_id
        if not project or not self.cost_code_id:
            return False
        amount = self.price_subtotal
        return {
            "project_id": project.id,
            "wbs_id": self.wbs_id.id,
            "cost_code_id": self.cost_code_id.id,
            "date": self.order_id.date_approve or fields.Date.context_today(self),
            "qty": self.product_qty,
            "uom_id": self.product_uom.id,
            "amount": amount,
            "partner_id": self.order_id.partner_id.id,
            "source_model": "purchase.order.line",
            "source_id": self.order_id.id,
            "source_line_id": self.id,
            "note": f"{self.order_id.name} - {self.name or self.product_id.display_name}",
        }
