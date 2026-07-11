# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo import api, fields, models


_PAYMENT_FAMILY_LABELS = {
    "tax_certificate_registration": "外经证登记",
}
_BUSINESS_CATEGORY_LABELS = {
    "tax.certificate.registration": "外经证登记",
}


class ScLegacyPaymentResidualFact(models.Model):
    _name = "sc.legacy.payment.residual.fact"
    _description = "历史付款残留事实"
    _order = "document_date desc, source_table, legacy_record_id"

    source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="历史父单ID", index=True)
    residual_reason = fields.Char(string="残差原因", index=True)
    payment_family = fields.Char(string="业务类型", index=True)
    payment_family_label = fields.Char(string="业务类型", compute="_compute_payment_family_label")
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    document_state = fields.Char(string="原始单据状态", index=True)
    document_state_label = fields.Char(string="单据状态", compute="_compute_document_state_label")
    deleted_flag = fields.Char(string="删除标记", index=True)
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    taxpayer_name = fields.Char(string="纳税人名称", index=True)
    taxpayer_identifier = fields.Char(string="纳税人识别号", index=True)
    partner_legacy_id = fields.Char(string="历史往来单位ID", index=True)
    partner_name = fields.Char(string="合同相对方名称", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    counterparty_tax_identifier = fields.Char(string="合同相对方纳税人识别号", index=True)
    contract_legacy_id = fields.Char(string="历史合同ID", index=True)
    contract_no = fields.Char(string="合同编号", index=True)
    contract_name = fields.Char(string="合同名称", index=True)
    contract_start_date = fields.Date(string="合同开始日期", index=True)
    contract_end_date = fields.Date(string="合同结束日期", index=True)
    request_legacy_id = fields.Char(string="历史申请单ID", index=True)
    planned_amount = fields.Float(string="合同金额")
    paid_amount = fields.Float(string="已付金额")
    invoice_amount = fields.Float(string="发票金额")
    payment_method = fields.Char(string="经营方式", index=True)
    bank_account = fields.Char(string="银行账号", index=True)
    handler_name = fields.Char(string="经办人", index=True)
    handler_phone = fields.Char(string="经办人联系电话", index=True)
    regional_tax_contact = fields.Char(string="区域所属税所联系人", index=True)
    regional_tax_contact_phone = fields.Char(string="区域所属税所联系人手机", index=True)
    operation_address = fields.Char(string="跨区域经营地址", index=True)
    tax_report_management_no = fields.Char(string="跨区域涉税事项报验管理编号", index=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True)
    creator_name = fields.Char(string="录入人", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="历史附件ID")
    attachment_links = fields.Char(string="历史附件链接", compute="_compute_attachment_links")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_legacy_payment_residual_fact_attachment_rel",
        "fact_id",
        "attachment_id",
        string="附件",
    )
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    def _compute_document_state_label(self):
        labels = {
            "0": "草稿",
            "1": "审批中",
            "2": "审核通过",
            "3": "已驳回",
            "4": "已作废",
            "5": "已关闭",
        }
        for rec in self:
            state = (rec.document_state or "").strip()
            rec.document_state_label = labels.get(state, state)

    @api.depends("payment_family")
    @api.depends_context(
        "current_business_category_code",
        "current_business_category_label",
        "default_business_category_code",
        "default_business_category_label",
        "default_payment_family",
    )
    def _compute_payment_family_label(self):
        context = self.env.context or {}
        context_label = (
            context.get("current_business_category_label")
            or context.get("default_business_category_label")
            or _BUSINESS_CATEGORY_LABELS.get(context.get("current_business_category_code"))
            or _BUSINESS_CATEGORY_LABELS.get(context.get("default_business_category_code"))
            or _PAYMENT_FAMILY_LABELS.get(context.get("default_payment_family"))
            or ""
        )
        for rec in self:
            payment_family = (rec.payment_family or "").strip()
            rec.payment_family_label = _PAYMENT_FAMILY_LABELS.get(payment_family, payment_family) or context_label

    def _compute_attachment_links(self):
        FileIndex = self.env["sc.legacy.file.index"].sudo() if "sc.legacy.file.index" in self.env else None
        for rec in self:
            attachment_ref = (rec.attachment_ref or "").strip()
            if not attachment_ref or FileIndex is None:
                rec.attachment_links = "历史附件 | legacy-file-id://%s" % attachment_ref if attachment_ref else False
                continue
            files = FileIndex.search([
                ("active", "=", True),
                ("bill_id", "=", attachment_ref),
            ], order="upload_time, id")
            if not files:
                rec.attachment_links = f"历史附件 | legacy-file-id://{attachment_ref}"
                continue
            lines = []
            seen = set()
            for item in files:
                name = (item.file_name or item.display_name or item.legacy_file_id or "").strip()
                path = (item.file_path or item.preview_path or "").strip()
                url = "legacy-file://" + path.lstrip("/") if path else "legacy-file-id://" + str(item.legacy_file_id or item.id).strip()
                key = (name, url)
                if not name or key in seen:
                    continue
                seen.add(key)
                lines.append(f"{name} | {url}")
            rec.attachment_links = " ".join(lines) if lines else attachment_ref

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            context = self.env.context or {}
            payment_family = vals.get("payment_family") or context.get("default_payment_family")
            if payment_family:
                vals["payment_family"] = payment_family
            if not vals.get("source_table"):
                vals["source_table"] = context.get("default_source_table") or "USER_ENTRY"
            if not vals.get("legacy_record_id"):
                vals["legacy_record_id"] = context.get("default_legacy_record_id") or "USER-%s" % uuid4().hex
        return super().create(vals_list)

    _sql_constraints = [
        (
            "legacy_payment_residual_unique",
            "unique(source_table, legacy_record_id)",
            "历史付款残留来源记录必须唯一。",
        ),
    ]
