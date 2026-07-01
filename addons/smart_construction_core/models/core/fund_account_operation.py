# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScFundAccountOperation(models.Model):
    _name = "sc.fund.account.operation"
    _description = "资金账户操作单"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "operation_date desc, id desc"

    name = fields.Char(string="单据编号", required=True, default="/", copy=False, tracking=True)
    operation_type = fields.Selection(
        [
            ("transfer_out", "资金划拨"),
            ("transfer_between", "资金调拨"),
            ("balance_adjustment", "余额调整"),
            ("fund_daily_report", "资金日报表"),
        ],
        string="业务类型",
        required=True,
        default=lambda self: self.env.context.get("default_operation_type") or "transfer_between",
        tracking=True,
        index=True,
    )
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        domain="[('target_model', '=', 'sc.fund.account.operation')]",
        index=True,
        tracking=True,
        ondelete="restrict",
    )
    operation_date = fields.Date(
        string="单据日期",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    source_account_id = fields.Many2one(
        "sc.fund.account",
        string="付款账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    target_account_id = fields.Many2one(
        "sc.fund.account",
        string="收款账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    source_project_id = fields.Many2one(
        "project.project",
        string="付款方项目",
        related="source_account_id.project_id",
        readonly=True,
    )
    target_project_id = fields.Many2one(
        "project.project",
        string="收款方项目",
        related="target_account_id.project_id",
        readonly=True,
    )
    fund_flow_label = fields.Char(string="业务方向", compute="_compute_fund_flow_label")
    fund_account_id = fields.Many2one(
        "sc.fund.account",
        string="账户",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: (self.env.ref("base.CNY", raise_if_not_found=False) or self.env.company.currency_id).id,
    )
    amount = fields.Monetary(string="金额", currency_field="currency_id", tracking=True)
    daily_income = fields.Monetary(string="当日收入", currency_field="currency_id", tracking=True)
    daily_expense = fields.Monetary(string="当日支出", currency_field="currency_id", tracking=True)
    account_balance = fields.Monetary(string="账面余额", currency_field="currency_id", tracking=True)
    bank_balance = fields.Monetary(string="银行余额", currency_field="currency_id", tracking=True)
    before_balance = fields.Monetary(string="调整前余额", currency_field="currency_id", tracking=True)
    after_balance = fields.Monetary(string="调整后余额", currency_field="currency_id", tracking=True)
    operation_reason = fields.Char(string="操作原因", required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "已完成"),
            ("cancelled", "已取消"),
        ],
        string="状态",
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    note = fields.Text(string="备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_fund_account_operation_attachment_rel",
        "operation_id",
        "attachment_id",
        string="附件",
    )
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True, index=True)
    legacy_document_state = fields.Char(string="历史单据状态", readonly=True, index=True)
    creator_name = fields.Char(string="历史录入人", readonly=True, index=True)
    created_time = fields.Datetime(string="历史录入时间", readonly=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)
    fund_operation_status_display = fields.Char(
        string="单据状态",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_project_name = fields.Char(
        string="项目名称",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_date_display = fields.Date(
        string="发生时间",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_account_no = fields.Char(
        string="账户号码",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_transfer_type = fields.Char(
        string="转账类别",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_reason_display = fields.Char(
        string="事由",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )
    fund_operation_source_created_at = fields.Datetime(
        string="录入时间",
        compute="_compute_fund_operation_formal_visible_fields",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "同一历史资金操作只能迁移一次。",
        ),
    ]

    @api.depends("operation_type", "source_account_id.project_id", "target_account_id.project_id")
    def _compute_fund_flow_label(self):
        for record in self:
            if record.operation_type == "fund_daily_report":
                record.fund_flow_label = _("账户日报")
                continue
            if record.operation_type == "balance_adjustment":
                record.fund_flow_label = _("账户余额调整")
                continue
            source_project = record.source_account_id.project_id
            target_project = record.target_account_id.project_id
            if source_project and target_project:
                record.fund_flow_label = _("同项目账户调拨") if source_project == target_project else _("项目间资金调拨")
            elif source_project and not target_project:
                record.fund_flow_label = _("项目转出到公司账户")
            elif target_project and not source_project:
                record.fund_flow_label = _("公司账户转入项目")
            else:
                record.fund_flow_label = _("公司账户间调拨")

    @staticmethod
    def _fund_operation_legacy_state_label(value):
        return {
            "-1": "已作废",
            "0": "未审核",
            "1": "审核中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
        }.get(str(value or ""), str(value or ""))

    def _fund_operation_state_label(self, state):
        return dict(self._fields["state"].selection).get(state, state or "")

    def _fund_operation_type_label(self, operation_type):
        return dict(self._fields["operation_type"].selection).get(operation_type, operation_type or "")

    def _fund_operation_visible_value(self, suffix):
        return ""

    @api.depends(
        "legacy_document_state",
        "state",
        "project_id.display_name",
        "operation_date",
        "fund_account_id.display_name",
        "source_account_id.display_name",
        "operation_type",
        "operation_reason",
        "creator_name",
        "created_time",
        "create_uid.name",
        "create_date",
    )
    def _compute_fund_operation_formal_visible_fields(self):
        for record in self:
            legacy_state = (record.legacy_document_state or "").strip()
            legacy_project_name = record._fund_operation_visible_value("project_name")
            legacy_account_name = record._fund_operation_visible_value("account_name")
            legacy_transfer_type = record._fund_operation_visible_value("transfer_type")
            legacy_reason = record._fund_operation_visible_value("reason")
            record.fund_operation_status_display = (
                record._fund_operation_legacy_state_label(legacy_state)
                if legacy_state
                else record._fund_operation_state_label(record.state)
            )
            record.fund_operation_project_name = (
                legacy_project_name
                or (record.project_id.display_name if record.project_id else "")
                or ""
            )
            record.fund_operation_date_display = record.operation_date
            record.fund_operation_account_no = (
                legacy_account_name
                or (record.fund_account_id.display_name if record.fund_account_id else "")
                or (record.source_account_id.display_name if record.source_account_id else "")
                or ""
            )
            record.fund_operation_transfer_type = (
                legacy_transfer_type
                or record._fund_operation_type_label(record.operation_type)
            )
            record.fund_operation_reason_display = record.operation_reason or legacy_reason or ""
            record.fund_operation_source_created_by = (
                record.creator_name
                or (record.create_uid.name if record.create_uid else "")
                or ""
            )
            record.fund_operation_source_created_at = record.created_time or record.create_date

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        return res

    @api.constrains(
        "operation_type",
        "source_account_id",
        "target_account_id",
        "fund_account_id",
        "amount",
        "before_balance",
        "after_balance",
    )
    def _check_operation_values(self):
        for record in self:
            if record.operation_type in ("transfer_out", "transfer_between"):
                if not record.source_account_id or not record.target_account_id:
                    raise ValidationError(_("资金划拨/调拨必须填写转出账户和转入账户。"))
                if record.source_account_id == record.target_account_id:
                    raise ValidationError(_("转出账户和转入账户不能相同。"))
                if record.amount <= 0:
                    raise ValidationError(_("资金划拨/调拨金额必须大于 0。"))
                if record.source_account_id.currency_id != record.target_account_id.currency_id:
                    raise ValidationError(_("转出账户和转入账户币种必须一致。"))
            if record.operation_type == "balance_adjustment":
                if not record.fund_account_id:
                    raise ValidationError(_("余额调整必须填写调整账户。"))
                if record.before_balance == record.after_balance:
                    raise ValidationError(_("余额调整前后金额不能相同。"))
            if record.operation_type == "fund_daily_report" and not record.fund_account_id:
                raise ValidationError(_("资金日报表必须填写账户。"))
            if record.operation_type == "fund_daily_report":
                if record.daily_income < 0 or record.daily_expense < 0:
                    raise ValidationError(_("资金日报收入和支出不能为负数。"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            context_date = self.env.context.get("default_operation_date") or self.env.context.get("current_document_date")
            if context_date:
                vals.setdefault("operation_date", context_date)
            context_amount = self.env.context.get("default_amount") or self.env.context.get("current_business_amount")
            if context_amount:
                vals.setdefault("amount", context_amount)
            context_reason = self.env.context.get("default_operation_reason") or self.env.context.get("default_note")
            if context_reason:
                vals.setdefault("operation_reason", context_reason)
            source_account_id = self.env.context.get("default_source_account_id")
            if source_account_id:
                vals.setdefault("source_account_id", source_account_id)
            target_account_id = self.env.context.get("default_target_account_id")
            if target_account_id:
                vals.setdefault("target_account_id", target_account_id)
            context_note = self.env.context.get("default_note")
            if context_note:
                vals.setdefault("note", context_note)
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
            if vals.get("name", "/") == "/":
                vals["name"] = seq.next_by_code("sc.fund.account.operation") or _("资金账户操作单")
        return super().create(vals_list)

    @api.model
    def _resolve_business_category_code(self, vals):
        code = (
            vals.get("business_category_code")
            or self.env.context.get("default_business_category_code")
            or self.env.context.get("business_category_code")
            or self.env.context.get("current_business_category_code")
        )
        if code:
            return code
        operation_type = vals.get("operation_type") or self.env.context.get("default_operation_type")
        if operation_type == "fund_daily_report":
            return "finance.fund.daily_report"
        if operation_type == "balance_adjustment":
            return "finance.fund.balance_adjustment"
        return "finance.fund.transfer"

    @api.model
    def _resolve_business_category_id(self, vals):
        code = self._resolve_business_category_code(vals)
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", self._name)],
            limit=1,
        )
        return category.id if category else False

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的资金账户操作单可以确认。"))
            before = rec._snapshot_audit_payload()
            rec._check_active_accounts()
            rec.write({"state": "confirmed"})
            rec._audit_transition(
                "fund_account_operation_confirmed",
                before,
                rec._snapshot_audit_payload(),
                "action_confirm",
            )

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("只有已确认的资金账户操作单可以完成。"))
            before = rec._snapshot_audit_payload()
            rec._check_active_accounts()
            rec.write({"state": "done"})
            rec._ensure_interfund_cash_ledger()
            rec._ensure_fund_daily_cash_ledger()
            rec._apply_account_balance_state()
            rec._audit_transition(
                "fund_account_operation_done",
                before,
                rec._snapshot_audit_payload(),
                "action_done",
            )

    def _ensure_fund_daily_cash_ledger(self):
        for rec in self:
            if rec.operation_type != "fund_daily_report":
                continue
            project = rec.project_id or rec.fund_account_id.project_id
            if not project:
                continue
            Ledger = self.env["sc.treasury.ledger"]
            currency = rec.currency_id or rec.fund_account_id.currency_id or project.company_id.currency_id
            date = rec.operation_date
            for direction, amount, note in (
                ("in", rec.daily_income, _("auto:fund_daily_report_done:income")),
                ("out", rec.daily_expense, _("auto:fund_daily_report_done:expense")),
            ):
                if not amount or amount <= 0:
                    continue
                domain = [
                    ("source_model", "=", rec._name),
                    ("source_res_id", "=", rec.id),
                    ("project_id", "=", project.id),
                    ("direction", "=", direction),
                    ("source_kind", "=", "daily_line"),
                ]
                existing = Ledger.sudo().search(domain, limit=1)
                vals = {
                    "date": date,
                    "partner_id": False,
                    "amount": amount,
                    "currency_id": currency.id,
                    "state": "posted",
                    "note": note,
                }
                if existing:
                    existing.sudo().write(vals)
                    continue
                Ledger.sudo().with_context(allow_ledger_auto=True).create(
                    dict(
                        vals,
                        project_id=project.id,
                        direction=direction,
                        source_kind="daily_line",
                        source_model=rec._name,
                        source_res_id=rec.id,
                    )
                )

    def _apply_account_balance_state(self):
        for rec in self:
            if rec.operation_type not in ("fund_daily_report", "balance_adjustment") or not rec.fund_account_id:
                continue
            vals = {
                "balance_as_of_date": rec.operation_date,
                "balance_source_operation_id": rec.id,
            }
            if rec.operation_type == "fund_daily_report":
                vals.update(
                    {
                        "current_account_balance": rec.account_balance,
                        "current_bank_balance": rec.bank_balance,
                        "current_balance_source": "fund_daily_report",
                    }
                )
            elif rec.operation_type == "balance_adjustment":
                vals.update(
                    {
                        "current_account_balance": rec.after_balance,
                        "current_balance_source": "balance_adjustment",
                    }
                )
            rec.fund_account_id.sudo().write(vals)

    def _ensure_interfund_cash_ledger(self):
        for rec in self:
            if rec.operation_type not in ("transfer_out", "transfer_between") or (rec.amount or 0.0) <= 0:
                continue
            source_project = rec.source_account_id.project_id
            target_project = rec.target_account_id.project_id
            if source_project and target_project and source_project == target_project:
                continue
            Ledger = self.env["sc.treasury.ledger"]
            if source_project:
                Ledger._ensure_interfund_ledger(
                    rec,
                    project=source_project,
                    direction="out",
                    amount=rec.amount,
                    date=rec.operation_date,
                    currency=rec.currency_id,
                    note=_("auto:fund_account_operation_done:out"),
                )
            if target_project:
                Ledger._ensure_interfund_ledger(
                    rec,
                    project=target_project,
                    direction="in",
                    amount=rec.amount,
                    date=rec.operation_date,
                    currency=rec.currency_id,
                    note=_("auto:fund_account_operation_done:in"),
                )

    def _check_active_accounts(self):
        self.ensure_one()
        accounts = self.env["sc.fund.account"]
        if self.operation_type in ("transfer_out", "transfer_between"):
            accounts |= self.source_account_id | self.target_account_id
        elif self.operation_type in ("balance_adjustment", "fund_daily_report"):
            accounts |= self.fund_account_id
        inactive = accounts.filtered(lambda account: account.state != "active")
        if inactive:
            raise UserError(_("资金账户 %s 未启用，不能办理该操作。") % ", ".join(inactive.mapped("display_name")))

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的资金账户操作单可以取消。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "cancelled"})
            rec._audit_transition(
                "fund_account_operation_cancelled",
                before,
                rec._snapshot_audit_payload(),
                "action_cancel",
            )

    def action_reset_draft(self):
        for rec in self:
            if rec.state != "cancelled":
                raise UserError(_("只有已取消的资金账户操作单可以重置为草稿。"))
            before = rec._snapshot_audit_payload()
            rec.write({"state": "draft"})
            rec._audit_transition(
                "fund_account_operation_reset_draft",
                before,
                rec._snapshot_audit_payload(),
                "action_reset_draft",
            )

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "state": self.state,
            "operation_type": self.operation_type,
            "business_category_id": self.business_category_id.id,
            "business_category_code": self.business_category_id.code,
            "operation_date": fields.Date.to_string(self.operation_date) if self.operation_date else False,
            "source_account_id": self.source_account_id.id,
            "target_account_id": self.target_account_id.id,
            "source_project_id": self.source_account_id.project_id.id,
            "target_project_id": self.target_account_id.project_id.id,
            "fund_account_id": self.fund_account_id.id,
            "project_id": self.project_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "amount": self.amount,
            "daily_income": self.daily_income,
            "daily_expense": self.daily_expense,
            "account_balance": self.account_balance,
            "bank_balance": self.bank_balance,
            "operation_reason": self.operation_reason,
        }

    def _audit_transition(self, event_code, before, after, action_name):
        self.ensure_one()
        return self.env["sc.audit.log"].write_event(
            event_code,
            self._name,
            self.id,
            action=action_name,
            before=before,
            after=after,
            company_id=self.company_id,
            project_id=self.project_id or self.source_account_id.project_id or self.target_account_id.project_id,
        )

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_fund_account_operation operation
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE operation.business_category_id IS NULL
               AND category.target_model = 'sc.fund.account.operation'
               AND category.code = CASE
                   WHEN operation.operation_type = 'fund_daily_report'
                       THEN 'finance.fund.daily_report'
                   WHEN operation.operation_type = 'balance_adjustment'
                       THEN 'finance.fund.balance_adjustment'
                   ELSE 'finance.fund.transfer'
               END
            """
        )
