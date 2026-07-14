# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import config

from . import operating_metrics as opm
from .state_machine import ScStateMachine


_logger = logging.getLogger(__name__)

CONTRACT_TAX_PERCENTAGES = (1.0, 3.0, 6.0, 9.0, 13.0)
SUPPLEMENT_CONTRACT_CATEGORY_CODES = {
    "contract.income.supplement",
    "contract.expense.supplement",
}
SUPPLEMENT_CONTRACT_EXPECTED_TYPES = {
    "contract.income.supplement": "out",
    "contract.expense.supplement": "in",
}


class ConstructionContract(models.Model):
    """
    Core contract master: covers both revenue and cost contracts with versioned
    amounts, structured lines, and status workflow.
    """

    _name = "construction.contract"
    _description = "项目合同"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation", "sc.delete.guard.mixin"]
    _state_from = ["draft"]
    _state_to = ["confirmed"]
    _cancel_state = "cancel"
    _order = "project_id, type, id desc"
    _rec_names_search = [
        "name",
        "subject",
        "legacy_contract_no",
        "legacy_external_contract_no",
        "legacy_document_no",
        "project_id.name",
        "partner_id.name",
    ]
    _sc_delete_guard_blocker_models = (
        "payment.request",
        "sc.contract.event",
        "sc.invoice.registration",
        "sc.payment.execution",
        "sc.plan",
        "sc.receipt.income",
        "sc.settlement.adjustment",
        "sc.material.rental.plan",
        "sc.material.rental.order",
        "sc.subcontract.plan",
        "sc.subcontract.request",
        "sc.subcontract.register",
        "sc.subcontract.settlement",
        "tender.bid",
    )

    def _register_hook(self):
        """Ensure model registration finishes cleanly."""
        res = super()._register_hook()
        return res

    # --- Identity & basics -------------------------------------------------
    name = fields.Char(
        string="平台单据编号",
        default="新建",
        readonly=True,
        copy=False,
        tracking=True,
    )
    subject = fields.Char(string="合同标题", required=True, tracking=True)
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
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('code', 'in', ['contract.income', 'contract.income.supplement', 'contract.expense', 'contract.expense.supplement'])]",
    )
    original_contract_id = fields.Many2one(
        "construction.contract",
        string="原合同",
        index=True,
        ondelete="restrict",
        domain="[('id', '!=', id), ('type', '=', type), ('business_category_id.code', 'not in', ['contract.income.supplement', 'contract.expense.supplement'])]",
        help="补充合同必须直接关联被补充的原合同。",
    )
    supplement_contract_ids = fields.One2many(
        "construction.contract",
        "original_contract_id",
        string="补充合同",
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目名称",
        required=True,
        index=True,
        tracking=True,
    )
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="发包人",
        required=True,
        index=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        "sc.dictionary",
        string="合同类别",
        domain=[("type", "=", "contract_category")],
    )
    expense_contract_category_auto_id = fields.Many2one(
        "sc.dictionary",
        string="自动支出分类",
        compute="_compute_expense_contract_category_auto_id",
        store=True,
        index=True,
        domain=[("type", "=", "expense_contract_category")],
        help="系统按合同标题/历史标题自动识别的支出合同分类。",
    )
    expense_contract_category_id = fields.Many2one(
        "sc.dictionary",
        string="支出合同分类",
        domain=[("type", "=", "expense_contract_category")],
        index=True,
        help="正式业务办理使用的支出合同分类；用户可按字典维护分类并手工调整。",
    )
    contract_type_id = fields.Many2one(
        "sc.dictionary",
        string="合同方向类型",
        domain=[("type", "=", "contract_type")],
    )
    name_short = fields.Char(string="简称")
    active = fields.Boolean(string="有效", default=True, index=True)

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
        help="使用合同税率百分比进行税额计算。",
    )
    amount_untaxed = fields.Monetary(
        string="合同金额",
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
        string="合同明细合计",
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
    settlement_amount = fields.Monetary(
        string="结算金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    invoice_amount = fields.Monetary(
        string="开票金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    uninvoiced_amount = fields.Monetary(
        string="未开票金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    received_amount = fields.Monetary(
        string="收款金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    unreceived_amount = fields.Monetary(
        string="未收款金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    paid_amount = fields.Monetary(
        string="付款金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_execution_amounts",
        compute_sudo=True,
    )

    # --- Dates & relations -------------------------------------------------
    date_contract = fields.Date(string="合同订立日期")
    date_start = fields.Date(string="计划开工日")
    date_end = fields.Date(string="计划竣工日")

    analytic_id = fields.Many2one(
        "account.analytic.account",
        string="分析账户",
    )
    engineering_address = fields.Char(string="工程地址")
    handler_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    entry_user_id = fields.Many2one("res.users", string="平台录入人", default=lambda self: self.env.user, index=True)
    entry_data = fields.Char(string="录入数据")
    archived = fields.Boolean(string="原件是否归档", index=True)
    budget_id = fields.Many2one(
        "project.budget",
        string="控制预算版本",
        domain="[('project_id', '=', project_id), ('is_active', '=', True)]",
    )

    line_ids = fields.One2many(
        "construction.contract.line",
        "contract_id",
        string="合同明细",
    )
    payment_request_count = fields.Integer(string="付款申请数", compute="_compute_ref_stats")
    settlement_count = fields.Integer(string="结算单数", compute="_compute_ref_stats")
    is_locked = fields.Boolean(string="被引用锁定", compute="_compute_ref_stats")

    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "construction_contract_attachment_rel",
        "contract_id",
        "attachment_id",
        string="合同附件",
    )
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False, tracking=True)

    @api.model
    def _tax_use_from_contract_type(self, contract_type: str) -> str:
        return "sale" if contract_type == "out" else "purchase"

    @api.model
    def _find_tax(self, *, name: str, amount: float, type_tax_use: str):
        """Return an account.tax scoped to company.

        - Search: company + contract-compatible type_tax_use + amount_type=percent + amount
        - If multiple, prefer same name; otherwise pick the first match.
        - Do not create missing taxes at runtime; raise for explicit configuration.
        """
        Tax = self.env["account.tax"].sudo()
        company = self.env.company
        domain = [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", [type_tax_use, "none"]),
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
    def _sc_format_contract_tax_name(self, amount):
        return f"{float(amount):g}%"

    @api.model
    def _sc_bind_xmlid(self, xmlid, record):
        module, name = str(xmlid or "").split(".", 1)
        Imd = self.env["ir.model.data"].sudo()
        row = Imd.search([("module", "=", module), ("name", "=", name)], limit=1)
        vals = {"model": record._name, "res_id": record.id, "noupdate": True}
        if row:
            row.write(vals)
        else:
            vals.update({"module": module, "name": name})
            Imd.create(vals)

    @api.model
    def _sc_contract_tax_group(self, company):
        Group = self.env["account.tax.group"].sudo().with_context(active_test=False)
        group = Group.search([("company_id", "=", company.id), ("name", "=", "合同税率")], limit=1)
        country = company.account_fiscal_country_id or company.partner_id.country_id
        if not country:
            country = self.env.ref("base.cn", raise_if_not_found=False)
        if group:
            if country and group.country_id != country:
                group.write({"country_id": country.id})
            return group
        vals = {"name": "合同税率", "company_id": company.id}
        if country:
            vals["country_id"] = country.id
        return Group.create(vals)

    @api.model
    def _sc_ensure_contract_tax_seeds(self):
        """Create one common percentage tax set per company and bind seed XMLIDs.

        Contract forms only need a percent for custom amount calculations. Using
        Odoo's neutral tax usage avoids duplicate sale/purchase labels such as
        two visible "9%" options in the same dropdown.
        """
        Tax = self.env["account.tax"].sudo().with_context(active_test=False)
        Company = self.env["res.company"].sudo()
        main_company = self.env.ref("base.main_company", raise_if_not_found=False)
        ICP = self.env["ir.config_parameter"].sudo()
        for company in Company.search([]):
            group = self._sc_contract_tax_group(company)
            country = company.account_fiscal_country_id or company.partner_id.country_id
            if not country:
                country = self.env.ref("base.cn", raise_if_not_found=False)
            for amount in CONTRACT_TAX_PERCENTAGES:
                name = self._sc_format_contract_tax_name(amount)
                domain = [
                    ("company_id", "=", company.id),
                    ("type_tax_use", "=", "none"),
                    ("amount_type", "=", "percent"),
                    ("amount", "=", float(amount)),
                    ("price_include", "=", False),
                ]
                candidates = Tax.search(domain, order="active desc, id asc")
                preferred = Tax.browse()
                if main_company and company.id == main_company.id:
                    preferred = self.env.ref(
                        f"smart_construction_seed.tax_{amount:g}",
                        raise_if_not_found=False,
                    )
                    if preferred and (preferred.company_id.id != company.id or preferred.amount != float(amount)):
                        preferred = Tax.browse()
                tax = preferred if preferred else candidates[:1]
                if tax:
                    vals = {}
                    if tax.name != name:
                        vals["name"] = name
                    if tax.type_tax_use != "none":
                        vals["type_tax_use"] = "none"
                    if tax.amount_type != "percent":
                        vals["amount_type"] = "percent"
                    if tax.amount != float(amount):
                        vals["amount"] = float(amount)
                    if tax.price_include:
                        vals["price_include"] = False
                    if tax.tax_group_id != group:
                        vals["tax_group_id"] = group.id
                    if country and tax.country_id != country:
                        vals["country_id"] = country.id
                    if not tax.active:
                        vals["active"] = True
                    if vals:
                        tax.write(vals)
                else:
                    vals = {
                        "name": name,
                        "company_id": company.id,
                        "tax_group_id": group.id,
                        "type_tax_use": "none",
                        "amount_type": "percent",
                        "amount": float(amount),
                        "price_include": False,
                        "active": True,
                    }
                    if country:
                        vals["country_id"] = country.id
                    tax = Tax.create(vals)
                duplicates = (candidates - tax).filtered(lambda item: item.active)
                if duplicates:
                    duplicates.write({"active": False})
                if main_company and company.id == main_company.id:
                    self._sc_bind_xmlid(f"smart_construction_seed.tax_{amount:g}", tax)
                    ICP.set_param(f"sc.seed.tax.none.{amount}", str(tax.id))
                    if float(amount) == 9.0:
                        self._sc_bind_xmlid("smart_construction_seed.tax_sale_9", tax)
                    if float(amount) == 13.0:
                        self._sc_bind_xmlid("smart_construction_seed.tax_purchase_13", tax)
        ICP.set_param("sc.seed.tax_seeded", "1")
        return True

    @api.model
    def _get_default_tax(self, contract_type):
        """Return default tax by contract type with self-healing fallback."""
        type_tax_use = self._tax_use_from_contract_type(contract_type or "out")
        if type_tax_use == "sale":
            name = "9%"
            amount = 9.0
            xmlid = "smart_construction_seed.tax_9"
        else:
            name = "13%"
            amount = 13.0
            xmlid = "smart_construction_seed.tax_13"

        # Prefer the seeded XMLID before falling back to a matching tax record.
        tax = self.env.ref(xmlid, raise_if_not_found=False)
        if tax:
            return tax

        try:
            return self._find_tax(name=name, amount=amount, type_tax_use=type_tax_use)
        except UserError:
            allow_test_mode = False
            in_test = getattr(self.env.registry, "in_test_mode", None)
            if callable(in_test):
                allow_test_mode = bool(in_test())
            allow = bool(config.get("test_enable")) or bool(self.env.context.get("sc_test_mode")) or allow_test_mode
            if not allow:
                raise
            Tax = self.env["account.tax"].sudo()
            domain = [
                ("company_id", "=", self.env.company.id),
                ("type_tax_use", "in", [type_tax_use, "none"]),
                ("amount_type", "=", "percent"),
                ("price_include", "=", False),
                ("amount", "=", float(amount)),
            ]
            existing = Tax.with_context(active_test=False).search(domain, limit=1)
            if existing:
                if not existing.active:
                    existing.active = True
                return existing
            tax = Tax.create(
                {
                    "name": name,
                    "company_id": self.env.company.id,
                    "type_tax_use": type_tax_use,
                    "amount_type": "percent",
                    "amount": float(amount),
                    "price_include": False,
                    "active": True,
                }
            )
            _logger.warning("[TEST] auto-created default tax: %s (%s%% %s)", name, amount, type_tax_use)
            return tax

    @api.model
    def _is_contract_tax_rate(self, tax):
        return bool(
            tax
            and tax.type_tax_use == "none"
            and tax.amount_type == "percent"
            and not tax.price_include
            and tax.tax_group_id.name == "合同税率"
        )

    @api.model
    def _contract_tax_for_amount(self, amount, company=False):
        company = company or self.env.company
        self.with_company(company)._sc_ensure_contract_tax_seeds()
        Tax = self.env["account.tax"].sudo().with_context(active_test=False)
        tax = Tax.search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "none"),
                ("amount_type", "=", "percent"),
                ("amount", "=", float(amount or 0.0)),
                ("price_include", "=", False),
                ("tax_group_id.name", "=", "合同税率"),
            ],
            order="active desc, id asc",
            limit=1,
        )
        if tax and not tax.active:
            tax.active = True
        return tax

    @api.model
    def _normalize_contract_tax_id(self, tax, company=False):
        if not tax:
            return tax
        if self._is_contract_tax_rate(tax):
            return tax
        if tax.amount_type == "percent" and not tax.price_include:
            normalized = self._contract_tax_for_amount(tax.amount, company or tax.company_id or self.env.company)
            if normalized:
                return normalized
        return tax

    @api.model
    def _is_contract_tax_compatible(self, tax, contract_type):
        if not tax:
            return False
        expected_use = self._tax_use_from_contract_type(contract_type or "out")
        return (
            tax.type_tax_use in (expected_use, "none")
            and tax.amount_type == "percent"
            and not tax.price_include
        )

    @api.model
    def _sync_contract_tax_ids_to_neutral(self):
        self._sc_ensure_contract_tax_seeds()
        rows = self.sudo().search([("tax_id", "!=", False)])
        for contract in rows:
            normalized = self._normalize_contract_tax_id(contract.tax_id, contract.company_id)
            if normalized and normalized != contract.tax_id:
                contract.with_context(skip_validation_check=True, tracking_disable=True).write({"tax_id": normalized.id})
        return True

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _contract_type_from_business_category_code(self, code):
        code = str(code or "").strip()
        if code in {"contract.income", "contract.income.supplement"}:
            return "out"
        if code in {"contract.expense", "contract.expense.supplement"}:
            return "in"
        return False

    @api.model
    def _contract_type_from_business_category_id(self, category_id):
        if not category_id:
            return False
        category = self.env["sc.business.category"].sudo().browse(category_id).exists()
        return self._contract_type_from_business_category_code(category.code) if category else False

    @api.model
    def _business_category_code_from_id(self, category_id):
        if not category_id:
            return False
        category = self.env["sc.business.category"].sudo().browse(category_id).exists()
        return category.code if category else False

    @api.model
    def _business_category_code_from_vals(self, vals, record=False):
        if "business_category_id" in vals:
            return self._business_category_code_from_id(vals.get("business_category_id"))
        if record and record.business_category_id:
            return record.business_category_id.code
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        return code or False

    @api.model
    def _is_supplement_contract_category_code(self, code):
        return code in SUPPLEMENT_CONTRACT_CATEGORY_CODES

    @api.model
    def _original_contract_from_vals(self, vals, record=False):
        if "original_contract_id" in vals:
            original_id = vals.get("original_contract_id")
        elif record:
            return record.original_contract_id
        else:
            original_id = False
        if isinstance(original_id, (list, tuple)):
            original_id = original_id[0] if original_id else False
        try:
            original_id = int(original_id) if original_id else False
        except (TypeError, ValueError):
            original_id = False
        return self.browse(original_id).exists() if original_id else self.browse()

    @api.model
    def _apply_original_contract_defaults_to_vals(self, vals):
        original = self._original_contract_from_vals(vals)
        if not original:
            return vals
        vals["type"] = original.type
        relation_fields = (
            "project_id",
            "partner_id",
            "currency_id",
            "tax_id",
            "category_id",
            "expense_contract_category_id",
            "contract_type_id",
            "budget_id",
            "analytic_id",
        )
        for field_name in relation_fields:
            source = original[field_name]
            vals[field_name] = source.id if source else False
        vals["engineering_address"] = original.engineering_address or False
        vals["date_start"] = original.date_start or False
        vals["date_end"] = original.date_end or False
        subject = str(vals.get("subject") or "").strip()
        if not subject or subject == "补充合同":
            vals["subject"] = "%s补充合同" % (original.subject or original.name or "原合同")
        return vals

    @api.model
    def _context_contract_type(self):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        return self._contract_type_from_business_category_code(code) or self.env.context.get("default_type") or False

    def _resolve_business_category_id(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        contract_type = (
            self._contract_type_from_business_category_code(code)
            or self.env.context.get("default_type")
            or vals.get("type")
            or "out"
        )
        if not code:
            code = "contract.income" if contract_type == "out" else "contract.expense"
        category = self.env["sc.business.category"].sudo().search(
            [
                ("code", "=", code),
                ("target_model", "in", ["construction.contract", "construction.contract.income", "construction.contract.expense"]),
            ],
            limit=1,
        )
        return category.id if category else False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        if project_id and "operation_strategy" in fields_list and not res.get("operation_strategy"):
            project = self.env["project.project"].browse(project_id).exists()
            if project:
                res["operation_strategy"] = project.operation_strategy
        context_code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        category_type = self._contract_type_from_business_category_code(context_code)
        contract_type = category_type or self.env.context.get("default_type") or res.get("type") or "out"
        if "type" in fields_list and (category_type or not res.get("type")):
            res["type"] = contract_type
        tax = self.env["account.tax"].browse(res.get("tax_id")).exists() if res.get("tax_id") else False
        if "tax_id" in fields_list and (not tax or not self._is_contract_tax_compatible(tax, contract_type)):
            default_tax = self._get_default_tax(contract_type)
            res["tax_id"] = default_tax.id
        if "business_category_id" in fields_list and not res.get("business_category_id"):
            category_id = self._resolve_business_category_id(res)
            if category_id:
                res["business_category_id"] = category_id
        return res

    @api.onchange("type")
    def _onchange_type(self):
        """Adjust default税率 and restrict selection by类型."""
        domain = {}
        if self.type:
            expected_use = "sale" if self.type == "out" else "purchase"
            if (not self.tax_id) or (self.tax_id.type_tax_use not in (expected_use, "none")):
                default_tax = self._get_default_tax(self.type)
                if default_tax:
                    self.tax_id = default_tax
            domain = {"tax_id": [("type_tax_use", "in", [expected_use, "none"])]}
        return {"domain": domain}

    @api.onchange("original_contract_id")
    def _onchange_original_contract_id(self):
        for contract in self:
            original = contract.original_contract_id
            if not original:
                continue
            contract.type = original.type
            contract.project_id = original.project_id
            contract.partner_id = original.partner_id
            contract.currency_id = original.currency_id
            contract.tax_id = original.tax_id
            contract.category_id = original.category_id
            contract.expense_contract_category_id = original.expense_contract_category_id
            contract.contract_type_id = original.contract_type_id
            contract.budget_id = original.budget_id
            contract.analytic_id = original.analytic_id
            contract.engineering_address = original.engineering_address
            contract.date_start = original.date_start
            contract.date_end = original.date_end
            if not contract.subject or contract.subject.strip() == "补充合同":
                contract.subject = "%s补充合同" % (original.subject or original.name or "原合同")

    def _compute_ref_stats(self):
        Pay = self.env["payment.request"]
        Settle = self.env["sc.settlement.order"]
        cancel_states_pay = {"cancel", "rejected", "cancelled"}
        cancel_states_settle = {"cancel", "cancelled"}
        for contract in self:
            pay_domain = [("contract_id", "=", contract.id)]
            if "state" in Pay._fields:
                pay_domain.append(("state", "not in", list(cancel_states_pay)))
            settle_domain = [("contract_id", "=", contract.id)]
            if "state" in Settle._fields:
                settle_domain.append(("state", "not in", list(cancel_states_settle)))
            pay_cnt = Pay.search_count(pay_domain)
            settle_cnt = Settle.search_count(settle_domain)
            contract.payment_request_count = pay_cnt
            contract.settlement_count = settle_cnt
            contract.is_locked = bool(pay_cnt or settle_cnt)

    def unlink(self):
        locked = self.filtered(lambda rec: rec.state not in ("draft", "cancel"))
        if locked:
            raise UserError("仅草稿或已取消的合同允许删除。")
        self._sc_raise_delete_blockers(action_label="删除合同")
        return super().unlink()

    @api.depends("amount_final")
    def _compute_execution_amounts(self):
        settlement_map = self._sum_amount_by_contract(
            "sc.settlement.order",
            "amount_total",
            excluded_states=("cancel", "cancelled"),
        )
        invoice_map = self._sum_amount_by_contract(
            "sc.invoice.registration",
            "amount_total",
            included_states=("registered", "legacy_confirmed"),
        )
        receipt_map = self._sum_amount_by_contract(
            "sc.receipt.income",
            "amount",
            included_states=("received", "legacy_confirmed"),
        )
        payment_map = opm.contract_actual_paid_amount_map(self.env, self.ids)
        for contract in self:
            total = contract.amount_final or 0.0
            invoice_amount = invoice_map.get(contract.id, 0.0)
            received_amount = receipt_map.get(contract.id, 0.0)
            paid_amount = payment_map.get(contract.id, 0.0)
            contract.settlement_amount = settlement_map.get(contract.id, 0.0)
            contract.invoice_amount = invoice_amount
            contract.uninvoiced_amount = max(total - invoice_amount, 0.0)
            contract.received_amount = received_amount
            contract.unreceived_amount = max(total - received_amount, 0.0)
            contract.paid_amount = paid_amount
            contract.unpaid_amount = max(total - paid_amount, 0.0)

    def _sum_amount_by_contract(self, model_name, amount_field, excluded_states=(), included_states=()):
        contract_ids = self.ids
        if not contract_ids or model_name not in self.env.registry:
            return {}
        Model = self.env[model_name].sudo()
        if amount_field not in Model._fields or "contract_id" not in Model._fields:
            return {}
        domain = [("contract_id", "in", contract_ids)]
        if included_states and "state" in Model._fields:
            domain.append(("state", "in", list(included_states)))
        elif excluded_states and "state" in Model._fields:
            domain.append(("state", "not in", list(excluded_states)))
        rows = Model.read_group(domain, [amount_field], ["contract_id"])
        return {
            row["contract_id"][0]: row.get(f"{amount_field}_sum", row.get(amount_field, 0.0)) or 0.0
            for row in rows
            if row.get("contract_id")
        }

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

            # 清理孤儿合同明细（对应预算行已被删除），否则后续写入会触发外键错误
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
        ScStateMachine.selection(ScStateMachine.CONTRACT),
        string="平台状态",
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
            if contract.tax_id.type_tax_use not in (expect, "none"):
                raise ValidationError("合同类型与税率类型不一致，请选择正确的税率。")
            if contract.tax_id.amount_type != "percent":
                raise ValidationError("合同仅支持百分比税率，请选择 amount_type=percent 的税。")
            if contract.tax_id.price_include:
                raise ValidationError("合同税率必须为不含税价，请选择未含税的税率。")

    @api.constrains("business_category_id", "original_contract_id", "type", "project_id", "partner_id")
    def _check_supplement_original_contract(self):
        for contract in self:
            code = contract.business_category_id.code if contract.business_category_id else False
            is_supplement = self._is_supplement_contract_category_code(code)
            if not is_supplement:
                if contract.original_contract_id:
                    raise ValidationError("原合同仅用于补充合同办理。")
                continue
            original = contract.original_contract_id
            if not original:
                raise ValidationError("补充合同必须先选择原合同。")
            if original == contract:
                raise ValidationError("补充合同不能关联自身作为原合同。")
            if self._is_supplement_contract_category_code(original.business_category_id.code if original.business_category_id else False):
                raise ValidationError("补充合同应直接关联原合同，不能再关联另一份补充合同。")
            expected_type = SUPPLEMENT_CONTRACT_EXPECTED_TYPES.get(code)
            if expected_type and (contract.type != expected_type or original.type != expected_type):
                raise ValidationError("补充合同的办理类型必须与原合同方向一致。")
            if contract.project_id and original.project_id and contract.project_id != original.project_id:
                raise ValidationError("补充合同的项目必须与原合同一致。")
            if contract.partner_id and original.partner_id and contract.partner_id != original.partner_id:
                raise ValidationError("补充合同的往来单位必须与原合同一致。")

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

    @api.depends(
        "name",
        "subject",
        "legacy_contract_no",
        "legacy_external_contract_no",
        "legacy_document_no",
        "project_id.display_name",
        "partner_id.display_name",
    )
    def _compute_display_name(self):
        for contract in self:
            subject = (contract.subject or "").strip()
            contract_no = (
                contract.legacy_contract_no
                or contract.legacy_external_contract_no
                or contract.legacy_document_no
                or ""
            ).strip()
            context_parts = [
                part
                for part in (
                    contract.project_id.display_name if contract.project_id else "",
                    contract.partner_id.display_name if contract.partner_id else "",
                )
                if part
            ]
            label = subject or contract_no or contract.name or _("合同")
            suffix_parts = []
            if contract_no and contract_no != label:
                suffix_parts.append(contract_no)
            suffix_parts.extend(context_parts[:2])
            if contract.name and contract.name not in (label, contract_no):
                suffix_parts.append(contract.name)
            contract.display_name = "%s（%s）" % (label, " / ".join(suffix_parts)) if suffix_parts else label

    def _expense_contract_category_rule_text(self):
        self.ensure_one()
        return " ".join(
            value
            for value in (
                self.subject,
                self.legacy_visible_title,
                self.legacy_visible_category,
                self.legacy_contract_no,
                self.legacy_document_no,
                self.legacy_external_contract_no,
                self.note,
            )
            if value
        )

    @api.model
    def _expense_contract_category_code_for_text(self, value):
        text = str(value or "")
        rules = (
            ("material", ("材料", "供货", "采购", "供应", "商砼", "混凝土", "砂石", "钢材", "水泥", "砖", "管材", "苗木")),
            ("labor", ("劳务", "人工", "用工", "清包", "班组", "工资")),
            ("machine", ("机械", "挖机", "装载机", "吊车", "台班", "设备", "泵车", "塔吊")),
            ("rental", ("租赁", "租用", "租入", "租金", "钢管租赁", "周转材料")),
            ("subcontract", ("分包", "专业分包", "专包", "专业承包")),
        )
        for code, keywords in rules:
            if any(keyword in text for keyword in keywords):
                return code
        return "other"

    @api.model
    def _expense_contract_category_by_code(self, code):
        return self.env["sc.dictionary"].sudo().search(
            [("type", "=", "expense_contract_category"), ("code", "=", code), ("active", "=", True)],
            limit=1,
        )

    @api.depends(
        "type",
        "subject",
        "legacy_visible_title",
        "legacy_visible_category",
        "legacy_contract_no",
        "legacy_document_no",
        "legacy_external_contract_no",
        "note",
    )
    def _compute_expense_contract_category_auto_id(self):
        category_model = self.env["sc.dictionary"].sudo()
        categories = {
            row.code: row
            for row in category_model.search([("type", "=", "expense_contract_category"), ("active", "=", True)])
            if row.code
        }
        for contract in self:
            if contract.type != "in":
                contract.expense_contract_category_auto_id = False
                continue
            code = contract._expense_contract_category_code_for_text(contract._expense_contract_category_rule_text())
            contract.expense_contract_category_auto_id = categories.get(code) or categories.get("other")

    # --- Sequencing --------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            category_contract_type = self._contract_type_from_business_category_id(vals.get("business_category_id"))
            context_contract_type = self._context_contract_type()
            if category_contract_type or context_contract_type or not vals.get("type"):
                vals["type"] = category_contract_type or context_contract_type or vals.get("type") or "out"
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            self._apply_original_contract_defaults_to_vals(vals)
            tax = self.env["account.tax"].browse(vals.get("tax_id")).exists() if vals.get("tax_id") else False
            if not self._is_contract_tax_compatible(tax, vals.get("type")):
                default_tax = self._get_default_tax(vals["type"])
                vals["tax_id"] = default_tax.id
            elif tax:
                vals["tax_id"] = self._normalize_contract_tax_id(tax, self.env.company).id
            if not vals.get("name") or vals["name"] == "新建":
                seq_code = (
                    "construction.contract.income"
                    if vals.get("type") == "out"
                    else "construction.contract.expense"
                )
                vals["name"] = seq.next_by_code(seq_code) or seq.next_by_code("construction.contract") or "新建"
            if vals.get("type") == "in" and not vals.get("expense_contract_category_id"):
                rule_text = " ".join(
                    str(vals.get(field_name) or "")
                    for field_name in (
                        "subject",
                        "legacy_visible_title",
                        "legacy_visible_category",
                        "legacy_contract_no",
                        "legacy_document_no",
                        "legacy_external_contract_no",
                        "note",
                    )
                )
                category = self._expense_contract_category_by_code(self._expense_contract_category_code_for_text(rule_text))
                if category:
                    vals["expense_contract_category_id"] = category.id
        records = super().create(vals_list)
        for record in records.filtered(lambda rec: rec.type == "in" and not rec.expense_contract_category_id and rec.expense_contract_category_auto_id):
            record.expense_contract_category_id = record.expense_contract_category_auto_id.id
        return records

    def init(self):
        self.env.cr.execute(
            """
            ALTER TABLE construction_contract
                ADD COLUMN IF NOT EXISTS original_contract_id integer
            """
        )
        self.env.cr.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                      FROM pg_constraint
                     WHERE conname = 'construction_contract_original_contract_id_fkey'
                ) THEN
                    ALTER TABLE construction_contract
                        ADD CONSTRAINT construction_contract_original_contract_id_fkey
                        FOREIGN KEY (original_contract_id)
                        REFERENCES construction_contract(id)
                        ON DELETE RESTRICT;
                END IF;
            END $$
            """
        )
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS construction_contract_original_contract_id_index
                ON construction_contract(original_contract_id)
            """
        )
        self.env.cr.execute(
            """
            UPDATE construction_contract contract
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE contract.business_category_id IS NULL
               AND category.code = CASE
                       WHEN contract.type = 'in' THEN 'contract.expense'
                       ELSE 'contract.income'
                   END
               AND category.target_model = 'construction.contract'
            """
        )
        self.env.cr.execute(
            """
            UPDATE construction_contract contract
               SET visible_unreceived_amount = CASE
                       WHEN regexp_replace(COALESCE(contract.legacy_visible_unreceived_amount, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(contract.legacy_visible_unreceived_amount, '[^0-9.-]', '', 'g')::numeric
                       ELSE GREATEST(
                           COALESCE(contract.visible_contract_amount, contract.legacy_contract_amount, contract.amount_untaxed, 0.0)
                           - COALESCE(contract.visible_received_amount, 0.0),
                           0.0
                       )
                   END,
                   visible_unreceived_rate = CASE
                       WHEN COALESCE(NULLIF(contract.legacy_visible_unreceived_rate, ''), '') != ''
                       THEN contract.legacy_visible_unreceived_rate
                       WHEN COALESCE(contract.visible_contract_amount, contract.legacy_contract_amount, contract.amount_untaxed, 0.0) != 0
                       THEN CONCAT(
                           ROUND(
                               (
                                   CASE
                                       WHEN regexp_replace(COALESCE(contract.legacy_visible_unreceived_amount, ''), '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                                       THEN regexp_replace(contract.legacy_visible_unreceived_amount, '[^0-9.-]', '', 'g')::numeric
                                       ELSE GREATEST(
                                           COALESCE(contract.visible_contract_amount, contract.legacy_contract_amount, contract.amount_untaxed, 0.0)
                                           - COALESCE(contract.visible_received_amount, 0.0),
                                           0.0
                                       )
                                   END
                               )
                               / COALESCE(contract.visible_contract_amount, contract.legacy_contract_amount, contract.amount_untaxed, 0.0)
                               * 100,
                               2
                           ),
                           '%'
                       )
                       ELSE ''
                   END
             WHERE contract.type = 'out'
            """
        )

    def write(self, vals):
        vals = dict(vals or {})
        if vals.get("tax_id"):
            tax = self.env["account.tax"].browse(vals.get("tax_id")).exists()
            normalized = self._normalize_contract_tax_id(tax, self.env.company)
            if normalized:
                vals["tax_id"] = normalized.id
        if "original_contract_id" in vals:
            for record in self:
                record_vals = dict(vals)
                self._apply_original_contract_defaults_to_vals(record_vals)
                super(ConstructionContract, record).write(record_vals)
            res = True
        else:
            res = super().write(vals)
        trigger_fields = {
            "type",
            "subject",
            "legacy_visible_title",
            "legacy_visible_category",
            "legacy_contract_no",
            "legacy_document_no",
            "legacy_external_contract_no",
            "note",
        }
        if trigger_fields.intersection(vals) and "expense_contract_category_id" not in vals:
            for record in self.filtered(lambda rec: rec.type == "in" and not rec.expense_contract_category_id and rec.expense_contract_category_auto_id):
                record.expense_contract_category_id = record.expense_contract_category_auto_id.id
        return res

    # --- State transitions -------------------------------------------------
    def action_confirm(self):
        for contract in self:
            old = contract.state
            if contract.state == "draft":
                if contract._requires_contract_approval() and contract.validation_status != "validated":
                    contract._request_contract_validation()
                    continue
                policy = self.env["sc.approval.policy"].get_active_policy(contract._name, company=contract.company_id)
                if policy and not contract._requires_contract_approval():
                    policy.assert_user_can_approve()
                contract.with_context(skip_validation_check=True).write(
                    {"state": "confirmed", "reject_reason": False}
                )
                contract._post_contract_state_message("合同状态：草稿 → 已生效")

    def _requires_contract_approval(self):
        self.ensure_one()
        return self.env["sc.approval.policy"].is_approval_required(self._name, company=self.company_id)

    def _request_contract_validation(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            reviews = self.request_validation()
            if not reviews:
                raise UserError(_("项目合同已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            raise UserError(_("项目合同已经在统一审批流程中，请等待审批完成。"))
        self.with_context(skip_validation_check=True).write({"reject_reason": False})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "draft"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        contracts_to_confirm = self.browse()
        for contract in self:
            if contract.state != "draft":
                continue
            if contract.validation_status != "validated":
                continue
            contract.with_context(skip_validation_check=True).write({"reject_reason": False})
            contracts_to_confirm |= contract
        if contracts_to_confirm:
            return contracts_to_confirm.with_context(skip_validation_check=True).action_confirm()
        return True

    def action_on_tier_rejected(self, reason=None):
        for contract in self:
            if contract.state != "draft":
                continue
            contract.with_context(skip_validation_check=True).write(
                {"reject_reason": reason or contract._get_tier_reject_reason()}
            )

    def _post_contract_state_message(self, body):
        for contract in self:
            try:
                contract.message_post(body=body)
            except (AccessError, UserError, ValidationError) as exc:
                _logger.warning(
                    "contract state message skipped contract=%s state=%s error=%s",
                    contract.id,
                    contract.state,
                    exc,
                )

    def action_set_running(self):
        for contract in self:
            old = contract.state
            if contract.state not in ("draft", "confirmed"):
                raise UserError("仅草稿/已生效的合同可置为执行中。")
            contract.state = "running"
            if old != contract.state:
                contract._post_contract_state_message("合同状态：%s → 执行中" % ("已生效" if old == "confirmed" else "草稿"))

    def action_close(self):
        for contract in self:
            old = contract.state
            if contract.state not in ("confirmed", "running"):
                raise UserError("仅已生效/执行中的合同可关闭。")
            if not contract.line_ids:
                raise UserError("无合同明细的合同不可关闭，请补充明细。")
            contract.state = "closed"
            if old != contract.state:
                contract._post_contract_state_message("合同状态：%s → 已关闭" % ("已生效" if old == "confirmed" else "执行中"))

    def action_cancel(self):
        for contract in self:
            old = contract.state
            if contract.is_locked:
                raise UserError("合同已被付款申请/结算单引用，禁止取消。")
            if contract.state != "cancel":
                contract.state = "cancel"
                if old != contract.state:
                    contract._post_contract_state_message("合同状态：取消")

    def action_reset_draft(self):
        for contract in self:
            old = contract.state
            if contract.is_locked:
                raise UserError("合同已被付款申请/结算单引用，禁止重置为草稿。")
            contract.state = "draft"
            if old != contract.state:
                contract._post_contract_state_message("合同状态：重置为草稿")

    def action_open_payment_requests(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_payment_request").read()[0]
        action["domain"] = [("contract_id", "=", self.id)]
        ctx = dict(self.env.context)
        ctx.update({"default_contract_id": self.id, "default_project_id": self.project_id.id})
        action["context"] = ctx
        return action

    def action_open_settlements(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_settlement_order").read()[0]
        action["domain"] = [("contract_id", "=", self.id)]
        ctx = dict(self.env.context)
        ctx.update({"default_contract_id": self.id, "default_project_id": self.project_id.id})
        action["context"] = ctx
        return action


class ConstructionContractLine(models.Model):
    """Business contract details with optional BoQ linkage."""

    _name = "construction.contract.line"
    _description = "合同明细"
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
        help="仅实际合同明细计入汇总，章节/父项不计入，用于分组/透视/看板统计。",
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
