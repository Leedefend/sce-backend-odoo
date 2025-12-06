# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectBudget(models.Model):
    _name = "project.budget"
    _description = "Project Budget"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="预算名称", required=True, tracking=True)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
        tracking=True,
    )
    version = fields.Char(string="版本号")
    version_date = fields.Date(string="版本日期", default=fields.Date.context_today)
    # 保持与原有 cost_domain 预算模型字段兼容，供项目计算依赖使用
    is_active = fields.Boolean(string="当前生效", default=True, tracking=True)
    # 兼容旧视图/列表的 active 字段，代理到 is_active，避免缺少数据库列报错
    active = fields.Boolean(related="is_active", string="启用", readonly=False, store=False)

    amount_cost_target = fields.Monetary(
        string="目标成本合计",
        currency_field="currency_id",
        tracking=True,
    )
    amount_revenue_target = fields.Monetary(
        string="目标收入合计",
        currency_field="currency_id",
        tracking=True,
    )
    note = fields.Text(string="说明")
    margin_target = fields.Monetary(
        string="目标毛利",
        currency_field="currency_id",
        tracking=True,
    )
    margin_rate_target = fields.Float(
        string="目标毛利率(%)",
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )

    line_ids = fields.One2many(
        "project.budget.line",
        "budget_id",
        string="预算行",
    )
    # 兼容旧版视图/用法：可选关联分析账户/合同
    contract_id = fields.Many2one(
        "account.analytic.account",
        string="关联合同",
        help="可选：用于映射主合同或成本中心，兼容旧版视图。",
    )

    _sql_constraints = [
        (
            "project_version_unique",
            "unique(project_id, version)",
            "同一项目下预算版本不能重复！",
        ),
    ]

    # 兼容旧版按钮：设为当前 / 停用 / 复制
    def action_set_active(self):
        """设为当前：将本预算设为生效，其他预算取消生效。"""
        for budget in self:
            if not budget.is_active:
                others = self.search([
                    ("project_id", "=", budget.project_id.id),
                    ("is_active", "=", True),
                    ("id", "!=", budget.id),
                ])
                others.write({"is_active": False})
                budget.is_active = True
        return True

    def action_archive_version(self):
        """停用当前预算版本。"""
        self.write({"is_active": False})
        return True

    def action_copy_version(self, copy_allocations=True):
        """复制预算版本，保持不激活，名称/版本可由用户再编辑。
        copy_allocations 兼容旧视图参数，当前直接复制全部字段。
        """
        new_records = self.env[self._name]
        for budget in self:
            new_vals = {
                "name": f"{budget.name} - 复制",
                "is_active": False,
                "active": True,
            }
            new_budget = budget.copy(new_vals)
            new_records |= new_budget
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": new_records[:1].id if new_records else False,
            "target": "current",
        }


class ProjectBudgetLine(models.Model):
    _name = "project.budget.line"
    _description = "Project Budget Line"

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
        index=True,
    )

    boq_line_id = fields.Many2one(
        "project.boq.line",
        string="清单行",
        index=True,
    )
    boq_code = fields.Char(
        string="清单编码",
        related="boq_line_id.code",
        store=True,
        readonly=True,
    )
    wbs_id = fields.Many2one(
        "project.wbs",
        string="WBS",
        index=True,
    )

    name = fields.Char(string="说明")
    sequence = fields.Integer(string="序号", default=10)

    budget_qty = fields.Float(string="预算工程量")
    budget_price = fields.Monetary(
        string="预算单价",
        currency_field="currency_id",
    )
    budget_amount = fields.Monetary(
        string="预算合价",
        currency_field="currency_id",
    )
    measure_rule = fields.Selection(
        [
            ("by_qty", "按工程量计价"),
            ("lump_sum", "总价包干"),
            ("by_schedule", "按节点"),
        ],
        string="计价方式",
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
    alloc_ids = fields.One2many(
        "project.budget.cost.alloc",
        "budget_boq_line_id",
        string="成本分摊",
        help="记录该清单行如何拆值到不同成本科目（兼容旧版视图）",
    )

    # 兼容旧版：预算说明
    note = fields.Text(string="说明")
    uom_id = fields.Many2one(
        "uom.uom",
        string="单位",
        related="boq_line_id.uom_id",
        store=True,
        readonly=True,
    )
    # 兼容旧字段：投标量/价/合价
    qty_bidded = fields.Float(string="标后工程量")
    price_bidded = fields.Monetary(
        string="标后单价",
        currency_field="currency_id",
    )
    amount_bidded = fields.Monetary(
        string="标后合价",
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="budget_id.currency_id",
        store=True,
        readonly=True,
    )

    # compute 逻辑放到 Phase-1 统一处理
