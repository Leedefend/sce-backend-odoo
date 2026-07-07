# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class TenderBid(models.Model):
    _name = "tender.bid"
    _description = "投标管理"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.business.scope.mixin"]
    _order = "project_id, id desc"

    name = fields.Char("投标编号", default="新建", copy=False)
    tender_name = fields.Char("投标名称", required=True, tracking=True)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        tracking=True,
    )
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
    )
    tender_round = fields.Integer("投标轮次", default=1)
    owner_id = fields.Many2one("res.partner", string="招标人/业主")
    legacy_owner_name = fields.Char("历史招标人/业主文本", index=True)
    bid_amount = fields.Monetary("投标报价", currency_field="currency_id", tracking=True)
    applicant_name = fields.Char("申请人", index=True, tracking=True)
    apply_date = fields.Date("申请日期", index=True, tracking=True)
    note = fields.Text("备注", tracking=True)
    created_time = fields.Datetime("录入时间", index=True, tracking=True)
    deadline = fields.Datetime("投标截止时间")
    open_date = fields.Datetime("开标时间")
    state = fields.Selection(
        [
            ("prepare", "准备投标"),
            ("estimating", "造价测算"),
            ("submitted", "已提交"),
            ("waiting", "等待开标"),
            ("won", "中标"),
            ("lost", "未中标"),
        ],
        string="状态",
        default="prepare",
        required=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    tech_attachment_ids = fields.Many2many(
        "ir.attachment",
        "tender_bid_tech_attachment_rel",
        "bid_id",
        "attachment_id",
        string="技术标附件",
    )
    biz_attachment_ids = fields.Many2many(
        "ir.attachment",
        "tender_bid_biz_attachment_rel",
        "bid_id",
        "attachment_id",
        string="商务标附件",
    )

    line_ids = fields.One2many("tender.bid.line", "bid_id", string="清单明细")
    amount_total = fields.Monetary(
        "清单合计", currency_field="currency_id", compute="_compute_amounts", store=True
    )

    # 子表单：投标文件购买 / 勘察 / 审查 / 开标 / 保证金
    doc_purchase_ids = fields.One2many("tender.doc.purchase", "bid_id", string="标书购买")
    survey_ids = fields.One2many("tender.survey", "bid_id", string="现场踏勘")
    review_ids = fields.One2many("tender.doc.review", "bid_id", string="文件审查")
    opening_ids = fields.One2many("tender.opening", "bid_id", string="开标登记")
    guarantee_ids = fields.One2many("tender.guarantee", "bid_id", string="保证金")

    guarantee_total = fields.Monetary(
        "保证金总额", currency_field="currency_id", compute="_compute_guarantee_stats", store=True
    )
    guarantee_outstanding = fields.Monetary(
        "在外保证金", currency_field="currency_id", compute="_compute_guarantee_stats", store=True
    )

    contract_id = fields.Many2one("construction.contract", string="关联合同", readonly=True)
    legacy_fact_model = fields.Char("来源通用模型", index=True)
    legacy_fact_id = fields.Integer("来源通用记录ID", index=True)
    legacy_fact_type = fields.Char("来源业务类型", index=True)
    legacy_note = fields.Text("历史来源说明")
    legacy_visible_document_state = fields.Char("历史单据状态", readonly=True)
    legacy_visible_opening_time = fields.Datetime("历史开标时间", readonly=True)
    legacy_visible_project_name = fields.Char("历史项目名称", readonly=True)
    legacy_visible_registration_time = fields.Datetime("历史登记时间", readonly=True)
    legacy_visible_creator_name = fields.Char("历史录入人", readonly=True)
    legacy_attachment_ref = fields.Char("历史附件引用", readonly=True, index=True)
    tender_bid_status_display = fields.Char(
        "单据状态",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )
    tender_bid_document_no = fields.Char(
        "单据编号",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )
    tender_bid_project_name = fields.Char(
        "项目名称",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )
    tender_bid_registration_time = fields.Datetime(
        "登记时间",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )
    tender_bid_push_result = fields.Char(
        "推送结果",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )
    tender_bid_source_created_by = fields.Char(
        "录入人",
        compute="_compute_tender_bid_formal_visible_fields",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ("legacy_tender_bid_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用投标事实已迁移为投标记录。"),
    ]

    @api.depends("name", "tender_name", "project_id")
    def _compute_display_name(self):
        for record in self:
            bid_no = (record.name or "").strip()
            project_name = record.project_id.display_name if record.project_id else ""
            title = (record.tender_name or record.legacy_visible_project_name or project_name or "").strip()
            parts = [
                title,
                bid_no if bid_no and bid_no != "新建" else "",
                project_name if project_name and project_name != title else "",
            ]
            record.display_name = " / ".join(part for part in parts if part) or bid_no or "投标记录"

    def _state_label(self, state):
        return dict(self._fields["state"].selection).get(state, state or "")

    @api.model
    def _legacy_document_state_label(self, state):
        return {
            "-1": "已作废",
            "0": "未审核",
            "1": "审核中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
        }.get(state, state or "")

    @api.depends(
        "name",
        "state",
        "project_id.display_name",
        "legacy_visible_document_state",
        "legacy_visible_project_name",
        "legacy_visible_registration_time",
        "legacy_visible_creator_name",
        "source_created_by",
        "source_created_at",
        "create_date",
        "create_uid.name",
    )
    def _compute_tender_bid_formal_visible_fields(self):
        for record in self:
            legacy_state = (record.legacy_visible_document_state or "").strip()
            record.tender_bid_status_display = (
                record._legacy_document_state_label(legacy_state)
                if legacy_state
                else record._state_label(record.state)
            )
            record.tender_bid_document_no = record.name or ""
            record.tender_bid_project_name = (
                record.legacy_visible_project_name
                or (record.project_id.display_name if record.project_id else "")
                or ""
            )
            record.tender_bid_registration_time = (
                record.legacy_visible_registration_time
                or record.source_created_at
                or record.create_date
            )
            record.tender_bid_push_result = record._state_label(record.state)
            record.tender_bid_source_created_by = (
                record.legacy_visible_creator_name
                or record.source_created_by
                or (record.create_uid.name if record.create_uid else "")
                or ""
            )

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
        if project_id and "owner_id" in fields_list and not res.get("owner_id"):
            project = self.env["project.project"].browse(project_id).exists()
            if project and project.owner_id:
                res["owner_id"] = project.owner_id.id
        if project_id and "operation_strategy" in fields_list and not res.get("operation_strategy"):
            project = self.env["project.project"].browse(project_id).exists()
            if project:
                res["operation_strategy"] = project.operation_strategy
        return res

    @api.onchange("project_id")
    def _onchange_project_id_owner(self):
        if self.project_id and not self.owner_id and self.project_id.owner_id:
            self.owner_id = self.project_id.owner_id

    @api.model
    def _normalize_line_commands(self, commands):
        normalized = []
        for command in commands or []:
            if not isinstance(command, (list, tuple)) or len(command) < 3 or command[0] != 0:
                normalized.append(command)
                continue
            line_vals = dict(command[2] or {})
            has_payload = any(
                line_vals.get(field_name)
                for field_name in ("code", "name", "spec", "uom_id", "quantity", "price")
            )
            if not has_payload:
                continue
            if not line_vals.get("name"):
                line_vals["name"] = line_vals.get("code") or line_vals.get("spec") or "未命名清单"
            normalized.append((command[0], command[1], line_vals))
        return normalized

    @api.depends("line_ids.amount")
    def _compute_amounts(self):
        for bid in self:
            bid.amount_total = sum(bid.line_ids.mapped("amount"))

    @api.depends("guarantee_ids.amount", "guarantee_ids.type")
    def _compute_guarantee_stats(self):
        for bid in self:
            total = 0.0
            out = 0.0
            for rec in bid.guarantee_ids:
                if rec.type == "out":
                    total += rec.amount or 0.0
                    out += rec.amount or 0.0
                elif rec.type == "return":
                    out -= rec.amount or 0.0
            bid.guarantee_total = total
            bid.guarantee_outstanding = out

    # ===== 状态流转 =====
    def _reload(self):
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_to_prepare(self):
        return self._set_state("prepare")

    def action_to_estimating(self):
        return self._set_state("estimating")

    def action_to_submitted(self):
        return self._set_state("submitted")

    def action_to_waiting(self):
        return self._set_state("waiting")

    def action_mark_won(self):
        return self._set_state("won")

    def action_mark_lost(self):
        return self._set_state("lost")

    def _set_state(self, target_state):
        old_states = {rec.id: rec.state for rec in self}
        res = self.write({"state": target_state})
        # 如果从其他状态切到 won，自动生成合同（使用合同默认状态，避免非法 state）
        if target_state == "won":
            for bid in self:
                if (
                    old_states.get(bid.id) != "won"
                    and not bid.contract_id
                    and "construction.contract" in self.env.registry
                ):
                    contract_vals = {
                        "name": f"{bid.project_id.name}-收入合同",
                        "subject": bid.tender_name or f"{bid.project_id.name}-收入合同",
                        "project_id": bid.project_id.id,
                        "partner_id": bid.owner_id.id,
                        "amount_final": bid.bid_amount or bid.amount_total or 0.0,
                        "type": "out",
                        # 不传 state，使用合同模型默认值；屏蔽 context 中的 default_state 干扰
                    }
                    contract = (
                        self.env["construction.contract"]
                        .with_context(default_state=False)
                        .create(contract_vals)
                    )
                    bid.contract_id = contract.id
        return self._reload() if res else res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = vals.get("project_id") or self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
                if not vals.get("owner_id"):
                    project = self.env["project.project"].browse(project_id).exists()
                    if project and project.owner_id:
                        vals["owner_id"] = project.owner_id.id
            if "line_ids" in vals:
                vals["line_ids"] = self._normalize_line_commands(vals.get("line_ids"))
        return super().create(vals_list)

    def write(self, vals):
        # 合同创建逻辑集中在 _set_state("won")，避免重复/非法类型
        if "line_ids" in vals:
            vals = dict(vals)
            vals["line_ids"] = self._normalize_line_commands(vals.get("line_ids"))
        return super().write(vals)


class TenderBidLine(models.Model):
    _name = "tender.bid.line"
    _description = "投标清单行"
    _order = "bid_id, sequence, id"

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    sequence = fields.Integer("序号", default=10)
    code = fields.Char("清单编码")
    name = fields.Char("清单名称", required=True)
    spec = fields.Char("项目特征")
    uom_id = fields.Many2one("uom.uom", string="单位")
    quantity = fields.Float("工程量", default=0.0)
    price = fields.Monetary("单价", currency_field="currency_id")
    amount = fields.Monetary(
        "合价", currency_field="currency_id", compute="_compute_amount", store=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="bid_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("quantity", "price")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.quantity or 0.0) * (line.price or 0.0)


class TenderDocPurchase(models.Model):
    _name = "tender.doc.purchase"
    _description = "投标文件购买申请"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade", tracking=True)
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    applicant_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user)
    apply_date = fields.Date("申请日期", default=fields.Date.context_today)
    amount = fields.Monetary("金额", currency_field="currency_id")
    invoice_no = fields.Char("发票号/凭证号")
    payment_method = fields.Char("缴费方式", index=True)
    receipt_partner_id = fields.Many2one(
        "res.partner",
        string="收款单位",
        domain=["|", ("supplier_rank", ">", 0), ("customer_rank", ">", 0)],
        index=True,
        tracking=True,
    )
    receipt_partner_name = fields.Char("历史/快照收款单位", index=True)
    receipt_payee_name = fields.Char("收款人", index=True)
    receipt_bank_name = fields.Char("开户银行", index=True)
    receipt_bank_account = fields.Char("收款账户", index=True)
    remark = fields.Text("备注")
    legacy_visible_applicant_name = fields.Char("历史申请人", readonly=True)
    legacy_visible_document_state = fields.Char("历史单据状态", readonly=True)
    legacy_source_created_by = fields.Char("录入人", index=True)
    legacy_source_created_at = fields.Datetime("录入时间", index=True)
    legacy_record_id = fields.Char("历史记录ID", index=True)
    legacy_source_table = fields.Char("来源表", index=True)
    legacy_attachment_ref = fields.Char("历史附件引用", readonly=True, index=True)
    attachment_ids = fields.Many2many("ir.attachment", string="附件")
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "审批中"), ("approved", "已通过"), ("rejected", "已驳回")],
        string="状态",
        default="draft",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency", related="bid_id.currency_id", store=True, readonly=True
    )

    def _receipt_partner_snapshot_values(self, partner):
        if not partner:
            return {}
        return {
            "receipt_partner_name": partner.display_name or partner.name,
            "receipt_payee_name": partner.sc_account_name or partner.name,
            "receipt_bank_name": partner.sc_bank_name or "",
            "receipt_bank_account": partner.sc_bank_account or "",
        }

    @api.onchange("receipt_partner_id")
    def _onchange_receipt_partner_id(self):
        result_values = {}
        for record in self:
            if record.receipt_partner_id:
                values = record._receipt_partner_snapshot_values(record.receipt_partner_id)
                record.receipt_partner_name = values.get("receipt_partner_name")
                record.receipt_payee_name = values.get("receipt_payee_name")
                record.receipt_bank_name = values.get("receipt_bank_name")
                record.receipt_bank_account = values.get("receipt_bank_account")
                result_values.update(values)
        if result_values:
            return {"value": result_values}
        return {}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get("receipt_partner_id")
            if partner_id:
                partner = self.env["res.partner"].browse(partner_id).exists()
                for key, value in self._receipt_partner_snapshot_values(partner).items():
                    if not vals.get(key):
                        vals[key] = value
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals or {})
        if "receipt_partner_id" in vals and vals.get("receipt_partner_id"):
            partner = self.env["res.partner"].browse(vals["receipt_partner_id"]).exists()
            for key, value in self._receipt_partner_snapshot_values(partner).items():
                if not vals.get(key):
                    vals[key] = value
        return super().write(vals)

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError("只有草稿状态的投标报名费申请可以提交。")
            missing = []
            if not record.bid_id:
                missing.append("投标")
            if not record.apply_date:
                missing.append("申请日期")
            if not record.amount or record.amount <= 0:
                missing.append("金额")
            if not record.payment_method:
                missing.append("缴费方式")
            if not record.receipt_partner_id and not record.receipt_partner_name:
                missing.append("收款单位")
            if not record.receipt_bank_account:
                missing.append("收款账户")
            if missing:
                raise UserError("提交前请补充：%s。" % "、".join(missing))
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        self.write({"state": "approved"})
        return True

    def action_reject(self):
        self.write({"state": "rejected"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class TenderSurvey(models.Model):
    _name = "tender.survey"
    _description = "投标项目勘察"

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    survey_date = fields.Date("踏勘日期", default=fields.Date.context_today)
    location = fields.Char("踏勘地点")
    member_ids = fields.Many2many("res.users", string="踏勘人员")
    issue_notes = fields.Text("现场问题与风险")
    attachment_ids = fields.Many2many("ir.attachment", string="现场照片/文件")


class TenderDocReview(models.Model):
    _name = "tender.doc.review"
    _description = "投标文件审查"

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    version = fields.Char("版本/批次")
    reviewer_ids = fields.Many2many("res.users", string="审查人")
    comment = fields.Text("审查意见")
    attachment_ids = fields.Many2many("ir.attachment", string="文件版本")
    state = fields.Selection(
        [("draft", "草稿"), ("reviewing", "审查中"), ("approved", "已通过"), ("rejected", "已驳回")],
        default="draft",
    )


class TenderOpening(models.Model):
    _name = "tender.opening"
    _description = "开标登记"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade", tracking=True)
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    open_time = fields.Datetime("开标时间")
    result = fields.Selection(
        [("pending", "未决"), ("won", "中标"), ("lost", "未中标"), ("backup", "候补")],
        default="pending",
        tracking=True,
    )
    win_price = fields.Monetary("中标价", currency_field="currency_id")
    competitor_ids = fields.One2many(
        "tender.opening.competitor", "opening_id", string="竞争对手"
    )
    remark = fields.Text("备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "tender_opening_attachment_rel",
        "opening_id",
        "attachment_id",
        string="附件",
    )
    currency_id = fields.Many2one(
        "res.currency", related="bid_id.currency_id", store=True, readonly=True
    )


class TenderOpeningCompetitor(models.Model):
    _name = "tender.opening.competitor"
    _description = "竞争对手报价"

    opening_id = fields.Many2one("tender.opening", string="开标记录", required=True, ondelete="cascade")
    name = fields.Char("竞争对手", required=True)
    quote = fields.Monetary("报价", currency_field="currency_id")
    rank = fields.Integer("名次")
    remark = fields.Char("备注")
    currency_id = fields.Many2one(
        "res.currency", related="opening_id.currency_id", store=True, readonly=True
    )


class TenderGuarantee(models.Model):
    _name = "tender.guarantee"
    _description = "投标保证金"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    bid_id = fields.Many2one("tender.bid", string="投标", required=True, ondelete="cascade", tracking=True)
    legacy_fact_id = fields.Integer(related="bid_id.legacy_fact_id", string="历史投标事实ID", readonly=True)
    legacy_visible_document_state = fields.Char("历史可见状态", readonly=True)
    legacy_visible_document_no = fields.Char("历史可见单据编号", readonly=True)
    legacy_visible_project_name = fields.Char("历史可见项目名称", readonly=True)
    legacy_visible_creator_name = fields.Char("历史可见录入人", readonly=True)
    legacy_visible_created_time = fields.Datetime("历史可见录入时间", readonly=True)
    legacy_visible_attachment = fields.Char("历史可见附件", readonly=True)
    project_id = fields.Many2one(related="bid_id.project_id", store=True, readonly=True)
    type = fields.Selection([("out", "支出"), ("return", "退回")], string="类型", required=True, default="out")
    date = fields.Date("单据日期", default=fields.Date.context_today)
    amount = fields.Monetary("金额", currency_field="currency_id", tracking=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    receipt_bank_account_id = fields.Many2one("res.partner.bank", string="收款账户")
    bank_account_id = fields.Many2one("res.partner.bank", string="付款账户")
    remark = fields.Char("备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "tender_guarantee_attachment_rel",
        "guarantee_id",
        "attachment_id",
        string="附件",
    )
    currency_id = fields.Many2one(
        "res.currency", related="bid_id.currency_id", store=True, readonly=True
    )
    deposit_status_display = fields.Char("状态", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_push_result = fields.Char("推送结果", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_kingdee_document_no = fields.Char("金蝶单据编号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_document_no = fields.Char("单据编号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_bid_project_title = fields.Char("投标项目名称", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_bid_project_name = fields.Char("投标项目", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_engineering_project_name = fields.Char("工程项目", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_type_display = fields.Char("保证金类型", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_company_name = fields.Char("所属公司", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_amount_display = fields.Char("保证金金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_return_date = fields.Char("退回日期", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_return_amount = fields.Char("退回金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_return_project = fields.Char("退回项目", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_return_document_no = fields.Char("退回单编号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_return_account = fields.Char("退回账户", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_project_name = fields.Char("项目名称", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_transfer_unit = fields.Char("转款单位", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_remittance_method = fields.Char("汇款方式", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_receipt_account_name = fields.Char("收款账户名称", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_received_amount_display = fields.Char("已退保证金金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_receipt_document_no = fields.Char("收保证金单号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_unit_name = fields.Char("单位", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_refund_amount = fields.Char("退还金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_receipt_account_no = fields.Char("收款账号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_receipt_bank_name = fields.Char("收款开户行", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_refund_account_no = fields.Char("退还账号", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_refund_bank_name = fields.Char("退还开户行", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_returned_amount_display = fields.Char("已退金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_unreturned_amount_display = fields.Char("未退金额", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_need_return_text = fields.Char("是否需要退回", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_payee_unit = fields.Char("收款单位", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_payment_account = fields.Char("支付账户", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_note_display = fields.Char("备注", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_attachment_text = fields.Char("附件", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_source_created_by = fields.Char("录入人", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)
    deposit_source_created_at = fields.Char("录入时间", compute="_compute_deposit_return_visible_fields", store=True, readonly=True)

    def _deposit_return_payload_by_id(self):
        payload_by_id = {}
        ids = [record.id for record in self if record.id]
        if not ids:
            return payload_by_id
        try:
            self.env.cr.execute("SELECT to_regclass('public.sc_p1_legacy_visible_alias_payload')")
            exists = self.env.cr.fetchone()
            if not exists or not exists[0]:
                return payload_by_id
            self.env.cr.execute(
                """
                SELECT res_id, payload
                  FROM sc_p1_legacy_visible_alias_payload
                 WHERE model = %s AND res_id = ANY(%s)
                """,
                [self._name, ids],
            )
            for res_id, payload in self.env.cr.fetchall():
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except ValueError:
                        payload = {}
                payload_by_id[int(res_id)] = payload if isinstance(payload, dict) else {}
        except Exception:
            return payload_by_id
        return payload_by_id

    @staticmethod
    def _deposit_return_payload_value(payload, label):
        value = payload.get(label) if isinstance(payload, dict) else ""
        return "" if value is None else str(value)

    @staticmethod
    def _deposit_return_state_label(value):
        labels = {
            "-1": "已作废",
            "0": "未审核",
            "1": "审核中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
            "draft": "草稿",
            "confirmed": "已确认",
            "cancel": "已取消",
        }
        return labels.get(str(value or ""), str(value or ""))

    @staticmethod
    def _deposit_return_amount_text(value):
        if value in (False, None, ""):
            return ""
        if float(value).is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def _deposit_return_clean_note(value):
        note = str(value or "").strip()
        if not note:
            return ""
        if note.startswith("历史投标保证金"):
            return ""
        if "old_id=" in note and "; " in note:
            suffix = note.rsplit("; ", 1)[-1].strip()
            return suffix if suffix and "old_id=" not in suffix else note
        return note

    def _deposit_return_attachment_text(self, payload_value):
        value = str(payload_value or self.legacy_visible_attachment or "").strip()
        if value:
            compact = value.replace("-", "").replace("_", "")
            if len(compact) == 32 and compact.isalnum():
                return "附件(1)"
            return value
        count = len(self.attachment_ids)
        return "附件(%s)" % count if count else ""

    @api.depends(
        "legacy_visible_document_state",
        "legacy_visible_document_no",
        "legacy_visible_project_name",
        "legacy_visible_creator_name",
        "legacy_visible_created_time",
        "legacy_visible_attachment",
        "project_id",
        "type",
        "amount",
        "state",
        "receipt_bank_account_id",
        "receipt_bank_account_id.partner_id",
        "bank_account_id",
        "remark",
        "attachment_ids",
    )
    def _compute_deposit_return_visible_fields(self):
        payload_by_id = self._deposit_return_payload_by_id()
        type_labels = dict(self._fields["type"].selection)
        for record in self:
            payload = payload_by_id.get(record.id, {})
            value = lambda label: record._deposit_return_payload_value(payload, label)
            project_name = record.legacy_visible_project_name or record.project_id.display_name or ""
            status = value("状态") or record._deposit_return_state_label(record.legacy_visible_document_state or record.state)
            payment_account = value("支付账户") or record.bank_account_id.acc_number or ""
            payee_unit = value("收款单位") or record.receipt_bank_account_id.partner_id.display_name or ""
            created_at = value("录入时间")
            if not created_at and record.legacy_visible_created_time:
                created_at = fields.Datetime.to_string(record.legacy_visible_created_time)
            record.deposit_status_display = status
            record.deposit_push_result = value("推送结果")
            record.deposit_kingdee_document_no = value("金蝶单据编号")
            record.deposit_document_no = value("单据编号") or record.legacy_visible_document_no or ""
            record.deposit_bid_project_title = value("投标项目名称") or project_name
            record.deposit_bid_project_name = value("投标项目") or project_name
            record.deposit_engineering_project_name = value("工程项目") or project_name
            record.deposit_type_display = value("保证金类型") or type_labels.get(record.type, "") or ""
            record.deposit_company_name = value("所属公司")
            record.deposit_amount_display = value("保证金金额") or record._deposit_return_amount_text(record.amount)
            record.deposit_return_date = value("退回日期")
            record.deposit_return_amount = value("退回金额")
            record.deposit_return_project = value("退回项目")
            record.deposit_return_document_no = value("退回单编号")
            record.deposit_return_account = value("退回账户")
            record.deposit_project_name = value("项目名称") or project_name
            record.deposit_transfer_unit = value("转款单位")
            record.deposit_remittance_method = value("汇款方式")
            record.deposit_receipt_account_name = value("收款账户名称")
            record.deposit_received_amount_display = value("已退保证金金额")
            record.deposit_receipt_document_no = value("收保证金单号")
            record.deposit_unit_name = value("单位")
            record.deposit_refund_amount = value("退还金额")
            record.deposit_receipt_account_no = value("收款账号")
            record.deposit_receipt_bank_name = value("收款开户行")
            record.deposit_refund_account_no = value("退还账号")
            record.deposit_refund_bank_name = value("退还开户行")
            record.deposit_returned_amount_display = value("已退金额")
            record.deposit_unreturned_amount_display = value("未退金额")
            record.deposit_need_return_text = value("是否需要退回")
            record.deposit_payee_unit = payee_unit
            record.deposit_payment_account = payment_account
            record.deposit_note_display = value("备注") or record._deposit_return_clean_note(record.remark)
            record.deposit_attachment_text = record._deposit_return_attachment_text(value("附件"))
            record.deposit_source_created_by = value("录入人") or record.legacy_visible_creator_name or ""
            record.deposit_source_created_at = created_at

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "bid_id" in fields_list and not res.get("bid_id"):
            project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
            try:
                project_id = int(project_id) if project_id else False
            except (TypeError, ValueError):
                project_id = False
            if project_id:
                bid = self.env["tender.bid"].search([("project_id", "=", project_id)], order="id desc", limit=1)
                if bid:
                    res["bid_id"] = bid.id
        return res

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True
