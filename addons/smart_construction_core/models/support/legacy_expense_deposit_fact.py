# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


_RAW_LEGACY_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")

_SOURCE_FAMILY_LABELS = {
    "company_financial_outflow": "公司财务支出",
    "expense_reimbursement": "费用报销",
    "pay_guarantee_deposit": "付款保证金缴纳",
    "pay_guarantee_deposit_refund": "付款保证金退回",
    "received_guarantee_deposit_register": "收取保证金登记",
    "received_guarantee_deposit_refund": "收取保证金退回",
}

_AMOUNT_FIELD_LABELS = {
    "BZJJE": "保证金金额",
    "FKJE": "付款金额",
    "THJE": "退回金额",
    "JE": "金额",
}


class ScLegacyExpenseDepositFact(models.Model):
    _name = "sc.legacy.expense.deposit.fact"
    _description = "历史费用/保证金事实"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="历史PID", index=True)
    source_family = fields.Char(string="来源类型", index=True)
    direction = fields.Selection(
        selection=[
            ("outflow", "流出"),
            ("inflow", "流入"),
            ("inflow_or_refund", "流入或退回"),
        ],
        string="收支方向",
        index=True,
    )
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    legacy_state = fields.Char(string="历史状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(string="历史项目ID", index=True)
    legacy_project_name = fields.Char(string="历史项目名称")
    legacy_tender_project_name = fields.Char(string="历史投标项目名称", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_partner_id = fields.Char(string="历史往来单位ID", index=True)
    legacy_partner_name = fields.Char(string="历史往来单位名称")
    source_amount = fields.Float(string="金额")
    source_amount_field = fields.Char(string="金额来源字段", index=True)
    source_amount_field_label = fields.Char(string="金额口径", compute="_compute_business_labels", store=True, index=True)
    source_family_label = fields.Char(string="业务类型", compute="_compute_business_labels", store=True, index=True)
    project_display_name = fields.Char(string="项目名称", compute="_compute_business_labels", store=True, index=True)
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", required=True, index=True)

    @api.depends(
        "source_family",
        "source_amount_field",
        "legacy_project_name",
        "project_id",
        "project_id.name",
    )
    def _compute_business_labels(self):
        for rec in self:
            source_family = (rec.source_family or "").strip()
            amount_field = (rec.source_amount_field or "").strip()
            project_name = (rec.legacy_project_name or rec.project_id.display_name or "").strip()
            if _RAW_LEGACY_ID_RE.match(project_name):
                project_name = f"历史未归档项目 {project_name}"
            rec.source_family_label = _SOURCE_FAMILY_LABELS.get(source_family, source_family)
            rec.source_amount_field_label = _AMOUNT_FIELD_LABELS.get(amount_field, amount_field)
            rec.project_display_name = project_name
