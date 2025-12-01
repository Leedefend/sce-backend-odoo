# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    """Extend stock moves with project/cost metadata for cost ledger writes."""

    _inherit = "stock.move"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        compute="_compute_project_fields",
        store=True,
        readonly=False,
    )
    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        domain="[('project_id', '=', project_id)]",
        compute="_compute_project_fields",
        store=True,
        readonly=False,
    )
    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
        compute="_compute_cost_code",
        store=True,
        readonly=False,
    )

    @api.depends(
        "picking_id",
        "picking_id.project_id",
        "product_id",
    )
    def _compute_project_fields(self):
        """Propagate项目/WBS信息:优先取采购行，其次取入库单抬头。"""
        for move in self:
            project = False
            wbs = False
            purchase_line = getattr(move, "purchase_line_id", False)
            if purchase_line:
                project = purchase_line.project_id or purchase_line.order_id.project_id
                wbs = getattr(purchase_line, "wbs_id", False)
            elif move.picking_id and move.picking_id.project_id:
                project = move.picking_id.project_id
            move.project_id = project.id if project else False
            move.wbs_id = wbs.id if wbs else False

    @api.depends("product_id")
    def _compute_cost_code(self):
        """Derive成本科目：采购行优先，其次读取产品默认值。"""
        for move in self:
            cost_code = False
            purchase_line = getattr(move, "purchase_line_id", False)
            if purchase_line and purchase_line.cost_code_id:
                cost_code = purchase_line.cost_code_id
            elif move.product_id.default_cost_code_id:
                cost_code = move.product_id.default_cost_code_id
            move.cost_code_id = cost_code.id if cost_code else False


class StockPicking(models.Model):
    """Hook incoming receipts to create project cost ledger entries."""

    _inherit = "stock.picking"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        help="用于将入库成本写入项目台账。",
    )

    def button_validate(self):
        """After standard validation, push成本信息至台账。"""
        for picking in self:
            if picking.project_id:
                picking.project_id._ensure_operation_allowed(
                    operation_label="确认出入库",
                    blocked_states=("paused", "closed"),
                )
        res = super().button_validate()
        if self._is_cost_enabled("smart_construction_core.sc_cost_from_stock"):
            self._create_cost_ledger_from_moves()
        return res

    def _is_cost_enabled(self, param_key):
        icp = self.env["ir.config_parameter"].sudo().with_company(self.env.company)
        val = icp.get_param(param_key, default="False")
        return str(val).lower() in ("1", "true", "yes")

    def _create_cost_ledger_from_moves(self):
        """Create ledger entries for each incoming move (材料成本自动落账)。"""
        ledger_obj = self.env["project.cost.ledger"]
        for picking in self.filtered(lambda p: p.picking_type_code == "incoming"):
            for move in picking.move_lines:
                if not move.project_id or not move.cost_code_id or move.quantity_done <= 0:
                    continue
                purchase_line = getattr(move, "purchase_line_id", False)
                base_price = purchase_line.price_unit if purchase_line else move.product_id.standard_price
                ledger_date = move.picking_id.date_done.date() if move.picking_id.date_done else fields.Date.context_today(self)
                amount = base_price * move.quantity_done
                vals = {
                    "project_id": move.project_id.id,
                    "wbs_id": move.wbs_id.id,
                    "cost_code_id": move.cost_code_id.id,
                    "date": ledger_date,
                    "qty": move.quantity_done,
                    "uom_id": move.product_uom.id,
                    "amount": amount,
                    "partner_id": picking.partner_id.id,
                    "source_model": "stock.move",
                    "source_id": move.id,
                    "source_line_id": move.id,
                    "note": f"{picking.name} - {move.product_id.display_name}",
                }
                existing = ledger_obj.search([
                    ("source_model", "=", "stock.move"),
                    ("source_line_id", "=", move.id),
                ], limit=1)
                if existing:
                    existing.write(vals)
                else:
                    ledger_obj.create(vals)
