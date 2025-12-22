# -*- coding: utf-8 -*-
"""
成本域聚合工具 / 领域服务。

兼容模型 project.budget.line 已移动至 budget_compat.py，
避免 cost_domain.py 里同时承担“领域服务 + 兼容层”的职责。
"""
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProjectBudget(models.Model):
    """Budget header scoped to a single project/contract version."""

    _name = "project.budget"
    _description = "项目预算头"
    _order = "project_id, version_date desc, id desc"

    name = fields.Char("预算名称", required=True)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
    )
    contract_id = fields.Many2one(
        "account.analytic.account",
        string="关联合同",
        domain="[('project_ids', 'in', project_id)]",
        help="可选：用于映射主合同或成本中心。",
    )
    origin_budget_id = fields.Many2one(
        "project.budget",
        string="复制来源",
        readonly=True,
        help="若该预算由复制生成，记录源预算版本以便审计追踪。",
    )

    version = fields.Char(
        "版本号",
        help="投标版/控制版/调整版，若未填写系统会按项目自动生成。",
        copy=False,
    )
    version_date = fields.Date("版本日期", default=fields.Date.context_today)
    is_active = fields.Boolean("当前生效", default=True)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        default=lambda self: self.env.company.currency_id.id,
    )

    amount_revenue_target = fields.Monetary("目标收入", currency_field="currency_id")
    amount_cost_target = fields.Monetary("目标成本", currency_field="currency_id")
    margin_target = fields.Monetary(
        "目标毛利", currency_field="currency_id", compute="_compute_margin", store=True
    )
    margin_rate_target = fields.Float(
        "目标毛利率(%)", compute="_compute_margin", store=True
    )

    note = fields.Text("说明")

    line_ids = fields.One2many(
        "project.budget.boq.line",
        "budget_id",
        string="预算清单",
    )

    _sql_constraints = [
        (
            "project_version_unique",
            "unique(project_id, version)",
            "同一项目的预算版本号必须唯一。",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """在创建预算时自动填充版本号。"""
        for vals in vals_list:
            project_id = vals.get("project_id")
            if project_id and not vals.get("version"):
                vals["version"] = self._generate_version_label(project_id)
        return super().create(vals_list)

    def _generate_version_label(self, project_id):
        """返回形如 V001 的连续版本号。"""
        count = self.search_count([("project_id", "=", project_id)])
        return f"V{count + 1:03d}"

    @api.depends("amount_revenue_target", "amount_cost_target")
    def _compute_margin(self):
        """Compute target margin/margin rate for reporting."""
        for rec in self:
            revenue = rec.amount_revenue_target or 0.0
            cost = rec.amount_cost_target or 0.0
            margin = revenue - cost
            rec.margin_target = margin
            rec.margin_rate_target = revenue and (margin / revenue) * 100.0 or 0.0

    def action_set_active(self):
        """Mark current budget as active and archive siblings."""
        for budget in self:
            if budget.is_active:
                continue
            others = self.search(
                [
                    ("project_id", "=", budget.project_id.id),
                    ("is_active", "=", True),
                    ("id", "!=", budget.id),
                ]
            )
            others.write({"is_active": False})
            budget.is_active = True
        return True

    def action_archive_version(self):
        """Archive the selected budget versions."""
        self.write({"is_active": False})
        return True

    def action_copy_version(self):
        """Duplicate budget; copy_allocations=False drops BoQ→科目映射."""
        self.ensure_one()
        copy_vals = {
            "name": f"{self.name} - 复制",
            "version": self._generate_version_label(self.project_id.id),
            "is_active": False,
            "version_date": fields.Date.context_today(self),
            "origin_budget_id": self.id,
        }
        new_budget = self.copy(copy_vals)
        if not self.env.context.get("copy_allocations", True):
            new_budget.line_ids.mapped("alloc_ids").unlink()
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.budget",
            "res_id": new_budget.id,
            "view_mode": "form",
            "target": "current",
            "context": {"default_project_id": new_budget.project_id.id},
        }


class ProjectBudgetBoqLine(models.Model):
    _name = "project.budget.boq.line"
    _description = "项目预算 / 中标清单行"
    _order = "budget_id, sequence, id"
    _rec_name = "name"

    budget_id = fields.Many2one(
        "project.budget",
        string="预算",
        required=True,
        ondelete="cascade",
        index=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="budget_id.project_id",
        store=True,
        readonly=True,
    )

    sequence = fields.Integer("序号", default=10)
    boq_code = fields.Char("清单编码")
    name = fields.Char("清单名称", required=True)

    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="对应工程结构",
        help="绑定工程结构以便在统计中核对预算与成本",
    )

    qty_bidded = fields.Float(
        "中标工程量",
        digits="Product Unit of Measure",
    )
    uom_id = fields.Many2one("uom.uom", string="计量单位")
    price_bidded = fields.Monetary(
        "中标单价",
        currency_field="currency_id",
    )
    amount_bidded = fields.Monetary(
        "中标合价",
        compute="_compute_bidded_amount",
        store=True,
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="budget_id.currency_id",
        store=True,
        readonly=True,
    )

    measure_rule = fields.Selection(
        [
            ("qty", "按工程量计价"),
            ("stage", "按阶段计价"),
            ("lump", "总价计价"),
        ],
        string="计价规则",
        default="qty",
    )

    revenue_recognition = fields.Selection(
        [
            ("progress", "按进度确认收入"),
            ("milestone", "按里程碑确认收入"),
            ("completion", "竣工一次性确认"),
        ],
        string="收入确认方式",
        default="progress",
    )

    def unlink(self):
        """防御：若已有合同清单行引用该预算清单行，禁止删除并给出友好提示。

        之前用户在界面操作时直接触发数据库外键报错（construction_contract_line_boq_line_id_fkey），
        这里提前拦截，避免出现难以理解的错误弹窗，并明确提示需要先处理合同行或取消关联。
        """
        ContractLine = self.env["construction.contract.line"]
        for rec in self:
            ref_lines = ContractLine.search([("boq_line_id", "=", rec.id)], limit=1)
            if ref_lines:
                raise UserError(
                    "清单行已被合同清单引用，不能删除。\n"
                    "清单：%s\n"
                    "请先在合同中调整或解除关联，再删除清单。"
                    % (rec.display_name or rec.id)
                )
        return super().unlink()

    note = fields.Char("备注")
    alloc_ids = fields.One2many(
        "project.budget.cost.alloc",
        "budget_boq_line_id",
        string="成本分摊",
        help="记录该清单行如何拆值到不同成本科目",
    )

    @api.depends("qty_bidded", "price_bidded")
    def _compute_bidded_amount(self):
        for line in self:
            qty = line.qty_bidded or 0.0
            price = line.price_bidded or 0.0
            line.amount_bidded = qty * price
