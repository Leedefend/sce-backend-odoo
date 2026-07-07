# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScLaborPlan(models.Model):
    _name = "sc.labor.plan"
    _description = "劳务计划"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

    name = fields.Char(string="计划单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    plan_date = fields.Date(string="计划日期", required=True, default=fields.Date.context_today, index=True)
    start_date = fields.Date(string="计划开始日期", index=True)
    end_date = fields.Date(string="计划结束日期", index=True)
    owner_id = fields.Many2one("res.users", string="负责人", default=lambda self: self.env.user, index=True)
    contractor_id = fields.Many2one("res.partner", string="建议劳务单位", index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.labor.plan.line", "plan_id", string="计划明细")
    note = fields.Text(string="计划说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_plan_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务计划已迁移为专业劳务计划。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.plan") or _("劳务计划")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交劳务计划前必须维护计划明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.constrains("start_date", "end_date")
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("计划开始日期不能晚于计划结束日期。"))


class ScLaborPlanLine(models.Model):
    _name = "sc.labor.plan.line"
    _description = "劳务计划明细"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one("sc.labor.plan", string="计划单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="plan_id.project_id", store=True, index=True)
    labor_team = fields.Char(string="班组")
    work_content = fields.Char(string="作业内容", required=True)
    planned_qty = fields.Float(string="计划人数", required=True, default=1)
    planned_work_hours = fields.Float(string="计划工时")
    note = fields.Char(string="备注")

    @api.constrains("planned_qty", "planned_work_hours")
    def _check_values(self):
        for record in self:
            if record.planned_qty <= 0:
                raise ValidationError(_("计划人数必须大于0。"))
            if record.planned_work_hours < 0:
                raise ValidationError(_("计划工时不能为负数。"))


class ScLaborRequest(models.Model):
    _name = "sc.labor.request"
    _description = "劳务申请"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(string="申请单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    request_date = fields.Date(string="申请日期", required=True, default=fields.Date.context_today, index=True)
    required_date = fields.Date(string="需用日期", index=True)
    requester_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user, index=True)
    owner_id = fields.Many2one("res.users", string="施工队负责人", related="requester_id", store=True, readonly=True, index=True)
    contractor_id = fields.Many2one("res.partner", string="建议劳务单位", index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_total = fields.Monetary(
        string="总含税金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    settlement_ratio = fields.Float(
        string="结算比例",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    invoice_amount = fields.Monetary(
        string="已开票金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    uninvoiced_amount = fields.Monetary(
        string="未开票金额",
        currency_field="currency_id",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    pricing_method = fields.Char(
        string="计价方式",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    construction_part = fields.Char(
        string="施工部位",
        compute="_compute_request_boundary_fields",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("approved", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.labor.request.line", "request_id", string="申请明细")
    note = fields.Text(string="申请说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_request_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务申请已迁移为专业劳务申请。"),
    ]

    @api.depends("line_ids.work_content")
    def _compute_request_boundary_fields(self):
        for record in self:
            contents = [content for content in record.line_ids.mapped("work_content") if content]
            record.amount_total = 0.0
            record.settlement_ratio = 0.0
            record.invoice_amount = 0.0
            record.paid_amount = 0.0
            record.unpaid_amount = 0.0
            record.uninvoiced_amount = 0.0
            record.pricing_method = False
            record.construction_part = "、".join(contents[:3]) or False

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.request") or _("劳务申请")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("提交劳务申请前必须维护申请明细。"))
            record.line_ids._check_values()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        for record in self:
            record.line_ids._check_values()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class ScLaborRequestLine(models.Model):
    _name = "sc.labor.request.line"
    _description = "劳务申请明细"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one("sc.labor.request", string="申请单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="request_id.project_id", store=True, index=True)
    labor_team = fields.Char(string="班组")
    work_content = fields.Char(string="作业内容", required=True)
    requested_qty = fields.Float(string="申请人数", required=True, default=1)
    planned_work_hours = fields.Float(string="计划工时")
    note = fields.Char(string="备注")

    @api.constrains("requested_qty", "planned_work_hours")
    def _check_values(self):
        for record in self:
            if record.requested_qty <= 0:
                raise ValidationError(_("申请人数必须大于0。"))
            if record.planned_work_hours < 0:
                raise ValidationError(_("计划工时不能为负数。"))


class ScAttendanceCheckin(models.Model):
    _name = "sc.attendance.checkin"
    _description = "考勤记录"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "attendance_date desc, id desc"

    name = fields.Char(string="考勤单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    attendance_date = fields.Date(string="考勤日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    work_content = fields.Char(string="作业内容", required=True)
    attendance_qty = fields.Float(string="出勤人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="考勤说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_attendance_checkin_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用考勤记录已迁移为专业考勤记录。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.attendance.checkin") or _("考勤记录")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿用工单可以提交。"))
            record._check_values()
            record.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交用工单可以确认。"))
            record._check_values()
            record.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交用工单可以取消。"))
            record.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消用工单可以重置为草稿。"))
            record.write({"state": "draft"})
        return True

    @api.constrains("attendance_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.attendance_qty <= 0:
                raise ValidationError(_("出勤人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))


class ScLaborUsage(models.Model):
    _name = "sc.labor.usage"
    _description = "劳务用工"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "usage_date desc, id desc"

    name = fields.Char(string="用工单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    usage_date = fields.Date(string="用工日期", required=True, default=fields.Date.context_today, index=True, tracking=True)
    labor_team = fields.Char(string="班组", required=True, index=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    work_content = fields.Char(string="作业内容", required=True)
    worker_qty = fields.Float(string="用工人数", required=True, default=1)
    work_hours = fields.Float(string="工时")
    foreman_name = fields.Char(string="带班人")
    recorder_id = fields.Many2one("res.users", string="记录人", default=lambda self: self.env.user, index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_labor_usage_attachment_rel",
        "usage_id",
        "attachment_id",
        string="附件",
    )
    note = fields.Text(string="用工说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_usage_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务用工已迁移为专业劳务用工。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.usage") or _("劳务用工")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿用工单可以提交。"))
            record._check_values()
            record.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交用工单可以确认。"))
            record._check_values()
            record.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交用工单可以取消。"))
            record.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消用工单可以重置为草稿。"))
            record.write({"state": "draft"})
        return True

    @api.constrains("worker_qty", "work_hours")
    def _check_values(self):
        for record in self:
            if record.worker_qty <= 0:
                raise ValidationError(_("用工人数必须大于0。"))
            if record.work_hours < 0:
                raise ValidationError(_("工时不能为负数。"))


class ScLaborSettlement(models.Model):
    _name = "sc.labor.settlement"
    _description = "劳务结算"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", required=True, index=True, tracking=True)
    settlement_date = fields.Date(string="结算日期", required=True, default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="结算金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    payment_paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_requested_amount = fields.Monetary(
        string="已申请金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    payment_unrequested_amount = fields.Monetary(
        string="未申请金额",
        currency_field="currency_id",
        compute="_compute_payment_boundary_amounts",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.labor.settlement.line", "settlement_id", string="结算明细")
    note = fields.Text(string="结算说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_settlement_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务结算已迁移为专业劳务结算。"),
    ]

    @api.depends("line_ids.amount_untaxed", "line_ids.tax_amount", "line_ids.amount_total")
    def _compute_amounts(self):
        for record in self:
            record.amount_untaxed = sum(record.line_ids.mapped("amount_untaxed"))
            record.tax_amount = sum(record.line_ids.mapped("tax_amount"))
            record.amount_total = sum(record.line_ids.mapped("amount_total"))

    @api.depends("amount_total")
    def _compute_payment_boundary_amounts(self):
        for record in self:
            amount = record.amount_total or 0.0
            record.payment_paid_amount = 0.0
            record.payment_unpaid_amount = amount
            record.payment_requested_amount = 0.0
            record.payment_unrequested_amount = amount

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.settlement") or _("劳务结算")
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿劳务结算可以提交。"))
            if not record.line_ids:
                raise ValidationError(_("提交结算前必须维护结算明细。"))
            record._check_business_anchor()
            record.line_ids._check_values()
            record.write({"state": "submitted"})
        return True

    def action_confirm(self):
        for record in self:
            if record.state != "submitted":
                raise UserError(_("只有已提交劳务结算可以确认。"))
            record._check_business_anchor()
            record.line_ids._check_values()
            record.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(_("只有草稿或已提交劳务结算可以取消。"))
            record.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancel":
                raise UserError(_("只有已取消劳务结算可以重置为草稿。"))
            record.write({"state": "draft"})
        return True

    def _check_business_anchor(self):
        for record in self:
            for line in record.line_ids.filtered("source_usage_id"):
                if line.source_usage_id.project_id != record.project_id:
                    raise UserError(_("劳务结算明细引用的用工来源必须属于同一项目。"))
                if line.source_usage_id.contractor_id and line.source_usage_id.contractor_id != record.contractor_id:
                    raise UserError(_("劳务结算明细引用的用工来源劳务单位必须与结算单一致。"))
                if line.source_usage_id.legacy_settlement_state not in ("unsettled", "unknown"):
                    raise UserError(_("劳务结算只能引用历史未结算或需复核的用工来源。"))


class ScLaborSettlementLine(models.Model):
    _name = "sc.labor.settlement.line"
    _description = "劳务结算明细"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.labor.settlement", string="结算单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="settlement_id.project_id", store=True, index=True)
    source_usage_id = fields.Many2one("sc.labor.usage", string="来源用工", index=True)
    labor_team = fields.Char(string="班组")
    work_content = fields.Char(string="作业内容", required=True)
    qty = fields.Float(string="结算数量", required=True, default=1)
    unit_name = fields.Char(string="单位")
    currency_id = fields.Many2one("res.currency", string="币种", related="settlement_id.currency_id", store=True)
    unit_price = fields.Monetary(string="结算单价", currency_field="currency_id", required=True)
    tax_rate = fields.Float(string="税率%")
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="含税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    note = fields.Char(string="备注")

    @api.depends("qty", "unit_price", "tax_rate")
    def _compute_amounts(self):
        for record in self:
            amount_untaxed = record.qty * record.unit_price
            tax_amount = amount_untaxed * record.tax_rate / 100
            record.amount_untaxed = amount_untaxed
            record.tax_amount = tax_amount
            record.amount_total = amount_untaxed + tax_amount

    @api.constrains("qty", "unit_price", "tax_rate")
    def _check_values(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("结算数量必须大于0。"))
            if record.unit_price < 0:
                raise ValidationError(_("结算单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))

    @api.constrains("source_usage_id", "settlement_id")
    def _check_source_usage_anchor(self):
        for record in self.filtered("source_usage_id"):
            settlement = record.settlement_id
            usage = record.source_usage_id
            if usage.project_id != settlement.project_id:
                raise ValidationError(_("来源用工必须属于同一项目。"))
            if usage.contractor_id and usage.contractor_id != settlement.contractor_id:
                raise ValidationError(_("来源用工劳务单位必须与结算单一致。"))
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("source_usage_id", "=", usage.id),
                    ("settlement_id.state", "!=", "cancel"),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(_("来源用工已经被其他未取消劳务结算引用，不能重复结算。"))


class ScLaborPrice(models.Model):
    _name = "sc.labor.price"
    _description = "劳务价格库"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(string="价格编号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="适用项目", index=True, tracking=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", index=True)
    labor_team = fields.Char(string="班组", index=True)
    work_content = fields.Char(string="作业内容", required=True, index=True, tracking=True)
    unit_name = fields.Char(string="计价单位", required=True, default="工日")
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    unit_price = fields.Monetary(string="单价", currency_field="currency_id", required=True, tracking=True)
    tax_rate = fields.Float(string="税率%")
    effective_date = fields.Date(string="生效日期", required=True, default=fields.Date.context_today, index=True)
    expire_date = fields.Date(string="失效日期", index=True)
    state = fields.Selection(
        [("draft", "草稿"), ("active", "生效"), ("inactive", "停用")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    note = fields.Text(string="价格说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_labor_price_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用劳务价格已迁移为专业劳务价格。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.labor.price") or _("劳务价格")
        return super().create(vals_list)

    def action_activate(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("只有草稿状态的劳务价格可以生效。"))
        self._check_values()
        self.write({"state": "active"})
        return True

    def action_deactivate(self):
        for record in self:
            if record.state != "active":
                raise UserError(_("只有生效状态的劳务价格可以停用。"))
        self.write({"state": "inactive"})
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state != "inactive":
                raise UserError(_("只有停用状态的劳务价格可以重置为草稿。"))
        self.write({"state": "draft"})
        return True

    @api.constrains("unit_price", "tax_rate", "effective_date", "expire_date")
    def _check_values(self):
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("劳务单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))
            if record.effective_date and record.expire_date and record.effective_date > record.expire_date:
                raise ValidationError(_("生效日期不能晚于失效日期。"))
