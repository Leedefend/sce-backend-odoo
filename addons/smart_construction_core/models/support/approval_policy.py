# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScApprovalPolicy(models.Model):
    _name = "sc.approval.policy"
    _description = "业务审批规则"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"

    BUSINESS_MODEL_SELECTION = [
        ("project.project", "项目立项"),
        ("project.task", "项目任务"),
        ("construction.contract", "项目合同"),
        ("sc.general.contract", "一般合同"),
        ("sc.legacy.purchase.contract.fact", "采购/一般合同"),
        ("project.material.plan", "物资计划"),
        ("purchase.order", "采购订单"),
        ("sc.settlement.order", "结算单"),
        ("payment.request", "付款/收款申请"),
        ("sc.expense.claim", "费用/保证金"),
        ("sc.receipt.income", "收款登记"),
        ("sc.payment.execution", "付款执行"),
        ("sc.invoice.registration", "发票登记"),
        ("sc.financing.loan", "融资借款"),
        ("sc.treasury.reconciliation", "资金对账"),
        ("sc.settlement.adjustment", "结算调整"),
    ]
    APPROVAL_SCOPE_GROUP_XMLIDS = {
        "project_manager": "smart_construction_core.group_sc_cap_project_manager",
        "material_manager": "smart_construction_core.group_sc_cap_material_manager",
        "purchase_manager": "smart_construction_core.group_sc_cap_purchase_manager",
        "finance_manager": "smart_construction_core.group_sc_cap_finance_manager",
        "contract_manager": "smart_construction_core.group_sc_cap_contract_manager",
        "cost_manager": "smart_construction_core.group_sc_cap_cost_manager",
        "settlement_manager": "smart_construction_core.group_sc_cap_settlement_manager",
    }
    APPROVAL_SCOPE_LABELS = {
        "project_manager": "项目负责人",
        "material_manager": "物资审核人",
        "purchase_manager": "采购审核人",
        "finance_manager": "财务审核人",
        "contract_manager": "合同审核人",
        "cost_manager": "成控审核人",
        "settlement_manager": "结算审核人",
    }

    name = fields.Char(required=True, tracking=True, string="业务名称")
    code = fields.Char(required=True, index=True, tracking=True, string="规则编码")
    active = fields.Boolean(default=True, tracking=True, string="启用")
    sequence = fields.Integer(default=10, index=True, string="顺序")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True, string="公司")

    target_model = fields.Selection(
        selection=BUSINESS_MODEL_SELECTION,
        required=True,
        index=True,
        tracking=True,
        string="业务单据",
    )
    model_name = fields.Char(compute="_compute_model_name", store=True, index=True, string="技术模型")
    approval_required = fields.Boolean(default=True, tracking=True, string="需要审核")
    trigger = fields.Selection(
        [("submit", "提交时"), ("confirm", "确认时"), ("sign", "签署时"), ("manual", "手动触发")],
        default="submit",
        required=True,
        tracking=True,
        string="触发时点",
    )
    mode = fields.Selection(
        [("none", "无需审核"), ("single", "单级审核"), ("linear", "多级顺序审核")],
        default="single",
        required=True,
        tracking=True,
        string="审核方式",
    )
    runtime_state = fields.Selection(
        [
            ("tier_validation", "已接入分级审批"),
            ("document_state", "按单据状态按钮执行"),
            ("policy_only", "仅配置规则"),
        ],
        default="policy_only",
        required=True,
        tracking=True,
        string="执行状态",
    )
    manager_scope_key = fields.Selection(
        selection="_selection_approval_scope",
        compute="_compute_manager_scope_key",
        inverse="_inverse_manager_scope_key",
        store=True,
        readonly=False,
        tracking=True,
        string="默认审批岗位",
    )
    manager_group_id = fields.Many2one("res.groups", tracking=True, string="默认审批执行组")
    step_ids = fields.One2many("sc.approval.step", "policy_id", string="审核步骤")
    step_count = fields.Integer(compute="_compute_step_count", string="步骤数")
    note = fields.Text(string="业务说明")

    _sql_constraints = [
        ("sc_approval_policy_code_uniq", "unique(code)", "审批规则编码不能重复。"),
        ("sc_approval_policy_model_company_uniq", "unique(target_model, company_id)", "同一公司下业务单据不能重复配置审批规则。"),
    ]

    @api.depends("target_model")
    def _compute_model_name(self):
        for rec in self:
            rec.model_name = rec.target_model or False

    @api.depends("step_ids")
    def _compute_step_count(self):
        for rec in self:
            rec.step_count = len(rec.step_ids)

    @api.model
    def _selection_approval_scope(self):
        return [(key, self.APPROVAL_SCOPE_LABELS[key]) for key in self.APPROVAL_SCOPE_GROUP_XMLIDS]

    @api.model
    def _group_for_approval_scope(self, scope_key):
        xmlid = self.APPROVAL_SCOPE_GROUP_XMLIDS.get(scope_key)
        return self.env.ref(xmlid, raise_if_not_found=False) if xmlid else False

    @api.model
    def _approval_scope_for_group(self, group):
        if not group:
            return False
        xmlids = group.get_external_id()
        group_xmlid = xmlids.get(group.id)
        for scope_key, xmlid in self.APPROVAL_SCOPE_GROUP_XMLIDS.items():
            if group_xmlid == xmlid:
                return scope_key
        return False

    @api.depends("manager_group_id")
    def _compute_manager_scope_key(self):
        for rec in self:
            rec.manager_scope_key = rec._approval_scope_for_group(rec.manager_group_id)

    def _inverse_manager_scope_key(self):
        for rec in self:
            group = rec._group_for_approval_scope(rec.manager_scope_key)
            rec.manager_group_id = group.id if group else False

    @api.constrains("approval_required", "mode")
    def _check_approval_mode(self):
        for rec in self:
            if not rec.approval_required and rec.mode != "none":
                raise ValidationError(_("无需审核的业务，审核方式应选择“无需审核”。"))

    @api.model
    def get_active_policy(self, model_name, company=None):
        company = company or self.env.company
        domain = [
            ("active", "=", True),
            ("target_model", "=", model_name),
            "|",
            ("company_id", "=", company.id),
            ("company_id", "=", False),
        ]
        return self.search(domain, order="company_id desc, sequence, id", limit=1)

    @api.model
    def is_approval_required(self, model_name, company=None):
        policy = self.get_active_policy(model_name, company=company)
        return bool(policy and policy.approval_required and policy.mode != "none")

    @api.model
    def next_state_after_submit(self, model_name, submitted_state, approved_state, company=None):
        return submitted_state if self.is_approval_required(model_name, company=company) else approved_state

    def assert_user_can_approve(self):
        current_user = self.env.user
        for policy in self:
            if not policy.approval_required or policy.mode == "none":
                continue
            groups = policy.step_ids.filtered("active").mapped("approve_group_id")
            if not groups and policy.manager_group_id:
                groups = policy.manager_group_id
            if not groups:
                raise ValidationError(_("审批规则 %s 已启用审核，但未配置审批岗位。") % policy.display_name)
            allowed = False
            for group in groups:
                xmlid = group.get_external_id().get(group.id)
                if xmlid and current_user.has_group(xmlid):
                    allowed = True
                    break
            if not allowed:
                raise ValidationError(_("你不具备 %s 的审核能力。") % policy.display_name)

    def _tier_sync_supported(self):
        self.ensure_one()
        return self.target_model in {
            "project.material.plan",
            "payment.request",
            "sc.expense.claim",
            "sc.settlement.order",
            "purchase.order",
            "construction.contract",
            "sc.general.contract",
            "sc.legacy.purchase.contract.fact",
            "sc.receipt.income",
            "sc.payment.execution",
            "sc.invoice.registration",
            "sc.financing.loan",
            "sc.treasury.reconciliation",
            "sc.settlement.adjustment",
        }

    def _tier_server_actions(self):
        self.ensure_one()
        mapping = {
            "project.material.plan": (
                "smart_construction_core.server_action_material_plan_tier_approved",
                "smart_construction_core.server_action_material_plan_tier_rejected",
            ),
            "payment.request": (
                "smart_construction_core.server_action_payment_request_on_approved",
                "smart_construction_core.server_action_payment_request_on_rejected",
            ),
            "sc.expense.claim": (
                "smart_construction_core.server_action_expense_claim_on_approved",
                "smart_construction_core.server_action_expense_claim_on_rejected",
            ),
            "sc.settlement.order": (
                "smart_construction_core.server_action_settlement_order_on_approved",
                "smart_construction_core.server_action_settlement_order_on_rejected",
            ),
            "purchase.order": (
                "smart_construction_core.server_action_purchase_order_on_approved",
                "smart_construction_core.server_action_purchase_order_on_rejected",
            ),
            "construction.contract": (
                "smart_construction_core.server_action_construction_contract_on_approved",
                "smart_construction_core.server_action_construction_contract_on_rejected",
            ),
            "sc.general.contract": (
                "smart_construction_core.server_action_general_contract_on_approved",
                "smart_construction_core.server_action_general_contract_on_rejected",
            ),
            "sc.legacy.purchase.contract.fact": (
                "smart_construction_core.server_action_legacy_purchase_contract_on_approved",
                "smart_construction_core.server_action_legacy_purchase_contract_on_rejected",
            ),
            "sc.receipt.income": (
                "smart_construction_core.server_action_receipt_income_on_approved",
                "smart_construction_core.server_action_receipt_income_on_rejected",
            ),
            "sc.payment.execution": (
                "smart_construction_core.server_action_payment_execution_on_approved",
                "smart_construction_core.server_action_payment_execution_on_rejected",
            ),
            "sc.invoice.registration": (
                "smart_construction_core.server_action_invoice_registration_on_approved",
                "smart_construction_core.server_action_invoice_registration_on_rejected",
            ),
            "sc.financing.loan": (
                "smart_construction_core.server_action_financing_loan_on_approved",
                "smart_construction_core.server_action_financing_loan_on_rejected",
            ),
            "sc.treasury.reconciliation": (
                "smart_construction_core.server_action_treasury_reconciliation_on_approved",
                "smart_construction_core.server_action_treasury_reconciliation_on_rejected",
            ),
            "sc.settlement.adjustment": (
                "smart_construction_core.server_action_settlement_adjustment_on_approved",
                "smart_construction_core.server_action_settlement_adjustment_on_rejected",
            ),
        }
        approve_xmlid, reject_xmlid = mapping.get(self.target_model, (None, None))
        approve_action = self.env.ref(approve_xmlid, raise_if_not_found=False) if approve_xmlid else False
        reject_action = self.env.ref(reject_xmlid, raise_if_not_found=False) if reject_xmlid else False
        return approve_action, reject_action

    def _tier_definition_domain(self, step):
        domain = []
        amount_field_by_model = {
            "payment.request": "amount",
            "sc.expense.claim": "amount",
            "sc.settlement.order": "amount_total",
            "purchase.order": "amount_total",
            "construction.contract": "amount_total",
            "sc.general.contract": "amount_total",
            "sc.legacy.purchase.contract.fact": "total_amount",
            "sc.receipt.income": "amount",
            "sc.payment.execution": "paid_amount",
            "sc.invoice.registration": "amount_total",
            "sc.financing.loan": "amount",
            "sc.treasury.reconciliation": "confirmation_amount",
            "sc.settlement.adjustment": "amount",
        }
        amount_field = amount_field_by_model.get(self.target_model)
        if amount_field and step.amount_min:
            domain.append((amount_field, ">=", step.amount_min))
        if amount_field and step.amount_max:
            domain.append((amount_field, "<=", step.amount_max))
        return repr(domain)

    def _tier_definition_vals(self, step):
        self.ensure_one()
        model = self.env["ir.model"].sudo()._get(self.target_model)
        approve_action, reject_action = self._tier_server_actions()
        return {
            "name": "%s - %s" % (self.name, step.name),
            "model_id": model.id,
            "model": self.target_model,
            "company_id": self.company_id.id or self.env.company.id,
            "active": bool(self.active and self.approval_required and self.mode != "none" and step.active),
            "sequence": step.sequence or self.sequence or 10,
            "review_type": "group",
            "reviewer_group_id": step.approve_group_id.id,
            "definition_type": "domain",
            "definition_domain": self._tier_definition_domain(step),
            "approve_sequence": self.mode == "linear",
            "server_action_id": approve_action.id if approve_action else False,
            "rejected_server_action_id": reject_action.id if reject_action else False,
        }

    def sync_tier_definitions(self):
        TierDefinition = self.env["tier.definition"].sudo()
        synced = TierDefinition.browse()
        for policy in self.sudo():
            if not policy._tier_sync_supported():
                for step in policy.step_ids.filtered("tier_definition_id"):
                    step.tier_definition_id.sudo().write({"active": False})
                continue
            if policy.runtime_state != "tier_validation":
                policy.with_context(skip_tier_sync=True).write({"runtime_state": "tier_validation"})
            for step in policy.step_ids:
                if not step.approve_group_id:
                    continue
                vals = policy._tier_definition_vals(step)
                if step.tier_definition_id:
                    step.tier_definition_id.sudo().write(vals)
                    tier_def = step.tier_definition_id
                else:
                    tier_def = TierDefinition.create(vals)
                    step.sudo().with_context(skip_tier_sync=True).write({"tier_definition_id": tier_def.id})
                synced |= tier_def
        return synced

    @api.model
    def sync_all_tier_definitions(self):
        return self.search([]).sync_tier_definitions()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            scope_key = vals.get("manager_scope_key")
            if scope_key and not vals.get("manager_group_id"):
                group = self._group_for_approval_scope(scope_key)
                vals["manager_group_id"] = group.id if group else False
        records = super().create(vals_list)
        if not self.env.context.get("skip_tier_sync"):
            records.sync_tier_definitions()
        return records

    def write(self, vals):
        if "manager_scope_key" in vals and "manager_group_id" not in vals:
            group = self._group_for_approval_scope(vals.get("manager_scope_key"))
            vals = dict(vals, manager_group_id=group.id if group else False)
        res = super().write(vals)
        if not self.env.context.get("skip_tier_sync"):
            self.sync_tier_definitions()
        return res