class ProjectCostCode(models.Model):
    _name = "project.cost.code"
    _description = "项目成本科目"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "code, id"

    name = fields.Char("名称", required=True)
    code = fields.Char("编码", required=True, index=True)
    parent_id = fields.Many2one("project.cost.code", string="上级科目", index=True)
    parent_path = fields.Char(index=True, unaccent=False)

    type = fields.Selection(
        [
            ("labor", "人工"),
            ("material", "材料"),
            ("machine", "机械"),
            ("subcontract", "分包"),
            ("measure", "措施费"),
            ("overhead", "管理费"),
            ("tax", "税金"),
            ("other", "其他"),
        ],
        string="成本类别",
        required=True,
    )

    level = fields.Integer("层级", compute="_compute_hierarchy", store=True, recursive=True)
    active = fields.Boolean(default=True)
    path_display = fields.Char("路径", compute="_compute_hierarchy", store=True, recursive=True)

    note = fields.Char("说明")

    @api.depends("parent_id", "parent_id.level", "parent_id.path_display", "code", "name")
    def _compute_hierarchy(self):
        for rec in self:
            if rec.parent_id:
                rec.level = (rec.parent_id.level or 0) + 1
                rec.path_display = f"{rec.parent_id.path_display or rec.parent_id.display_name} / {rec.code} {rec.name}"
            else:
                rec.level = 1
                rec.path_display = f"{rec.code} {rec.name}" if rec.code else rec.name

