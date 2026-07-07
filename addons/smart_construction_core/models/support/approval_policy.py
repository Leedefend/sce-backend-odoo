# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScApprovalPolicy(models.Model):
    _name = "sc.approval.policy"
    _description = "业务审批规则"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.delete.guard.mixin"]
    _order = "sequence, id"
    _runtime_authority = "base_tier_validation"
    LEGACY_FACT_MODELS = {"sc.legacy.purchase.contract.fact"}

    BUSINESS_MODEL_SELECTION = [
        ("project.project", "项目立项"),
        ("project.task", "项目任务"),
        ("construction.contract", "项目合同"),
        ("sc.general.contract", "一般合同（公司）"),
        ("sc.legacy.purchase.contract.fact", "历史采购/一般合同事实（只读）"),
        ("project.material.plan", "物资计划"),
        ("sc.material.outbound", "材料出库/损耗"),
        ("purchase.order", "采购订单"),
        ("sc.settlement.order", "结算单"),
        ("payment.request", "付款/收款申请"),
        ("sc.expense.claim", "费用/保证金"),
        ("sc.receipt.income", "收款登记"),
        ("sc.payment.execution", "付款执行"),
        ("sc.invoice.registration", "发票登记"),
        ("sc.financing.loan", "融资借款"),
        ("sc.self.funding.registration", "自筹垫付/退回"),
        ("sc.treasury.reconciliation", "资金对账"),
        ("sc.settlement.adjustment", "结算调整"),
    ]
    APPROVAL_SCOPE_GROUP_XMLIDS = {
        "executive": "smart_construction_core.group_sc_role_executive",
        "business_admin": "smart_construction_core.group_sc_role_business_admin",
        "operation_user": "smart_construction_core.group_sc_role_operation_user",
        "partner_manager": "smart_construction_core.group_sc_role_partner_manager",
        "project_user": "smart_construction_core.group_sc_role_project_user",
        "project_manager": "smart_construction_core.group_sc_cap_project_manager",
        "material_manager": "smart_construction_core.group_sc_cap_material_manager",
        "purchase_manager": "smart_construction_core.group_sc_cap_purchase_manager",
        "finance_manager": "smart_construction_core.group_sc_cap_finance_manager",
        "finance_user": "smart_construction_core.group_sc_role_finance_user",
        "temporary_finance": "smart_construction_core.group_sc_role_temporary_finance",
        "contract_manager": "smart_construction_core.group_sc_cap_contract_manager",
        "contract_user": "smart_construction_core.group_sc_role_contract_admin",
        "cost_manager": "smart_construction_core.group_sc_cap_cost_manager",
        "cost_user": "smart_construction_core.group_sc_role_cost_user",
        "settlement_manager": "smart_construction_core.group_sc_cap_settlement_manager",
        "settlement_user": "smart_construction_core.group_sc_role_settlement_user",
    }
    APPROVAL_SCOPE_LABELS = {
        "executive": "管理层/总经理终审",
        "business_admin": "业务配置管理员",
        "operation_user": "经营审核人",
        "partner_manager": "客商资料审核人",
        "project_user": "项目部/工程部经办",
        "project_manager": "项目负责人",
        "material_manager": "物资审核人",
        "purchase_manager": "采购审核人",
        "finance_user": "财务经办人",
        "finance_manager": "财务审核人",
        "temporary_finance": "受限财务",
        "contract_user": "合同经办人",
        "contract_manager": "合同审核人",
        "cost_user": "成本经办人",
        "cost_manager": "成控审核人",
        "settlement_user": "结算经办人",
        "settlement_manager": "结算审核人",
    }
    USER_VISIBLE_TEMPLATE_MARKER = "[user_visible_approval_template_v1]"
    USER_VISIBLE_APPROVAL_TEMPLATES = {
        "project_contract_approval": {
            "mode": "linear",
            "manager_scope_key": "contract_manager",
            "note": "施工/收入合同默认按用户可见业务流程审核：合同经办、经营审核、项目负责人、成控审核、管理层终审。业务配置管理员可按金额或管理要求调整步骤。",
            "steps": [
                ("合同经办确认", "contract_user"),
                ("经营部审核", "operation_user"),
                ("项目负责人审核", "project_manager"),
                ("成控审核", "cost_manager"),
                ("管理层/总经理终审", "executive"),
            ],
        },
        "general_contract_approval": {
            "mode": "linear",
            "manager_scope_key": "contract_manager",
            "note": "一般合同默认按合同经办、经营审核、财务审核、管理层终审处理。",
            "steps": [
                ("合同经办确认", "contract_user"),
                ("经营部审核", "operation_user"),
                ("财务审核", "finance_manager"),
                ("管理层/总经理终审", "executive"),
            ],
        },
        "purchase_order_approval": {
            "mode": "linear",
            "manager_scope_key": "purchase_manager",
            "note": "采购订单默认按项目经办、项目负责人、采购审核、财务审核处理。",
            "steps": [
                ("项目部/工程部经办确认", "project_user"),
                ("项目负责人审核", "project_manager"),
                ("采购审核", "purchase_manager"),
                ("财务审核", "finance_manager"),
            ],
        },
        "settlement_order_approval": {
            "mode": "linear",
            "manager_scope_key": "settlement_manager",
            "note": "结算单默认按结算经办、项目负责人、成控审核、结算审核处理。",
            "steps": [
                ("结算经办确认", "settlement_user"),
                ("项目负责人审核", "project_manager"),
                ("成控审核", "cost_manager"),
                ("结算审核", "settlement_manager"),
            ],
        },
        "payment_request_approval": {
            "mode": "linear",
            "manager_scope_key": "finance_manager",
            "note": "付款/收款申请默认按财务经办、项目负责人、财务审核、管理层终审处理。",
            "steps": [
                ("财务经办确认", "finance_user"),
                ("项目负责人审核", "project_manager"),
                ("财务审核", "finance_manager"),
                ("管理层/总经理终审", "executive"),
            ],
        },
        "receipt_income_optional_approval": {
            "mode": "none",
            "manager_scope_key": "finance_manager",
            "note": "收款登记默认不强制审核；启用后建议按财务经办、经营审核、财务审核处理。",
            "steps": [
                ("财务经办确认", "finance_user"),
                ("经营部审核", "operation_user"),
                ("财务审核", "finance_manager"),
            ],
        },
        "settlement_adjustment_optional_approval": {
            "mode": "none",
            "manager_scope_key": "settlement_manager",
            "note": "结算调整默认不强制审核；启用后建议按结算经办、成控审核、结算审核处理。",
            "steps": [
                ("结算经办确认", "settlement_user"),
                ("成控审核", "cost_manager"),
                ("结算审核", "settlement_manager"),
            ],
        },
    }

    name = fields.Char(required=True, tracking=True, string="业务名称")
    code = fields.Char(required=True, index=True, tracking=True, string="规则编码")
    active = fields.Boolean(default=True, tracking=True, string="规则有效")
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
    approval_required = fields.Boolean(default=True, tracking=True, string="启用审批")
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

    @api.model
    def _normalize_approval_toggle_vals(self, vals, current_mode=None):
        normalized = dict(vals)
        if "approval_required" in normalized:
            approval_required = bool(normalized.get("approval_required"))
            if not approval_required:
                normalized["mode"] = "none"
            elif normalized.get("mode") in (None, False, "none") and current_mode in (None, False, "none"):
                normalized["mode"] = "single"
        elif "mode" in normalized:
            if normalized.get("mode") == "none":
                normalized["approval_required"] = False
            elif normalized.get("mode") in ("single", "linear"):
                normalized["approval_required"] = True
        return normalized

    @api.onchange("approval_required")
    def _onchange_approval_required(self):
        for rec in self:
            if not rec.approval_required:
                rec.mode = "none"
            elif rec.mode == "none":
                rec.mode = "single"

    @api.onchange("mode")
    def _onchange_mode(self):
        for rec in self:
            if rec.mode == "none":
                rec.approval_required = False
            elif rec.mode in ("single", "linear"):
                rec.approval_required = True

    @api.constrains("approval_required", "mode")
    def _check_approval_mode(self):
        for rec in self:
            if not rec.approval_required and rec.mode != "none":
                raise ValidationError(_("无需审核的业务，审核方式应选择“无需审核”。"))
            if rec.target_model in self.LEGACY_FACT_MODELS and rec.active and rec.approval_required:
                raise ValidationError(_("历史事实模型只作为只读承载，不再作为业务审批对象。"))

    @api.model
    def get_active_policy(self, model_name, company=None):
        if model_name in self.LEGACY_FACT_MODELS:
            return self.browse()
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
            "sc.material.outbound",
            "payment.request",
            "sc.expense.claim",
            "sc.settlement.order",
            "purchase.order",
            "construction.contract",
            "sc.general.contract",
            "sc.receipt.income",
            "sc.payment.execution",
            "sc.invoice.registration",
            "sc.financing.loan",
            "sc.self.funding.registration",
            "sc.treasury.reconciliation",
            "sc.settlement.adjustment",
        }

    def runtime_authority(self):
        """审批运行时以 base_tier_validation 为准，本模型只做业务配置入口和同步器。"""
        return self._runtime_authority

    def _tier_server_actions(self):
        self.ensure_one()
        mapping = {
            "project.material.plan": (
                "smart_construction_core.server_action_material_plan_tier_approved",
                "smart_construction_core.server_action_material_plan_tier_rejected",
            ),
            "sc.material.outbound": (
                "smart_construction_core.server_action_material_outbound_on_approved",
                "smart_construction_core.server_action_material_outbound_on_rejected",
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
            "sc.self.funding.registration": (
                "smart_construction_core.server_action_self_funding_registration_on_approved",
                "smart_construction_core.server_action_self_funding_registration_on_rejected",
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
            "sc.material.outbound": "amount_total",
            "sc.settlement.order": "amount_total",
            "purchase.order": "amount_total",
            "construction.contract": "amount_total",
            "sc.general.contract": "amount_total",
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

    @api.model
    def apply_user_visible_approval_templates(self):
        """Align default approval templates with user-visible business roles."""
        Step = self.env["sc.approval.step"].sudo()
        changed = False
        for code, template in self.USER_VISIBLE_APPROVAL_TEMPLATES.items():
            policy = self.sudo().search([("code", "=", code)], limit=1)
            if not policy:
                continue
            current_scope_keys = policy.step_ids.sorted("sequence").mapped("approval_scope_key")
            template_scope_keys = [scope_key for _name, scope_key in template["steps"]]
            already_template = current_scope_keys == template_scope_keys
            managed_template = self.USER_VISIBLE_TEMPLATE_MARKER in (policy.note or "")
            user_customized = (
                not managed_template
                and len(current_scope_keys) > 1
                and not already_template
            )
            if user_customized:
                continue
            manager_group = self._group_for_approval_scope(template["manager_scope_key"])
            policy_vals = {
                "approval_required": template["mode"] != "none",
                "mode": template["mode"],
                "manager_scope_key": template["manager_scope_key"],
                "manager_group_id": manager_group.id if manager_group else False,
                "note": "%s %s" % (self.USER_VISIBLE_TEMPLATE_MARKER, template["note"]),
            }
            policy.with_context(skip_tier_sync=True).write(policy_vals)

            if not already_template:
                policy.step_ids.with_context(skip_tier_sync=True, skip_delete_guard=True).unlink()
                sequence = 10
                for name, scope_key in template["steps"]:
                    group = self._group_for_approval_scope(scope_key)
                    Step.with_context(skip_tier_sync=True).create(
                        {
                            "policy_id": policy.id,
                            "sequence": sequence,
                            "name": name,
                            "approval_scope_key": scope_key,
                            "approve_group_id": group.id if group else False,
                        }
                    )
                    sequence += 10
            changed = True
        if changed:
            self.search([("code", "in", list(self.USER_VISIBLE_APPROVAL_TEMPLATES))]).sync_tier_definitions()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update(self._normalize_approval_toggle_vals(vals))
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
        if vals.get("approval_required") is True and "mode" not in vals:
            records_with_none_mode = self.filtered(lambda rec: rec.mode == "none")
            records_with_active_mode = self - records_with_none_mode
            res = True
            if records_with_none_mode:
                none_mode_vals = records_with_none_mode._normalize_approval_toggle_vals(vals, current_mode="none")
                res = super(ScApprovalPolicy, records_with_none_mode).write(none_mode_vals) and res
            if records_with_active_mode:
                active_mode_vals = records_with_active_mode._normalize_approval_toggle_vals(vals, current_mode="single")
                res = super(ScApprovalPolicy, records_with_active_mode).write(active_mode_vals) and res
            if not self.env.context.get("skip_tier_sync"):
                self.sync_tier_definitions()
            return res
        vals = self._normalize_approval_toggle_vals(vals, current_mode=self[:1].mode if len(self) == 1 else None)
        res = super().write(vals)
        if not self.env.context.get("skip_tier_sync"):
            self.sync_tier_definitions()
        return res

    def unlink(self):
        active_policies = self.filtered("active")
        if active_policies:
            raise UserError("请先停用审批规则后再删除。")
        self._sc_raise_delete_blockers(action_label="删除审批规则")
        return super().unlink()


class ScApprovalStep(models.Model):
    _name = "sc.approval.step"
    _description = "业务审批步骤"
    _inherit = ["sc.delete.guard.mixin"]
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
        if self.env.context.get("skip_delete_guard"):
            tier_definitions = self.mapped("tier_definition_id").sudo()
            res = super().unlink()
            if tier_definitions:
                tier_definitions.write({"active": False})
            return res
        active_steps = self.filtered("active")
        if active_steps:
            raise UserError("请先停用审批步骤后再删除。")
        tier_definitions = self.mapped("tier_definition_id").sudo()
        res = super().unlink()
        if tier_definitions:
            tier_definitions.write({"active": False})
        return res