class ScApprovalStep(models.Model):
    _name = "sc.approval.step"
    _description = "业务审批步骤"
    _order = "policy_id, sequence, id"

    policy_id = fields.Many2one("sc.approval.policy", required=True, ondelete="cascade", index=True, string="审批规则")
    active = fields.Boolean(default=True, string="启用")
    sequence = fields.Integer(default=10, index=True, string="顺序")
    name = fields.Char(required=True, string="步骤名称")
    approval_scope_key = fields.Selection(
        selection="_selection_approval_scope",
        compute="_compute_approval_scope_key",
        inverse="_inverse_approval_scope_key",
        store=True,
        readonly=False,
        required=True,
        string="审批岗位",
    )
    approve_group_id = fields.Many2one("res.groups", required=True, string="审批执行组")
    tier_definition_id = fields.Many2one("tier.definition", readonly=True, copy=False, string="OCA审批定义")
    amount_min = fields.Monetary(string="金额下限")
    amount_max = fields.Monetary(string="金额上限")
    currency_id = fields.Many2one(
        "res.currency",
        related="policy_id.company_id.currency_id",
        store=True,
        readonly=True,
        string="币种",
    )
    condition_note = fields.Char(string="适用条件")
    note = fields.Text(string="说明")

    @api.constrains("amount_min", "amount_max")
    def _check_amount_range(self):
        for rec in self:
            if rec.amount_min and rec.amount_max and rec.amount_min > rec.amount_max:
                raise ValidationError(_("审核步骤的金额下限不能大于金额上限。"))

    @api.model
    def _selection_approval_scope(self):
        return self.env["sc.approval.policy"]._selection_approval_scope()

    @api.model
    def _group_for_approval_scope(self, scope_key):
        return self.env["sc.approval.policy"]._group_for_approval_scope(scope_key)

    @api.model
    def _approval_scope_for_group(self, group):
        return self.env["sc.approval.policy"]._approval_scope_for_group(group)

    @api.depends("approve_group_id")
    def _compute_approval_scope_key(self):
        for rec in self:
            rec.approval_scope_key = rec._approval_scope_for_group(rec.approve_group_id)

    def _inverse_approval_scope_key(self):
        for rec in self:
            group = rec._group_for_approval_scope(rec.approval_scope_key)
            rec.approve_group_id = group.id if group else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            scope_key = vals.get("approval_scope_key")
            if scope_key and not vals.get("approve_group_id"):
                group = self._group_for_approval_scope(scope_key)
                vals["approve_group_id"] = group.id if group else False
        records = super().create(vals_list)
        if not self.env.context.get("skip_tier_sync"):
            records.mapped("policy_id").sync_tier_definitions()
        return records

    def write(self, vals):
        if "approval_scope_key" in vals and "approve_group_id" not in vals:
            group = self._group_for_approval_scope(vals.get("approval_scope_key"))
            vals = dict(vals, approve_group_id=group.id if group else False)
        res = super().write(vals)
        if not self.env.context.get("skip_tier_sync"):
            self.mapped("policy_id").sync_tier_definitions()
        return res

    def unlink(self):
        tier_definitions = self.mapped("tier_definition_id").sudo()
        res = super().unlink()
        if tier_definitions:
            tier_definitions.write({"active": False})
        return res
