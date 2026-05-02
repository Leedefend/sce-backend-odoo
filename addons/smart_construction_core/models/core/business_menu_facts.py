# -*- coding: utf-8 -*-
import hashlib

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


class ScProjectBudgetFact(models.Model):
    _name = "sc.project.budget.fact"
    _description = "项目预算业务事实"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("material_budget", "物资预算"),
            ("labor_budget", "人工预算"),
            ("machine_budget", "机械预算"),
            ("subcontract_budget", "分包预算"),
            ("measure_budget", "措施费"),
            ("tax_budget", "税费"),
        ]

    cost_code_id = fields.Many2one("project.cost.code", string="预算科目", index=True)
    budget_basis = fields.Char(string="编制依据")
    original_budget_amount = fields.Monetary(string="原预算金额", currency_field="currency_id")
    adjusted_budget_amount = fields.Monetary(string="调整后预算金额", currency_field="currency_id")

    def _business_specific_fields(self):
        return ["cost_code_id", "budget_basis", "original_budget_amount", "adjusted_budget_amount"]

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            record._require_fields(["budget_basis"])
            if record.adjusted_budget_amount and record.adjusted_budget_amount < record.original_budget_amount:
                raise ValidationError(_("调整后预算金额不能小于原预算金额。"))


class ScProjectDocumentFact(models.Model):
    _name = "sc.project.document.fact"
    _description = "施工资料业务事实"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("safety_document", "安全资料"),
            ("quality_document", "质量资料"),
            ("self_inspection_document", "自检资料"),
            ("archive_document", "归档备案"),
        ]

    document_category = fields.Char(string="资料类别")
    document_version = fields.Char(string="版本")
    archive_no = fields.Char(string="归档编号")
    owner_name = fields.Char(string="责任人")

    def _business_specific_fields(self):
        return ["document_category", "document_version", "archive_no", "owner_name"]

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type == "archive_document":
                record._require_fields(["archive_no", "owner_name"])
            else:
                record._require_fields(["document_category", "owner_name"])


