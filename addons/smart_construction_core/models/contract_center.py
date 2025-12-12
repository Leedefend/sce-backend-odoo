# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ConstructionContract(models.Model):
    """
    Core contract master: covers both revenue and cost contracts with versioned
    amounts, structured lines, and status workflow.
    """

    _name = "construction.contract"
    _description = "项目合同"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "project_id, type, id desc"

    # --- Identity & basics -------------------------------------------------
    name = fields.Char(
        string="合同编号",
        default="新建",
        readonly=True,
        copy=False,
        tracking=True,
    )
    subject = fields.Char(string="合同名称", required=True, tracking=True)
    type = fields.Selection(
        [
            ("out", "收入合同"),
            ("in", "支出合同"),
        ],
        string="合同类型",
        required=True,
        index=True,
        tracking=True,
        default="out",
    )
    project_id = fields.Many2one(
        "project.project",
        string="所属项目",
        required=True,
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="合同相对方",
        required=True,
        index=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        "sc.dictionary",
        string="合同类别",
        domain=[("type", "=", "contract_category")],
    )
    contract_type_id = fields.Many2one(
        "sc.dictionary",
        string="合同方向类型",
        domain=[("type", "=", "contract_type")],
    )
    name_short = fields.Char(string="简称")

    company_id = fields.Many2one(
        "res.company",
        string="公司",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    # --- Amounts -----------------------------------------------------------
    tax_rate = fields.Float(
        string="税率(%)",
        help="可选：用于根据合同行金额自动计算税额。",
        default=0.0,
    )
    amount_untaxed = fields.Monetary(
        string="不含税金额",
        compute="_compute_amount_total",
        store=True,
        tracking=True,
    )
    amount_tax = fields.Monetary(
        string="税额",
        compute="_compute_amount_total",
        store=True,
    )
    amount_total = fields.Monetary(
        string="含税金额",
        compute="_compute_amount_total",
        store=True,
        tracking=True,
    )
    line_amount_total = fields.Monetary(
        string="合同行金额",
        compute="_compute_line_amount_total",
        currency_field="currency_id",
        store=True,
    )
    amount_change = fields.Monetary(
        string="累计变更金额",
        compute="_compute_final_amount",
        currency_field="currency_id",
        store=True,
    )
    amount_final = fields.Monetary(
        string="最终合同价",
        compute="_compute_final_amount",
        currency_field="currency_id",
        store=True,
    )

    # --- Dates & relations -------------------------------------------------
    date_contract = fields.Date(string="签订日期")
    date_start = fields.Date(string="计划开工日")
    date_end = fields.Date(string="计划竣工日")

    analytic_id = fields.Many2one(
        "account.analytic.account",
        string="分析账户",
    )
    budget_id = fields.Many2one(
        "project.budget",
        string="控制预算版本",
        domain="[('project_id', '=', project_id), ('is_active', '=', True)]",
    )

    line_ids = fields.One2many(
        "construction.contract.line",
        "contract_id",
        string="合同行",
    )

    note = fields.Text(string="备注")
    # --- Change order ------------------------------------------------------
    change_order_ids = fields.One2many(
        "project.change.order",
        "contract_id",
        string="变更单",
    )

    def action_generate_lines_from_budget(self):
        """Populate contract lines from the active budget BoQ."""
        Budget = self.env["project.budget"]
        ContractLine = self.env["construction.contract.line"]
        for contract in self:
            if contract.state != "draft":
                raise UserError("仅草稿状态的合同可以重新生成清单。")
            if not contract.project_id:
                raise UserError("请先选择项目。")
            budget = contract.budget_id
            if not budget:
                budget = Budget.search([
                    ("project_id", "=", contract.project_id.id),
                    ("is_active", "=", True),
                ], limit=1)
            if not budget:
                raise UserError("当前项目缺少生效预算版本，无法生成合同清单。")
            if not budget.line_ids:
                raise UserError("预算版本中没有预算清单行。")

            contract.line_ids.unlink()
            vals_list = [
                {
                    "contract_id": contract.id,
                    "boq_line_id": line.id,
                    "qty_contract": line.qty_bidded or 0.0,
                    "price_contract": line.price_bidded or 0.0,
                }
                for line in budget.line_ids
            ]
            ContractLine.create(vals_list)

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已生效"),
            ("running", "执行中"),
            ("closed", "已关闭"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )

    # --- Computations ------------------------------------------------------
    @api.depends("line_amount_total", "tax_rate")
    def _compute_amount_total(self):
        for contract in self:
            untaxed = contract.line_amount_total or 0.0
            rate = contract.tax_rate or 0.0
            tax_amount = untaxed * rate / 100.0
            contract.amount_untaxed = untaxed
            contract.amount_tax = tax_amount
            contract.amount_total = untaxed + tax_amount

    @api.depends("line_ids.amount_contract")
    def _compute_line_amount_total(self):
        for contract in self:
            contract.line_amount_total = sum(contract.line_ids.mapped("amount_contract"))

    @api.depends("amount_total")
    def _compute_final_amount(self):
        for contract in self:
            # 变更模块尚未上线，留出接口，当前默认 0
            change_amount = 0.0
            contract.amount_change = change_amount
            contract.amount_final = (contract.amount_total or 0.0) + change_amount

    # --- Sequencing --------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "新建":
                vals["name"] = seq.next_by_code("construction.contract") or "新建"
        return super().create(vals_list)

    # --- State transitions -------------------------------------------------
    def action_confirm(self):
        for contract in self:
            if contract.state == "draft":
                contract.state = "confirmed"

    def action_set_running(self):
        for contract in self:
            if contract.state in ("draft", "confirmed"):
                contract.state = "running"

    def action_close(self):
        for contract in self:
            if contract.state in ("confirmed", "running"):
                contract.state = "closed"

    def action_cancel(self):
        for contract in self:
            if contract.state != "cancel":
                contract.state = "cancel"

    def action_reset_draft(self):
        for contract in self:
            contract.state = "draft"


class ConstructionContractLine(models.Model):
    """Structured BoQ lines derived from budget master with contract-specific quantities/prices."""

    _name = "construction.contract.line"
    _description = "合同清单行"
    _order = "sequence, id"

    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        required=True,
        ondelete="cascade",
    )
    project_id = fields.Many2one(
        related="contract_id.project_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="contract_id.currency_id",
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(default=10)

    boq_line_id = fields.Many2one(
        "project.budget.boq.line",
        string="对应中标清单",
        required=True,
        ondelete="restrict",
        domain="[('project_id', '=', project_id)]",
    )
    boq_code = fields.Char(
        related="boq_line_id.boq_code",
        store=True,
        readonly=True,
        string="清单编码",
    )
    boq_name = fields.Char(
        related="boq_line_id.name",
        store=True,
        readonly=True,
        string="清单名称",
    )
    wbs_id = fields.Many2one(
        related="boq_line_id.wbs_id",
        store=True,
        readonly=True,
        string="WBS/分部分项",
    )
    uom_id = fields.Many2one(
        related="boq_line_id.uom_id",
        store=True,
        readonly=True,
        string="计量单位",
    )

    qty_contract = fields.Float(
        string="合同工程量",
        digits="Product Unit of Measure",
    )
    price_contract = fields.Monetary(
        string="合同单价",
        currency_field="currency_id",
    )
    amount_contract = fields.Monetary(
        string="合同合价",
        compute="_compute_amount_contract",
        store=True,
        currency_field="currency_id",
    )

    note = fields.Char("备注")

    @api.depends("qty_contract", "price_contract")
    def _compute_amount_contract(self):
        for line in self:
            qty = line.qty_contract or 0.0
            price = line.price_contract or 0.0
            line.amount_contract = qty * price
class ProjectProject(models.Model):
    """
    Project-level helpers for quick visibility of connected contracts.
    """

    _inherit = "project.project"

    contract_ids = fields.One2many(
        "construction.contract",
        "project_id",
        string="项目合同",
    )
    contract_count = fields.Integer(
        string="合同数量",
        compute="_compute_contract_stats",
    )
    contract_income_total = fields.Monetary(
        string="收入合同金额",
        compute="_compute_contract_stats",
        currency_field="company_currency_id",
    )
    contract_expense_total = fields.Monetary(
        string="支出合同金额",
        compute="_compute_contract_stats",
        currency_field="company_currency_id",
    )

    @api.depends(
        "contract_ids.amount_final",
        "contract_ids.type",
        "contract_ids.currency_id",
    )
    def _compute_contract_stats(self):
        for project in self:
            income = 0.0
            expense = 0.0
            for contract in project.contract_ids:
                amount = contract.amount_final or 0.0
                if contract.type == "out":
                    income += amount
                else:
                    expense += amount
            project.contract_count = len(project.contract_ids)
            project.contract_income_total = income
            project.contract_expense_total = expense
            project.contract_amount = income
            project.subcontract_amount = expense
