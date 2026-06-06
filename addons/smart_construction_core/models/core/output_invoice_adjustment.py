# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScOutputInvoiceAdjustment(models.Model):
    _name = "sc.output.invoice.adjustment"
    _description = "销项变更登记"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "adjustment_date desc, id desc"

    name = fields.Char(string="变更单号", required=True, default="新建", copy=False, tracking=True)
    adjustment_type = fields.Selection(
        [("red_flush", "红冲")],
        string="变更类型",
        default="red_flush",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [("draft", "草稿"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    adjustment_date = fields.Date(string="变更日期", default=fields.Date.context_today, required=True, index=True)
    original_ledger_id = fields.Many2one(
        "sc.output.invoice.ledger",
        string="需红冲销项票",
        required=True,
        domain=[("active", "=", True), ("adjustment_kind", "=", "normal")],
        ondelete="restrict",
        tracking=True,
    )
    generated_invoice_id = fields.Many2one(
        "sc.invoice.registration",
        string="生成红冲销项票",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True, index=True)
    contract_id = fields.Many2one("construction.contract", string="合同", readonly=True, index=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    original_source_model = fields.Selection(
        [
            ("sc.receipt.invoice.line", "收款发票明细"),
            ("sc.invoice.registration", "销项冲抵/红冲"),
        ],
        string="原票来源模型",
        readonly=True,
        index=True,
    )
    original_source_record_id = fields.Integer(string="原票来源ID", readonly=True, index=True)
    invoice_no = fields.Char(string="原发票号码", readonly=True, index=True)
    red_flush_invoice_no = fields.Char(string="红冲发票号码", index=True)
    invoice_issue_company = fields.Char(string="开票单位", readonly=True, index=True)
    invoice_party_name = fields.Char(string="开票抬头", readonly=True)
    original_invoice_amount = fields.Monetary(string="原发票金额", currency_field="currency_id", readonly=True)
    original_amount_no_tax = fields.Monetary(string="原不含税金额", currency_field="currency_id", readonly=True)
    original_tax_amount = fields.Monetary(string="原税额", currency_field="currency_id", readonly=True)
    original_surcharge_amount = fields.Monetary(string="原附加税", currency_field="currency_id", readonly=True)
    red_flush_invoice_amount = fields.Monetary(
        string="红冲价税合计",
        currency_field="currency_id",
        compute="_compute_red_flush_amounts",
        store=True,
    )
    red_flush_amount_no_tax = fields.Monetary(
        string="红冲不含税金额",
        currency_field="currency_id",
        compute="_compute_red_flush_amounts",
        store=True,
    )
    red_flush_tax_amount = fields.Monetary(
        string="红冲税额",
        currency_field="currency_id",
        compute="_compute_red_flush_amounts",
        store=True,
    )
    red_flush_surcharge_amount = fields.Monetary(
        string="红冲附加税",
        currency_field="currency_id",
        compute="_compute_red_flush_amounts",
        store=True,
    )
    reason = fields.Text(string="红冲原因")
    note = fields.Text(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.output.invoice.adjustment") or _("销项变更登记")
        records = super().create(vals_list)
        records._sync_original_invoice_snapshot()
        return records

    def write(self, vals):
        if any(rec.state == "confirmed" for rec in self) and set(vals) - {"note", "message_follower_ids"}:
            raise UserError(_("已确认的销项变更登记不能修改。"))
        res = super().write(vals)
        if "original_ledger_id" in vals:
            self._sync_original_invoice_snapshot()
        return res

    @api.onchange("original_ledger_id")
    def _onchange_original_ledger_id(self):
        self._sync_original_invoice_snapshot()

    @api.depends(
        "original_invoice_amount",
        "original_amount_no_tax",
        "original_tax_amount",
        "original_surcharge_amount",
    )
    def _compute_red_flush_amounts(self):
        for rec in self:
            rec.red_flush_invoice_amount = rec._negative(rec.original_invoice_amount)
            rec.red_flush_amount_no_tax = rec._negative(rec.original_amount_no_tax or rec.original_invoice_amount)
            rec.red_flush_tax_amount = rec._negative(rec.original_tax_amount)
            rec.red_flush_surcharge_amount = rec._negative(rec.original_surcharge_amount)

    @api.model
    def _negative(self, amount):
        return -abs(amount or 0.0)

    def _sync_original_invoice_snapshot(self):
        for rec in self:
            ledger = rec.original_ledger_id
            if not ledger:
                continue
            source = rec._original_source_record(ledger)
            rec.project_id = ledger.project_id or getattr(source, "project_id", False)
            rec.partner_id = ledger.partner_id or getattr(source, "partner_id", False)
            rec.contract_id = ledger.contract_id or getattr(source, "contract_id", False)
            rec.currency_id = (
                ledger.currency_id
                or getattr(source, "currency_id", False)
                or rec.currency_id
                or self.env.company.currency_id
            )
            rec.original_source_model = ledger.source_model
            rec.original_source_record_id = ledger.source_record_id
            rec.invoice_no = ledger.invoice_no
            rec.red_flush_invoice_no = rec.red_flush_invoice_no or ledger.invoice_no
            rec.invoice_issue_company = ledger.invoice_issue_company
            rec.invoice_party_name = ledger.invoice_party_name
            rec.original_invoice_amount = ledger.invoice_amount
            rec.original_amount_no_tax = ledger.amount_no_tax
            rec.original_tax_amount = ledger.tax_amount
            rec.original_surcharge_amount = ledger.surcharge_amount

    def _original_source_record(self, ledger):
        if not ledger.source_model or not ledger.source_record_id:
            return self.env["sc.receipt.invoice.line"].browse()
        return self.env[ledger.source_model].browse(ledger.source_record_id)

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的销项变更登记可以确认。"))
            rec._sync_original_invoice_snapshot()
            rec._validate_red_flush_ready()
            generated = rec._create_red_flush_invoice_registration()
            rec.write({"generated_invoice_id": generated.id, "state": "confirmed"})

    def action_cancel(self):
        for rec in self:
            if rec.generated_invoice_id:
                raise UserError(_("已生成红冲销项票的变更登记不能取消。"))
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的销项变更登记可以取消。"))
            rec.state = "cancel"

    def _validate_red_flush_ready(self):
        self.ensure_one()
        if not self.original_ledger_id:
            raise UserError(_("请先选择需要红冲的销项票。"))
        if self.original_ledger_id.adjustment_kind != "normal":
            raise UserError(_("只能对正常开票记录做红冲，不能重复红冲红冲记录。"))
        if self.generated_invoice_id:
            raise UserError(_("该变更登记已经生成红冲销项票。"))
        if not (self.red_flush_invoice_no or "").strip():
            raise UserError(_("请填写红冲发票号码。"))
        if (self.red_flush_invoice_no or "").strip() == (self.invoice_no or "").strip():
            raise UserError(_("红冲发票号码不能与原发票号码相同。"))
        existing = self.search(
            [
                ("id", "!=", self.id),
                ("state", "=", "confirmed"),
                ("original_ledger_id", "=", self.original_ledger_id.id),
            ],
            limit=1,
        )
        if existing:
            raise UserError(_("该销项票已在变更登记 %s 中完成红冲。") % existing.display_name)
        if not self.project_id:
            raise UserError(_("原销项票缺少项目，不能生成红冲销项票。"))
        if not self.red_flush_invoice_amount:
            raise UserError(_("原销项票金额为 0，不能生成红冲销项票。"))

    def _create_red_flush_invoice_registration(self):
        self.ensure_one()
        note_parts = [
            _("由销项变更登记 %s 确认红冲自动生成。") % self.name,
            _("原票来源：%s#%s，原发票号码：%s。")
            % (self.original_source_model, self.original_source_record_id, self.invoice_no or ""),
        ]
        if self.reason:
            note_parts.append(_("红冲原因：%s") % self.reason)
        if self.note:
            note_parts.append(self.note)
        return self.env["sc.invoice.registration"].create(
            {
                "source_origin": "manual",
                "source_kind": "output_invoice_tax",
                "direction": "output",
                "state": "registered",
                "project_id": self.project_id.id,
                "partner_id": self.partner_id.id,
                "contract_id": self.contract_id.id,
                "document_no": self.name,
                "document_date": self.adjustment_date,
                "invoice_date": self.adjustment_date,
                "invoice_no": self.red_flush_invoice_no or self.invoice_no,
                "invoice_issue_company": self.invoice_issue_company,
                "amount_no_tax": self.red_flush_amount_no_tax,
                "tax_amount": self.red_flush_tax_amount,
                "amount_total": self.red_flush_invoice_amount,
                "surcharge_amount": self.red_flush_surcharge_amount,
                "currency_id": self.currency_id.id,
                "red_flush_adjustment_id": self.id,
                "red_flush_origin_source_model": self.original_source_model,
                "red_flush_origin_source_record_id": self.original_source_record_id,
                "red_flush_origin_invoice_no": self.invoice_no,
                "note": "\n".join(note_parts),
            }
        )
