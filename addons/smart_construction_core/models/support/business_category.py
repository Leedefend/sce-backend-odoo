# -*- coding: utf-8 -*-
import ast
import json
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.misc import file_path


BUSINESS_CATEGORY_TEMPLATE_VERSION = "2026-06-13.1"
CONTRACT_HANDLING_CATEGORY_CODES = {
    "contract.income",
    "contract.income.supplement",
    "contract.expense",
    "contract.expense.supplement",
}
BUSINESS_CATEGORY_ACTION_BINDINGS = {
    "site.construction.diary": "smart_construction_core.action_sc_construction_diary",
    "site.quality.issue": "smart_construction_core.action_sc_quality_issue",
    "site.quality.rectification": "smart_construction_core.action_sc_quality_rectification",
    "site.quality.recheck": "smart_construction_core.action_sc_quality_recheck",
    "site.safety.issue": "smart_construction_core.action_sc_safety_issue",
    "site.safety.rectification": "smart_construction_core.action_sc_safety_rectification",
    "site.safety.recheck": "smart_construction_core.action_sc_safety_recheck",
    "contract.income": "smart_construction_core.action_construction_contract_handling",
    "contract.income.supplement": "smart_construction_core.action_construction_contract_handling",
    "contract.expense": "smart_construction_core.action_construction_contract_handling",
    "contract.expense.supplement": "smart_construction_core.action_construction_contract_handling",
    "settlement.income": "smart_construction_core.action_sc_settlement_order",
    "settlement.expense": "smart_construction_core.action_sc_settlement_order",
    "finance.payment.apply.pay": "smart_construction_core.action_payment_request_user_payment_apply",
    "finance.payment.apply.receive": "smart_construction_core.action_payment_request_receive",
    "finance.payment.execution.partner": "smart_construction_core.action_sc_payment_execution_partner_payment",
    "finance.payment.execution.company": "smart_construction_core.action_sc_payment_execution_company_finance_expense",
    "finance.receipt.income.project": "smart_construction_core.action_sc_receipt_income_user_income",
    "finance.receipt.income.progress": "smart_construction_core.action_sc_receipt_income_engineering_progress",
    "finance.receipt.income.residual": "smart_construction_core.action_sc_receipt_income_user_income",
    "finance.expense.reimbursement": "smart_construction_core.action_sc_expense_claim_reimbursement_request",
    "finance.expense.project": "smart_construction_core.action_sc_expense_claim_project",
    "finance.deposit.bid.pay": "smart_construction_core.action_sc_bid_deposit_pay",
    "finance.deposit.bid.return": "smart_construction_core.action_sc_bid_deposit_return",
    "finance.deposit.self_funding.return": "smart_construction_core.action_sc_self_funding_deposit_refund",
    "finance.deposit.contract.pay": "smart_construction_core.action_sc_contract_deposit_pay",
    "finance.deposit.contract.return": "smart_construction_core.action_sc_contract_deposit_return",
    "finance.deduction.bill": "smart_construction_core.action_sc_expense_claim_deduction_bill",
    "finance.deduction.paid": "smart_construction_core.action_sc_expense_claim_deduction_paid",
    "finance.deduction.refund": "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
    "finance.fund.transfer": "smart_construction_core.action_sc_fund_account_between_user",
    "finance.fund.daily_report": "smart_construction_core.action_sc_fund_daily_user_report",
    "finance.fund.balance_adjustment": "smart_construction_core.action_sc_fund_balance_adjustment",
    "finance.loan.borrowing": "smart_construction_core.action_sc_financing_loan_borrowing_request",
    "finance.loan.contractor_project_borrow": "smart_construction_core.action_sc_financing_loan_contractor_project_borrow",
    "finance.loan.project_borrow_company": "smart_construction_core.action_sc_financing_loan_project_borrow_company",
    "finance.self_funding.income": "smart_construction_core.action_sc_self_funding_registration_income",
    "finance.self_funding.refund": "smart_construction_core.action_sc_self_funding_registration_refund",
    "finance.repayment.registration": "smart_construction_core.action_sc_expense_claim_repayment_registration",
    "finance.repayment.contractor_project": "smart_construction_core.action_sc_expense_claim_contractor_project_repay",
    "finance.repayment.project_company": "smart_construction_core.action_sc_expense_claim_project_repay_company",
    "finance.responsibility.arrival_confirmation": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    "finance.responsibility.self_funding_income": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    "finance.responsibility.self_funding_refund": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    "finance.responsibility.company_contractor.balance": "smart_construction_core.action_sc_company_contractor_responsibility_summary",
    "invoice.output.application": "smart_construction_core.action_sc_invoice_application_user",
    "invoice.output.registration": "smart_construction_core.action_sc_invoice_registration_user",
    "invoice.input.report": "smart_construction_core.action_sc_invoice_input_report_user",
    "invoice.prepaid_tax": "smart_construction_core.action_sc_invoice_prepaid_tax_user",
    "tax.deduction.registration": "smart_construction_core.action_sc_tax_deduction_registration_user",
    "tax.certificate.registration": "smart_construction_core.action_sc_tax_certificate_registration_user",
    "material.plan": "smart_construction_core.action_project_material_plan_my",
    "material.purchase.request": "smart_construction_core.action_sc_material_purchase_request",
    "material.acceptance": "smart_construction_core.action_sc_material_acceptance",
    "material.rfq": "smart_construction_core.action_sc_material_rfq",
    "material.inbound": "smart_construction_core.action_sc_material_inbound_handling",
    "material.outbound": "smart_construction_core.action_sc_material_outbound",
    "material.return": "smart_construction_core.action_sc_material_return",
    "material.transfer": "smart_construction_core.action_sc_material_transfer",
    "material.loss": "smart_construction_core.action_sc_material_loss",
    "material.settlement": "smart_construction_core.action_sc_material_settlement",
}
BUSINESS_CATEGORY_DEFAULT_VALUE_DEFAULTS = {
    "finance.receipt.income.project": {
        "source_kind": "receipt_income",
        "income_category": "收入",
    },
    "finance.receipt.income.progress": {
        "source_kind": "receipt_income",
        "income_category": "工程进度款收入",
    },
    "finance.receipt.income.residual": {
        "source_kind": "residual_receipt",
        "receipt_flow_label": "残余收款",
        "income_category": "其他收款",
    },
}
BUSINESS_CATEGORY_LEDGER_POLICY_DEFAULTS = {
    "finance.fund.transfer": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.fund.daily_report": {
        "facts": ["sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
        "responsibility_scope": "state_or_ledger_input",
    },
    "finance.fund.balance_adjustment": {
        "facts": [],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
        "responsibility_scope": "account_state_adjustment",
        "cashflow_policy": "not_applicable",
    },
    "finance.loan.borrowing": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.loan.contractor_project_borrow": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.loan.project_borrow_company": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.repayment.registration": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.repayment.contractor_project": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.repayment.project_company": {
        "facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
    },
    "finance.self_funding.income": {
        "facts": ["sc.treasury.ledger", "sc.finance.business.fact", "sc.company.contractor.responsibility.fact"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
        "responsibility_scope": "company_contractor",
    },
    "finance.self_funding.refund": {
        "facts": ["sc.treasury.ledger", "sc.finance.business.fact", "sc.company.contractor.responsibility.fact"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
        "responsibility_scope": "company_contractor",
        "balance_guard": "self_funding_balance",
    },
    "finance.deduction.bill": {
        "facts": ["sc.finance.business.fact", "sc.company.contractor.responsibility.fact", "sc.company.contractor.responsibility.summary"],
        "terminal_action": "action_done",
        "payment_request_policy": "not_applicable",
        "balance_policy": "noncash_deduction",
        "responsibility_scope": "company_contractor",
        "business_cognition": "company_deducts_tax_fee_then_charges_to_project_or_contractor",
    },
    "material.inbound": {
        "facts": ["sc.material.inbound", "sc.material.stock.summary"],
        "terminal_action": "action_receive",
        "cost_triggers": {"receive_project_cost_ledger": False},
    },
    "material.outbound": {
        "facts": ["sc.material.outbound", "sc.material.stock.summary", "project.cost.ledger"],
        "terminal_action": "action_issue",
        "cost_triggers": {"issue_project_cost_ledger": True},
    },
    "material.return": {
        "facts": ["sc.material.outbound", "sc.material.stock.summary"],
        "terminal_action": "action_issue",
        "cost_triggers": {"issue_project_cost_ledger": False},
    },
    "material.transfer": {
        "facts": ["sc.material.outbound", "sc.material.inbound", "sc.material.stock.summary"],
        "terminal_action": "action_issue",
        "cost_triggers": {"issue_project_cost_ledger": False},
    },
    "material.loss": {
        "facts": ["sc.material.outbound", "sc.material.stock.summary", "project.cost.ledger"],
        "terminal_action": "action_issue",
        "cost_triggers": {"issue_project_cost_ledger": True},
        "approval_triggers": {"issue_loss_before_project_cost": True},
    },
    "material.settlement": {
        "facts": ["sc.material.settlement", "project.cost.ledger", "payment.request"],
        "terminal_action": "action_confirm",
        "cost_triggers": {"confirm_project_cost_ledger": True, "confirm_payment_request": True},
    },
}
BUSINESS_CATEGORY_REQUIRED_FIELD_DEFAULTS = {
    "settlement.income": ["project_id", "partner_id", "contract_id", "line_ids"],
    "settlement.expense": ["project_id", "partner_id", "contract_id", "line_ids"],
    "finance.fund.transfer": ["operation_date", "amount", "source_account_id", "target_account_id"],
    "finance.loan.borrowing": ["project_id", "partner_id", "document_date", "amount"],
    "finance.loan.contractor_project_borrow": ["project_id", "partner_id", "document_date", "amount"],
    "finance.loan.project_borrow_company": ["project_id", "partner_id", "document_date", "amount"],
    "finance.expense.reimbursement": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payee",
        "receipt_account_name",
        "payee_account",
        "payment_account_name",
        "payer_account",
    ],
    "finance.expense.project": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payee",
        "receipt_account_name",
        "payee_account",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deposit.bid.pay": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payee",
        "receipt_account_name",
        "payee_account",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deposit.contract.pay": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payee",
        "receipt_account_name",
        "payee_account",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deposit.bid.return": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deposit.self_funding.return": [
        "project_id",
        "partner_id",
        "amount",
        "expense_type",
        "receipt_account_name",
        "payee_account",
    ],
    "finance.deposit.contract.return": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deduction.paid": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "expense_type",
        "payee",
        "receipt_account_name",
        "payee_account",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deduction.refund": [
        "payment_request_id",
        "project_id",
        "partner_id",
        "amount",
        "expense_type",
        "payment_account_name",
        "payer_account",
    ],
    "finance.deduction.bill": ["project_id", "partner_id", "deduction_line_ids", "expense_type"],
    "finance.repayment.registration": ["project_id", "partner_id", "amount", "expense_type"],
    "finance.repayment.contractor_project": ["project_id", "partner_id", "amount", "expense_type"],
    "finance.repayment.project_company": ["project_id", "partner_id", "amount", "expense_type"],
    "finance.self_funding.income": [
        "project_id",
        "partner_id",
        "document_date",
        "amount",
        "payment_account_name",
        "partner_account_name",
    ],
    "finance.self_funding.refund": [
        "project_id",
        "partner_id",
        "document_date",
        "amount",
        "payment_account_name",
        "partner_account_name",
    ],
}
BUSINESS_CATEGORY_OBSOLETE_REQUIRED_FIELDS = {
    "settlement.income": ["amount_total"],
    "settlement.expense": ["amount_total"],
}
BUSINESS_CATEGORY_ATTACHMENT_POLICY_DEFAULTS = {
    "finance.expense.reimbursement": "required",
    "finance.expense.project": "required",
    "finance.deposit.bid.pay": "required",
    "finance.deposit.bid.return": "required",
    "finance.deposit.self_funding.return": "required",
    "finance.deposit.contract.pay": "required",
    "finance.deposit.contract.return": "required",
    "finance.deduction.bill": "required",
    "finance.deduction.paid": "required",
    "finance.deduction.refund": "required",
    "finance.repayment.registration": "required",
    "finance.repayment.contractor_project": "required",
    "finance.repayment.project_company": "required",
    "finance.self_funding.income": "required",
    "finance.self_funding.refund": "required",
}
BUSINESS_CATEGORY_APPROVAL_POLICY_DEFAULTS = {
    "finance.expense.reimbursement": "smart_construction_core.approval_policy_expense_claim",
    "finance.expense.project": "smart_construction_core.approval_policy_expense_claim",
    "finance.deposit.bid.pay": "smart_construction_core.approval_policy_expense_claim",
    "finance.deposit.bid.return": "smart_construction_core.approval_policy_expense_claim",
    "finance.deposit.self_funding.return": "smart_construction_core.approval_policy_expense_claim",
    "finance.deposit.contract.pay": "smart_construction_core.approval_policy_expense_claim",
    "finance.deposit.contract.return": "smart_construction_core.approval_policy_expense_claim",
    "finance.deduction.bill": "smart_construction_core.approval_policy_expense_claim",
    "finance.deduction.paid": "smart_construction_core.approval_policy_expense_claim",
    "finance.deduction.refund": "smart_construction_core.approval_policy_expense_claim",
    "finance.repayment.registration": "smart_construction_core.approval_policy_expense_claim",
    "finance.repayment.contractor_project": "smart_construction_core.approval_policy_expense_claim",
    "finance.repayment.project_company": "smart_construction_core.approval_policy_expense_claim",
    "finance.self_funding.income": "smart_construction_core.approval_policy_self_funding_registration",
    "finance.self_funding.refund": "smart_construction_core.approval_policy_self_funding_registration",
}


