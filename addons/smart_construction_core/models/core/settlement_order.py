# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..support import operating_metrics as opm
from ..support.state_guard import raise_guard
from ..support.state_machine import ScStateMachine


class ScSettlementOrder(models.Model):
    _name = "sc.settlement.order"
    _description = "结算单"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "id desc"
    _rec_names_search = [
        "name",
        "title",
        "project_id.name",
        "partner_id.name",
        "settlement_unit_id.name",
        "legacy_counterparty_name",
        "contract_id.subject",
        "contract_id.legacy_contract_no",
        "contract_id.legacy_document_no",
        "legacy_contract_no",
        "legacy_fact_model",
        "legacy_fact_type",
    ]

    name = fields.Char(string="结算单号", required=True, default="新建", copy=False)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
        default=lambda self: self.env.context.get("default_contract_id"),
    )
    partner_id = fields.Many2one("res.partner", string="往来单位")
    legacy_counterparty_name = fields.Char(string="历史往来单位文本", index=True)
    title = fields.Char(string="标题", index=True)
    document_date = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    settlement_unit_id = fields.Many2one("res.partner", string="结算单位", index=True)
    employer_name = fields.Char(string="发包人", compute="_compute_party_names", store=True)
    contractor_name = fields.Char(string="承包人", compute="_compute_party_names", store=True)
    settlement_type = fields.Selection(
        [("out", "支出结算"), ("in", "收入结算")],
        string="收支类型",
        default="out",
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.settlement.order')]",
    )
    settlement_flow_label = fields.Char(string="办理事项", compute="_compute_settlement_flow_label")
    expense_contract_category_id = fields.Many2one(
        "sc.dictionary",
        string="合同分类",
        related="contract_id.expense_contract_category_id",
        store=True,
        readonly=True,
        index=True,
    )
    settlement_category_id = fields.Many2one(
        "sc.dictionary",
        string="结算分类",
        domain=[("type", "=", "expense_contract_category")],
        index=True,
    )
    legacy_settlement_category = fields.Char(string="迁移结算分类", index=True)
    settlement_category_display = fields.Char(
        string="结算分类显示",
        compute="_compute_settlement_category_display",
        store=True,
        index=True,
    )
    settlement_stage = fields.Selection(
        [
            ("plan", "结算计划"),
            ("declared", "结算申报"),
            ("preliminary", "工程初审"),
            ("first_review", "一审"),
            ("second_review", "二审"),
            ("final", "结算定案"),
            ("spot_check", "结算抽查"),
        ],
        string="结算阶段编码",
        default="declared",
        index=True,
    )
    settlement_stage_id = fields.Many2one(
        "sc.dictionary",
        string="结算阶段",
        domain=[("type", "=", "settlement_stage")],
        index=True,
    )
    date_settlement = fields.Date(string="结算日期", default=fields.Date.context_today)
    planned_settlement_date = fields.Date(string="计划结算日期", index=True)
    declared_date = fields.Date(string="申报日期", index=True)
    final_approved_date = fields.Date(string="定案日期", index=True)
    approved_date = fields.Date(string="审定日期", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(
        string="金额合计",
        currency_field="currency_id",
        compute="_compute_amount_total",
        store=True,
    )
    settlement_amount = fields.Monetary(string="结算金额", currency_field="currency_id", index=True)
    contract_subject = fields.Char(
        string="合同名称",
        related="contract_id.subject",
        store=True,
        readonly=True,
    )
    contract_total_amount = fields.Monetary(
        string="合同总额",
        currency_field="currency_id",
        compute="_compute_contract_snapshot",
        store=True,
        compute_sudo=True,
    )
    submitted_amount = fields.Monetary(string="送审金额", currency_field="currency_id")
    approved_amount = fields.Monetary(string="审定金额", currency_field="currency_id")
    requested_fund_amount = fields.Monetary(string="申请资金金额", currency_field="currency_id")
    legacy_document_state = fields.Char(string="原始单据状态", index=True)
    legacy_contract_no = fields.Char(string="合同编号", index=True)
    settlement_period_start = fields.Date(string="起始结算日期", index=True)
    settlement_period_end = fields.Date(string="终止结算日期", index=True)
    legacy_payment_state = fields.Char(string="付款状态", index=True)
    legacy_paid_amount = fields.Monetary(string="原始已付款金额", currency_field="currency_id")
    legacy_unpaid_amount = fields.Monetary(string="原始未付款金额", currency_field="currency_id")
    legacy_payment_request_state = fields.Char(string="支付申请状态", index=True)
    legacy_unrequested_amount = fields.Monetary(string="原始未申请金额", currency_field="currency_id")
    engineering_address = fields.Char(
        string="工程地址",
        compute="_compute_contract_snapshot",
        store=True,
        compute_sudo=True,
    )
    deduction_amount = fields.Monetary(
        string="扣款金额",
        currency_field="currency_id",
        compute="_compute_adjustment_breakdown",
        compute_sudo=True,
    )
    unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
    )
    settlement_description = fields.Text(string="结算说明")
    entry_user_id = fields.Many2one("res.users", string="录入人", default=lambda self: self.env.user, index=True)
    entry_data = fields.Char(string="录入数据")
    note = fields.Text(string="备注")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    line_ids = fields.One2many(
        "sc.settlement.order.line",
        "settlement_id",
        string="结算行",
    )
    payment_request_ids = fields.One2many(
        "payment.request",
        "settlement_id",
        string="关联付款申请",
        readonly=True,
    )
    payment_request_line_ids = fields.One2many(
        "payment.request.line",
        "settlement_id",
        string="付款申请明细",
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
    )
    remaining_amount = fields.Monetary(
        string="待付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
    )
    amount_paid = fields.Monetary(
        string="已付累计",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
        help="按付款申请的已付口径汇总的金额（状态见 _get_paid_payment_states）。",
    )
    amount_payable = fields.Monetary(
        string="可付余额",
        currency_field="currency_id",
        compute="_compute_paid_amounts",
        store=True,
        compute_sudo=True,
        help="可付余额 = 结算金额 - 已付累计；为负时代表存在超付风险。",
    )
    purchase_order_ids = fields.Many2many(
        comodel_name="purchase.order",
        relation="sc_settlement_order_purchase_rel",
        column1="settlement_id",
        column2="purchase_id",
        string="采购订单",
        help="与本结算单关联的采购订单，用于三单匹配。",
    )
    invoice_ref = fields.Char(string="发票号/票据号")
    invoice_amount = fields.Monetary(string="发票金额", currency_field="currency_id")
    invoice_date = fields.Date(string="发票日期")
    reject_reason = fields.Char(string="驳回原因", readonly=True, copy=False)
    attachment_ids = fields.Many2many("ir.attachment", "sc_settlement_order_attachment_rel", "settlement_id", "attachment_id", string="结算附件")
    attachment_count = fields.Integer(string="附件数", compute="_compute_attachment_count")

    compliance_contract_ok = fields.Boolean(string="合同一致", compute="_compute_compliance_summary", store=False)
    compliance_state = fields.Selection(
        [("ok", "通过"), ("warn", "警告"), ("block", "阻断")],
        string="匹配状态",
        compute="_compute_compliance_summary",
        store=False,
    )
    compliance_message = fields.Text(string="匹配提示", compute="_compute_compliance_summary", store=False)

    @api.depends(
        "line_ids.amount",
        "payment_request_ids",
        "payment_request_ids.state",
        "payment_request_ids.amount",
        "payment_request_line_ids",
        "payment_request_line_ids.current_pay_amount",
        "payment_request_line_ids.request_id.state",
        "payment_request_line_ids.request_id.settlement_id",
    )
    def _compute_paid_amounts(self):
        """Phase7-1: 结算单的已付/可付口径，统一由 operating_metrics 提供。"""
        paid_map = opm.settlement_paid_map(self.env, self.ids)
        for order in self:
            total = order.amount_total or 0.0
            paid = paid_map.get(order.id, 0.0)
            remaining = total - paid
            order.paid_amount = paid
            order.remaining_amount = remaining
            order.amount_paid = paid
            order.amount_payable = remaining
            order.unpaid_amount = remaining

    state = fields.Selection(
        ScStateMachine.selection(ScStateMachine.SETTLEMENT_ORDER),
        string="状态",
        default="draft",
    )

    _sql_constraints = [
        ("legacy_settlement_order_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用结算单已迁移为专业结算单。"),
    ]

    @api.constrains("partner_id", "legacy_fact_model")
    def _check_partner_required_for_manual_records(self):
        for order in self:
            if not order.partner_id and not order.legacy_fact_model:
                raise ValidationError(_("结算单必须选择往来单位。"))

    @api.constrains("project_id", "contract_id", "settlement_type")
    def _check_contract_header_consistency(self):
        for order in self:
            contract = order.contract_id
            if not contract:
                continue
            if order.project_id and contract.project_id and contract.project_id != order.project_id:
                raise ValidationError(_("合同所属项目与结算单项目不一致。"))
            expected_contract_type = order._contract_type_for_settlement_type(order.settlement_type)
            if expected_contract_type and contract.type and contract.type != expected_contract_type:
                raise ValidationError(_("合同类型与收支类型不一致。"))

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped("amount"))

    @api.depends(
        "name",
        "title",
        "settlement_flow_label",
        "settlement_type",
        "amount_payable",
        "remaining_amount",
        "settlement_amount",
        "amount_total",
        "currency_id.symbol",
        "project_id.display_name",
        "partner_id.display_name",
        "settlement_unit_id.display_name",
        "legacy_counterparty_name",
        "contract_id.subject",
        "contract_id.legacy_contract_no",
        "contract_id.legacy_document_no",
    )
    def _compute_display_name(self):
        for order in self:
            flow = (
                order.settlement_flow_label
                or (_("收入合同结算") if order.settlement_type == "in" else _("支出合同结算"))
            )
            if flow and _("结算") not in flow:
                flow = _("%s结算") % flow
            project_name = order.project_id.display_name or ""
            partner_name = (
                order.settlement_unit_id.display_name
                or order.partner_id.display_name
                or order.legacy_counterparty_name
                or ""
            )
            contract_label = ""
            if order.contract_id:
                contract_label = (
                    order.contract_id.subject
                    or order.contract_id.legacy_contract_no
                    or order.contract_id.legacy_document_no
                    or ""
                )
            amount_text = order._display_amount_label()
            document_no = (order.name or "").strip()
            parts = [
                part
                for part in (flow, project_name, partner_name, contract_label, amount_text, document_no)
                if part
            ]
            order.display_name = " / ".join(parts) or document_no or _("结算单")

    def _display_amount_label(self):
        self.ensure_one()
        amount = (
            self.amount_payable
            or self.remaining_amount
            or self.settlement_amount
            or self.amount_total
            or 0.0
        )
        if not amount:
            return ""
        symbol = (self.currency_id.symbol or "").strip()
        return "%s%s" % (symbol, "{:,.2f}".format(amount))

    @api.depends("settlement_category_id.name", "expense_contract_category_id.name")
    def _compute_settlement_category_display(self):
        for order in self:
            category = order.settlement_category_id or order.expense_contract_category_id
            order.settlement_category_display = category.name or ""

    @api.depends("settlement_type", "settlement_category_id.name", "expense_contract_category_id.name", "legacy_settlement_category")
    def _compute_settlement_flow_label(self):
        for order in self:
            category = order.settlement_category_display or order.legacy_settlement_category
            if category:
                order.settlement_flow_label = category
            elif order.settlement_type == "in":
                order.settlement_flow_label = _("收入合同结算")
            else:
                order.settlement_flow_label = _("支出合同结算")

    @api.depends("settlement_type", "partner_id", "legacy_counterparty_name", "company_id.partner_id")
    def _compute_party_names(self):
        for order in self:
            company_partner = order.company_id.partner_id
            company_name = company_partner.display_name if company_partner else (order.company_id.name or "")
            partner_name = order.partner_id.display_name or order.legacy_counterparty_name or ""
            if order.settlement_type == "in":
                order.employer_name = partner_name
                order.contractor_name = company_name
            else:
                order.employer_name = company_name
                order.contractor_name = partner_name

    @api.depends("contract_id.amount_final", "contract_id.amount_total", "contract_id.engineering_address", "project_id")
    def _compute_contract_snapshot(self):
        for order in self:
            contract = order.contract_id
            order.contract_total_amount = contract.amount_final or contract.amount_total or 0.0
            order.engineering_address = (
                contract.engineering_address
                or getattr(order.project_id, "sc_address", False)
                or getattr(order.project_id, "location", False)
                or ""
            )

    @api.depends("adjustment_ids.adjustment_type", "adjustment_ids.amount", "adjustment_ids.state")
    def _compute_adjustment_breakdown(self):
        for order in self:
            order.deduction_amount = sum(
                order.adjustment_ids.filtered(
                    lambda adjustment: adjustment.adjustment_type == "deduction"
                    and adjustment.state in ("confirmed", "legacy_confirmed")
                ).mapped("amount")
            )

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for order in self:
            actual_count = len(order.attachment_ids)
            if actual_count:
                order.attachment_count = actual_count
                continue
            attachment_text = (order._settlement_attachment_ref_value() or "").strip()
            match = re.search(r"附件\((\d+)\)", attachment_text)
            order.attachment_count = int(match.group(1)) if match else int(bool(attachment_text))

    def _settlement_attachment_ref_value(self):
        return ""

    @api.onchange("settlement_stage_id")
    def _onchange_settlement_stage_id(self):
        for order in self:
            if order.settlement_stage_id and order.settlement_stage_id.code:
                order.settlement_stage = order.settlement_stage_id.code

    @api.constrains("purchase_order_ids", "partner_id")
    def _check_po_vendor_consistency(self):
        for rec in self:
            if not rec.purchase_order_ids or not rec.partner_id:
                continue
            wrong = rec.purchase_order_ids.filtered(lambda po: po.partner_id.id != rec.partner_id.id)
            if wrong:
                raise ValidationError(
                    _("采购订单供应商与结算单往来单位不一致：%s")
                    % ", ".join(wrong.mapped("name")[:10])
                )

    @api.depends(
        "contract_id",
        "payment_request_ids.contract_id",
        "purchase_order_ids",
        "purchase_order_ids.state",
        "purchase_order_ids.partner_id",
        "partner_id",
        "invoice_ref",
        "invoice_amount",
        "invoice_date",
        "amount_total",
    )
    def _compute_compliance_summary(self):
        for rec in self:
            missing = []
            mismatch = []
            warnings = []

            # 合同一致性
            if rec.contract_id and rec.payment_request_ids:
                wrong = rec.payment_request_ids.filtered(
                    lambda r: r.contract_id and r.contract_id.id != rec.contract_id.id
                )
                if wrong:
                    mismatch.append(_("付款申请合同与结算单不一致"))

            # 采购来源
            if not rec.purchase_order_ids:
                missing.append(_("采购订单"))
            else:
                bad_state = rec.purchase_order_ids.filtered(lambda po: po.state not in ("purchase", "done"))
                if bad_state:
                    mismatch.append(_("采购订单状态不合规"))
                # 供应商不一致由 constrains 硬拦，这里不重复

            # 发票信息软提示
            if not rec.invoice_ref:
                warnings.append(_("缺少发票信息"))
            else:
                if rec.invoice_amount and rec.amount_total and rec.invoice_amount < rec.amount_total:
                    warnings.append(_("发票金额小于结算金额"))

            # 汇总状态：block > warn > ok
            if mismatch:
                rec.compliance_state = "block"
            elif missing or warnings:
                rec.compliance_state = "warn"
            else:
                rec.compliance_state = "ok"

            lines = []
            if mismatch:
                lines.append(_("【阻断】") + "；".join(mismatch))
            if missing:
                lines.append(_("【缺失】") + "；".join(missing))
            if warnings:
                lines.append(_("【提示】") + "；".join(warnings))
            rec.compliance_message = "\n".join(lines) if lines else _("匹配正常")
            rec.compliance_contract_ok = not bool(mismatch)

    def _get_bool_param(self, key, default=True):
        val = self.env["ir.config_parameter"].sudo().get_param(key)
        if val is None:
            return default
        return str(val).strip().lower() in ("1", "true", "yes", "y", "on")

    def _check_contract_consistency_or_raise(self, strict=True):
        """
        strict=True 用于 approve 时强制校验；strict=False 受参数控制。
        """
        self.ensure_one()
        hard_block = self._get_bool_param("sc.settlement.check_contract.hard_block", True)
        if not hard_block and not strict:
            return
        if self.contract_id and self.payment_request_ids:
            wrong = self.payment_request_ids.filtered(
                lambda r: r.contract_id and r.contract_id.id != self.contract_id.id
            )
            if wrong:
                raise UserError(
                    _("合同不一致，禁止继续操作。请检查结算单合同与关联付款申请合同。")
                )

    def _check_purchase_orders_or_raise(self, strict=True):
        """
        strict=True 用于 approve 时强制校验；strict=False 受参数控制。
        """
        self.ensure_one()
        hard_block = self._get_bool_param("sc.settlement.check_purchase.hard_block", True)
        if not hard_block and not strict:
            return

        if not self.purchase_order_ids:
            if strict:
                raise UserError(_("缺少采购订单来源，无法批准结算单。"))
            return

        bad_state = self.purchase_order_ids.filtered(lambda po: po.state not in ("purchase", "done"))
        if bad_state:
            raise UserError(
                _("采购订单状态不合规（需为 已采购/完成），问题订单：%s")
                % ", ".join(bad_state.mapped("name")[:10])
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
            try:
                project_id = int(project_id) if project_id else False
            except (TypeError, ValueError):
                project_id = False
            if project_id:
                vals.setdefault("project_id", project_id)
            if vals.get("name", "新建") in (False, "新建"):
                seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
                vals["name"] = seq or _("Settlement")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("提交结算单"),
                    reasons=[_("只有草稿状态的结算单可以提交")],
                )
            rec._check_business_anchor_or_raise()
            rec._check_line_contracts_or_raise()
            rec._check_contract_consistency_or_raise(strict=False)
            rec._check_purchase_orders_or_raise(strict=False)
        self.env["sc.data.validator"].validate_or_raise(
            scope={"res_model": self._name, "res_ids": self.ids}
        )
        policy = self.env["sc.approval.policy"]
        for rec in self:
            if policy.is_approval_required(rec._name, company=rec.company_id):
                rec.write({"state": "submit", "reject_reason": False})
                company = rec.company_id or self.env.company
                rec.with_company(company).with_context(
                    allowed_company_ids=[company.id],
                ).request_validation()
            else:
                rec.write({"state": "approve", "reject_reason": False})

    def action_approve(self):
        policy_model = self.env["sc.approval.policy"]
        for rec in self:
            if rec.state not in ("draft", "submit"):
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("审批结算单"),
                    reasons=[_("只有草稿或已提交状态的结算单可以审批")],
                )
            rec._check_business_anchor_or_raise()
            rec._check_line_contracts_or_raise()
            rec._check_contract_consistency_or_raise(strict=True)
            rec._check_purchase_orders_or_raise(strict=True)
            if policy_model.is_approval_required(rec._name, company=rec.company_id):
                if rec.validation_status != "validated":
                    raise_guard(
                        "SETTLEMENT_TIER_INCOMPLETE",
                        f"结算单[{rec.display_name}]",
                        _("审批结算单"),
                        reasons=[_("统一审批流程尚未完成")],
                    )
            else:
                policy = policy_model.get_active_policy(rec._name, company=rec.company_id)
                if policy:
                    policy.assert_user_can_approve()
        self.env["sc.data.validator"].validate_or_raise(
            scope={"res_model": self._name, "res_ids": self.ids}
        )
        self.write({"state": "approve"})

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submit"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("OCA审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("审批通过结算单"),
                    reasons=[_("只有已提交状态的结算单可以执行审批通过回调")],
                )
            rec._check_business_anchor_or_raise()
            rec._check_line_contracts_or_raise()
            rec._check_contract_consistency_or_raise(strict=True)
            rec._check_purchase_orders_or_raise(strict=True)
            if rec.validation_status != "validated":
                raise_guard(
                    "SETTLEMENT_TIER_INCOMPLETE",
                    f"结算单[{rec.display_name}]",
                    _("审批结算单"),
                    reasons=[_("统一审批流程尚未完成")],
                )
            rec.write({"state": "approve", "reject_reason": False})

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("驳回结算单"),
                    reasons=[_("只有已提交状态的结算单可以执行审批驳回回调")],
                )
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or rec._get_tier_reject_reason(),
                }
            )

    def action_done(self):
        for rec in self:
            if rec.state != "approve":
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("完成结算单"),
                    reasons=[_("只有已批准状态的结算单可以完成")],
                )
            rec._check_business_anchor_or_raise()
            rec.write({"state": "done"})

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "submit", "approve"):
                raise_guard(
                    "SETTLEMENT_INVALID_TRANSITION",
                    f"结算单[{rec.display_name}]",
                    _("作废结算单"),
                    reasons=[_("只有草稿、已提交或已批准状态的结算单可以作废")],
                )
            rec._check_payments_before_cancel()
            rec.write({"state": "cancel"})

    def _check_business_anchor_or_raise(self):
        for rec in self:
            if not rec.project_id:
                raise_guard(
                    "SETTLEMENT_MISSING_PROJECT",
                    f"结算单[{rec.display_name}]",
                    _("校验结算单"),
                    reasons=[_("结算单必须关联项目")],
                )
            if not rec.partner_id and not rec.legacy_fact_model:
                raise_guard(
                    "SETTLEMENT_MISSING_PARTNER",
                    f"结算单[{rec.display_name}]",
                    _("校验结算单"),
                    reasons=[_("结算单必须选择往来单位")],
                )
            if not rec.line_ids:
                raise_guard(
                    "SETTLEMENT_MISSING_LINES",
                    f"结算单[{rec.display_name}]",
                    _("校验结算单"),
                    reasons=[_("结算单必须维护结算明细")],
                )
            if rec.amount_total <= 0:
                raise_guard(
                    "SETTLEMENT_INVALID_AMOUNT",
                    f"结算单[{rec.display_name}]",
                    _("校验结算单"),
                    reasons=[_("结算金额必须大于0")],
                )
            for line in rec.line_ids:
                if line.qty <= 0:
                    raise_guard(
                        "SETTLEMENT_INVALID_LINE_QTY",
                        f"结算单[{rec.display_name}]",
                        _("校验结算明细"),
                        reasons=[_("结算行数量必须大于0")],
                    )
                if line.price_unit < 0:
                    raise_guard(
                        "SETTLEMENT_INVALID_LINE_PRICE",
                        f"结算单[{rec.display_name}]",
                        _("校验结算明细"),
                        reasons=[_("结算行单价不能为负数")],
                    )

    def _check_payments_before_cancel(self):
        Payment = self.env["payment.request"]
        for rec in self:
            count = Payment.search_count(
                [
                    ("settlement_id", "=", rec.id),
                    ("state", "in", ["approve", "approved", "done"]),
                ]
            )
            if count:
                raise_guard(
                    "P0_SETTLEMENT_CANCEL_BLOCKED",
                    f"结算单[{rec.display_name}]",
                    _("作废结算单"),
                    reasons=[_("已关联付款申请：%s 条") % count],
                    hints=[_("请先取消/完成关联付款申请后再作废结算单")],
                )

    def write(self, vals):
        if vals.get("state") == "cancel":
            self._check_payments_before_cancel()
        return super().write(vals)

    # ------------------------------------------------------------------
    # 合同联动：选合同后自动带出项目/公司/币种/往来单位/收支类型
    # ------------------------------------------------------------------
    def _settlement_type_from_context(self):
        code = self.env.context.get("current_business_category_code") or self.env.context.get("default_business_category_code")
        if code == "settlement.income":
            return "in"
        if code == "settlement.expense":
            return "out"
        settlement_type = self.env.context.get("current_settlement_type") or self.env.context.get("default_settlement_type")
        return settlement_type if settlement_type in ("in", "out") else False

    def _effective_settlement_type(self, settlement_type=None):
        return self._settlement_type_from_context() or settlement_type or self.settlement_type

    def _contract_type_for_settlement_type(self, settlement_type=None):
        settlement_type = self._effective_settlement_type(settlement_type)
        if settlement_type == "in":
            return "out"
        if settlement_type == "out":
            return "in"
        return False

    def _contract_domain_for_settlement(self):
        self.ensure_one()
        domain = []
        if self.project_id:
            domain.append(("project_id", "=", self.project_id.id))
        contract_type = self._contract_type_for_settlement_type()
        if contract_type:
            domain.append(("type", "=", contract_type))
        return domain

    def _contract_matches_settlement(self, contract):
        self.ensure_one()
        if not contract:
            return True
        if self.project_id and contract.project_id and contract.project_id != self.project_id:
            return False
        contract_type = self._contract_type_for_settlement_type()
        if contract_type and contract.type and contract.type != contract_type:
            return False
        return True

    @api.onchange("project_id", "settlement_type")
    def _onchange_project_or_settlement_type_contract_domain(self):
        for rec in self:
            if rec.contract_id and not rec._contract_matches_settlement(rec.contract_id):
                rec.contract_id = False
        return {"domain": {"contract_id": self[:1]._contract_domain_for_settlement() if self else []}}

    @api.onchange("contract_id")
    def _onchange_contract_id_fill_header(self):
        values = {}
        for rec in self:
            c = rec.contract_id
            if not c:
                continue
            if rec.project_id and getattr(c, "project_id", False) and c.project_id != rec.project_id:
                rec.contract_id = False
                values["contract_id"] = False
                continue
            # 项目/公司/币种
            if not rec.project_id and getattr(c, "project_id", False):
                rec.project_id = c.project_id.id
                values["project_id"] = [c.project_id.id, c.project_id.display_name]
            if not rec.company_id and getattr(c, "company_id", False):
                rec.company_id = c.company_id.id
                values["company_id"] = [c.company_id.id, c.company_id.display_name]
            if not rec.currency_id:
                cur = getattr(c, "currency_id", False) or (rec.company_id.currency_id if rec.company_id else False)
                if cur:
                    rec.currency_id = cur.id
                    values["currency_id"] = [cur.id, cur.display_name]
            # 往来单位（合同相对方）
            partner = getattr(c, "partner_id", False)
            if partner:
                rec.partner_id = partner.id
                rec.settlement_unit_id = partner.id
                values["partner_id"] = [partner.id, partner.display_name]
                values["settlement_unit_id"] = [partner.id, partner.display_name]
            # 收支类型：收入合同->收入结算(in)，支出合同->支出结算(out)
            if getattr(c, "type", False):
                settlement_type = "in" if c.type == "out" else "out"
                rec.settlement_type = settlement_type
                values["settlement_type"] = settlement_type
        return {
            "value": values,
            "domain": {"contract_id": self[:1]._contract_domain_for_settlement() if self else []},
        }

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    def _resolve_business_category_id(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        settlement_type = self._effective_settlement_type(vals.get("settlement_type")) or "out"
        if not code:
            code = "settlement.income" if settlement_type == "in" else "settlement.expense"
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", "sc.settlement.order")],
            limit=1,
        )
        return category.id if category else False

    @api.model
    def _settlement_stage_id_by_code(self, code):
        code = str(code or "").strip() or "declared"
        stage = self.env["sc.dictionary"].sudo().search(
            [("type", "=", "settlement_stage"), ("code", "=", code), ("active", "=", True)],
            limit=1,
        )
        return stage.id if stage else False

    @api.model
    def _normalize_settlement_stage_defaults(self, vals, *, apply_default=False):
        if vals.get("settlement_stage_id"):
            stage = self.env["sc.dictionary"].sudo().browse(vals["settlement_stage_id"]).exists()
            if stage and stage.code:
                vals["settlement_stage"] = stage.code
            return vals
        if "settlement_stage_id" in vals and not vals.get("settlement_stage_id"):
            vals["settlement_stage"] = False
            return vals
        if not apply_default and "settlement_stage" not in vals:
            return vals
        stage_code = vals.get("settlement_stage") or "declared"
        stage_id = self._settlement_stage_id_by_code(stage_code)
        if stage_id:
            vals["settlement_stage_id"] = stage_id
        return vals

    @api.model
    def _backfill_settlement_stage_ids(self):
        self.env.cr.execute(
            """
            UPDATE sc_settlement_order settlement
               SET settlement_stage_id = stage.id
              FROM sc_dictionary stage
             WHERE settlement.settlement_stage_id IS NULL
               AND stage.type = 'settlement_stage'
               AND stage.code = COALESCE(settlement.settlement_stage, 'declared')
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_settlement_order settlement
               SET settlement_stage_id = stage.id,
                   settlement_stage = 'declared'
              FROM sc_dictionary stage
             WHERE settlement.settlement_stage_id IS NULL
               AND (settlement.settlement_stage IS NULL OR settlement.settlement_stage = '')
               AND stage.type = 'settlement_stage'
               AND stage.code = 'declared'
            """
        )
        return True

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        if "settlement_type" in fields_list:
            settlement_type = self._settlement_type_from_context()
            if settlement_type:
                res["settlement_type"] = settlement_type
        if "business_category_id" in fields_list and not res.get("business_category_id"):
            category_id = self._resolve_business_category_id(res)
            if category_id:
                res["business_category_id"] = category_id
        if "settlement_stage_id" in fields_list and not res.get("settlement_stage_id"):
            stage_id = self._settlement_stage_id_by_code(res.get("settlement_stage") or "declared")
            if stage_id:
                res["settlement_stage_id"] = stage_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            if vals.get("name", "新建") in (False, "新建"):
                seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
                vals["name"] = seq or _("Settlement")
            self._normalize_settlement_stage_defaults(vals, apply_default=True)
            self._normalize_feedback_defaults(vals)
        records = super().create(vals_list)
        records._apply_contract_defaults_if_needed()
        return records

    def init(self):
        self._backfill_history_surface_fields()
        self.env.cr.execute(
            """
            UPDATE sc_settlement_order settlement
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE settlement.business_category_id IS NULL
               AND category.code = CASE
                       WHEN settlement.settlement_type = 'in' THEN 'settlement.income'
                       ELSE 'settlement.expense'
                   END
               AND category.target_model = 'sc.settlement.order'
            """
        )
        self._backfill_settlement_stage_ids()

    def _backfill_history_surface_fields(self):
        return

    def write(self, vals):
        self._normalize_settlement_stage_defaults(vals)
        self._normalize_feedback_defaults(vals)
        if vals.get("state") == "cancel":
            self._check_payments_before_cancel()
        res = super().write(vals)
        if {"contract_id", "partner_id", "date_settlement", "document_date", "final_approved_date", "approved_date"} & set(vals):
            self._apply_contract_defaults_if_needed()
        return res

    @api.model
    def _normalize_feedback_defaults(self, vals):
        if vals.get("partner_id") and not vals.get("settlement_unit_id"):
            vals["settlement_unit_id"] = vals["partner_id"]
        if vals.get("document_date") and not vals.get("date_settlement"):
            vals["date_settlement"] = vals["document_date"]
        if vals.get("date_settlement") and not vals.get("document_date"):
            vals["document_date"] = vals["date_settlement"]
        if vals.get("approved_date") and not vals.get("final_approved_date"):
            vals["final_approved_date"] = vals["approved_date"]
        if vals.get("final_approved_date") and not vals.get("approved_date"):
            vals["approved_date"] = vals["final_approved_date"]
        return vals

    def _apply_contract_defaults_if_needed(self):
        """兜底：导入/批量写入绕过 onchange 时也能带出合同信息。"""
        for rec in self:
            c = rec.contract_id
            if not c:
                if rec.partner_id and not rec.settlement_unit_id:
                    rec.with_context(skip_onchange=True).sudo().write({"settlement_unit_id": rec.partner_id.id})
                continue
            updates = {}
            if not rec.project_id and getattr(c, "project_id", False):
                updates["project_id"] = c.project_id.id
            if not rec.company_id and getattr(c, "company_id", False):
                updates["company_id"] = c.company_id.id
            if not rec.currency_id:
                cur = getattr(c, "currency_id", False) or (updates.get("company_id") and self.env["res.company"].browse(updates["company_id"]).currency_id)
                if cur:
                    updates["currency_id"] = cur.id
            partner = getattr(c, "partner_id", False)
            if partner and not rec.partner_id:
                updates["partner_id"] = partner.id
            effective_partner = self.env["res.partner"].browse(updates["partner_id"]) if updates.get("partner_id") else rec.partner_id
            if effective_partner and not rec.settlement_unit_id:
                updates["settlement_unit_id"] = effective_partner.id
            if not rec.settlement_type and getattr(c, "type", False):
                updates["settlement_type"] = "in" if c.type == "out" else "out"
            if rec.date_settlement and not rec.document_date:
                updates["document_date"] = rec.date_settlement
            if rec.document_date and not rec.date_settlement:
                updates["date_settlement"] = rec.document_date
            if rec.final_approved_date and not rec.approved_date:
                updates["approved_date"] = rec.final_approved_date
            if rec.approved_date and not rec.final_approved_date:
                updates["final_approved_date"] = rec.approved_date
            if updates:
                rec.with_context(skip_onchange=True).sudo().write(updates)

    def _check_line_contracts_or_raise(self):
        for rec in self:
            for line in rec.line_ids:
                if not line.contract_id:
                    raise_guard(
                        "SETTLEMENT_CONTRACT_REQUIRED",
                        f"结算单[{rec.display_name}]",
                        _("校验结算行合同"),
                        reasons=[_("结算行未绑定合同")],
                    )
                if line.contract_id and rec.project_id:
                    if line.contract_id.project_id.id != rec.project_id.id:
                        raise_guard(
                            "SETTLEMENT_CONTRACT_MISMATCH",
                            f"结算单[{rec.display_name}]",
                            _("校验结算行合同"),
                            reasons=[_("合同项目与结算单项目不一致")],
                        )


