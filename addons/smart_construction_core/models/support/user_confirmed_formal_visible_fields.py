# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib

from lxml import etree

from odoo import fields, models

from .p1_daily_business_visible_alias_fields import P1_ALIAS_LABELS, _alias_field_name


def _formal_field_name(model_name, source_field, label):
    key = "%s|%s|%s" % (model_name, source_field, label)
    return "uc_formal_%s" % hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _p1_field_pairs(model_name, labels):
    return [(_alias_field_name(label), label) for label in labels if label != "附件"]


USER_CONFIRMED_FORMAL_VISIBLE_SOURCES = {
    "tender.bid": _p1_field_pairs(
        "tender.bid",
        ["单据状态", "推送结果", "单据编号", "项目名称", "登记时间", "录入人"],
    ),
    "construction.contract.expense": [
        ("legacy_visible_contract_date", "签订日期"),
        ("legacy_visible_title", "标题"),
        ("legacy_visible_counterparty", "往来单位"),
        ("legacy_visible_invoice_amount", "已开票金额"),
        ("legacy_visible_received_amount", "已付款金额"),
        ("legacy_visible_invoice_unreceived_amount", "未开票金额"),
    ],
    "sc.settlement.order": [
        ("settlement_acceptance_document_state", "单据状态"),
        ("settlement_acceptance_document_no", "单据编号"),
        ("settlement_acceptance_project_name", "项目名称"),
        ("settlement_acceptance_title", "标题/结算内容"),
        ("settlement_acceptance_paid_amount", "已付款金额"),
        ("settlement_acceptance_requested_amount", "已申请金额"),
        ("settlement_acceptance_unrequested_amount", "未申请金额"),
        ("settlement_acceptance_note", "结算说明/备注"),
        ("settlement_acceptance_created_at", "录入时间"),
    ],
    "sc.construction.diary": [
        ("diary_status_display", "单据状态"),
        ("diary_project_name", "项目名称"),
        ("diary_document_no", "单据编号"),
        ("diary_date_display", "日期"),
        ("diary_construction_part", "施工部位"),
        ("diary_manpower_count_display", "出勤人数"),
        ("diary_equipment_attendance", "出勤机械"),
        ("diary_source_created_by", "录入人"),
        ("diary_source_created_at", "录入时间"),
    ],
    "project.material.plan": [
        ("material_plan_status_display", "单据状态"),
        ("material_plan_document_no", "单据编号"),
        ("material_plan_document_date", "单据日期"),
        ("material_plan_arrival_date", "到货时间"),
        ("material_plan_material_name", "采购材料名称"),
        ("material_plan_specification", "规格型号"),
        ("material_plan_unit", "单位"),
        ("material_plan_quantity", "数量"),
        ("material_plan_material_alias", "材料别名(设计/清单)"),
        ("material_plan_note", "备注"),
        ("material_plan_project_name", "项目名称"),
        ("material_plan_source_created_by", "录入人"),
        ("material_plan_source_created_at", "录入时间"),
    ],
    "sc.legacy.direct.acceptance.fact": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "项目名称"),
        ("legacy_visible_02", "单据编号"),
        ("legacy_visible_03", "单据日期"),
        ("legacy_visible_03", "结算状态"),
        ("legacy_visible_04", "租赁单位"),
        ("legacy_visible_04", "还租单号"),
        ("legacy_visible_05", "使用单位名称"),
        ("legacy_visible_05", "单据日期"),
        ("legacy_visible_06", "材料名称"),
        ("legacy_visible_06", "租赁单位"),
        ("legacy_visible_07", "规格型号"),
        ("legacy_visible_07", "单据结算金额"),
        ("legacy_visible_08", "数量"),
        ("legacy_visible_08", "赔偿费"),
        ("legacy_visible_09", "单价"),
        ("legacy_visible_09", "维修费"),
        ("legacy_visible_10", "租赁押金"),
        ("legacy_visible_10", "进出场费"),
        ("legacy_visible_11", "备注"),
        ("legacy_visible_12", "备注"),
        ("legacy_visible_13", "录入人"),
        ("legacy_visible_14", "录入时间"),
        ("legacy_visible_15", "项目名称"),
        ("legacy_visible_15", "抵扣押金"),
        ("legacy_visible_16", "使用单位"),
    ],
    "sc.subcontract.request": _p1_field_pairs(
        "sc.subcontract.request",
        ["单据状态", "单据编号", "项目名称", "标题", "分包商", "分包类型", "分包内容", "数量", "单价", "金额", "本月合价", "录入人", "录入时间"],
    ),
    "sc.labor.usage": [
        ("labor_usage_status_display", "单据状态"),
        ("labor_usage_document_no", "单据编号"),
        ("labor_usage_project_name", "项目名称"),
        ("labor_usage_document_date", "单据日期"),
        ("labor_usage_title", "标题"),
        ("labor_usage_labor_team_name", "劳务单位"),
        ("labor_usage_work_type", "工种"),
        ("labor_usage_construction_part", "施工部位"),
        ("labor_usage_quantity", "数量"),
        ("labor_usage_price_unit", "单价"),
        ("labor_usage_amount", "金额"),
        ("labor_usage_work_content", "工作内容"),
        ("labor_usage_attachment_text", "附件"),
        ("labor_usage_settlement_status", "结算状态"),
        ("labor_usage_note", "备注"),
        ("labor_usage_source_created_by", "录入人"),
        ("labor_usage_source_created_at", "录入时间"),
    ],
    "sc.equipment.usage": [
        ("state", "单据状态"),
        ("project_id", "项目名称"),
        ("name", "单据编号"),
        ("document_date", "单据日期"),
        ("supplier_id", "租赁单位"),
        ("former_supplier_name", "曾用名单位"),
        ("equipment_name", "机械名称"),
        ("specification", "规格型号"),
        ("uom_text", "单位"),
        ("work_hours", "工作时间"),
        ("price_unit", "单价"),
        ("amount", "金额"),
        ("attachment_ids", "附件"),
        ("note", "备注"),
        ("source_created_by", "录入人"),
        ("source_created_at", "录入时间"),
    ],
    "sc.material.rfq": [
        ("quote_status_display", "单据状态"),
        ("quote_document_no", "单据编号"),
        ("quote_supplier_name", "供应商名称"),
        ("quote_inquiry_time", "询价时间"),
        ("quote_material_name", "材料名称"),
        ("quote_material_spec", "规格型号"),
        ("quote_quantity_display", "数量"),
        ("quote_tax_price_display", "含税单价"),
        ("quote_tax_amount_display", "含税总金额"),
        ("quote_total_quantity_display", "总数量"),
        ("quote_total_amount_display", "总金额"),
        ("quote_note_display", "备注"),
        ("quote_contact_name", "联系人"),
        ("quote_contact_phone", "联系电话"),
        ("quote_attachment_text", "附件"),
        ("quote_selected_text", "是否中标"),
        ("quote_project_name", "项目名称"),
        ("quote_source_created_by", "录入人"),
        ("quote_source_created_at", "录入时间"),
    ],
    "sc.material.inbound": [
        ("document_status", "单据状态"),
        ("name", "入库单号"),
        ("inbound_date", "单据日期"),
        ("supplier_id", "供应商名称"),
        ("material_name_summary", "材料名称"),
        ("material_spec_summary", "规格型号"),
        ("quantity_summary", "数量"),
        ("unit_price_summary", "单价"),
        ("tax_rate_text", "税率"),
        ("tax_included_amount", "含税金额"),
        ("total_qty", "入库总数量"),
        ("payment_status_text", "付款状态"),
        ("payment_paid_amount", "已付款金额"),
        ("payment_unpaid_amount", "未付款金额"),
        ("settlement_status_text", "结算状态"),
        ("settlement_settled_amount", "已结算金额"),
        ("project_name_display", "项目名称"),
        ("line_note_summary", "备注"),
        ("attachment_ids", "附件"),
        ("source_created_by", "录入人"),
        ("source_created_at", "录入时间"),
        ("buyer_name", "采购人"),
    ],
    "sc.material.rental.order": [
        ("rental_order_status_display", "单据状态"),
        ("rental_order_document_no", "单据编号"),
        ("rental_order_project_name", "项目名称"),
        ("rental_order_settlement_status", "结算状态"),
        ("rental_order_document_date", "单据日期"),
        ("rental_order_partner_name", "租赁单位"),
        ("rental_order_use_unit_name", "使用单位"),
        ("rental_order_material_name", "材料名称"),
        ("rental_order_material_spec", "规格型号"),
        ("rental_order_quantity", "数量"),
        ("rental_order_unit_price", "单价"),
        ("rental_order_deposit_amount", "租赁押金"),
        ("rental_order_settlement_amount", "单据结算金额"),
        ("rental_order_compensation_fee", "赔偿费"),
        ("rental_order_repair_fee", "维修费"),
        ("rental_order_transport_fee", "进出场费"),
        ("rental_order_deposit_deduction", "抵扣押金"),
        ("rental_order_note", "备注"),
        ("rental_order_attachment_text", "附件"),
        ("rental_order_source_created_by", "录入人"),
        ("rental_order_source_created_at", "录入时间"),
    ],
    "sc.tax.deduction.registration": _p1_field_pairs("sc.tax.deduction.registration", ["录入时间"]),
    "sc.invoice.registration": _p1_field_pairs("sc.invoice.registration", ["项目名称"]),
    "sc.fund.account.operation": _p1_field_pairs(
        "sc.fund.account.operation",
        ["单据状态", "项目名称", "发生时间", "账户号码", "转账类别", "事由", "录入人", "录入时间"],
    ),
    "sc.receipt.income": [
        ("legacy_visible_03", "日期"),
        ("legacy_visible_04", "对方单位/付款单位"),
        ("legacy_visible_07", "工程款收入"),
    ],
    "tender.guarantee": _p1_field_pairs("tender.guarantee", [label for label in P1_ALIAS_LABELS.get("tender.guarantee", []) if label != "附件"]),
    "sc.expense.claim": _p1_field_pairs("sc.expense.claim", ["推送结果", "所属公司", "标题", "项目名称"]),
    "payment.request": _p1_field_pairs("payment.request", ["单据状态"]),
    "sc.financing.loan": _p1_field_pairs("sc.financing.loan", [label for label in P1_ALIAS_LABELS.get("sc.financing.loan", []) if label != "附件"]),
    "sc.payment.execution": _p1_field_pairs(
        "sc.payment.execution",
        ["收款单位", "实际收款单位", "支付类别", "付款内容", "类型（成本）", "付款单关联来源"],
    ),
    "sc.legacy.fuel.card.recharge.fact": [
        ("fuel_recharge_amount_display", "充值总额"),
        ("fuel_recharge_date_display", "充值日期"),
    ],
    "sc.office.admin.document": _p1_field_pairs(
        "sc.office.admin.document",
        ["单据状态", "单据编号", "项目名称", "申请人姓名", "所在部门", "请假天数", "请假时间", "销假时间", "备注", "请假时长", "录入人", "录入时间"],
    ),
    "sc.hr.payroll.document": [
        ("payroll_document_status_display", "单据状态"),
        ("payroll_document_project_name", "项目名称"),
        ("payroll_document_no", "单据编号"),
        ("payroll_document_date", "单据日期"),
        ("payroll_document_salary_month", "工资月份"),
        ("payroll_document_net_salary", "本次实发工资总额"),
        ("payroll_document_gross_salary", "本次应发工资总额"),
        ("payroll_document_payment_status", "付款状态"),
        ("payroll_document_paid_amount", "已付款金额"),
        ("payroll_document_unpaid_amount", "未付款金额"),
        ("payroll_document_note", "备注"),
        ("payroll_document_attachment_text", "附件"),
        ("payroll_document_source_created_by", "录入人"),
        ("payroll_document_source_created_at", "录入时间"),
    ],
    "sc.document.admin.document": _p1_field_pairs(
        "sc.document.admin.document",
        ["单据状态", "项目名称", "资料类型", "资料说明", "录入人", "备注", "录入时间"],
    ),
}