class ScMaterialDocument(models.Model):
    _name = "sc.material.document"
    _description = "物资业务单据"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("purchase_request", "采购申请"),
            ("rfq", "询比价"),
            ("inbound", "入库单"),
            ("outbound", "出库单"),
            ("settlement", "材料结算"),
        ]

    product_id = fields.Many2one("product.product", string="材料", index=True)
    material_spec = fields.Char(string="规格型号")
    warehouse_id = fields.Many2one("stock.warehouse", string="仓库")
    source_location_id = fields.Many2one("stock.location", string="来源库位")
    dest_location_id = fields.Many2one("stock.location", string="目标库位")
    supplier_quote = fields.Monetary(string="供应商报价", currency_field="currency_id")

    def _business_specific_fields(self):
        return [
            "product_id",
            "material_spec",
            "warehouse_id",
            "source_location_id",
            "dest_location_id",
            "supplier_quote",
        ]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type in ("purchase_request", "rfq", "inbound", "outbound", "settlement"):
                record._require_fields(["quantity"])
            if record.fact_type == "inbound":
                record._require_fields(["dest_location_id"])
            if record.fact_type == "outbound":
                record._require_fields(["source_location_id"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type == "rfq" and not (record.supplier_quote or record.amount):
                raise ValidationError(_("询比价完成前必须填写供应商报价或金额。"))
            if record.fact_type == "settlement":
                record._require_fields(["amount"])


class ScLaborDocument(models.Model):
    _name = "sc.labor.document"
    _description = "劳务业务单据"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("labor_plan", "劳务计划"),
            ("labor_request", "劳务申请"),
            ("labor_employment", "劳务用工"),
            ("attendance_record", "考勤记录"),
            ("labor_settlement", "劳务结算"),
            ("labor_price_library", "劳务价格库"),
        ]

    labor_team = fields.Char(string="班组")
    work_content = fields.Char(string="作业内容")
    worker_count = fields.Integer(string="人数")
    work_hours = fields.Float(string="工时")
    attendance_date = fields.Date(string="考勤日期")

    def _business_specific_fields(self):
        return ["labor_team", "work_content", "worker_count", "work_hours", "attendance_date"]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type in ("labor_plan", "labor_request", "labor_employment", "attendance_record", "labor_settlement"):
                record._require_fields(["labor_team", "work_content"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type == "attendance_record":
                record._require_fields(["attendance_date"])
            if record.fact_type in ("labor_employment", "attendance_record") and record.worker_count <= 0:
                raise ValidationError(_("劳务用工或考勤记录完成前人数必须大于0。"))
            if record.fact_type == "labor_settlement":
                record._require_fields(["amount"])


class ScEquipmentDocument(models.Model):
    _name = "sc.equipment.document"
    _description = "机械设备业务单据"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("equipment_plan", "设备计划"),
            ("equipment_request", "设备申请"),
            ("equipment_usage", "设备使用登记"),
            ("equipment_settlement", "设备结算"),
            ("equipment_price_library", "设备价格库"),
        ]

    equipment_name = fields.Char(string="设备名称")
    equipment_code = fields.Char(string="设备编号")
    usage_location = fields.Char(string="使用地点")
    usage_hours = fields.Float(string="使用台时")
    operator_name = fields.Char(string="操作人员")

    def _business_specific_fields(self):
        return ["equipment_name", "equipment_code", "usage_location", "usage_hours", "operator_name"]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            record._require_fields(["equipment_name"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type == "equipment_usage":
                record._require_fields(["usage_location", "operator_name"])
                if record.usage_hours <= 0:
                    raise ValidationError(_("设备使用登记完成前使用台时必须大于0。"))
            if record.fact_type == "equipment_settlement":
                record._require_fields(["amount"])


class ScSubcontractDocument(models.Model):
    _name = "sc.subcontract.document"
    _description = "专业分包业务单据"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("subcontract_plan", "分包计划"),
            ("subcontract_request", "分包申请"),
            ("subcontract_register", "分包登记"),
            ("subcontract_settlement", "分包结算"),
            ("subcontract_price_library", "分包价格库"),
        ]

    subcontract_scope = fields.Char(string="分包范围")
    contract_id = fields.Many2one("construction.contract", string="关联合同", index=True)
    subcontractor_id = fields.Many2one("res.partner", string="分包单位", index=True)
    start_date = fields.Date(string="开始日期")
    end_date = fields.Date(string="结束日期")

    def _business_specific_fields(self):
        return ["subcontract_scope", "contract_id", "subcontractor_id", "start_date", "end_date"]

    @api.constrains("start_date", "end_date")
    def _check_subcontract_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("分包开始日期不能晚于结束日期。"))

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            record._require_fields(["subcontract_scope"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type in ("subcontract_register", "subcontract_settlement"):
                record._require_fields(["subcontractor_id"])
            if record.fact_type == "subcontract_settlement":
                record._require_fields(["amount"])


class ScConstructionInspection(models.Model):
    _name = "sc.construction.inspection"
    _description = "施工检查整改"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("quality_check", "质量检查"),
            ("quality_rectification", "质量整改"),
            ("safety_check", "安全检查"),
            ("safety_rectification", "安全整改"),
        ]

    inspection_location = fields.Char(string="检查部位")
    issue_level = fields.Selection(
        [("normal", "一般"), ("important", "重要"), ("critical", "重大")],
        string="问题等级",
        default="normal",
    )
    responsible_party_id = fields.Many2one("res.partner", string="责任单位", index=True)
    rectification_deadline = fields.Date(string="整改期限")
    rectification_result = fields.Text(string="整改结果")

    def _business_specific_fields(self):
        return [
            "inspection_location",
            "issue_level",
            "responsible_party_id",
            "rectification_deadline",
            "rectification_result",
        ]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            record._require_fields(["inspection_location", "responsible_party_id"])
            if record.fact_type in ("quality_rectification", "safety_rectification"):
                record._require_fields(["rectification_deadline"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type in ("quality_rectification", "safety_rectification"):
                record._require_fields(["rectification_result"])


class ScConstructionReport(models.Model):
    _name = "sc.construction.report"
    _description = "施工报表"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [("daily_report", "日报表"), ("weekly_report", "周报表"), ("monthly_report", "月报表")]

    period_start = fields.Date(string="期间开始")
    period_end = fields.Date(string="期间结束")
    weather = fields.Char(string="天气")
    manpower_count = fields.Integer(string="现场人数")
    completed_work = fields.Text(string="完成工作")
    next_plan = fields.Text(string="下步计划")

    def _business_specific_fields(self):
        return ["period_start", "period_end", "weather", "manpower_count", "completed_work", "next_plan"]

    @api.constrains("period_start", "period_end")
    def _check_report_period_order(self):
        for record in self:
            if record.period_start and record.period_end and record.period_start > record.period_end:
                raise ValidationError(_("报表期间开始不能晚于期间结束。"))

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            record._require_fields(["period_start", "period_end", "completed_work"])


class ScFinanceExpenseDocument(models.Model):
    _name = "sc.finance.expense.document"
    _description = "费用报销扩展单据"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("advance_fund", "备用金"),
            ("borrowing_form", "借款单"),
            ("repayment_form", "还款单"),
            ("project_expense_claim", "项目费用报销单"),
        ]

    expense_category = fields.Char(string="费用类别")
    payee_id = fields.Many2one("res.partner", string="收款对象", index=True)
    bank_account = fields.Char(string="收款账户")
    invoice_no = fields.Char(string="发票号码")
    repayment_due_date = fields.Date(string="还款期限")

    def _business_specific_fields(self):
        return ["expense_category", "payee_id", "bank_account", "invoice_no", "repayment_due_date"]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            if record.fact_type in ("advance_fund", "borrowing_form", "repayment_form", "project_expense_claim"):
                record._require_fields(["expense_category", "payee_id", "amount"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type in ("borrowing_form", "repayment_form"):
                record._require_fields(["repayment_due_date"])


class ScFundOperation(models.Model):
    _name = "sc.fund.operation"
    _description = "资金账户操作"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("funding_plan_summary", "资金计划汇总"),
            ("fund_transfer_out", "资金划拨"),
            ("fund_transfer_between", "资金调拨"),
            ("balance_adjustment", "余额调整"),
            ("fund_daily_report", "资金日报表"),
        ]

    source_account = fields.Char(string="转出账户")
    target_account = fields.Char(string="转入账户")
    operation_reason = fields.Char(string="操作原因")
    before_balance = fields.Monetary(string="调整前余额", currency_field="currency_id")
    after_balance = fields.Monetary(string="调整后余额", currency_field="currency_id")

    def _business_specific_fields(self):
        return ["operation_reason", "source_account", "target_account", "amount", "before_balance", "after_balance"]

    def _check_submit_requirements(self):
        super()._check_submit_requirements()
        for record in self:
            record._require_fields(["operation_reason"])
            if record.fact_type in ("fund_transfer_out", "fund_transfer_between"):
                record._require_fields(["source_account", "target_account", "amount"])

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            if record.fact_type == "balance_adjustment" and record.before_balance == record.after_balance:
                raise ValidationError(_("余额调整完成前调整前余额和调整后余额不能相同。"))


class ScAnalysisReportFact(models.Model):
    _name = "sc.analysis.report.fact"
    _description = "统计分析报表事实"
    _inherit = ["sc.business.fact.mixin", "mail.thread", "mail.activity.mixin"]

    def _selection_fact_type(self):
        return [
            ("project_profit_statistics", "项目利润统计"),
            ("project_cost_statistics", "项目成本汇总"),
            ("funding_plan_statistics", "资金计划统计表"),
            ("inbound_statistics", "入库统计"),
            ("outbound_statistics", "出库统计"),
            ("return_statistics", "退货统计"),
            ("inventory_statistics", "库存统计表"),
            ("material_settlement_detail", "材料结算明细表"),
            ("salary_statistics", "薪资统计"),
            ("labor_statistics", "劳务统计"),
            ("attendance_statistics", "考勤统计汇总表"),
            ("tender_detail_report", "投标明细表"),
            ("tender_statistics_report", "投标统计表"),
        ]

    report_period_start = fields.Date(string="统计开始")
    report_period_end = fields.Date(string="统计结束")
    metric_name = fields.Char(string="指标名称")
    metric_value = fields.Float(string="指标值")
    metric_unit = fields.Char(string="指标单位")

    def _business_specific_fields(self):
        return ["report_period_start", "report_period_end", "metric_name", "metric_value", "metric_unit"]

    @api.constrains("report_period_start", "report_period_end")
    def _check_analysis_period_order(self):
        for record in self:
            if record.report_period_start and record.report_period_end and record.report_period_start > record.report_period_end:
                raise ValidationError(_("统计开始不能晚于统计结束。"))

    def _check_done_requirements(self):
        super()._check_done_requirements()
        for record in self:
            record._require_fields(["report_period_start", "report_period_end", "metric_name"])


class ScBusinessMenuTaxonomySeed(models.AbstractModel):
    _name = "sc.business.menu.taxonomy.seed"
    _description = "业务菜单体系同步"

    def _formal(self, model, fact_type):
        return {"model": model, "fact_type": fact_type}

    def _target_tree(self):
        f = self._formal
        return {
            "智慧大屏": {
                "公司驾驶舱": "smart_construction_core.action_sc_operating_metrics_project",
                "项目驾驶舱": "smart_construction_core.action_project_dashboard",
                "资金驾驶舱": "smart_construction_core.action_sc_finance_dashboard",
                "成本驾驶舱": "smart_construction_core.action_project_cost_ledger",
            },
            "工作台": {
                "工作台": "smart_construction_core.action_sc_project_workbench",
                "我的项目": "smart_construction_core.action_sc_project_my_list",
                "我的审批": "smart_construction_core.action_sc_project_workbench",
                "最近访问": "smart_construction_core.action_sc_project_workbench",
            },
            "项目中心": {
                "项目管理": {
                    "项目立项": "smart_construction_core.action_project_initiation",
                    "项目台账": "smart_construction_core.action_sc_project_list",
                    "项目看板": "smart_construction_core.action_project_dashboard",
                    "项目资料": "smart_construction_core.action_sc_project_document",
                },
                "投标管理": {
                    "投标项目": "smart_construction_core.action_tender_bid",
                    "投标准备": "smart_construction_core.action_sc_tender_prepare",
                    "开标记录": "smart_construction_core.action_sc_tender_opening",
                    "中标记录": "smart_construction_core.action_sc_tender_won",
                    "投标保证金": "smart_construction_core.action_sc_tender_guarantee",
                },
                "项目预算": {
                    "预算清单": "smart_construction_core.action_project_boq_line",
                    "物资预算": "smart_construction_core.action_project_budget_material",
                    "人工预算": "smart_construction_core.action_project_budget_labor",
                    "机械预算": "smart_construction_core.action_project_budget_machine",
                    "分包预算": "smart_construction_core.action_project_budget_subcontract",
                    "措施费": "smart_construction_core.action_project_budget_measure",
                    "税费": "smart_construction_core.action_project_budget_tax",
                },
                "施工资料": {
                    "现场资料": "smart_construction_core.action_sc_project_document",
                    "安全资料": "smart_construction_core.action_sc_project_document_safety",
                    "质量资料": "smart_construction_core.action_sc_project_document_quality",
                    "自检资料": "smart_construction_core.action_sc_project_document_self_inspection",
                    "归档备案": "smart_construction_core.action_sc_project_document_archive",
                },
            },
            "合同中心": {
                "收入合同": {
                    "收入合同台账": "smart_construction_core.action_construction_contract_income",
                    "收入合同签证": "smart_construction_core.action_sc_settlement_adjustment",
                    "收入合同执行": "smart_construction_core.action_construction_contract_income_execution",
                    "收入合同结算": "smart_construction_core.action_sc_settlement_order_income",
                },
                "支出合同": {
                    "支出合同台账": "smart_construction_core.action_construction_contract_expense",
                    "一般合同": "smart_construction_core.action_sc_general_contract",
                    "支出合同签证": "smart_construction_core.action_sc_settlement_adjustment",
                    "支出合同执行": "smart_construction_core.action_construction_contract_expense_execution",
                    "支出合同结算": "smart_construction_core.action_sc_settlement_order_expense",
                },
            },
            "物资与分包": {
                "物资管理": {
                    "材料计划": "smart_construction_core.action_project_material_plan",
                    "采购申请": "smart_construction_core.action_sc_material_purchase_request",
                    "询比价": "smart_construction_core.action_sc_material_rfq",
                    "采购订单": "smart_construction_core.action_sc_purchase_order",
                    "入库单": "smart_construction_core.action_sc_material_inbound",
                    "出库单": "smart_construction_core.action_sc_material_outbound",
                    "材料结算": "smart_construction_core.action_sc_material_settlement",
                    "材料价格库": "smart_construction_core.action_sc_material_price_library",
                },
                "劳务管理": {
                    "劳务计划": "smart_construction_core.action_sc_labor_plan",
                    "劳务申请": "smart_construction_core.action_sc_labor_request",
                    "劳务用工": "smart_construction_core.action_sc_labor_usage",
                    "考勤记录": "smart_construction_core.action_sc_attendance_checkin",
                    "劳务结算": "smart_construction_core.action_sc_labor_settlement",
                    "劳务价格库": "smart_construction_core.action_sc_labor_price",
                },
                "机械设备": {
                    "设备计划": "smart_construction_core.action_sc_equipment_plan",
                    "设备申请": "smart_construction_core.action_sc_equipment_request",
                    "设备使用登记": "smart_construction_core.action_sc_equipment_usage",
                    "设备结算": "smart_construction_core.action_sc_equipment_settlement",
                    "设备价格库": "smart_construction_core.action_sc_equipment_price",
                },
                "专业分包": {
                    "分包计划": "smart_construction_core.action_sc_subcontract_plan",
                    "分包申请": "smart_construction_core.action_sc_subcontract_request",
                    "分包登记": "smart_construction_core.action_sc_subcontract_register",
                    "分包结算": "smart_construction_core.action_sc_subcontract_settlement",
                    "分包价格库": "smart_construction_core.action_sc_subcontract_price",
                },
            },
            "施工管理": {
                "进度管理": "smart_construction_core.action_project_progress_entry",
                "检查标准": "smart_construction_core.action_sc_check_standard",
                "检查项维护": "smart_construction_core.action_sc_check_standard_item",
                "质量检查": "smart_construction_core.action_sc_quality_issue",
                "质量整改": "smart_construction_core.action_sc_quality_rectification",
                "质量复验": "smart_construction_core.action_sc_quality_recheck",
                "安全检查": "smart_construction_core.action_sc_safety_issue",
                "安全整改": "smart_construction_core.action_sc_safety_rectification",
                "安全复验": "smart_construction_core.action_sc_safety_recheck",
                "现场照片": "smart_construction_core.action_sc_site_photo_batch",
                "施工日志": "smart_construction_core.action_sc_construction_diary",
                "日报表": "smart_construction_core.action_sc_construction_daily_report",
                "周报表": "smart_construction_core.action_sc_construction_weekly_report",
                "月报表": "smart_construction_core.action_sc_construction_monthly_report",
            },
            "成本中心": {
                "目标成本": "smart_construction_core.action_project_budget",
                "预算清单分摊": "smart_construction_core.action_project_budget_cost_alloc",
                "进度计量": "smart_construction_core.action_project_progress_entry",
                "成本台账": "smart_construction_core.action_project_cost_ledger",
                "成本汇总": "smart_construction_core.action_project_cost_ledger",
                "经营利润": "smart_construction_core.action_sc_operating_metrics_project",
            },
            "财务中心": {
                "收付款管理": {
                    "收款登记": "smart_construction_core.action_sc_receipt_income",
                    "付款申请": "smart_construction_core.action_payment_request_pay",
                    "付款登记": "smart_construction_core.action_sc_payment_execution",
                },
                "发票管理": {
                    "开票申请": "smart_construction_core.action_sc_invoice_registration",
                    "销项发票": "smart_construction_core.action_sc_invoice_output",
                    "进项发票": "smart_construction_core.action_sc_invoice_input",
                },
                "资金计划": {
                    "资金计划申报": "smart_construction_core.action_project_funding_baseline",
                    "资金计划汇总": "smart_construction_core.action_project_funding_baseline_summary",
                },
                "费用报销": {
                    "备用金": "smart_construction_core.action_sc_expense_claim_advance_fund",
                    "借款单": "smart_construction_core.action_sc_financing_loan_borrowing",
                    "还款单": "smart_construction_core.action_sc_expense_claim_repayment",
                    "费用报销单": "smart_construction_core.action_sc_expense_claim_expense",
                    "项目费用报销单": "smart_construction_core.action_sc_expense_claim_project",
                },
                "资金账户": {
                    "账户管理": "smart_construction_core.action_sc_fund_account",
                    "资金对账": "smart_construction_core.action_sc_treasury_reconciliation",
                    "融资借款": "smart_construction_core.action_sc_financing_loan",
                    "资金划拨": "smart_construction_core.action_sc_fund_transfer_out",
                    "资金调拨": "smart_construction_core.action_sc_fund_transfer_between",
                    "余额调整": "smart_construction_core.action_sc_fund_balance_adjustment",
                    "资金日报表": "smart_construction_core.action_sc_fund_daily_summary",
                },
                "保证金管理": {
                    "投标保证金缴纳": "smart_construction_core.action_sc_expense_claim_deposit",
                    "投标保证金退回": "smart_construction_core.action_sc_expense_claim_deposit",
                    "合同保证金登记": "smart_construction_core.action_sc_expense_claim_deposit",
                    "合同保证金退回": "smart_construction_core.action_sc_expense_claim_deposit",
                },
            },
            "统计分析": {
                "经营分析": {
                    "项目经营分析": "smart_construction_core.action_sc_operating_metrics_project",
                    "项目利润统计": "smart_construction_core.action_sc_operating_metrics_project",
                    "项目成本汇总": "smart_construction_core.action_project_cost_ledger",
                    "合同执行表": "smart_construction_core.action_project_contract_overview",
                },
                "财务分析": {
                    "客户账款": "smart_construction_core.action_sc_ar_ap_project_summary",
                    "供应商账款": "smart_construction_core.action_sc_ar_ap_company_summary",
                    "收款统计表": "smart_construction_core.action_sc_treasury_ledger_income",
                    "付款统计表": "smart_construction_core.action_payment_ledger",
                    "账户收支统计表": "smart_construction_core.action_sc_account_income_expense_summary",
                    "资金计划统计表": "smart_construction_core.action_project_funding_baseline_summary",
                },
                "物资分析": {
                    "入库统计": "smart_construction_core.action_sc_material_inbound",
                    "出库统计": "smart_construction_core.action_sc_material_outbound",
                    "退货统计": "smart_construction_core.action_sc_material_outbound",
                    "库存统计表": "smart_construction_core.action_sc_legacy_report_inventory",
                    "材料结算明细表": "smart_construction_core.action_sc_material_settlement_line",
                },
                "人资分析": {
                    "薪资统计": "smart_construction_core.action_sc_legacy_report_inventory",
                    "劳务统计": "smart_construction_core.action_sc_labor_settlement",
                    "考勤统计汇总表": "smart_construction_core.action_sc_attendance_checkin",
                },
                "投标分析": {
                    "投标明细表": "smart_construction_core.action_tender_bid",
                    "投标统计表": "smart_construction_core.action_tender_bid",
                },
            },
            "基础设置": {
                "客户": "smart_construction_core.action_sc_customer_partner",
                "供应商": "smart_construction_core.action_sc_supplier_partner",
                "内部单位": "smart_construction_core.action_sc_organization_department",
                "材料档案": "smart_construction_core.action_sc_material_product_template",
                "预算类型": "smart_construction_core.action_project_cost_code",
                "数据字典": "smart_construction_core.action_sc_dictionary_manage",
                "审批配置": "smart_construction_core.action_sc_approval_policy",
                "系统权限": "smart_construction_core.action_sc_capability",
            },
        }

    TOP_XMLIDS = {
        "智慧大屏": "menu_sc_projection_root",
        "工作台": "menu_sc_workspace_center",
        "项目中心": "menu_sc_project_center",
        "合同中心": "menu_sc_contract_center",
        "物资与分包": "menu_sc_material_center",
        "施工管理": "menu_sc_construction_management_center",
        "成本中心": "menu_sc_cost_center",
        "财务中心": "menu_sc_finance_center",
        "统计分析": "menu_sc_data_center",
        "基础设置": "menu_sc_business_config_center",
    }

    KNOWN_MENU_XMLIDS = {
        ("项目中心", "项目管理"): "menu_sc_project_management_group",
        ("项目中心", "投标管理"): "menu_sc_tender_management_group",
        ("项目中心", "项目预算"): "menu_sc_project_budget_group",
        ("项目中心", "施工资料"): "menu_sc_doc_center",
        ("合同中心", "收入合同"): "menu_sc_income_contract_group",
        ("合同中心", "支出合同"): "menu_sc_expense_contract_group",
        ("物资与分包", "物资管理"): "menu_sc_material_management_group",
        ("物资与分包", "劳务管理"): "menu_sc_labor_management_group",
        ("物资与分包", "机械设备"): "menu_sc_equipment_management_group",
        ("物资与分包", "专业分包"): "menu_sc_subcontract_management_group",
        ("财务中心", "收付款管理"): "menu_sc_receipt_payment_group",
        ("财务中心", "发票管理"): "menu_sc_invoice_management_group",
        ("财务中心", "资金计划"): "menu_sc_funding_plan_group",
        ("财务中心", "费用报销"): "menu_sc_expense_reimbursement_group",
        ("财务中心", "资金账户"): "menu_sc_fund_account_group",
        ("财务中心", "保证金管理"): "menu_sc_deposit_management_group",
        ("统计分析", "经营分析"): "menu_sc_business_analysis_group",
        ("统计分析", "财务分析"): "menu_sc_finance_analysis_group",
    }

    def _slug(self, value):
        mapping = {
            "智慧大屏": "dashboard",
            "工作台": "workspace",
            "项目中心": "project",
            "合同中心": "contract",
            "物资与分包": "material_subcontract",
            "施工管理": "construction",
            "成本中心": "cost",
            "财务中心": "finance",
            "统计分析": "analysis",
            "基础设置": "settings",
            "公司驾驶舱": "company_dashboard",
            "项目驾驶舱": "project_cockpit",
            "资金驾驶舱": "fund_cockpit",
            "成本驾驶舱": "cost_cockpit",
            "工作台": "workspace_home",
            "我的项目": "my_project",
            "我的审批": "my_approval",
            "最近访问": "recent_visit",
        }
        return mapping.get(value) or "m" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]

    def _xmlid_record(self, xmlid):
        return self.env.ref(xmlid, raise_if_not_found=False)

    def _ensure_xmlid(self, name, model, record):
        imd = self.env["ir.model.data"].sudo()
        existing = imd.search([("module", "=", "smart_construction_core"), ("name", "=", name)], limit=1)
        vals = {"module": "smart_construction_core", "name": name, "model": model, "res_id": record.id, "noupdate": False}
        if existing:
            existing.write(vals)
        else:
            imd.create(vals)

    def _search_view_id_for_model(self, model):
        view = self.env["ir.ui.view"].sudo().search([("model", "=", model), ("type", "=", "search")], limit=1)
        return view.id if view else False

    def _ensure_views_for_model(self, model):
        view_model = self.env["ir.ui.view"].sudo()
        record_model = self.env[model]
        specific_fields = [name for name in record_model._business_specific_fields() if name in record_model._fields]
        specific_field_set = set(specific_fields)
        common_left_fields = [
            "document_no",
            "name",
            "fact_type",
            "project_id",
            "partner_id",
            "department_id",
        ]
        common_right_fields = [
            "requester_id",
            "handler_id",
            "business_date",
            "planned_date",
            "due_date",
            "quantity",
            "uom_id",
            "unit_price",
            "amount",
            "tax_amount",
            "currency_id",
            "active",
        ]
        common_left_form = "\n".join(
            '                                <field name="%s"/>' % name
            for name in common_left_fields
            if name in record_model._fields and name not in specific_field_set
        )
        common_right_form = "\n".join(
            '                                <field name="%s"/>' % name
            for name in common_right_fields
            if name in record_model._fields and name not in specific_field_set
        )
        specific_search = "\n".join('                    <field name="%s"/>' % name for name in specific_fields[:4])
        specific_tree = "\n".join('                    <field name="%s"/>' % name for name in specific_fields[:5])
        specific_form = "\n".join('                            <field name="%s"/>' % name for name in specific_fields)
        specific_group = ""
        if specific_form:
            specific_group = """
                        <group string="业务信息">
                            <group>
                            %s
                            </group>
                        </group>
            """ % specific_form
        specs = {
            "search": """
                <search string="业务事实">
                    <field name="name"/>
                    <field name="document_no"/>
                    <field name="project_id"/>
                    <field name="partner_id"/>
                    <field name="requester_id"/>
                    <field name="handler_id"/>
%(specific_search)s
                    <filter string="草稿" name="state_draft" domain="[('state', '=', 'draft')]"/>
                    <filter string="办理中" name="state_in_progress" domain="[('state', '=', 'in_progress')]"/>
                    <filter string="已完成" name="state_done" domain="[('state', '=', 'done')]"/>
                    <filter string="已取消" name="state_cancel" domain="[('state', '=', 'cancel')]"/>
                    <filter string="按项目" name="group_project" context="{'group_by': 'project_id'}"/>
                    <filter string="按类型" name="group_type" context="{'group_by': 'fact_type'}"/>
                    <filter string="按状态" name="group_state" context="{'group_by': 'state'}"/>
                    <filter string="按经办人" name="group_handler" context="{'group_by': 'handler_id'}"/>
                </search>
            """ % {"specific_search": specific_search},
            "tree": """
                <tree string="业务事实" default_order="business_date desc, id desc">
                    <field name="business_date"/>
                    <field name="document_no"/>
                    <field name="name"/>
                    <field name="fact_type"/>
                    <field name="project_id"/>
                    <field name="partner_id"/>
%(specific_tree)s
                    <field name="handler_id"/>
                    <field name="due_date"/>
                    <field name="quantity" sum="数量合计"/>
                    <field name="amount" sum="金额合计"/>
                    <field name="state"/>
                </tree>
            """ % {"specific_tree": specific_tree},
            "form": """
                <form string="业务事实">
                    <header>
                        <button name="action_submit" type="object" string="提交" class="btn-primary" invisible="state != 'draft'"/>
                        <button name="action_done" type="object" string="完成" class="btn-primary" invisible="state not in ['draft', 'in_progress']"/>
                        <button name="action_cancel" type="object" string="取消" invisible="state in ['done', 'cancel']"/>
                        <button name="action_reset_draft" type="object" string="重置草稿" invisible="state == 'draft'"/>
                        <field name="state" widget="statusbar" statusbar_visible="draft,in_progress,done,cancel"/>
                    </header>
                    <sheet>
%(specific_group)s
                        <group>
                            <group>
%(common_left_form)s
                            </group>
                            <group>
%(common_right_form)s
                            </group>
                        </group>
                        <group string="说明">
                            <group>
                                <field name="description"/>
                                <field name="result_note"/>
                            </group>
                        </group>
                    </sheet>
                    <chatter/>
                </form>
            """ % {
                "specific_group": specific_group,
                "common_left_form": common_left_form,
                "common_right_form": common_right_form,
            },
        }
        for view_type, arch in specs.items():
            view = view_model.search([("name", "=", "%s.%s" % (model, view_type)), ("model", "=", model)], limit=1)
            vals = {"name": "%s.%s" % (model, view_type), "model": model, "type": view_type, "arch": arch}
            if view:
                view.write(vals)
            else:
                view_model.create(vals)

    def _ensure_formal_action(self, spec, name):
        model = spec["model"]
        fact_type = spec["fact_type"]
        self._ensure_views_for_model(model)
        domain = "[('fact_type', '=', '%s')]" % fact_type
        action_model = self.env["ir.actions.act_window"].sudo()
        action = action_model.search([("name", "=", name), ("res_model", "=", model), ("domain", "=", domain)], limit=1)
        vals = {
            "name": name,
            "res_model": model,
            "view_mode": "tree,form",
            "domain": domain,
            "context": repr({"default_fact_type": fact_type, "default_name": name, "search_default_group_project": 1}),
        }
        search_view_id = self._search_view_id_for_model(model)
        if search_view_id:
            vals["search_view_id"] = search_view_id
        if action:
            action.write(vals)
        else:
            action = action_model.create(vals)
        return action

    def _ensure_menu(self, xml_name, name, parent, sequence, action=None):
        menu = self._xmlid_record("smart_construction_core.%s" % xml_name)
        vals = {"name": name, "parent_id": parent.id, "sequence": sequence, "active": True}
        vals["action"] = "ir.actions.act_window,%s" % action.id if action else False
        if menu:
            menu.sudo().write(vals)
        else:
            menu = self.env["ir.ui.menu"].sudo().with_context(
                active_test=False,
                **{"ir.ui.menu.full_list": True},
            ).search(
                [("name", "=", name), ("parent_id", "=", parent.id)],
                limit=1,
            )
            if menu:
                menu.write(vals)
            else:
                menu = self.env["ir.ui.menu"].sudo().create(vals)
            if not xml_name.startswith("menu_sc_full_"):
                self._ensure_xmlid(xml_name, "ir.ui.menu", menu)
        return menu

    def _action_for_leaf(self, action_spec, leaf_name):
        if isinstance(action_spec, dict):
            action = self._ensure_formal_action(action_spec, leaf_name)
        else:
            action = self._xmlid_record(action_spec)
        if action:
            self._ensure_action_tree_form(action)
        return action

    def _ensure_action_tree_form(self, action):
        if action._name != "ir.actions.act_window":
            return
        modes = [mode.strip() for mode in (action.view_mode or "").split(",") if mode.strip()]
        if not any(mode in ("tree", "list") for mode in modes):
            modes.insert(0, "tree")
        if "form" not in modes:
            modes.append("form")
        next_view_mode = ",".join(dict.fromkeys(modes))
        if next_view_mode != action.view_mode:
            action.sudo().write({"view_mode": next_view_mode})

    def _deactivate_duplicate_target_menus(self, parent, name):
        menus = self.env["ir.ui.menu"].sudo().with_context(
            active_test=False,
            **{"ir.ui.menu.full_list": True},
        ).search(
            [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
            order="sequence,id",
        )
        if len(menus) > 1:
            menus[1:].write({"active": False})

    def _target_menu_paths(self, root):
        root_name = root.with_context(lang="zh_CN").name
        paths = {root_name}
        for top_name, top_children in self._target_tree().items():
            top_path = "%s/%s" % (root_name, top_name)
            paths.add(top_path)
            for child_name, child_value in top_children.items():
                child_path = "%s/%s" % (top_path, child_name)
                paths.add(child_path)
                if isinstance(child_value, dict) and "model" not in child_value:
                    for leaf_name in child_value:
                        paths.add("%s/%s" % (child_path, leaf_name))
        return paths

    def _menu_path(self, menu):
        names = []
        current = menu.with_context(lang="zh_CN")
        while current:
            names.append(current.name)
            current = current.parent_id.with_context(lang="zh_CN") if current.parent_id else False
        return "/".join(reversed(names))

    def _active_menu_subtree(self, root):
        collected = self.env["ir.ui.menu"].sudo()

        def walk(menu):
            nonlocal collected
            active_children = self.env["ir.ui.menu"].sudo().with_context(
                active_test=False,
                lang="zh_CN",
                **{"ir.ui.menu.full_list": True},
            ).search(
                [("parent_id", "=", menu.id), ("active", "=", True)],
                order="sequence,id",
            )
            for child in active_children:
                collected |= child
                walk(child)

        root = root.sudo().with_context(active_test=False, lang="zh_CN")
        if root.active:
            collected |= root
        walk(root)
        return collected

    def _deactivate_non_target_menus(self, root):
        target_paths = self._target_menu_paths(root)
        menus = self._active_menu_subtree(root)
        stale_menus = menus.filtered(lambda menu: self._menu_path(menu) not in target_paths)
        if stale_menus:
            stale_menus.write({"active": False})

    def _deactivate_duplicate_menu_paths(self, root):
        menus = self._active_menu_subtree(root)
        by_path = {}
        external_ids = menus.get_external_id()
        for menu in menus:
            path = self._menu_path(menu)
            by_path.setdefault(path, []).append(menu)
        for path_menus in by_path.values():
            if len(path_menus) <= 1:
                continue

            def score(menu):
                xmlid = external_ids.get(menu.id, "")
                generated_xmlid = xmlid.startswith("smart_construction_core.menu_sc_full_")
                return (
                    1 if xmlid else 0,
                    0 if generated_xmlid else 1,
                    -int(menu.sequence or 0),
                    -menu.id,
                )

            keep = max(path_menus, key=score)
            stale = [menu.id for menu in path_menus if menu.id != keep.id]
            if stale:
                self.env["ir.ui.menu"].sudo().browse(stale).write({"active": False})

    def target_tree(self):
        return self._target_tree()

    @api.model
    def sync_full_coverage(self):
        root = self.env.ref("smart_construction_core.menu_sc_root").sudo()
        top_sequence = 5
        for top_name, top_children in self._target_tree().items():
            top_menu = self._ensure_menu(self.TOP_XMLIDS[top_name], top_name, root, top_sequence)
            top_sequence += 10
            child_sequence = 10
            for child_name, child_value in top_children.items():
                if isinstance(child_value, dict) and "model" not in child_value:
                    container_xmlid = self.KNOWN_MENU_XMLIDS.get(
                        (top_name, child_name),
                        "menu_sc_full_%s_%s" % (self._slug(top_name), self._slug(child_name)),
                    )
                    container = self._ensure_menu(container_xmlid, child_name, top_menu, child_sequence)
                    self._deactivate_duplicate_target_menus(top_menu, child_name)
                    leaf_sequence = 10
                    for leaf_name, action_spec in child_value.items():
                        action = self._action_for_leaf(action_spec, leaf_name)
                        code = "%s_%s_%s" % (self._slug(top_name), self._slug(child_name), self._slug(leaf_name))
                        self._ensure_menu("menu_sc_full_%s" % code, leaf_name, container, leaf_sequence, action=action)
                        self._deactivate_duplicate_target_menus(container, leaf_name)
                        leaf_sequence += 10
                else:
                    action = self._action_for_leaf(child_value, child_name)
                    code = "%s_%s" % (self._slug(top_name), self._slug(child_name))
                    self._ensure_menu("menu_sc_full_%s" % code, child_name, top_menu, child_sequence, action=action)
                    self._deactivate_duplicate_target_menus(top_menu, child_name)
                child_sequence += 10
        self._deactivate_duplicate_menu_paths(root)
        self._deactivate_non_target_menus(root)
        return True