class ProjectCostLedger(models.Model):
    _name = "project.cost.ledger"
    _description = "项目成本台账"
    _order = "date desc, id desc"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
    )

    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        index=True,
    )

    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
        required=True,
        index=True,
    )

    date = fields.Date("发生日期", index=True, default=fields.Date.context_today)
    period = fields.Char("期间(YYYY-MM)", index=True)

    qty = fields.Float("数量")
    uom_id = fields.Many2one("uom.uom", string="单位")
    amount = fields.Monetary("金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        default=lambda self: self.env.company.currency_id.id,
    )

    partner_id = fields.Many2one("res.partner", string="往来单位/人员")
    source_model = fields.Char("来源模型")
    source_id = fields.Integer("来源记录ID")
    source_line_id = fields.Integer("来源行ID")

    note = fields.Char("备注/摘要")

    @staticmethod
    def _compute_period_value(date_value):
        if not date_value:
            return False
        date_obj = fields.Date.to_date(date_value)
        return date_obj.strftime("%Y-%m") if date_obj else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("period") and vals.get("date"):
                vals["period"] = self._compute_period_value(vals["date"])
        project_ids = {vals.get("project_id") for vals in vals_list if vals.get("project_id")}
        if project_ids:
            projects = self.env["project.project"].browse(project_ids)
            projects._ensure_operation_allowed(
                operation_label="记载成本台账",
                blocked_states=("paused", "closed"),
            )
        return super().create(vals_list)

    def write(self, vals):
        if "date" in vals and "period" not in vals:
            vals = dict(vals)
            vals["period"] = self._compute_period_value(vals.get("date"))
        return super().write(vals)


class ProjectBudgetCostAlloc(models.Model):
    _name = "project.budget.cost.alloc"
    _description = "预算清单与成本科目分摊"
    _order = "budget_boq_line_id, cost_code_id, id"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="budget_boq_line_id.project_id",
        store=True,
        readonly=True,
        index=True,
    )

    budget_boq_line_id = fields.Many2one(
        "project.budget.boq.line",
        string="预算清单行",
        required=True,
        ondelete="cascade",
        index=True,
    )

    cost_code_id = fields.Many2one(
        "project.cost.code",
        string="成本科目",
        required=True,
        index=True,
    )

    ratio = fields.Float("分摊比例(0-1)", help="建议值，可不强制合计=1")
    amount_budget = fields.Monetary("对应预算金额", currency_field="currency_id")

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="budget_boq_line_id.currency_id",
        store=True,
        readonly=True,
    )

    note = fields.Char("说明")

class ProjectProgressEntry(models.Model):
    _name = "project.progress.entry"
    _description = "项目进度计量记录"
    _order = "date desc, id desc"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        required=True,
        index=True,
    )

    date = fields.Date("计量日期", default=fields.Date.context_today, index=True)

    qty_done = fields.Float("本期完成工程量")
    qty_cum = fields.Float("累计完成工程量", help="可通过定时任务自动更新")

    progress_rate = fields.Float("累计完成比例(%)")
    note = fields.Char("备注")

    @api.model_create_multi
    def create(self, vals_list):
        project_ids = {vals.get("project_id") for vals in vals_list if vals.get("project_id")}
        if project_ids:
            projects = self.env["project.project"].browse(project_ids)
            projects._ensure_operation_allowed(
                operation_label="新增进度计量",
                blocked_states=("paused", "closed", "closing"),
            )
        return super().create(vals_list)
