# -*- coding: utf-8 -*-
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

    _sql_constraints = [
        ("legacy_tender_bid_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用投标事实已迁移为投标记录。"),
    ]

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
    receipt_partner_name = fields.Char("收款单位", index=True)
    receipt_payee_name = fields.Char("收款人", index=True)
    receipt_bank_name = fields.Char("开户银行", index=True)
    receipt_bank_account = fields.Char("收款账户", index=True)
    remark = fields.Text("备注")
    legacy_visible_applicant_name = fields.Char("历史申请人", readonly=True)
    legacy_visible_document_state = fields.Char("历史单据状态", readonly=True)
    legacy_source_created_by = fields.Char("录入人", index=True)
    legacy_source_created_at = fields.Datetime("录入时间", index=True)
    legacy_record_id = fields.Char("旧系统记录ID", index=True)
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

    def action_submit(self):
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
