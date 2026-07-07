# -*- coding: utf-8 -*-
from datetime import date, datetime
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


def _parse_legacy_date(value):
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return False
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).date()
        except ValueError:
            continue
    return False


def _parse_legacy_datetime(value):
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    return False


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


def _lv(index):
    return "legacy" + "_visible_" + f"{index:02d}"


class ProjectMaterialPlanDirectAcceptanceVisible(models.Model):
    _inherit = "project.material.plan"

    _add_legacy_visible_fields(locals())
    material_plan_status_display = fields.Char(
        string="单据状态",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_document_no = fields.Char(
        string="单据编号",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_document_date = fields.Char(
        string="单据日期",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_arrival_date = fields.Char(
        string="到货时间",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_material_name = fields.Char(
        string="采购材料名称",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_specification = fields.Char(
        string="规格型号",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_unit = fields.Char(
        string="单位",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_quantity = fields.Char(
        string="数量",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_material_alias = fields.Char(
        string="材料别名(设计/清单)",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_note = fields.Char(
        string="备注",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_attachment_text = fields.Char(
        string="附件",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_project_name = fields.Char(
        string="项目名称",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )
    material_plan_source_created_at = fields.Char(
        string="录入时间",
        compute="_compute_material_plan_formal_visible_fields",
        store=True,
        readonly=True,
    )

    @api.depends(
        "state",
        "name",
        "date_plan",
        "material_name_summary",
        "material_spec_summary",
        "material_uom_summary",
        "total_plan_qty",
        "line_note_summary",
        "line_attachment_count",
        "attachment_ids",
        "project_id",
        "source_created_by",
        "source_created_at",
        _lv(1),
        _lv(2),
        _lv(3),
        _lv(4),
        _lv(5),
        _lv(6),
        _lv(7),
        _lv(8),
        _lv(9),
        _lv(10),
        _lv(11),
        _lv(12),
        _lv(13),
        _lv(14),
    )
    def _compute_material_plan_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            source_created_at = (
                fields.Datetime.to_string(record.source_created_at)
                if record.source_created_at
                else False
            )
            attachment_text = record[_lv(11)]
            if not attachment_text:
                attachment_count = len(record.attachment_ids) + (record.line_attachment_count or 0)
                attachment_text = "附件(%s)" % attachment_count if attachment_count else False

            record.material_plan_status_display = record[_lv(1)] or state_labels.get(record.state) or False
            record.material_plan_document_no = record[_lv(2)] or record.name or False
            record.material_plan_document_date = record[_lv(3)] or (
                record.date_plan.isoformat() if record.date_plan else False
            )
            record.material_plan_arrival_date = record[_lv(4)] or False
            record.material_plan_material_name = record[_lv(5)] or record.material_name_summary or False
            record.material_plan_specification = record[_lv(6)] or record.material_spec_summary or False
            record.material_plan_unit = record[_lv(7)] or record.material_uom_summary or False
            record.material_plan_quantity = record[_lv(8)] or (
                str(record.total_plan_qty) if record.total_plan_qty else False
            )
            record.material_plan_material_alias = record[_lv(9)] or False
            record.material_plan_note = record[_lv(10)] or record.line_note_summary or False
            record.material_plan_attachment_text = attachment_text
            record.material_plan_project_name = record[_lv(12)] or record.project_id.display_name or False
            record.material_plan_source_created_by = record[_lv(13)] or record.source_created_by or False
            record.material_plan_source_created_at = record[_lv(14)] or source_created_at or False


class MaterialRfqDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rfq"

    _add_legacy_visible_fields(locals())
    quote_status_display = fields.Char(string="单据状态", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_document_no = fields.Char(string="单据编号", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_supplier_name = fields.Char(string="供应商名称", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_inquiry_time = fields.Char(string="询价时间", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_material_name = fields.Char(string="材料名称", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_material_spec = fields.Char(string="规格型号", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_quantity_display = fields.Char(string="数量", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_tax_price_display = fields.Char(string="含税单价", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_tax_amount_display = fields.Char(string="含税总金额", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_total_quantity_display = fields.Char(string="总数量", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_total_amount_display = fields.Char(string="总金额", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_note_display = fields.Char(string="备注", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_contact_name = fields.Char(string="联系人", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_contact_phone = fields.Char(string="联系电话", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_attachment_text = fields.Char(string="附件", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_selected_text = fields.Char(string="是否中标", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_project_name = fields.Char(string="项目名称", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_source_created_by = fields.Char(string="录入人", compute="_compute_quote_visible_fields", store=True, readonly=True)
    quote_source_created_at = fields.Char(string="录入时间", compute="_compute_quote_visible_fields", store=True, readonly=True)

    @staticmethod
    def _quote_visible_number(value):
        if value in (None, False, ""):
            return ""
        return str(value)

    def _quote_visible_attachment_text(self):
        self.ensure_one()
        if self[_lv(15)]:
            return self[_lv(15)]
        if self._quote_uses_acceptance_surface():
            return ""
        count = len(self.attachment_ids)
        return "附件(%s)" % count if count else ""

    def _quote_uses_acceptance_surface(self):
        self.ensure_one()
        return bool(self.legacy_fact_model and self.legacy_fact_type)

    def _quote_visible_or_fallback(self, index, fallback):
        self.ensure_one()
        value = self[_lv(index)]
        if self._quote_uses_acceptance_surface():
            return value or ""
        return value or fallback or ""

    @api.depends(
        *[_lv(index) for index in range(1, 20)],
        "name",
        "state",
        "selected_supplier_id",
        "project_id",
        "rfq_date",
        "contact_name",
        "contact_phone",
        "attachment_ids",
        "source_created_by",
        "source_created_at",
        "line_ids.supplier_id",
        "line_ids.material_catalog_id",
        "line_ids.product_id",
        "line_ids.material_spec",
        "line_ids.qty",
        "line_ids.unit_price",
        "line_ids.amount",
        "line_ids.note",
        "line_ids.selected",
    )
    def _compute_quote_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            line = record.line_ids[:1]
            selected_line = record.line_ids.filtered("selected")[:1]
            supplier = record.selected_supplier_id or (selected_line.supplier_id if selected_line else False) or (line.supplier_id if line else False)
            material_name = ""
            if line:
                material_name = line.material_catalog_id.display_name or line.product_id.display_name or ""
            created_at = record[_lv(19)]
            if not created_at and record.source_created_at:
                created_at = fields.Datetime.to_string(record.source_created_at)
            if record._quote_uses_acceptance_surface() and not record[_lv(19)]:
                created_at = ""
            record.quote_status_display = record._quote_visible_or_fallback(1, state_labels.get(record.state, ""))
            record.quote_document_no = record._quote_visible_or_fallback(2, record.name)
            record.quote_supplier_name = record._quote_visible_or_fallback(3, supplier.display_name if supplier else "")
            record.quote_inquiry_time = record._quote_visible_or_fallback(4, fields.Date.to_string(record.rfq_date) if record.rfq_date else "")
            record.quote_material_name = record._quote_visible_or_fallback(5, material_name)
            record.quote_material_spec = record._quote_visible_or_fallback(6, line.material_spec if line else "")
            record.quote_quantity_display = record._quote_visible_or_fallback(7, record._quote_visible_number(line.qty) if line else "")
            record.quote_tax_price_display = record._quote_visible_or_fallback(8, record._quote_visible_number(line.unit_price) if line else "")
            record.quote_tax_amount_display = record._quote_visible_or_fallback(9, record._quote_visible_number(line.amount) if line else "")
            record.quote_total_quantity_display = record._quote_visible_or_fallback(10, record._quote_visible_number(sum(record.line_ids.mapped("qty"))))
            record.quote_total_amount_display = record._quote_visible_or_fallback(11, record._quote_visible_number(sum(record.line_ids.mapped("amount"))))
            record.quote_note_display = record._quote_visible_or_fallback(12, line.note if line else "")
            record.quote_contact_name = record._quote_visible_or_fallback(13, record.contact_name)
            record.quote_contact_phone = record._quote_visible_or_fallback(14, record.contact_phone)
            record.quote_attachment_text = record._quote_visible_attachment_text()
            record.quote_selected_text = record._quote_visible_or_fallback(16, "是" if selected_line else "")
            record.quote_project_name = record._quote_visible_or_fallback(17, record.project_id.display_name)
            record.quote_source_created_by = record._quote_visible_or_fallback(18, record.source_created_by)
            record.quote_source_created_at = created_at


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
        string="历史结算状态",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
        index=True,
    )
    legacy_settlement_state = fields.Selection(
        [("settled", "已结算"), ("unsettled", "未结算"), ("unknown", "未识别")],
        string="历史结算状态分类",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
        index=True,
    )
    legacy_settlement_amount = fields.Monetary(
        string="历史结算金额",
        currency_field="currency_id",
        compute="_compute_legacy_labor_settlement_fields",
        store=True,
        readonly=True,
    )
    document_date_text = fields.Char(
        string="单据日期",
        compute="_compute_formal_labor_usage_visible_fields",
        store=True,
        readonly=True,
    )
    construction_part = fields.Char(
        string="施工部位",
        compute="_compute_formal_labor_usage_visible_fields",
        store=True,
        readonly=True,
    )
    amount_total = fields.Monetary(
        string="总金额",
        currency_field="currency_id",
        compute="_compute_formal_labor_usage_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_status_display = fields.Char(
        string="单据状态",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_document_no = fields.Char(
        string="单据编号",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_project_name = fields.Char(
        string="项目名称",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_document_date = fields.Char(
        string="单据日期",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_title = fields.Char(
        string="标题",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_labor_team_name = fields.Char(
        string="劳务单位",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_work_type = fields.Char(
        string="工种",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_construction_part = fields.Char(
        string="施工部位",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_quantity = fields.Char(
        string="数量",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_price_unit = fields.Char(
        string="单价",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_amount = fields.Char(
        string="金额",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_work_content = fields.Char(
        string="工作内容",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_settlement_status = fields.Char(
        string="结算状态",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_note = fields.Char(
        string="备注",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_attachment_text = fields.Char(
        string="附件",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )
    labor_usage_source_created_at = fields.Char(
        string="录入时间",
        compute="_compute_labor_usage_formal_visible_fields",
        store=True,
        readonly=True,
    )

    @api.depends("legacy_fact_type", _lv(8), _lv(9), _lv(12))
    def _compute_legacy_labor_settlement_fields(self):
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:方单":
                status = record[_lv(8)]
                amount = record[_lv(9)]
            elif record.legacy_fact_type == "direct_acceptance:零星用工":
                status = record[_lv(12)]
                amount = record[_lv(9)]
            else:
                status = False
                amount = False
            record.legacy_settlement_status = status or False
            record.legacy_settlement_state = _normalize_legacy_settlement_state(status)
            record.legacy_settlement_amount = _parse_legacy_amount(amount)

    @api.depends("legacy_fact_type", _lv(4), _lv(9), _lv(10))
    def _compute_formal_labor_usage_visible_fields(self):
        for record in self:
            if record.legacy_fact_type in ("direct_acceptance:方单", "direct_acceptance:零星用工"):
                record.document_date_text = record[_lv(4)] or False
                record.construction_part = record[_lv(10)] or False
                record.amount_total = _parse_legacy_amount(record[_lv(9)])
            else:
                record.document_date_text = record.usage_date.isoformat() if record.usage_date else False
                record.construction_part = record.work_content or False
                record.amount_total = 0.0

    @api.depends(
        "legacy_fact_type",
        "state",
        "name",
        "project_id",
        "usage_date",
        "labor_team",
        "contractor_id",
        "work_content",
        "worker_qty",
        "work_hours",
        "amount_total",
        "note",
        "attachment_ids",
        "source_created_by",
        "source_created_at",
        _lv(1),
        _lv(2),
        _lv(3),
        _lv(4),
        _lv(5),
        _lv(6),
        _lv(7),
        _lv(8),
        _lv(9),
        _lv(10),
        _lv(11),
        _lv(12),
        _lv(13),
        _lv(14),
        _lv(15),
    )
    def _compute_labor_usage_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            source_created_at = (
                fields.Datetime.to_string(record.source_created_at)
                if record.source_created_at
                else False
            )
            attachment_text = record[_lv(11)] or (
                "附件(%s)" % len(record.attachment_ids) if record.attachment_ids else False
            )

            record.labor_usage_status_display = record[_lv(1)] or state_labels.get(record.state) or False
            record.labor_usage_document_no = record[_lv(2)] or record.name or False
            record.labor_usage_project_name = record[_lv(3)] or record.project_id.display_name or False
            record.labor_usage_document_date = record[_lv(4)] or (
                record.usage_date.isoformat() if record.usage_date else False
            )
            record.labor_usage_attachment_text = attachment_text

            if record.legacy_fact_type == "direct_acceptance:方单":
                record.labor_usage_title = record[_lv(5)] or record.work_content or False
                record.labor_usage_labor_team_name = (
                    record[_lv(6)] or record.contractor_id.display_name or record.labor_team or False
                )
                record.labor_usage_work_type = False
                record.labor_usage_construction_part = record[_lv(7)] or False
                record.labor_usage_quantity = False
                record.labor_usage_price_unit = False
                record.labor_usage_amount = record[_lv(9)] or (
                    str(record.amount_total) if record.amount_total else False
                )
                record.labor_usage_work_content = False
                record.labor_usage_settlement_status = record[_lv(8)] or False
                record.labor_usage_note = record[_lv(10)] or record.note or False
                record.labor_usage_source_created_by = record[_lv(12)] or record.source_created_by or False
                record.labor_usage_source_created_at = record[_lv(13)] or source_created_at or False
            elif record.legacy_fact_type == "direct_acceptance:零星用工":
                record.labor_usage_title = False
                record.labor_usage_labor_team_name = (
                    record[_lv(5)] or record.contractor_id.display_name or record.labor_team or False
                )
                record.labor_usage_work_type = record[_lv(6)] or record.work_content or False
                record.labor_usage_construction_part = False
                record.labor_usage_quantity = record[_lv(7)] or (
                    str(record.worker_qty) if record.worker_qty else False
                )
                record.labor_usage_price_unit = record[_lv(8)] or False
                record.labor_usage_amount = record[_lv(9)] or (
                    str(record.amount_total) if record.amount_total else False
                )
                record.labor_usage_work_content = record[_lv(10)] or record.work_content or False
                record.labor_usage_settlement_status = record[_lv(12)] or False
                record.labor_usage_note = record[_lv(13)] or record.note or False
                record.labor_usage_source_created_by = record[_lv(14)] or record.source_created_by or False
                record.labor_usage_source_created_at = record[_lv(15)] or source_created_at or False
            else:
                record.labor_usage_title = False
                record.labor_usage_labor_team_name = (
                    record.contractor_id.display_name or record.labor_team or False
                )
                record.labor_usage_work_type = record.work_content or False
                record.labor_usage_construction_part = False
                record.labor_usage_quantity = str(record.worker_qty) if record.worker_qty else False
                record.labor_usage_price_unit = False
                record.labor_usage_amount = str(record.amount_total) if record.amount_total else False
                record.labor_usage_work_content = record.work_content or False
                record.labor_usage_settlement_status = record.legacy_settlement_status or False
                record.labor_usage_note = record.note or False
                record.labor_usage_source_created_by = record.source_created_by or False
                record.labor_usage_source_created_at = source_created_at

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
                       WHEN legacy_fact_type = 'direct_acceptance:方单' THEN NULLIF({lv08}, '')
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' THEN NULLIF({lv12}, '')
                       ELSE NULL
                   END,
                   legacy_settlement_state = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND {lv08} = '已结算' THEN 'settled'
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND {lv08} = '未结算' THEN 'unsettled'
                       WHEN legacy_fact_type = 'direct_acceptance:方单' AND COALESCE({lv08}, '') != '' THEN 'unknown'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND {lv12} = '已结算' THEN 'settled'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND {lv12} = '未结算' THEN 'unsettled'
                       WHEN legacy_fact_type = 'direct_acceptance:零星用工' AND COALESCE({lv12}, '') != '' THEN 'unknown'
                       ELSE NULL
                   END,
                   legacy_settlement_amount = CASE
                       WHEN regexp_replace(
                                COALESCE(
                                    CASE
                                        WHEN legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
                                        THEN {lv09}
                                        ELSE NULL
                                    END,
                                    ''
                                ),
                                '[^0-9\\.-]',
                                '',
                                'g'
                            ) ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace({lv09}, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE 0.0
                   END
             WHERE legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
            """.format(lv08=_lv(8), lv09=_lv(9), lv12=_lv(12))
        )


class SubcontractRequestDirectAcceptanceVisible(models.Model):
    _inherit = "sc.subcontract.request"

    _add_legacy_visible_fields(locals())
    subcontract_request_status_display = fields.Char(
        string="单据状态",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_document_no = fields.Char(
        string="单据编号",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_project_name = fields.Char(
        string="项目名称",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_title = fields.Char(
        string="标题",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_subcontractor = fields.Char(
        string="分包商",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_type_display = fields.Char(
        string="分包类型",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_content = fields.Char(
        string="分包内容",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_quantity_display = fields.Char(
        string="数量",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_price_unit_display = fields.Char(
        string="单价",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_amount_display = fields.Char(
        string="金额",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_monthly_amount_display = fields.Char(
        string="本月合价",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_note_display = fields.Char(
        string="备注",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_attachment_text = fields.Char(
        string="附件",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )
    subcontract_request_source_created_at = fields.Char(
        string="录入时间",
        compute="_compute_subcontract_request_formal_visible_fields",
        store=True,
        readonly=True,
    )

    @api.depends(
        "legacy_fact_type",
        "state",
        "name",
        "project_id",
        "subcontract_scope",
        "suggested_subcontractor_id",
        "subcontract_type_text",
        "quantity_total",
        "price_unit",
        "amount_total",
        "monthly_amount_total",
        "note",
        "attachment_ids",
        *[_lv(index) for index in range(1, 16)],
    )
    def _compute_subcontract_request_formal_visible_fields(self):
        state_map = {
            "draft": "草稿",
            "submitted": "已提交",
            "approved": "已确认",
            "cancel": "已取消",
        }
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:分包方单":
                record.subcontract_request_status_display = record[_lv(1)] or False
                record.subcontract_request_document_no = record[_lv(2)] or False
                record.subcontract_request_project_name = record[_lv(3)] or False
                record.subcontract_request_title = record[_lv(4)] or False
                record.subcontract_request_subcontractor = record[_lv(5)] or False
                record.subcontract_request_type_display = record[_lv(6)] or False
                record.subcontract_request_content = record[_lv(7)] or False
                record.subcontract_request_quantity_display = record[_lv(8)] or False
                record.subcontract_request_price_unit_display = record[_lv(9)] or False
                record.subcontract_request_amount_display = record[_lv(10)] or False
                record.subcontract_request_monthly_amount_display = record[_lv(11)] or False
                record.subcontract_request_note_display = record[_lv(12)] or False
                record.subcontract_request_attachment_text = record[_lv(13)] or False
                record.subcontract_request_source_created_by = record[_lv(14)] or False
                record.subcontract_request_source_created_at = record[_lv(15)] or False
            else:
                record.subcontract_request_status_display = state_map.get(record.state, record.state or "")
                record.subcontract_request_document_no = record.name or False
                record.subcontract_request_project_name = record.project_id.display_name or False
                record.subcontract_request_title = record.subcontract_scope or False
                record.subcontract_request_subcontractor = record.suggested_subcontractor_id.display_name or False
                record.subcontract_request_type_display = record.subcontract_type_text or False
                record.subcontract_request_content = record.subcontract_scope or False
                record.subcontract_request_quantity_display = str(record.quantity_total or "") if record.quantity_total else ""
                record.subcontract_request_price_unit_display = str(record.price_unit or "") if record.price_unit else ""
                record.subcontract_request_amount_display = str(record.amount_total or "") if record.amount_total else ""
                record.subcontract_request_monthly_amount_display = (
                    str(record.monthly_amount_total or "") if record.monthly_amount_total else ""
                )
                record.subcontract_request_note_display = record.note or False
                record.subcontract_request_attachment_text = "附件(%s)" % len(record.attachment_ids) if record.attachment_ids else ""
                record.subcontract_request_source_created_by = record.applicant_id.name or False
                record.subcontract_request_source_created_at = fields.Datetime.to_string(record.create_date) if record.create_date else ""

    def init(self):
        super().init()
        visible_fields = {index: _lv(index) for index in range(1, 16)}
        self.env.cr.execute(
            f"""
            UPDATE sc_subcontract_request
               SET subcontract_request_status_display = NULLIF({visible_fields[1]}, ''),
                   subcontract_request_document_no = NULLIF({visible_fields[2]}, ''),
                   subcontract_request_project_name = NULLIF({visible_fields[3]}, ''),
                   subcontract_request_title = NULLIF({visible_fields[4]}, ''),
                   subcontract_request_subcontractor = NULLIF({visible_fields[5]}, ''),
                   subcontract_request_type_display = NULLIF({visible_fields[6]}, ''),
                   subcontract_request_content = NULLIF({visible_fields[7]}, ''),
                   subcontract_request_quantity_display = NULLIF({visible_fields[8]}, ''),
                   subcontract_request_price_unit_display = NULLIF({visible_fields[9]}, ''),
                   subcontract_request_amount_display = NULLIF({visible_fields[10]}, ''),
                   subcontract_request_monthly_amount_display = NULLIF({visible_fields[11]}, ''),
                   subcontract_request_note_display = NULLIF({visible_fields[12]}, ''),
                   subcontract_request_attachment_text = NULLIF({visible_fields[13]}, ''),
                   subcontract_request_source_created_by = NULLIF({visible_fields[14]}, ''),
                   subcontract_request_source_created_at = NULLIF({visible_fields[15]}, '')
             WHERE legacy_fact_type = 'direct_acceptance:分包方单'
            """
        )


class EquipmentUsageDirectAcceptanceVisible(models.Model):
    _inherit = "sc.equipment.usage"

    _add_legacy_visible_fields(locals())
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    document_date = fields.Date(
        string="单据日期",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    specification = fields.Char(
        string="规格型号",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    uom_text = fields.Char(
        string="单位",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    work_hours = fields.Float(
        string="工作时间",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    price_unit = fields.Monetary(
        string="单价",
        currency_field="currency_id",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(
        string="金额",
        currency_field="currency_id",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    former_supplier_name = fields.Char(
        string="曾用名单位",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_by = fields.Char(
        string="录入人",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_at = fields.Datetime(
        string="录入时间",
        compute="_compute_formal_equipment_usage_visible_fields",
        store=True,
        readonly=True,
    )

    @api.depends(
        "legacy_fact_type",
        "usage_date",
        "usage_hours",
        "recorder_id",
        "create_date",
        _lv(4),
        _lv(6),
        _lv(8),
        _lv(9),
        _lv(10),
        _lv(11),
        _lv(12),
        _lv(15),
        _lv(16),
    )
    def _compute_formal_equipment_usage_visible_fields(self):
        for record in self:
            if record.legacy_fact_type == "direct_acceptance:机械台班记录" or record.legacy_acceptance_label == "机械台班记录":
                record.document_date = _parse_legacy_date(record[_lv(4)]) or record.usage_date or False
                record.former_supplier_name = record[_lv(6)] or False
                record.specification = record[_lv(8)] or False
                record.uom_text = record[_lv(9)] or False
                record.work_hours = _parse_legacy_amount(record[_lv(10)])
                record.price_unit = _parse_legacy_amount(record[_lv(11)])
                record.amount = _parse_legacy_amount(record[_lv(12)])
                record.source_created_by = record[_lv(15)] or False
                record.source_created_at = _parse_legacy_datetime(record[_lv(16)])
            else:
                record.document_date = record.usage_date or False
                record.former_supplier_name = False
                record.specification = False
                record.uom_text = False
                record.work_hours = record.usage_hours or 0.0
                record.price_unit = 0.0
                record.amount = 0.0
                record.source_created_by = record.recorder_id.name or False
                record.source_created_at = record.create_date or False

    def init(self):
        lv4 = _lv(4)
        lv6 = _lv(6)
        lv8 = _lv(8)
        lv9 = _lv(9)
        lv10 = _lv(10)
        lv11 = _lv(11)
        lv12 = _lv(12)
        lv15 = _lv(15)
        lv16 = _lv(16)
        self.env.cr.execute(
            """
            UPDATE sc_equipment_usage
               SET currency_id = %s
             WHERE currency_id IS NULL
            """,
            (self.env.company.currency_id.id,),
        )
        self.env.cr.execute(
            f"""
            UPDATE sc_equipment_usage
               SET document_date = CASE
                       WHEN (legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录')
                            AND left(COALESCE({lv4}, ''), 10) ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'
                       THEN left({lv4}, 10)::date
                       ELSE usage_date
                   END,
                   specification = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录'
                       THEN NULLIF({lv8}, '')
                       ELSE NULL
                   END,
                   former_supplier_name = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录'
                       THEN NULLIF({lv6}, '')
                       ELSE NULL
                   END,
                   uom_text = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录'
                       THEN NULLIF({lv9}, '')
                       ELSE NULL
                   END,
                   work_hours = CASE
                       WHEN (legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录')
                            AND regexp_replace(COALESCE({lv10}, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace({lv10}, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE COALESCE(usage_hours, 0.0)
                   END,
                   price_unit = CASE
                       WHEN (legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录')
                            AND regexp_replace(COALESCE({lv11}, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace({lv11}, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE 0.0
                   END,
                   amount = CASE
                       WHEN (legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录')
                            AND regexp_replace(COALESCE({lv12}, ''), '[^0-9\\.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                       THEN regexp_replace({lv12}, '[^0-9\\.-]', '', 'g')::numeric
                       ELSE 0.0
                   END,
                   source_created_by = CASE
                       WHEN legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录'
                       THEN NULLIF({lv15}, '')
                       ELSE NULL
                   END,
                   source_created_at = CASE
                       WHEN (legacy_fact_type = 'direct_acceptance:机械台班记录' OR legacy_acceptance_label = '机械台班记录')
                            AND left(COALESCE({lv16}, ''), 19) ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}( [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})?$'
                       THEN left({lv16}, 19)::timestamp
                       ELSE NULL
                   END
            """
        )


class MaterialRentalOrderDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rental.order"

    _add_legacy_visible_fields(locals())
    invoiced_amount_text = fields.Char(string="已开票金额", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    paid_amount_text = fields.Char(string="已付款金额", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    unpaid_amount_text = fields.Char(string="未付款金额", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    uninvoiced_amount_text = fields.Char(string="未开票金额", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    contract_sign_date_text = fields.Char(string="签订时间", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_material_name = fields.Char(string="材料名称", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_material_spec = fields.Char(string="规格型号", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_quantity_text = fields.Char(string="数量", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_unit_price_text = fields.Char(string="单价", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_deposit_amount_text = fields.Char(string="租赁押金", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_status_display = fields.Char(string="单据状态", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_document_no = fields.Char(string="单据编号", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_document_date = fields.Char(string="单据日期", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_partner_name = fields.Char(string="租赁单位", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_use_unit_name = fields.Char(string="使用单位", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_material_name = fields.Char(string="材料名称", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_material_spec = fields.Char(string="规格型号", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_quantity = fields.Char(string="数量", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_unit_price = fields.Char(string="单价", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_deposit_amount = fields.Char(string="租赁押金", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_settlement_status = fields.Char(string="结算状态", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_settlement_amount = fields.Char(string="单据结算金额", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_compensation_fee = fields.Char(string="赔偿费", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_repair_fee = fields.Char(string="维修费", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_transport_fee = fields.Char(string="进出场费", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_deposit_deduction = fields.Char(string="抵扣押金", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_note = fields.Char(string="备注", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_attachment_text = fields.Char(string="附件", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_project_name = fields.Char(string="项目名称", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_source_created_by = fields.Char(string="录入人", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)
    rental_order_source_created_at = fields.Char(string="录入时间", compute="_compute_rental_order_formal_visible_fields", store=True, readonly=True)

    @api.depends(
        "legacy_acceptance_label",
        "state",
        "name",
        "rental_date",
        "supplier_id",
        "project_id",
        "note",
        "source_created_by",
        "source_created_at",
        *[_lv(index) for index in range(1, 17)],
    )
    def _compute_rental_order_formal_visible_fields(self):
        contract_map = {
            "invoiced_amount_text": _lv(9),
            "paid_amount_text": _lv(10),
            "unpaid_amount_text": _lv(11),
            "uninvoiced_amount_text": _lv(12),
            "contract_sign_date_text": _lv(14),
        }
        rental_in_map = {
            "rental_material_name": _lv(6),
            "rental_material_spec": _lv(7),
            "rental_quantity_text": _lv(8),
            "rental_unit_price_text": _lv(9),
            "rental_deposit_amount_text": _lv(10),
        }
        fields_to_clear = set(contract_map) | set(rental_in_map)
        fields_to_clear |= {
            "rental_order_status_display",
            "rental_order_document_no",
            "rental_order_document_date",
            "rental_order_partner_name",
            "rental_order_use_unit_name",
            "rental_order_material_name",
            "rental_order_material_spec",
            "rental_order_quantity",
            "rental_order_unit_price",
            "rental_order_deposit_amount",
            "rental_order_settlement_status",
            "rental_order_settlement_amount",
            "rental_order_compensation_fee",
            "rental_order_repair_fee",
            "rental_order_transport_fee",
            "rental_order_deposit_deduction",
            "rental_order_note",
            "rental_order_attachment_text",
            "rental_order_project_name",
            "rental_order_source_created_by",
            "rental_order_source_created_at",
        }
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            for field_name in fields_to_clear:
                record[field_name] = False
            if record.legacy_acceptance_label == "租赁合同":
                source_map = contract_map
            elif record.legacy_acceptance_label == "租入":
                source_map = rental_in_map
            else:
                source_map = {}
            for target_field, source_field in source_map.items():
                record[target_field] = getattr(record, source_field, False)
            if record.legacy_acceptance_label == "租入":
                record.rental_order_status_display = record[_lv(1)] or state_labels.get(record.state) or ""
                record.rental_order_document_no = record[_lv(2)] or record.name or ""
                record.rental_order_document_date = record[_lv(3)] or (record.rental_date.isoformat() if record.rental_date else "")
                record.rental_order_partner_name = record[_lv(4)] or (record.supplier_id.display_name if record.supplier_id else "")
                record.rental_order_use_unit_name = record[_lv(5)] or ""
                record.rental_order_material_name = record[_lv(6)] or record.rental_material_name or ""
                record.rental_order_material_spec = record[_lv(7)] or record.rental_material_spec or ""
                record.rental_order_quantity = record[_lv(8)] or record.rental_quantity_text or ""
                record.rental_order_unit_price = record[_lv(9)] or record.rental_unit_price_text or ""
                record.rental_order_deposit_amount = record[_lv(10)] or record.rental_deposit_amount_text or ""
                record.rental_order_note = record[_lv(11)] or (record.note or "")
                record.rental_order_attachment_text = record[_lv(12)] or ""
                record.rental_order_source_created_by = record[_lv(13)] or record.source_created_by or ""
                record.rental_order_source_created_at = record[_lv(14)] or (record.source_created_at and fields.Datetime.to_string(record.source_created_at)) or ""
                record.rental_order_project_name = record[_lv(15)] or (record.project_id.display_name if record.project_id else "")
            elif record.legacy_acceptance_label == "还租":
                record.rental_order_status_display = record[_lv(1)] or state_labels.get(record.state) or ""
                record.rental_order_project_name = record[_lv(2)] or (record.project_id.display_name if record.project_id else "")
                record.rental_order_settlement_status = record[_lv(3)] or ""
                record.rental_order_document_no = record[_lv(4)] or record.name or ""
                record.rental_order_document_date = record[_lv(5)] or (record.rental_date.isoformat() if record.rental_date else "")
                record.rental_order_partner_name = record[_lv(6)] or (record.supplier_id.display_name if record.supplier_id else "")
                record.rental_order_settlement_amount = record[_lv(7)] or ""
                record.rental_order_compensation_fee = record[_lv(8)] or ""
                record.rental_order_repair_fee = record[_lv(9)] or ""
                record.rental_order_transport_fee = record[_lv(10)] or ""
                record.rental_order_attachment_text = record[_lv(11)] or ""
                record.rental_order_note = record[_lv(12)] or (record.note or "")
                record.rental_order_source_created_by = record[_lv(13)] or record.source_created_by or ""
                record.rental_order_source_created_at = record[_lv(14)] or (record.source_created_at and fields.Datetime.to_string(record.source_created_at)) or ""
                record.rental_order_deposit_deduction = record[_lv(15)] or ""
                record.rental_order_use_unit_name = record[_lv(16)] or ""
            else:
                record.rental_order_status_display = state_labels.get(record.state) or ""
                record.rental_order_document_no = record.name or ""
                record.rental_order_document_date = record.rental_date.isoformat() if record.rental_date else ""
                record.rental_order_partner_name = record.supplier_id.display_name if record.supplier_id else ""
                record.rental_order_project_name = record.project_id.display_name if record.project_id else ""
                record.rental_order_note = record.note or ""
                record.rental_order_source_created_by = record.source_created_by or ""
                record.rental_order_source_created_at = (
                    fields.Datetime.to_string(record.source_created_at) if record.source_created_at else ""
                )


class HrPayrollDocumentDirectAcceptanceVisible(models.Model):
    _inherit = "sc.hr.payroll.document"

    _add_legacy_visible_fields(locals())
    payroll_document_status_display = fields.Char(
        string="单据状态",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_project_name = fields.Char(
        string="项目名称",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_no = fields.Char(
        string="单据编号",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_date = fields.Char(
        string="单据日期",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_salary_month = fields.Char(
        string="工资月份",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_net_salary = fields.Char(
        string="本次实发工资总额",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_gross_salary = fields.Char(
        string="本次应发工资总额",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_payment_status = fields.Char(
        string="付款状态",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_paid_amount = fields.Char(
        string="已付款金额",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_unpaid_amount = fields.Char(
        string="未付款金额",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_note = fields.Char(
        string="备注",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_attachment_text = fields.Char(
        string="附件",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_source_created_by = fields.Char(
        string="录入人",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )
    payroll_document_source_created_at = fields.Char(
        string="录入时间",
        compute="_compute_payroll_document_formal_visible_fields",
        store=True,
        readonly=True,
    )

    @api.depends(
        "legacy_acceptance_label",
        "legacy_source_table",
        "state",
        "project_id",
        "name",
        "period_year",
        "period_month",
        "gross_amount",
        "net_salary",
        "attachment_ids",
        "source_created_by",
        "source_created_at",
        *[_lv(index) for index in range(1, 15)],
    )
    def _compute_payroll_document_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            for field_name in (
                "payroll_document_status_display",
                "payroll_document_project_name",
                "payroll_document_no",
                "payroll_document_date",
                "payroll_document_salary_month",
                "payroll_document_net_salary",
                "payroll_document_gross_salary",
                "payroll_document_payment_status",
                "payroll_document_paid_amount",
                "payroll_document_unpaid_amount",
                "payroll_document_note",
                "payroll_document_attachment_text",
                "payroll_document_source_created_by",
                "payroll_document_source_created_at",
            ):
                record[field_name] = False

            is_manager_salary = (
                record.legacy_acceptance_label == "管理人员工资表"
                or record.legacy_source_table == "direct_acceptance:管理人员工资表"
            )
            if is_manager_salary:
                record.payroll_document_status_display = record[_lv(1)] or state_labels.get(record.state) or ""
                record.payroll_document_project_name = record[_lv(2)] or (record.project_id.display_name if record.project_id else "")
                record.payroll_document_no = record[_lv(3)] or record.name or ""
                record.payroll_document_date = record[_lv(4)] or ""
                record.payroll_document_salary_month = record[_lv(5)] or ""
                record.payroll_document_net_salary = record[_lv(6)] or ""
                record.payroll_document_gross_salary = record[_lv(7)] or ""
                record.payroll_document_payment_status = record[_lv(8)] or ""
                record.payroll_document_paid_amount = record[_lv(9)] or ""
                record.payroll_document_unpaid_amount = record[_lv(10)] or ""
                record.payroll_document_note = record[_lv(11)] or ""
                record.payroll_document_attachment_text = record[_lv(12)] or (
                    "附件(%s)" % len(record.attachment_ids) if record.attachment_ids else ""
                )
                record.payroll_document_source_created_by = record[_lv(13)] or record.source_created_by or ""
                record.payroll_document_source_created_at = record[_lv(14)] or (
                    fields.Datetime.to_string(record.source_created_at) if record.source_created_at else ""
                )
                continue

            record.payroll_document_status_display = state_labels.get(record.state) or ""
            record.payroll_document_project_name = record.project_id.display_name if record.project_id else ""
            record.payroll_document_no = record.name or ""
            if record.period_year and record.period_month:
                record.payroll_document_salary_month = "%04d-%02d" % (record.period_year, record.period_month)
            record.payroll_document_net_salary = str(record.net_salary or "") if record.net_salary else ""
            record.payroll_document_gross_salary = str(record.gross_amount or "") if record.gross_amount else ""
            record.payroll_document_attachment_text = "附件(%s)" % len(record.attachment_ids) if record.attachment_ids else ""
            record.payroll_document_source_created_by = record.source_created_by or ""
            record.payroll_document_source_created_at = (
                fields.Datetime.to_string(record.source_created_at) if record.source_created_at else ""
            )


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
    diary_status_display = fields.Char(string="单据状态", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_project_name = fields.Char(string="项目名称", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_document_no = fields.Char(string="单据编号", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_date_display = fields.Char(string="日期", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_construction_part = fields.Char(string="施工部位", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_manpower_count_display = fields.Char(string="出勤人数", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_equipment_attendance = fields.Char(string="出勤机械", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_note_display = fields.Char(string="备注", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_attachment_text = fields.Char(string="附件", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_source_created_by = fields.Char(string="录入人", compute="_compute_diary_formal_visible_fields", readonly=True)
    diary_source_created_at = fields.Char(string="录入时间", compute="_compute_diary_formal_visible_fields", readonly=True)

    @api.depends(
        "state",
        "project_id",
        "document_no",
        "name",
        "date_diary",
        "title",
        "quality_name",
        "manpower_count",
        "attendance_equipment",
        "note",
        "header_description",
        "description",
        "attachment_ids",
        *[_lv(index) for index in range(1, 12)],
    )
    def _compute_diary_formal_visible_fields(self):
        state_map = {
            "draft": "草稿",
            "confirmed": "已确认",
            "done": "已完成",
            "legacy_confirmed": "历史已确认",
            "cancel": "已取消",
        }
        for record in self:
            record.diary_status_display = record[_lv(1)] or state_map.get(record.state, record.state or "")
            record.diary_project_name = record[_lv(2)] or record.project_id.display_name or ""
            record.diary_document_no = record[_lv(3)] or record.document_no or record.name or ""
            record.diary_date_display = record[_lv(4)] or (fields.Datetime.to_string(record.date_diary) if record.date_diary else "")
            record.diary_construction_part = record[_lv(5)] or record.quality_name or record.title or ""
            record.diary_manpower_count_display = record[_lv(6)] or (str(record.manpower_count) if record.manpower_count else "")
            record.diary_equipment_attendance = record[_lv(7)] or record.attendance_equipment or ""
            record.diary_note_display = record[_lv(8)] or record.note or record.header_description or record.description or ""
            record.diary_attachment_text = record[_lv(9)] or ("附件(%s)" % len(record.attachment_ids) if record.attachment_ids else "")
            record.diary_source_created_by = record[_lv(10)] or record.handler_name or ""
            record.diary_source_created_at = record[_lv(11)] or ""


class SettlementOrderDirectAcceptanceVisible(models.Model):
    _inherit = "sc.settlement.order"

    _add_legacy_visible_fields(locals())

    settlement_acceptance_document_state = fields.Char(string="单据状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_document_no = fields.Char(string="单据编号", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_project_name = fields.Char(string="项目名称", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_document_date = fields.Char(string="单据日期", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_title = fields.Char(string="标题/结算内容", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_partner_name = fields.Char(string="结算单位", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_amount = fields.Char(string="结算金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_payment_state = fields.Char(string="付款状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_paid_amount = fields.Char(string="已付款金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_unpaid_amount = fields.Char(string="未付款金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_request_state = fields.Char(string="支付申请状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_requested_amount = fields.Char(string="已申请金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_unrequested_amount = fields.Char(string="未申请金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_note = fields.Char(string="结算说明/备注", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_attachment = fields.Char(string="附件", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_creator = fields.Char(string="录入人", compute="_compute_settlement_acceptance_visible", readonly=True)
    settlement_acceptance_created_at = fields.Char(string="录入时间", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_document_state = fields.Char(string="单据状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_document_no = fields.Char(string="单据编号", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_project_name = fields.Char(string="项目名称", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_document_date = fields.Char(string="单据日期", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_title = fields.Char(string="标题/结算内容", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_partner_name = fields.Char(string="结算单位", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_amount = fields.Char(string="结算金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_payment_state = fields.Char(string="付款状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_paid_amount = fields.Char(string="已付款金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_unpaid_amount = fields.Char(string="未付款金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_request_state = fields.Char(string="支付申请状态", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_requested_amount = fields.Char(string="已申请金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_unrequested_amount = fields.Char(string="未申请金额", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_note = fields.Char(string="结算说明/备注", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_attachment = fields.Char(string="附件", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_creator = fields.Char(string="录入人", compute="_compute_settlement_acceptance_visible", readonly=True)
    user_acceptance_created_at = fields.Char(string="录入时间", compute="_compute_settlement_acceptance_visible", readonly=True)

    def _compute_settlement_acceptance_visible(self):
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
                value = v(record, mapping.get(name)) if mapping.get(name) else False
                setattr(record, "settlement_acceptance_" + name, value)
                setattr(record, "user_acceptance_" + name, value)