class ScBusinessCategory(models.Model):
    _name = "sc.business.category"
    _description = "Business Category"
    _order = "industry_template, domain, sequence, name"
    _rec_name = "display_name"

    name = fields.Char(string="业务类别", required=True, translate=True)
    code = fields.Char(string="稳定编码", required=True, index=True)
    display_name = fields.Char(string="显示名称", compute="_compute_display_name", store=True)
    active = fields.Boolean(string="启用", default=True, index=True)
    sequence = fields.Integer(string="排序", default=10)
    template_key = fields.Char(string="模板键", index=True, readonly=True)
    template_version = fields.Char(string="模板版本", readonly=True)
    action_xmlid = fields.Char(string="绑定入口 Action", index=True)
    parent_id = fields.Many2one("sc.business.category", string="上级类别", index=True, ondelete="restrict")
    child_ids = fields.One2many("sc.business.category", "parent_id", string="下级类别")
    industry_template = fields.Selection(
        [
            ("construction", "建筑行业模板"),
            ("general", "通用模板"),
            ("customer", "客户自定义"),
        ],
        string="模板归属",
        default="construction",
        required=True,
        index=True,
    )
    domain = fields.Selection(
        [
            ("finance", "资金财务"),
            ("invoice_tax", "发票税务"),
            ("contract", "合同结算"),
            ("material", "物资采购"),
            ("site", "现场履约"),
            ("general", "通用业务"),
        ],
        string="能力域",
        default="general",
        required=True,
        index=True,
    )
    target_model = fields.Char(string="正式模型", required=True, index=True)
    direction = fields.Selection(
        [
            ("pay", "付款"),
            ("receive", "收款"),
            ("transfer", "转账"),
            ("noncash", "非现金/状态"),
            ("noncash_tax", "非现金税务"),
            ("cost", "成本"),
            ("cost_reversal", "成本转回"),
            ("income", "收入"),
            ("mixed", "复合"),
            ("reference", "追溯参考"),
        ],
        string="业务方向",
        default="mixed",
        required=True,
        index=True,
    )
    source_aliases = fields.Text(string="用户/历史别名")
    default_values_json = fields.Text(string="默认值 JSON", default="{}")
    domain_json = fields.Text(string="入口过滤 JSON", default="[]")
    required_fields_json = fields.Text(string="必填字段 JSON", default="[]")
    visible_groups_json = fields.Text(string="表单分组 JSON", default="[]")
    form_policy_json = fields.Text(string="表单策略 JSON", default="{}")
    ledger_policy_json = fields.Text(string="下游策略 JSON", default="{}")
    attachment_policy = fields.Selection(
        [
            ("none", "不要求"),
            ("recommended", "建议上传"),
            ("required", "必须上传"),
        ],
        string="附件策略",
        default="recommended",
        required=True,
    )
    approval_policy_id = fields.Many2one("sc.approval.policy", string="默认审批策略", ondelete="set null")
    note = fields.Text(string="说明")

    _sql_constraints = [
        ("sc_business_category_code_uniq", "unique(code)", "业务分类编码不能重复。"),
        ("sc_business_category_template_key_uniq", "unique(template_key)", "业务分类模板键不能重复。"),
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for category in self:
            category.display_name = category.name or category.code or ""

    @api.constrains(
        "default_values_json",
        "domain_json",
        "required_fields_json",
        "visible_groups_json",
        "form_policy_json",
        "ledger_policy_json",
    )
    def _check_json_fields(self):
        json_fields = {
            "default_values_json": dict,
            "domain_json": list,
            "required_fields_json": list,
            "visible_groups_json": list,
            "form_policy_json": dict,
            "ledger_policy_json": dict,
        }
        for record in self:
            for field_name, expected_type in json_fields.items():
                raw_value = record[field_name] or ("[]" if expected_type is list else "{}")
                try:
                    parsed = json.loads(raw_value)
                except (TypeError, ValueError) as err:
                    raise ValidationError(_("%s 不是有效 JSON：%s") % (record._fields[field_name].string, err))
                if not isinstance(parsed, expected_type):
                    raise ValidationError(_("%s 的 JSON 顶层类型不正确。") % record._fields[field_name].string)

    def action_open_target_records(self):
        self.ensure_one()
        if self.target_model not in self.env:
            raise ValidationError(_("业务分类绑定的正式模型不存在：%s") % self.target_model)
        try:
            domain = json.loads(self.domain_json or "[]")
        except (TypeError, ValueError):
            domain = []
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 业务记录" % (self.name or self.code),
            "res_model": self.target_model,
            "view_mode": "tree,form",
            "domain": domain,
            "context": json.loads(self.default_values_json or "{}"),
            "target": "current",
        }

    def action_open_bound_entry(self):
        self.ensure_one()
        if not self.action_xmlid:
            return self.action_open_target_records()
        action = self.env.ref(self.action_xmlid, raise_if_not_found=False)
        if not action:
            return self.action_open_target_records()
        result = action.sudo().read()[0]
        result.setdefault("context", {})
        try:
            defaults = json.loads(self.default_values_json or "{}")
        except (TypeError, ValueError):
            defaults = {}
        raw_context = result.get("context") or {}
        if isinstance(raw_context, str):
            try:
                parsed_context = ast.literal_eval(raw_context)
            except (SyntaxError, ValueError):
                parsed_context = {}
            context = dict(parsed_context) if isinstance(parsed_context, dict) else {}
        else:
            context = dict(raw_context) if isinstance(raw_context, dict) else {}
        context.update({"default_%s" % key: value for key, value in defaults.items()})
        context["current_business_category_code"] = self.code
        context["default_business_category_code"] = self.code
        context["current_business_category_label"] = self.name or self.display_name or ""
        context["default_business_category_label"] = self.name or self.display_name or ""
        result_domain = self._combine_bound_action_domain(result.get("domain"))
        result.update(
            {
                "name": self.name,
                "context": context,
                "domain": result_domain,
                "target": "current",
            }
        )
        return result

    def _combine_bound_action_domain(self, action_domain):
        self.ensure_one()
        bound_domain = self._parse_action_domain(action_domain)
        try:
            category_domain = json.loads(self.domain_json or "[]")
        except (TypeError, ValueError):
            category_domain = []
        if bound_domain is None:
            return category_domain or action_domain or []
        if bound_domain and category_domain:
            return expression.AND([bound_domain, category_domain])
        return category_domain or bound_domain

    def _parse_action_domain(self, action_domain):
        if not action_domain:
            return []
        if isinstance(action_domain, list):
            return action_domain
        if isinstance(action_domain, tuple):
            return list(action_domain)
        if isinstance(action_domain, str):
            try:
                parsed = ast.literal_eval(action_domain)
            except (SyntaxError, ValueError):
                return None
            return list(parsed) if isinstance(parsed, (list, tuple)) else []
        return []

    @api.model
    def _sync_template_action_bindings(self):
        """Sync system-owned template metadata without overwriting customer-maintained fields."""
        for code, action_xmlid in BUSINESS_CATEGORY_ACTION_BINDINGS.items():
            category = self.sudo().search([("code", "=", code)], limit=1)
            if not category:
                continue
            vals = {
                "template_key": code,
                "template_version": BUSINESS_CATEGORY_TEMPLATE_VERSION,
                "action_xmlid": action_xmlid,
            }
            if (category.display_name or "").strip() != (category.name or category.code or "").strip():
                vals["display_name"] = category.name or category.code or ""
            default_values = BUSINESS_CATEGORY_DEFAULT_VALUE_DEFAULTS.get(code)
            if default_values is not None:
                vals["default_values_json"] = json.dumps(default_values, ensure_ascii=False, sort_keys=True, default=str)
            ledger_policy = self._merge_template_ledger_policy(
                category.ledger_policy_json,
                BUSINESS_CATEGORY_LEDGER_POLICY_DEFAULTS.get(code),
            )
            if ledger_policy is not None:
                vals["ledger_policy_json"] = json.dumps(ledger_policy, ensure_ascii=False, sort_keys=True, default=str)
            effective_ledger_policy = ledger_policy
            if effective_ledger_policy is None:
                try:
                    effective_ledger_policy = json.loads(category.ledger_policy_json or "{}")
                except (TypeError, ValueError):
                    effective_ledger_policy = {}
            required_fields = self._merge_template_required_fields(
                category.required_fields_json,
                BUSINESS_CATEGORY_REQUIRED_FIELD_DEFAULTS.get(code),
                effective_ledger_policy,
                obsolete=BUSINESS_CATEGORY_OBSOLETE_REQUIRED_FIELDS.get(code),
            )
            if required_fields is not None:
                vals["required_fields_json"] = json.dumps(required_fields, ensure_ascii=False, default=str)
            attachment_policy = BUSINESS_CATEGORY_ATTACHMENT_POLICY_DEFAULTS.get(code)
            if attachment_policy and category.attachment_policy in (False, "none", "recommended"):
                vals["attachment_policy"] = attachment_policy
            approval_policy_xmlid = BUSINESS_CATEGORY_APPROVAL_POLICY_DEFAULTS.get(code)
            if approval_policy_xmlid and not category.approval_policy_id:
                approval_policy = self.env.ref(approval_policy_xmlid, raise_if_not_found=False)
                if approval_policy:
                    vals["approval_policy_id"] = approval_policy.id
            category.write(
                vals
            )
        return True

    @api.model
    def _sync_seed_form_policies(self):
        """Sync product-owned form policies from noupdate seed records."""
        xml_policy_codes = set()
        product_owned_contract_fields = {
            "name",
            "domain",
            "target_model",
            "direction",
            "sequence",
            "source_aliases",
            "default_values_json",
            "domain_json",
            "required_fields_json",
            "visible_groups_json",
            "ledger_policy_json",
            "attachment_policy",
            "note",
        }
        try:
            seed_path = file_path("smart_construction_core/data/business_category_seed.xml")
        except FileNotFoundError:
            seed_path = None
        if seed_path:
            try:
                root = ET.parse(seed_path).getroot()
            except Exception:
                root = None
            xmlid_prefix = "smart_construction_core."
            if root is not None:
                for record in root.findall(".//record"):
                    if record.get("model") != "sc.business.category":
                        continue
                    xmlid = str(record.get("id") or "").strip()
                    if not xmlid:
                        continue
                    form_policy = None
                    target_model = None
                    code = None
                    seed_vals = {}
                    for field in record.findall("field"):
                        field_name = field.get("name")
                        field_text = (field.text or "").strip()
                        if field_name == "code":
                            code = field_text
                        elif field_name == "form_policy_json":
                            form_policy = (field.text or "").strip()
                        elif field_name == "target_model":
                            target_model = field_text
                        if field_name in product_owned_contract_fields:
                            seed_vals[field_name] = int(field_text or "0") if field_name == "sequence" else field_text
                    if (not form_policy or form_policy == "{}") and not target_model:
                        continue
                    category = self.env.ref(f"{xmlid_prefix}{xmlid}", raise_if_not_found=False)
                    if not category or category._name != "sc.business.category":
                        continue
                    xml_policy_codes.add(str(category.code or "").strip())
                    vals = {}
                    if form_policy and form_policy != "{}" and (category.form_policy_json or "").strip() != form_policy:
                        vals["form_policy_json"] = form_policy
                    if target_model and (category.target_model or "").strip() != target_model:
                        vals["target_model"] = target_model
                    if code in CONTRACT_HANDLING_CATEGORY_CODES:
                        for field_name, value in seed_vals.items():
                            current = category[field_name]
                            if field_name == "sequence":
                                if int(current or 0) != int(value or 0):
                                    vals[field_name] = int(value or 0)
                            elif (current or "").strip() != (value or "").strip():
                                vals[field_name] = value
                    if vals:
                        category.sudo().write(vals)
        try:
            from .business_form_policy_templates import get_business_category_form_policy_templates
        except Exception:
            return bool(xml_policy_codes)
        for code, policy in get_business_category_form_policy_templates().items():
            category = self.sudo().search([("code", "=", code)], limit=1)
            if not category:
                continue
            vals = {}
            form_policy = json.dumps(policy or {}, ensure_ascii=False, sort_keys=True, default=str)
            if form_policy and form_policy != "{}" and (category.form_policy_json or "").strip() != form_policy:
                vals["form_policy_json"] = form_policy
            required_fields = [
                field.get("name")
                for field in policy.get("fields") or []
                if field.get("name") and "create" in (field.get("required_profiles") or [])
            ]
            if required_fields:
                required_fields_json = json.dumps(required_fields, ensure_ascii=False, default=str)
                if (category.required_fields_json or "").strip() != required_fields_json:
                    vals["required_fields_json"] = required_fields_json
            if vals:
                category.sudo().write(vals)
        return True

    @api.model
    def _merge_template_required_fields(self, current_raw, defaults, ledger_policy=None, obsolete=None):
        if not defaults:
            return None
        try:
            current = json.loads(current_raw or "[]")
        except (TypeError, ValueError):
            current = []
        if not isinstance(current, list):
            current = []
        merged = list(current)
        changed = False
        obsolete_fields = {str(field_name) for field_name in (obsolete or []) if field_name}
        if obsolete_fields:
            trimmed = [field_name for field_name in merged if field_name not in obsolete_fields]
            if trimmed != merged:
                merged = trimmed
                changed = True
        for field_name in defaults:
            if field_name not in merged:
                merged.append(field_name)
                changed = True
        if isinstance(ledger_policy, dict) and ledger_policy.get("payment_request_policy") == "not_applicable":
            if "payment_request_id" in merged:
                merged = [field_name for field_name in merged if field_name != "payment_request_id"]
                changed = True
        return merged if changed else None

    @api.model
    def _merge_template_ledger_policy(self, current_raw, defaults):
        if not defaults:
            return None
        try:
            current = json.loads(current_raw or "{}")
        except (TypeError, ValueError):
            current = {}
        if not isinstance(current, dict):
            current = {}
        changed = False
        for key, value in defaults.items():
            if key == "cost_triggers":
                current_triggers = current.get("cost_triggers")
                if not isinstance(current_triggers, dict):
                    current_triggers = {}
                    current["cost_triggers"] = current_triggers
                    changed = True
                for trigger, default_value in value.items():
                    if trigger not in current_triggers:
                        current_triggers[trigger] = default_value
                        changed = True
            elif key == "facts":
                current_facts = current.get("facts")
                if not isinstance(current_facts, list):
                    current_facts = []
                    current["facts"] = current_facts
                    changed = True
                for fact in value:
                    if fact not in current_facts:
                        current_facts.append(fact)
                        changed = True
            elif key not in current:
                current[key] = value
                changed = True
            elif key == "terminal_action" and value == "action_done" and current.get(key) == "action_confirm":
                current[key] = value
                changed = True
        if defaults.get("payment_request_policy") == "not_applicable":
            current_facts = current.get("facts")
            if isinstance(current_facts, list) and "payment.ledger" in current_facts:
                current["facts"] = [fact for fact in current_facts if fact != "payment.ledger"]
                changed = True
        return current if changed else None
