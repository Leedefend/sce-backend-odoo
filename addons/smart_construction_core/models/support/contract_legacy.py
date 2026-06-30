# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ConstructionContractLegacy(models.Model):
    _inherit = "construction.contract"

    amount_untaxed = fields.Monetary(string="平台合同金额")
    legacy_contract_id = fields.Char(index=True)
    legacy_project_id = fields.Char(index=True)
    legacy_contract_no = fields.Char(string="合同编号", index=True)
    legacy_document_no = fields.Char(string="单据编号", index=True)
    legacy_external_contract_no = fields.Char(string="自编合同编号", index=True)
    legacy_status = fields.Char(string="单据状态编码", index=True)
    legacy_deleted_flag = fields.Char(string="历史删除标识", index=True)
    legacy_counterparty_text = fields.Char(string="发包人文本")
    legacy_income_surface_visible = fields.Boolean(string="收入合同台账可见", default=True, index=True)
    legacy_contract_amount = fields.Monetary(string="原系统合同金额", currency_field="currency_id")
    legacy_contract_amount_source = fields.Char(string="原系统金额来源字段", index=True)
    legacy_contract_amount_delta = fields.Monetary(
        string="口径差额",
        currency_field="currency_id",
        compute="_compute_legacy_contract_amount_delta",
        store=True,
    )
    visible_contract_amount = fields.Monetary(
        string="合同金额",
        currency_field="currency_id",
        compute="_compute_visible_contract_amount",
        store=True,
        help="用户原施工合同台账口径金额；历史数据优先取旧系统合同金额，新建数据回退平台合同明细金额。",
    )
    document_status = fields.Char(string="单据状态", compute="_compute_document_status")
    engineering_category_text = fields.Char(string="工程类别")
    affiliated_person = fields.Char(string="挂靠人")
    engineering_content = fields.Text(string="合同内容")
    contract_duration_text = fields.Text(string="合同工期")
    contract_payment_method_text = fields.Text(string="合同约定付款方式")
    entry_user_text = fields.Char(string="录入人")
    entry_time = fields.Datetime(string="录入时间")
    approval_info = fields.Text(string="审批信息")
    attachment_text = fields.Text(string="附件")
    visible_invoice_amount = fields.Monetary(string="累计开票", currency_field="currency_id")
    visible_received_amount = fields.Monetary(string="累计收款", currency_field="currency_id")
    visible_unreceived_amount = fields.Monetary(string="未收款", currency_field="currency_id")
    visible_unreceived_rate = fields.Char(string="未收款比例")
    visible_invoice_amount_source = fields.Char(string="累计开票来源字段", index=True)
    visible_received_amount_source = fields.Char(string="累计收款来源字段", index=True)
    visible_unreceived_amount_source = fields.Char(string="未收款来源字段", index=True)
    legacy_visible_document_state = fields.Char(string="历史可见单据状态", readonly=True)
    legacy_visible_document_no = fields.Char(string="历史可见单据编号", readonly=True)
    legacy_visible_contract_date = fields.Date(string="历史可见合同订立日期", readonly=True)
    legacy_visible_archived = fields.Char(string="历史可见原件是否归档", readonly=True)
    legacy_visible_counterparty = fields.Char(string="历史可见发包人", readonly=True)
    legacy_visible_contractor = fields.Char(string="历史可见承包人", readonly=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True)
    legacy_visible_title = fields.Char(string="历史可见合同标题", readonly=True)
    legacy_visible_category = fields.Char(string="历史可见工程类别", readonly=True)
    legacy_visible_contract_no = fields.Char(string="历史可见合同编号", readonly=True)
    legacy_visible_amount = fields.Char(string="历史可见合同金额", readonly=True)
    legacy_visible_settlement_amount = fields.Char(string="历史可见结算金额", readonly=True)
    legacy_visible_invoice_amount = fields.Char(string="历史可见累计开票", readonly=True)
    legacy_visible_invoice_unreceived_amount = fields.Char(string="历史可见开票未收款", readonly=True)
    legacy_visible_received_amount = fields.Char(string="历史可见累计收款", readonly=True)
    legacy_visible_unreceived_amount = fields.Char(string="历史可见未收款", readonly=True)
    legacy_visible_unreceived_rate = fields.Char(string="历史可见未收款比例", readonly=True)
    legacy_visible_affiliated_person = fields.Char(string="历史可见挂靠人", readonly=True)
    legacy_visible_engineering_address = fields.Char(string="历史可见工程地址", readonly=True)
    legacy_visible_engineering_content = fields.Text(string="历史可见合同内容", readonly=True)
    legacy_visible_contract_duration_days = fields.Char(string="历史可见合同工期天数", readonly=True)
    legacy_visible_creator_name = fields.Char(string="历史可见录入人", readonly=True)
    legacy_visible_created_time = fields.Datetime(string="历史可见录入时间", readonly=True)
    legacy_visible_attachment = fields.Text(string="历史可见附件", readonly=True)
    contract_unreceived_amount = fields.Monetary(
        string="平台未收款",
        currency_field="currency_id",
        compute="_compute_contract_receivable_amounts",
        compute_sudo=True,
    )
    contract_unreceived_rate = fields.Char(
        string="平台未收款比例",
        compute="_compute_contract_receivable_amounts",
        compute_sudo=True,
    )

    @api.depends("legacy_contract_amount", "amount_untaxed")
    def _compute_legacy_contract_amount_delta(self):
        for rec in self:
            rec.legacy_contract_amount_delta = (rec.legacy_contract_amount or 0.0) - (rec.amount_untaxed or 0.0)

    @api.depends("legacy_contract_amount", "amount_untaxed")
    def _compute_visible_contract_amount(self):
        for rec in self:
            rec.visible_contract_amount = rec.legacy_contract_amount or rec.amount_untaxed or 0.0

    @api.depends("legacy_status", "state")
    def _compute_document_status(self):
        status_map = {
            "0": "未提交",
            "1": "审核中",
            "2": "审核通过",
            "3": "审核驳回",
            "4": "已作废",
            "审核通过": "审核通过",
        }
        state_map = {
            "draft": "未提交",
            "confirmed": "审核通过",
            "running": "审核通过",
            "closed": "审核通过",
            "cancel": "已作废",
        }
        for rec in self:
            code = (rec.legacy_status or "").strip()
            rec.document_status = status_map.get(code) or state_map.get(rec.state) or code or ""

    @api.depends("visible_contract_amount", "received_amount")
    def _compute_contract_receivable_amounts(self):
        for rec in self:
            total = rec.visible_contract_amount or 0.0
            unreceived = total - (rec.received_amount or 0.0)
            rec.contract_unreceived_amount = unreceived
            if not total:
                rec.contract_unreceived_rate = ""
                continue
            rec.contract_unreceived_rate = f"{unreceived / total * 100:.2f}%"