USER_CONFIRMED_FORMAL_VISIBLE_FIELDS = {
    model_name: [
        {
            "source_field": source_field,
            "field_name": _formal_field_name(model_name, source_field, label),
            "label": label,
        }
        for source_field, label in list(dict.fromkeys(pairs))
        if label != "附件"
    ]
    for model_name, pairs in USER_CONFIRMED_FORMAL_VISIBLE_SOURCES.items()
}


def _inject_formal_visible_fields(self, result, view_type):
    if view_type != "form" or not isinstance(result, dict):
        return result
    entries = [
        entry
        for entry in USER_CONFIRMED_FORMAL_VISIBLE_FIELDS.get(self._name, [])
        if entry["field_name"] in self._fields
    ]
    if not entries:
        return result
    arch = result.get("arch") or ""
    if not arch:
        return result
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return result
    existing = {node.get("name") for node in root.xpath(".//field[@name]")}
    missing = [entry for entry in entries if entry["field_name"] not in existing]
    if not missing:
        return result
    sheet = root.xpath("//sheet")
    parent = sheet[0] if sheet else root
    group = etree.Element("group", string="用户确认业务字段")
    for entry in missing:
        etree.SubElement(group, "field", name=entry["field_name"], string=entry["label"])
    parent.append(group)
    result["arch"] = etree.tostring(root, encoding="unicode")
    return result