class ScSettlementOrderLine(models.Model):
    _name = "sc.settlement.order.line"
    _description = "结算单明细"
    _order = "id"

    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        required=True,
        ondelete="cascade",
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="settlement_id.project_id",
        store=True,
        readonly=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
    )
    name = fields.Char(string="名称", required=True)
    qty = fields.Float(string="数量", default=1.0, digits="Product Unit of Measure")
    price_unit = fields.Monetary(string="单价", currency_field="currency_id", default=0.0)
    amount = fields.Monetary(string="金额", currency_field="currency_id", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("qty", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.qty or 0.0) * (line.price_unit or 0.0)

    def _ensure_manager_role(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Change Contract",
                reasons=["manager role required"],
            )

    def _ensure_contract_required(self, contract_id=None):
        if not contract_id:
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Bind Contract",
                reasons=["contract_id is required"],
            )

    def _ensure_contract_match(self, contract_id, project_id):
        if not contract_id or not project_id:
            return
        contract = self.env["construction.contract"].browse(contract_id)
        if contract.project_id and contract.project_id.id != project_id:
            raise_guard(
                "SETTLEMENT_CONTRACT_MISMATCH",
                "Settlement Line",
                "Bind Contract",
                reasons=["contract project mismatch"],
            )

    def _audit_contract(self, event_code, before_id, after_id, reason=None, require_reason=False):
        Audit = self.env["sc.audit.log"]
        for rec in self:
            Audit.write_event(
                event_code=event_code,
                model=rec._name,
                res_id=rec.id,
                action=event_code,
                before={"contract_id": before_id},
                after={"contract_id": after_id},
                reason=reason,
                require_reason=require_reason,
                project_id=rec.project_id.id if rec.project_id else False,
                company_id=rec.settlement_id.company_id.id if rec.settlement_id else False,
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("contract_id") and vals.get("settlement_id"):
                settlement = self.env["sc.settlement.order"].browse(vals.get("settlement_id"))
                if settlement.contract_id:
                    vals["contract_id"] = settlement.contract_id.id
            if not self.env.context.get("legacy_migration_allow_missing_contract"):
                self._ensure_contract_required(vals.get("contract_id"))
            if vals.get("settlement_id"):
                settlement = self.env["sc.settlement.order"].browse(vals.get("settlement_id"))
                self._ensure_contract_match(vals.get("contract_id"), settlement.project_id.id)
        return super().create(vals_list)

    def write(self, vals):
        if "contract_id" in vals and not self.env.context.get("allow_contract_change"):
            raise_guard(
                "SETTLEMENT_CONTRACT_REQUIRED",
                "Settlement Line",
                "Change Contract",
                reasons=["use action_bind_contract/action_unbind_contract"],
            )
        if "contract_id" in vals:
            if not vals.get("contract_id") and not self.env.context.get("allow_contract_change"):
                self._ensure_contract_required(False)
        res = super().write(vals)
        if "contract_id" in vals:
            for rec in self:
                if rec.contract_id:
                    rec._ensure_contract_required(rec.contract_id.id)
                    rec._ensure_contract_match(rec.contract_id.id, rec.project_id.id)
                elif not self.env.context.get("allow_contract_change"):
                    rec._ensure_contract_required(False)
        return res

    def action_bind_contract(self, contract_id, reason=None):
        self.ensure_one()
        self._ensure_contract_required(contract_id)
        self._ensure_contract_match(contract_id, self.project_id.id)
        before_id = self.contract_id.id if self.contract_id else False
        require_reason = False
        if before_id and before_id != contract_id:
            self._ensure_manager_role()
            require_reason = True
        if require_reason and not reason:
            raise_guard(
                "AUDIT_REASON_REQUIRED",
                "Audit",
                "Write",
                reasons=["reason is required"],
            )
        self.with_context(allow_contract_change=True).write({"contract_id": contract_id})
        self._audit_contract(
            "contract_bound",
            before_id=before_id,
            after_id=contract_id,
            reason=reason,
            require_reason=require_reason,
        )
        return True

    def action_unbind_contract(self, reason=None):
        self.ensure_one()
        self._ensure_manager_role()
        if not reason:
            raise_guard(
                "AUDIT_REASON_REQUIRED",
                "Audit",
                "Write",
                reasons=["reason is required"],
            )
        before_id = self.contract_id.id if self.contract_id else False
        self.with_context(allow_contract_change=True).write({"contract_id": False})
        self._audit_contract(
            "contract_unbound",
            before_id=before_id,
            after_id=False,
            reason=reason,
            require_reason=True,
        )
        return True
