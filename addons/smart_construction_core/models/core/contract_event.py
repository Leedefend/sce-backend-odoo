# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    @api.constrains("amount_impact", "tax_amount")
    def _check_amounts(self):
        for rec in self:
            if rec.tax_amount < 0:
                raise ValidationError(_("税额不能为负数。"))

    def action_submit(self):
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        self.write({"state": "approved"})
        return True

    def action_reject(self):
        self.write({"state": "rejected"})
        return True

    def action_done(self):
        self.write({"state": "done"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True
