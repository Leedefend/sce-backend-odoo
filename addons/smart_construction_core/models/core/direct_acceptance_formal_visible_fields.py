# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


def _parse_legacy_amount(value):
    text = str(value or "").replace(",", "").replace("￥", "").replace("¥", "").strip()
    if not text:
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0))


def _normalize_legacy_settlement_state(value):
    text = str(value or "").strip()
    if text == "已结算":
        return "settled"
    if text == "未结算":
        return "unsettled"
    return "unknown" if text else False


def _add_legacy_visible_fields(namespace):
    namespace["legacy_acceptance_label"] = fields.Char(string="验收菜单", readonly=True, index=True)
    namespace["legacy_acceptance_sort_id"] = fields.Integer(string="验收排序锚点", readonly=True, index=True)
    for index in range(1, 61):
        namespace[f"legacy_visible_{index:02d}"] = fields.Char(
            string=f"历史验收可见字段{index:02d}",
            readonly=True,
        )


class ProjectMaterialPlanDirectAcceptanceVisible(models.Model):
    _inherit = "project.material.plan"

    _add_legacy_visible_fields(locals())


class MaterialRfqDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rfq"

    _add_legacy_visible_fields(locals())


class MaterialInboundDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.inbound"

    _add_legacy_visible_fields(locals())


