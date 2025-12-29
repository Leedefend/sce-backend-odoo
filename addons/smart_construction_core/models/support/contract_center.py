# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class ConstructionContract(models.Model):
    """
    Core contract master: covers both revenue and cost contracts with versioned
    amounts, structured lines, and status workflow.
    """

    _name = "construction.contract"
    _description = "项目合同"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "project_id, type, id desc"

    def _register_hook(self):
        """Ensure model registration finishes cleanly."""
        res = super()._register_hook()
        return res

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
    tax_id = fields.Many2one(
        "account.tax",
        string="税率",
        required=True,
        help="使用 account.tax 主数据进行税额计算，收入合同使用销项税，支出合同使用进项税。",
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

    @api.model
    def _tax_use_from_contract_type(self, contract_type: str) -> str:
        return "sale" if contract_type == "out" else "purchase"

    @api.model
    def _find_tax(self, *, name: str, amount: float, type_tax_use: str):
        """Return an account.tax scoped to company.

        - Search: company + type_tax_use/all + amount_type=percent + amount
        - If multiple, prefer same name; otherwise pick the first match.
        - Do not create missing taxes at runtime; raise for explicit configuration.
        """
        Tax = self.env["account.tax"].sudo()
        company = self.env.company
        domain = [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", [type_tax_use, "all"]),
            ("amount_type", "=", "percent"),
            ("amount", "=", float(amount)),
        ]
        candidates = Tax.with_context(active_test=False).search(domain)
        if candidates:
            exact = candidates.filtered(lambda t: t.name == name)
            tax = (exact or candidates[:1])[0]
            if not tax.active:
                tax.active = True
            return tax

        raise UserError(
            "缺少默认税率：%(name)s %(amount)s%% %(use)s\n"
            "请在税率主数据中创建后再试。" % {"name": name, "amount": amount, "use": type_tax_use}
        )

    @api.model
    def _get_default_tax(self, contract_type):
        """Return default tax by contract type with self-healing fallback."""
        type_tax_use = self._tax_use_from_contract_type(contract_type or "out")
        if type_tax_use == "sale":
            name = "销项VAT 9%"
            amount = 9.0
        else:
            name = "进项VAT 13%"
            amount = 13.0
        return self._find_tax(
            name=name,
            amount=amount,
            type_tax_use=type_tax_use,
        )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        contract_type = res.get("type") or "out"
        if "tax_id" in fields_list and not res.get("tax_id"):
            default_tax = self._get_default_tax(contract_type)
            res["tax_id"] = default_tax.id
        return res

    @api.onchange("type")
    def _onchange_type(self):
        """Adjust default税率 and restrict selection by类型."""
        domain = {}
        if self.type:
            expected_use = "sale" if self.type == "out" else "purchase"
            if (not self.tax_id) or (self.tax_id.type_tax_use not in (expected_use, "all")):
                default_tax = self._get_default_tax(self.type)
                if default_tax:
                    self.tax_id = default_tax
            domain = {"tax_id": [("type_tax_use", "in", [expected_use, "all"])]}
        return {"domain": domain}

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

            # 清理孤儿合同行（对应预算行已被删除），否则后续写入会触发外键错误
            orphans = contract.line_ids.filtered(lambda l: not l.boq_line_id)
            if orphans:
                orphans.sudo().unlink()

            # 不再整表 unlink，避免存在引用时的外键报错；改为 upsert
            existing = {l.boq_line_id.id: l for l in contract.line_ids}
            for line in budget.line_ids:
                payload = {
                    "qty_contract": line.qty_bidded or 0.0,
                    "price_contract": line.price_bidded or 0.0,
                }
                if line.id in existing:
                    existing[line.id].write(payload)
                else:
                    payload.update(
                        {
                            "contract_id": contract.id,
                            "boq_line_id": line.id,
                        }
                    )
                    ContractLine.create(payload)

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
    @api.depends("line_amount_total", "tax_id")
    def _compute_amount_total(self):
        for contract in self:
            currency = contract.currency_id or contract.company_currency_id
            untaxed = currency.round(contract.line_amount_total or 0.0)
            rate = contract.tax_id.amount if contract.tax_id else 0.0
            tax_amount = 0.0
            if contract.tax_id and contract.tax_id.amount_type == "percent" and not contract.tax_id.price_include:
                tax_amount = currency.round(untaxed * rate / 100.0)
            contract.amount_untaxed = untaxed
            contract.amount_tax = tax_amount
            contract.amount_total = currency.round(untaxed + tax_amount)

    @api.constrains("tax_id", "type")
    def _check_tax_type(self):
        for contract in self:
            if not contract.tax_id:
                continue
            expect = "sale" if contract.type == "out" else "purchase"
            if contract.tax_id.type_tax_use not in (expect, "all"):
                raise ValidationError("合同类型与税率类型不一致，请选择正确的税率。")
            if contract.tax_id.amount_type != "percent":
                raise ValidationError("合同仅支持百分比税率，请选择 amount_type=percent 的税。")
            if contract.tax_id.price_include:
                raise ValidationError("合同税率必须为不含税价，请选择未含税的税率。")

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
            if not vals.get("type"):
                vals["type"] = "out"
            if not vals.get("tax_id"):
                default_tax = self._get_default_tax(vals["type"])
                vals["tax_id"] = default_tax.id
            if not vals.get("name") or vals["name"] == "新建":
                seq_code = (
                    "construction.contract.income"
                    if vals.get("type") == "out"
                    else "construction.contract.expense"
                )
                vals["name"] = seq.next_by_code(seq_code) or seq.next_by_code("construction.contract") or "新建"
        return super().create(vals_list)

    # --- State transitions -------------------------------------------------
    def action_confirm(self):
        for contract in self:
            old = contract.state
            if not contract.line_ids:
                raise UserError("请先录入合同行后再确认。")
            if contract.state == "draft":
                contract.state = "confirmed"
                contract.message_post(body="合同状态：草稿 → 已生效")

    def action_set_running(self):
        for contract in self:
            old = contract.state
            if contract.state not in ("draft", "confirmed"):
                raise UserError("仅草稿/已生效的合同可置为执行中。")
            contract.state = "running"
            if old != contract.state:
                contract.message_post(body="合同状态：%s → 执行中" % ("已生效" if old == "confirmed" else "草稿"))

    def action_close(self):
        for contract in self:
            old = contract.state
            if contract.state not in ("confirmed", "running"):
                raise UserError("仅已生效/执行中的合同可关闭。")
            if not contract.line_ids:
                raise UserError("无合同行的合同不可关闭，请补充清单。")
            contract.state = "closed"
            if old != contract.state:
                contract.message_post(body="合同状态：%s → 已关闭" % ("已生效" if old == "confirmed" else "执行中"))

    def action_cancel(self):
        for contract in self:
            old = contract.state
            if contract.state != "cancel":
                contract.state = "cancel"
                if old != contract.state:
                    contract.message_post(body="合同状态：取消")

    def action_reset_draft(self):
        for contract in self:
            old = contract.state
            contract.state = "draft"
            if old != contract.state:
                contract.message_post(body="合同状态：重置为草稿")


class ConstructionContractLine(models.Model):
    """Structured BoQ lines derived from budget master with contract-specific quantities/prices."""

    _name = "construction.contract.line"
    _description = "合同清单行"
    _order = "sequence, id"

    @api.model
    def _auto_init(self):
        # 防御性补列：老库缺少新增的存储字段时，确保列存在再继续初始化
        res = super()._auto_init()
        cr = self._cr
        cr.execute(
            """
            ALTER TABLE construction_contract_line
                ADD COLUMN IF NOT EXISTS amount_contract_leaf numeric,
                ADD COLUMN IF NOT EXISTS boq_amount_leaf numeric,
                ADD COLUMN IF NOT EXISTS delta_amount numeric,
                ADD COLUMN IF NOT EXISTS boq_amount_source varchar
            """
        )
        return res

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
        required=False,
        ondelete="set null",
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
        group_operator=False,
        help="展示口径：合同工程量 * 合同单价。为防止父项/标题行重复统计，统计场景请使用 amount_contract_leaf。",
    )
    amount_contract_leaf = fields.Monetary(
        string="合同合价(叶子)",
        currency_field="currency_id",
        compute="_compute_amount_contract_leaf",
        store=True,
        group_operator="sum",
        help="仅实际合同行计入汇总，章节/父项不计入，用于分组/透视/看板统计。",
    )
    boq_amount_leaf = fields.Monetary(
        string="清单合价(基准)",
        currency_field="currency_id",
        compute="_compute_boq_amount_leaf",
        store=True,
        readonly=True,
        group_operator="sum",
        help="对应清单的叶子合价，用于合同对标基准；若目标字段缺失则退化为清单展示合价。",
    )
    delta_amount = fields.Monetary(
        string="差额(合同-清单)",
        currency_field="currency_id",
        compute="_compute_delta_amount",
        store=True,
        group_operator="sum",
        help="合同合价(叶子) 与 清单合价(叶子) 之差，便于快速查看溢价/节约。",
    )
    boq_amount_source = fields.Selection(
        [
            ("amount_leaf", "BOQ叶子合价"),
            ("amount_bidded", "预算中标合价"),
            ("qty_price", "数量×单价回退"),
            ("none", "无基准"),
        ],
        string="基准来源",
        compute="_compute_boq_amount_leaf",
        store=True,
        readonly=True,
        help="标记基准取值来源，便于排查差额口径：优先 amount_leaf，其次 amount_bidded，再次 qty*price，最后无基准。",
    )

    note = fields.Char("备注")

    @api.depends("qty_contract", "price_contract")
    def _compute_amount_contract(self):
        for line in self:
            qty = line.qty_contract or 0.0
            price = line.price_contract or 0.0
            line.amount_contract = qty * price

    @api.depends("qty_contract", "price_contract")
    def _compute_amount_contract_leaf(self):
        for line in self:
            # 当前模型无章节/父子结构，默认全部为叶子；若未来引入父子，可在此跳过章节行
            line.amount_contract_leaf = (line.qty_contract or 0.0) * (line.price_contract or 0.0)

    @api.depends("amount_contract_leaf", "boq_amount_leaf")
    def _compute_delta_amount(self):
        for line in self:
            line.delta_amount = (line.amount_contract_leaf or 0.0) - (line.boq_amount_leaf or 0.0)

    @api.depends(
        "boq_line_id",
        "boq_line_id.write_date",
        "boq_line_id.amount_bidded",
        "boq_line_id.qty_bidded",
        "boq_line_id.price_bidded",
    )
    def _compute_boq_amount_leaf(self):
        for line in self:
            boq = line.boq_line_id
            if not boq:
                line.boq_amount_leaf = 0.0
                line.boq_amount_source = "none"
                continue
            if hasattr(boq, "amount_leaf"):
                line.boq_amount_leaf = boq.amount_leaf or 0.0
                line.boq_amount_source = "amount_leaf"
            elif hasattr(boq, "amount_bidded"):
                line.boq_amount_leaf = boq.amount_bidded or 0.0
                line.boq_amount_source = "amount_bidded"
            else:
                qty = getattr(boq, "qty_bidded", False)
                price = getattr(boq, "price_bidded", False)
                if qty is not False and price is not False:
                    line.boq_amount_leaf = (qty or 0.0) * (price or 0.0)
                    line.boq_amount_source = "qty_price"
                else:
                    line.boq_amount_leaf = 0.0
                    line.boq_amount_source = "none"
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
            company_currency = project.company_currency_id or project.company_id.currency_id
            for contract in project.contract_ids:
                amount = contract.amount_final or 0.0
                currency = contract.currency_id or company_currency
                amount = currency._convert(amount, company_currency, contract.company_id, fields.Date.today())
                if contract.type == "out":
                    income += amount
                else:
                    expense += amount
            project.contract_count = len(project.contract_ids)
            project.contract_income_total = income
            project.contract_expense_total = expense
            project.contract_amount = income
            project.subcontract_amount = expense