def _make_get_view(class_name):
    def get_view(self, view_id=None, view_type="form", **options):
        result = super(globals()[class_name], self).get_view(view_id=view_id, view_type=view_type, **options)
        return _inject_formal_visible_fields(self, result, view_type)

    return get_view


def _extension_attrs(model_name, entries, class_name):
    attrs = {
        "_inherit": model_name,
        "__module__": __name__,
    }
    label_totals = {}
    for entry in entries:
        label = entry["label"]
        label_totals[label] = label_totals.get(label, 0) + 1
    label_seen = {}
    for entry in entries:
        label = entry["label"]
        label_seen[label] = label_seen.get(label, 0) + 1
        field_string = "用户确认%s" % label
        if label_totals.get(label, 0) > 1:
            field_string = "%s%s" % (field_string, label_seen[label])
        attrs[entry["field_name"]] = fields.Text(
            string=field_string,
            help="用户确认数据正式承接字段；用于历史数据延续和后续业务办理。",
            copy=False,
        )

    attrs["get_view"] = _make_get_view(class_name)
    return attrs


for _index, (_model_name, _entries) in enumerate(USER_CONFIRMED_FORMAL_VISIBLE_FIELDS.items(), start=1):
    _class_name = "ScUserConfirmedFormalVisible%s" % "".join(part.capitalize() for part in _model_name.split("."))
    globals()[_class_name] = type(_class_name, (models.Model,), _extension_attrs(_model_name, _entries, _class_name))
