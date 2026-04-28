# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "tier.validation"]

    _state_from = ["draft", "sent"]
    _state_to = ["purchase"]
    _cancel_state = "cancel"

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
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False, tracking=True)

    def button_confirm(self):
        for order in self:
            if order.project_id:
                order.project_id._ensure_operation_allowed(
                    operation_label="确认采购订单",
                    blocked_states=("paused", "closed"),
                )
            if order._requires_purchase_approval() and order.validation_status != "validated":
                order._request_purchase_validation()
                continue
            policy = self.env["sc.approval.policy"].get_active_policy(order._name, company=order.company_id)
            if policy and not order._requires_purchase_approval():
                policy.assert_user_can_approve()
        to_confirm = self.filtered(
            lambda order: not order._requires_purchase_approval() or order.validation_status == "validated"
        )
        if not to_confirm:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("采购订单已提交审批"),
                    "message": _("请等待采购审批能力组完成统一审批。"),
                    "type": "success",
                    "sticky": False,
                },
            }
        res = super(PurchaseOrder, to_confirm).button_confirm()
        if self._is_cost_enabled("smart_construction_core.sc_cost_from_purchase"):
            to_confirm._create_cost_ledger_entries()
        return res

    def _requires_purchase_approval(self):
        self.ensure_one()
        return self.env["sc.approval.policy"].is_approval_required(self._name, company=self.company_id)

    def _request_purchase_validation(self):
        self.ensure_one()
        if self.state not in ("draft", "sent"):
            raise UserError(_("仅询价单/报价单可以提交采购审批。"))
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("采购订单已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("采购订单已经在统一审批流程中，请等待审批完成。"))
        self.with_context(skip_validation_check=True).write({"reject_reason": False})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state in ("draft", "sent")

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for order in self:
            if order.state not in ("draft", "sent"):
                continue
            if order.validation_status != "validated":
                raise UserError(_("采购订单尚未完成统一审批流程。"))
            order.with_context(skip_validation_check=True).write({"reject_reason": False})
        return self.button_confirm()

    def action_on_tier_rejected(self, reason=None):
        for order in self:
            if order.state not in ("draft", "sent"):
                continue
            order.with_context(skip_validation_check=True).write(
                {"reject_reason": reason or order._get_tier_reject_reason()}
            )

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
        string="工程结构",
        domain="[('project_id', '=', project_id)]",
    )
    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
        help="填写后可自动写入成本台账。",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("project_id") and vals.get("order_id"):
                order = self.env["purchase.order"].browse(vals["order_id"])
                vals["project_id"] = order.project_id.id
        return super().create(vals_list)

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
