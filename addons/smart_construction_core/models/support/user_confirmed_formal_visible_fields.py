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
        ("user_acceptance_document_state", "单据状态"),
        ("user_acceptance_document_no", "单据编号"),
        ("user_acceptance_project_name", "项目名称"),
        ("user_acceptance_title", "标题/结算内容"),
        ("user_acceptance_paid_amount", "已付款金额"),
        ("user_acceptance_requested_amount", "已申请金额"),
        ("user_acceptance_unrequested_amount", "未申请金额"),
        ("user_acceptance_note", "结算说明/备注"),
        ("user_acceptance_created_at", "录入时间"),
    ],
    "sc.construction.diary": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "项目名称"),
        ("legacy_visible_03", "单据编号"),
        ("legacy_visible_04", "日期"),
        ("legacy_visible_05", "施工部位"),
        ("legacy_visible_06", "出勤人数"),
        ("legacy_visible_07", "出勤机械"),
        ("legacy_visible_10", "录入人"),
        ("legacy_visible_11", "录入时间"),
    ],
    "project.material.plan": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "单据编号"),
        ("legacy_visible_03", "单据日期"),
        ("legacy_visible_04", "到货时间"),
        ("legacy_visible_05", "采购材料名称"),
        ("legacy_visible_06", "规格型号"),
        ("legacy_visible_07", "单位"),
        ("legacy_visible_08", "数量"),
        ("legacy_visible_09", "材料别名(设计/清单)"),
        ("legacy_visible_10", "备注"),
        ("legacy_visible_12", "项目名称"),
        ("legacy_visible_13", "录入人"),
        ("legacy_visible_14", "录入时间"),
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
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "单据编号"),
        ("legacy_visible_03", "项目名称"),
        ("legacy_visible_04", "单据日期"),
        ("legacy_visible_05", "标题"),
        ("legacy_visible_06", "工种"),
        ("legacy_visible_07", "施工部位"),
        ("legacy_visible_07", "数量"),
        ("legacy_visible_08", "结算状态"),
        ("legacy_visible_08", "单价"),
        ("legacy_visible_09", "总金额"),
        ("legacy_visible_09", "金额"),
        ("legacy_visible_10", "备注"),
        ("legacy_visible_10", "工作内容"),
        ("legacy_visible_12", "录入人"),
        ("legacy_visible_12", "结算状态"),
        ("legacy_visible_13", "录入时间"),
        ("legacy_visible_13", "备注"),
        ("legacy_visible_14", "录入人"),
        ("legacy_visible_15", "录入时间"),
    ],
    "sc.equipment.usage": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "项目名称"),
        ("legacy_visible_03", "单据编号"),
        ("legacy_visible_04", "单据日期"),
        ("legacy_visible_05", "租赁单位"),
        ("legacy_visible_06", "曾用名单位"),
        ("legacy_visible_07", "机械名称"),
        ("legacy_visible_08", "规格型号"),
        ("legacy_visible_09", "单位"),
        ("legacy_visible_10", "工作时间"),
        ("legacy_visible_11", "单价"),
        ("legacy_visible_12", "金额"),
        ("legacy_visible_14", "备注"),
        ("legacy_visible_15", "录入人"),
        ("legacy_visible_16", "录入时间"),
    ],
    "sc.material.rfq": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_02", "单据编号"),
        ("legacy_visible_03", "供应商名称"),
        ("legacy_visible_04", "询价时间"),
        ("legacy_visible_05", "材料名称"),
        ("legacy_visible_06", "规格型号"),
        ("legacy_visible_07", "数量"),
        ("legacy_visible_08", "含税单价"),
        ("legacy_visible_09", "含税总金额"),
        ("legacy_visible_10", "总数量"),
        ("legacy_visible_11", "总金额"),
        ("legacy_visible_12", "备注"),
        ("legacy_visible_16", "是否中标"),
        ("legacy_visible_17", "项目名称"),
        ("legacy_visible_18", "录入人"),
        ("legacy_visible_19", "录入时间"),
    ],
    "sc.material.inbound": [
        ("legacy_visible_01", "单据状态"),
        ("legacy_visible_03", "单据日期"),
        ("legacy_visible_04", "供应商名称"),
        ("legacy_visible_05", "材料名称"),
        ("legacy_visible_06", "规格型号"),
        ("legacy_visible_07", "数量"),
        ("legacy_visible_08", "单价"),
        ("legacy_visible_09", "税率"),
        ("legacy_visible_11", "入库总数量"),
        ("legacy_visible_12", "付款状态"),
        ("legacy_visible_13", "已付款金额"),
        ("legacy_visible_14", "未付款金额"),
        ("legacy_visible_15", "结算状态"),
        ("legacy_visible_16", "已结算金额"),
        ("legacy_visible_17", "项目名称"),
        ("legacy_visible_18", "备注"),
        ("legacy_visible_20", "录入人"),
        ("legacy_visible_21", "录入时间"),
        ("legacy_visible_22", "采购人"),
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
        ("accepted_visible_06", "充值总额"),
        ("accepted_visible_07", "充值日期"),
    ],
    "sc.office.admin.document": _p1_field_pairs(
        "sc.office.admin.document",
        ["单据状态", "单据编号", "项目名称", "申请人姓名", "所在部门", "请假天数", "请假时间", "销假时间", "备注", "请假时长", "录入人", "录入时间"],
    ),
    "sc.hr.payroll.document": [
        ("legacy_visible_05", "工资月份"),
        ("legacy_visible_06", "本次实发工资总额"),
        ("legacy_visible_07", "本次应发工资总额"),
        ("legacy_visible_08", "付款状态"),
        ("legacy_visible_09", "已付款金额"),
        ("legacy_visible_10", "未付款金额"),
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
        etree.SubElement(group, "field", name=entry["field_name"])
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
    for entry in entries:
        attrs[entry["field_name"]] = fields.Text(
            string=entry["label"],
            help="用户确认数据正式承接字段；用于历史数据延续和后续业务办理。",
            copy=False,
        )

    attrs["get_view"] = _make_get_view(class_name)
    return attrs


for _index, (_model_name, _entries) in enumerate(USER_CONFIRMED_FORMAL_VISIBLE_FIELDS.items(), start=1):
    _class_name = "ScUserConfirmedFormalVisible%s" % "".join(part.capitalize() for part in _model_name.split("."))
    globals()[_class_name] = type(_class_name, (models.Model,), _extension_attrs(_model_name, _entries, _class_name))
