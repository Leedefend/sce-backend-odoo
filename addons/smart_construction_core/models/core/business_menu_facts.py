# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScBusinessFactMixin(models.AbstractModel):
    _name = "sc.business.fact.mixin"
    _description = "业务事实通用字段"
    _order = "business_date desc, id desc"

    name = fields.Char(string="名称", required=True, default="新建", tracking=True)
    document_no = fields.Char(string="业务编号", copy=False, readonly=True, index=True)
    fact_type = fields.Selection(selection="_selection_fact_type", string="业务类型", required=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    requester_id = fields.Many2one(
        "res.users",
        string="申请人",
        default=lambda self: self.env.user,
        index=True,
        tracking=True,
    )
    handler_id = fields.Many2one("res.users", string="经办人", index=True, tracking=True)
    department_id = fields.Many2one("hr.department", string="部门", index=True)
    business_date = fields.Date(string="业务日期", default=fields.Date.context_today, index=True)
    planned_date = fields.Date(string="计划日期", index=True)
    due_date = fields.Date(string="截止日期", index=True)
    quantity = fields.Float(string="数量")
    uom_id = fields.Many2one("uom.uom", string="单位")
    unit_price = fields.Monetary(string="单价", currency_field="currency_id")
    amount = fields.Monetary(string="金额", currency_field="currency_id")
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("in_progress", "办理中"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    description = fields.Text(string="说明")
    result_note = fields.Text(string="办理结果")
    active = fields.Boolean(string="有效", default=True, index=True)

    def _selection_fact_type(self):
        return []

    def _business_specific_fields(self):
        return []

    def _require_fields(self, field_names):
        missing = []
        for field_name in field_names:
            field = self._fields[field_name]
            if not self[field_name]:
                missing.append(field.string)
        if missing:
            raise ValidationError(_("请补齐以下字段后再办理：%s") % "、".join(missing))

    def _check_submit_requirements(self):
        for record in self:
            record._require_fields(["name", "fact_type"])

    def _check_done_requirements(self):
        self._check_submit_requirements()

    @api.constrains("quantity", "unit_price", "amount", "tax_amount")
    def _check_non_negative_amounts(self):
        for record in self:
            for field_name in ("quantity", "unit_price", "amount", "tax_amount"):
                if record[field_name] < 0:
                    raise ValidationError(_("%s不能为负数。") % record._fields[field_name].string)

    @api.constrains("planned_date", "due_date")
    def _check_plan_due_order(self):
        for record in self:
            if record.planned_date and record.due_date and record.planned_date > record.due_date:
                raise ValidationError(_("计划日期不能晚于截止日期。"))

    @api.model_create_multi
    def create(self, vals_list):
        type_labels = dict(self._selection_fact_type())
        for vals in vals_list:
            fact_type = vals.get("fact_type") or self.env.context.get("default_fact_type")
            vals.setdefault("fact_type", fact_type)
            if vals.get("name", "新建") == "新建" and fact_type:
                vals["name"] = type_labels.get(fact_type) or self.env.context.get("default_name") or "新建"
            vals.setdefault("document_no", self._next_document_no(fact_type))
        return super().create(vals_list)

    def _next_document_no(self, fact_type):
        token = (fact_type or self._name).upper().replace(".", "_").replace("-", "_")
        return "%s-%s" % (token[:24], self.env["ir.sequence"].sudo().next_by_code("sc.business.fact") or "NEW")

    def action_submit(self):
        self._check_submit_requirements()
        self.write({"state": "in_progress"})
        return True

    def action_confirm(self):
        return self.action_submit()

    def action_done(self):
        self._check_done_requirements()
        self.write({"state": "done"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScDashboardCockpitFact(models.Model):
    _name = "sc.dashboard.cockpit.fact"
    _description = "驾驶舱业务事实"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [("fund_cockpit", "资金驾驶舱"), ("cost_cockpit", "成本驾驶舱")]

    cockpit_scope = fields.Selection(
        [("company", "公司"), ("project", "项目"), ("department", "部门")],
        string="驾驶舱范围",
        default="project",
    )
    metric_period = fields.Selection(
        [("day", "日"), ("week", "周"), ("month", "月"), ("quarter", "季"), ("year", "年")],
        string="统计周期",
        default="month",
    )
    metric_value = fields.Float(string="指标值")
    source_model = fields.Char(string="来源模型")
    source_res_id = fields.Integer(string="来源记录ID")

    _sql_constraints = [
        (
            "dashboard_cockpit_source_unique",
            "unique(fact_type, source_model, source_res_id)",
            "同一来源指标已经进入驾驶舱。",
        ),
    ]

    def _business_specific_fields(self):
        return ["cockpit_scope", "metric_period", "metric_value", "source_model", "source_res_id"]


class ScWorkbenchItem(models.Model):
    _name = "sc.workbench.item"
    _description = "工作台事项"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [("my_todo", "我的待办"), ("my_approval", "我的审批"), ("recent_visit", "最近访问")]

    source_model = fields.Char(string="来源模型")
    source_res_id = fields.Integer(string="来源记录ID")
    priority = fields.Selection(
        [("low", "低"), ("normal", "普通"), ("high", "高"), ("urgent", "紧急")],
        string="优先级",
        default="normal",
    )
    todo_deadline = fields.Date(string="待办期限")

    _sql_constraints = [
        (
            "workbench_item_source_unique",
            "unique(fact_type, source_model, source_res_id)",
            "同一来源事项已经进入工作台。",
        ),
    ]

    def _business_specific_fields(self):
        return ["source_model", "source_res_id", "priority", "todo_deadline"]
