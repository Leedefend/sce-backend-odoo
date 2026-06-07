# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScContractEvent(models.Model):
    _name = "sc.contract.event"
    _description = "合同履约事件"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "event_date desc, id desc"

    name = fields.Char(string="事件名称", required=True, tracking=True)
    event_type = fields.Selection(
        [
            ("design_change", "设计变更"),
            ("site_instruction", "现场签证"),
            ("quality_price_approval", "认质认价"),
            ("material_price_adjustment", "材料调差"),
            ("claim", "争议索赔"),
            ("output_value_report", "产值申报"),
            ("settlement_audit", "结算审核"),
            ("legacy_amount_difference", "历史金额差异"),
            ("legacy_approval", "历史审批"),
        ],
        string="事件类型",
        required=True,
        index=True,
        tracking=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    contract_id = fields.Many2one("construction.contract", string="合同", index=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="相对方/供应商", index=True)
    cost_code_id = fields.Many2one("project.cost.code", string="成本科目", index=True)
    event_no = fields.Char(string="业务单号", index=True)
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入"), ("system", "系统")], string="来源端", default="pc", index=True)
    event_date = fields.Date(string="事件日期", default=fields.Date.context_today, index=True)
    applicant_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user, index=True)
    department_id = fields.Many2one("hr.department", string="申请部门", index=True)
    amount_impact = fields.Monetary(string="金额影响", currency_field="currency_id")
    tax_excluded_amount = fields.Monetary(string="不含税金额", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="币种", default=lambda self: self.env.company.currency_id.id, required=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id")
    change_limit_amount = fields.Monetary(string="变更控制上限", currency_field="currency_id")
    limit_control_result = fields.Selection([("ok", "未超限"), ("warn", "预警"), ("block", "超限阻断")], string="上限控制结果", default="ok", index=True)
    settlement_included = fields.Boolean(string="纳入结算")
    attachment_ids = fields.Many2many("ir.attachment", "sc_contract_event_attachment_rel", "event_id", "attachment_id", string="事件附件")
    description = fields.Text(string="事件说明")
    basis = fields.Text(string="依据")
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已审批"), ("rejected", "已驳回"), ("done", "已完成"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_key = fields.Char(string="来源业务键", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.constrains("amount_impact", "tax_amount")
    def _check_amounts(self):
        for rec in self:
            if rec.tax_amount < 0:
                raise ValidationError(_("税额不能为负数。"))

    def action_submit(self):
        for rec in self:
            if rec.state not in ("draft", "rejected"):
                raise UserError(_("只有草稿或已驳回的合同履约事件可以提交。"))
            rec._check_business_anchor()
            rec.write({"state": "submitted"})
        return True

    def action_approve(self):
        for rec in self:
            if rec.state != "submitted":
                raise UserError(_("只有已提交的合同履约事件可以审批。"))
            rec._check_business_anchor()
            rec.write({"state": "approved"})
        return True

    def action_reject(self):
        for rec in self:
            if rec.state != "submitted":
                raise UserError(_("只有已提交的合同履约事件可以驳回。"))
            rec.write({"state": "rejected"})
        return True

    def action_done(self):
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("只有已审批的合同履约事件可以完成。"))
            rec._check_business_anchor()
            rec.write({"state": "done"})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "submitted", "rejected"):
                raise UserError(_("只有草稿、已提交或已驳回的合同履约事件可以取消。"))
            rec.write({"state": "cancel"})
        return True

    def _check_business_anchor(self):
        for rec in self:
            if not rec.event_date:
                raise UserError(_("合同履约事件必须填写事件日期。"))
            if rec.contract_id and rec.contract_id.project_id != rec.project_id:
                raise UserError(_("合同履约事件的合同必须属于当前项目。"))