class LaborUsageDirectAcceptanceVisible(models.Model):
    _inherit = "sc.labor.usage"

    _add_legacy_visible_fields(locals())
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    legacy_settlement_status = fields.Char(
        string="旧系统结算状态",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
        index=True,
    )
    legacy_settlement_state = fields.Selection(
        [("settled", "已结算"), ("unsettled", "未结算"), ("unknown", "未识别")],
        string="旧系统结算状态分类",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
        index=True,
    )
    legacy_settlement_amount = fields.Monetary(
        string="旧系统结算金额",
        currency_field="currency_id",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
    )

    @api.depends("legacy_fact_type", "legacy_visible_08", "legacy_visible_09", "legacy_visible_12")
    def _compute_legacy_labor_settlement_fields(self):
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:方单":
                status = record.legacy_visible_08
                amount = record.legacy_visible_09
            elif record.legacy_fact_type == "direct_acceptance:零星用工":
                status = record.legacy_visible_12
                amount = record.legacy_visible_09
            else:
                status = False
                amount = False
            record.legacy_settlement_status = status or False
            record.legacy_settlement_state = _normalize_legacy_settlement_state(status)
            record.legacy_settlement_amount = _parse_legacy_amount(amount)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_labor_usage
               SET currency_id = %s
             WHERE currency_id IS NULL
            """,
            (self.env.company.currency_id.id,),
        )
        self.env.cr.execute(
            """
            UPDATE sc_labor_usage usage
               SET legacy_settlement_status = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:方单' THEN NULLIF(legacy_visible_08, '')
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' THEN NULLIF(legacy_visible_12, '')
                       ELSE NULL
                   END,
                   legacy_settlement_state = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND legacy_visible_08 = '已结算' THEN 'settled'
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND legacy_visible_08 = '未结算' THEN 'unsettled'
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND COALESCE(legacy_visible_08, '') != '' THEN 'unknown'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND legacy_visible_12 = '已结算' THEN 'settled'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND legacy_visible_12 = '未结算' THEN 'unsettled'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND COALESCE(legacy_visible_12, '') != '' THEN 'unknown'
                       ELSE NULL
                   END,
                   legacy_settlement_amount = CASE
                       WHEN regexp_replace(
                                COALESCE(
                                    CASE
                                        WHEN legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
                                        THEN legacy_visible_09
                                        ELSE NULL
                                    END,
                                    ''
                                ),
                                '[^0-9\\.-]',
                                '',
                                'g'
                            ) ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace(legacy_visible_09, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE 0.0
                   END
             WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
            """
        )


class SubcontractRequestDirectAcceptanceVisible(models.Model):
    _inherit = "sc.subcontract.request"

    _add_legacy_visible_fields(locals())


class EquipmentUsageDirectAcceptanceVisible(models.Model):
    _inherit = "sc.equipment.usage"

    _add_legacy_visible_fields(locals())


class MaterialRentalOrderDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rental.order"

    _add_legacy_visible_fields(locals())


class HrPayrollDocumentDirectAcceptanceVisible(models.Model):
    _inherit = "sc.hr.payroll.document"

    _add_legacy_visible_fields(locals())


class FundAccountOperationDirectAcceptanceVisible(models.Model):
    _inherit = "sc.fund.account.operation"

    _add_legacy_visible_fields(locals())


class ReceiptIncomeDirectAcceptanceVisible(models.Model):
    _inherit = "sc.receipt.income"

    _add_legacy_visible_fields(locals())


class InvoiceRegistrationDirectAcceptanceVisible(models.Model):
    _inherit = "sc.invoice.registration"

    _add_legacy_visible_fields(locals())


class ConstructionContractDirectAcceptanceVisible(models.Model):
    _inherit = "construction.contract"

    _add_legacy_visible_fields(locals())


class ConstructionContractExpenseDirectAcceptanceVisible(models.Model):
    _inherit = "construction.contract.expense"

    _add_legacy_visible_fields(locals())


class ConstructionDiaryDirectAcceptanceVisible(models.Model):
    _inherit = "sc.construction.diary"

    _add_legacy_visible_fields(locals())


class SettlementOrderDirectAcceptanceVisible(models.Model):
    _inherit = "sc.settlement.order"

    _add_legacy_visible_fields(locals())

    user_acceptance_document_state = fields.Char(string="用户验收单据状态", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_document_no = fields.Char(string="用户验收单据编号", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_project_name = fields.Char(string="用户验收项目名称", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_document_date = fields.Char(string="用户验收单据日期", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_title = fields.Char(string="用户验收标题/结算内容", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_partner_name = fields.Char(string="用户验收结算单位", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_amount = fields.Char(string="用户验收结算金额", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_payment_state = fields.Char(string="用户验收付款状态", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_paid_amount = fields.Char(string="用户验收已付款金额", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_unpaid_amount = fields.Char(string="用户验收未付款金额", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_request_state = fields.Char(string="用户验收支付申请状态", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_requested_amount = fields.Char(string="用户验收已申请金额", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_unrequested_amount = fields.Char(string="用户验收未申请金额", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_note = fields.Char(string="用户验收结算说明/备注", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_attachment = fields.Char(string="用户验收附件", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_creator = fields.Char(string="用户验收录入人", compute="_compute_user_acceptance_settlement_visible", readonly=True)
    user_acceptance_created_at = fields.Char(string="用户验收录入时间", compute="_compute_user_acceptance_settlement_visible", readonly=True)

    def _compute_user_acceptance_settlement_visible(self):
        def v(record, index):
            return getattr(record, "legacy_visible_%02d" % index, False) or False

        maps = {
            "材料结算单": {
                "document_state": 1,
                "project_name": 2,
                "document_no": 3,
                "title": 4,
                "partner_name": 5,
                "document_date": 6,
                "amount": 7,
                "payment_state": 8,
                "paid_amount": 9,
                "unpaid_amount": 10,
                "request_state": 11,
                "requested_amount": 12,
                "unrequested_amount": 13,
                "note": 14,
                "attachment": 15,
                "creator": 16,
                "created_at": 17,
            },
            "劳务结算": {
                "document_state": 1,
                "document_no": 2,
                "project_name": 3,
                "document_date": 4,
                "title": 5,
                "partner_name": 6,
                "amount": 7,
                "payment_state": 8,
                "paid_amount": 9,
                "unpaid_amount": 10,
                "request_state": 11,
                "requested_amount": 12,
                "unrequested_amount": 13,
                "note": 14,
                "attachment": 15,
                "creator": 16,
                "created_at": 17,
            },
            "分包结算单": {
                "document_state": 1,
                "project_name": 2,
                "document_no": 3,
                "title": 4,
                "partner_name": 5,
                "amount": 6,
                "payment_state": 7,
                "paid_amount": 8,
                "unpaid_amount": 9,
                "request_state": 10,
                "requested_amount": 11,
                "unrequested_amount": 12,
                "document_date": 16,
                "note": 17,
                "attachment": 18,
                "creator": 19,
                "created_at": 20,
            },
            "机械结算单": {
                "document_state": 1,
                "document_no": 2,
                "project_name": 3,
                "document_date": 4,
                "partner_name": 5,
                "title": 6,
                "amount": 7,
                "payment_state": 8,
                "paid_amount": 9,
                "unpaid_amount": 10,
                "request_state": 11,
                "requested_amount": 12,
                "unrequested_amount": 13,
                "attachment": 14,
                "creator": 15,
                "created_at": 16,
            },
            "租赁结算单": {
                "document_state": 1,
                "document_no": 2,
                "project_name": 3,
                "document_date": 4,
                "partner_name": 5,
                "title": 6,
                "amount": 7,
                "payment_state": 8,
                "paid_amount": 9,
                "unpaid_amount": 10,
                "request_state": 11,
                "requested_amount": 12,
                "unrequested_amount": 13,
                "attachment": 14,
                "creator": 15,
                "created_at": 16,
            },
            "工程结算单": {
                "document_state": 1,
                "document_no": 2,
                "document_date": 3,
                "project_name": 4,
                "amount": 7,
                "title": 8,
                "partner_name": 9,
                "note": 13,
                "attachment": 16,
                "creator": 17,
                "created_at": 18,
            },
        }
        field_names = [
            "document_state",
            "document_no",
            "project_name",
            "document_date",
            "title",
            "partner_name",
            "amount",
            "payment_state",
            "paid_amount",
            "unpaid_amount",
            "request_state",
            "requested_amount",
            "unrequested_amount",
            "note",
            "attachment",
            "creator",
            "created_at",
        ]
        for record in self:
            mapping = maps.get(record.legacy_acceptance_label or "", {})
            for name in field_names:
                setattr(record, "user_acceptance_" + name, v(record, mapping.get(name)) if mapping.get(name) else False)
