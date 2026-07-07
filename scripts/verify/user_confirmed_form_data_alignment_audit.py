# -*- coding: utf-8 -*-
"""Audit data alignment between locked user-confirmed lists and formal forms.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/user_confirmed_form_data_alignment_audit.py

The earlier form-capability audit proves that list fields are represented on
forms.  This audit is stricter: for visible list fields that map to formal
business fields, it checks whether non-empty accepted/list values are carried
by the corresponding formal form fields on actual records.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from lxml import etree
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (
    MODEL_LABEL_SOURCE_OVERRIDES,
    P1_ALIAS_COMPAT_LABELS,
    P1_ALIAS_LABELS,
    _alias_field_name,
    _format_alias_value,
)


BASELINE_CANDIDATES = (
    Path("/mnt/scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json"),
    Path("scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json"),
)
OUTPUT_DIR_CANDIDATES = (
    Path("/mnt/docs/audit/user_confirmed_form_data_alignment"),
    Path("docs/audit/user_confirmed_form_data_alignment"),
    Path("/tmp/user_confirmed_form_data_alignment"),
)
PRODUCT_KEY = "construction.standard"
RECORD_LIMIT = int(os.environ.get("USER_CONFIRMED_ALIGNMENT_RECORD_LIMIT", "0") or "0")
SAMPLE_LIMIT = int(os.environ.get("USER_CONFIRMED_ALIGNMENT_SAMPLE_LIMIT", "30") or "30")
SKIP_FIELD_NAMES = {
    "id",
    "active",
    "display_name",
    "create_date",
    "create_uid",
    "write_date",
    "write_uid",
    "message_attachment_count",
}
SKIP_FIELD_TYPES = {"binary", "html", "one2many"}
SOURCE_ONLY_PREFIXES = ("legacy_visible_", "accepted_visible_", "user_acceptance_", "p1_visible_")
FORMAL_PREFIXES = ("legacy_visible_", "accepted_visible_", "user_acceptance_", "p1_visible_")
GENERIC_LEGACY_VISIBLE_RE = re.compile(r"legacy_visible_\d{2}$")
NON_HANDLING_LABELS = {
    "附件",
    "单据状态",
    "状态",
    "推送结果",
    "开票状态",
    "付款状态",
    "结算状态",
    "是否中标",
    "是否需要退回",
    "录入人",
    "录入时间",
    "历史录入人",
    "历史录入时间",
    "创建人",
    "创建时间",
}

P1_ALIAS_FIELD_LABELS = {
    model_name: {
        _alias_field_name(label): label
        for label in list(dict.fromkeys(list(labels) + P1_ALIAS_COMPAT_LABELS.get(model_name, [])))
    }
    for model_name, labels in P1_ALIAS_LABELS.items()
}


def _load_baseline():
    for path in BASELINE_CANDIDATES:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), path
    raise FileNotFoundError("missing user_confirmed_formal_menu_policy_62.json")


def _output_dir():
    for path in OUTPUT_DIR_CANDIDATES:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
            return path
        except OSError:
            continue
    raise OSError("cannot create audit output directory")


def _menus_for_product(baseline):
    for product in baseline.get("products") or []:
        if product.get("product_key") != PRODUCT_KEY:
            continue
        menus = []
        for group in product.get("menu_groups") or []:
            for menu in group.get("menus") or []:
                if menu.get("enabled", True):
                    row = dict(menu)
                    row["group_label"] = group.get("label") or group.get("group_label") or ""
                    menus.append(row)
        return menus
    return []


def _action_view_id(action_read, view_type):
    for view_id, mode in action_read.get("views") or []:
        if mode == view_type and view_id:
            return int(view_id)
    return False


def _view_arch(model_name, view_type, view_id=False):
    Model = env[model_name].sudo()  # noqa: F821
    try:
        data = Model.get_view(view_id=view_id or None, view_type=view_type)
    except AttributeError:
        data = Model.fields_view_get(view_id=view_id or None, view_type=view_type, toolbar=False)
    return data.get("arch") or data.get("arch_db") or ""


def _view_fields(arch):
    if not arch:
        return []
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    fields = []
    for node in root.xpath(".//field[@name]"):
        name = node.get("name")
        if not name:
            continue
        fields.append({"name": name, "label": node.get("string") or ""})
    return fields


def _safe_domain(action):
    try:
        value = safe_eval(
            action.domain or "[]",
            {"context": {}, "uid": env.uid, "active_id": False, "active_ids": []},  # noqa: F821
        )
        return value or [], ""
    except Exception as exc:
        return [], "domain_eval_failed:%s" % exc


def _formal_equivalent_fields(model_name, alias_field, model_fields):
    label = P1_ALIAS_FIELD_LABELS.get(model_name, {}).get(alias_field)
    if not label:
        return set()
    return _label_equivalent_fields(model_name, label, model_fields)


def _label_equivalent_fields(model_name, label, model_fields):
    if not label:
        return set()
    candidates = set(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label) or [])
    if model_name == "project.project" and label == "关联单位":
        candidates.add("partner_id")
    for candidate_name, field in model_fields.items():
        if field.string == label:
            candidates.add(candidate_name)
    return {field_name for field_name in candidates if field_name in model_fields}


def _is_source_only_field(field_name):
    return field_name.startswith(SOURCE_ONLY_PREFIXES)


def _is_formal_field(field_name):
    if GENERIC_LEGACY_VISIBLE_RE.match(field_name):
        return False
    if field_name.startswith("legacy_visible_"):
        return True
    return not field_name.startswith(FORMAL_PREFIXES)


def _field_candidates(model_name, field_name, label, form_field_names, model_fields):
    candidates = set()
    if field_name in form_field_names:
        candidates.add(field_name)
    if field_name.startswith("p1_visible_"):
        candidates |= _formal_equivalent_fields(model_name, field_name, model_fields)
    elif field_name.startswith(("legacy_visible_", "accepted_visible_", "user_acceptance_")):
        candidates |= _label_equivalent_fields(model_name, label, model_fields)
    else:
        candidates |= _label_equivalent_fields(model_name, label, model_fields)
    candidates = {
        name for name in candidates
        if name in model_fields
        and (
            name in form_field_names
            or (name.startswith("legacy_visible_") and not GENERIC_LEGACY_VISIBLE_RE.match(name))
        )
    }
    if _is_source_only_field(field_name):
        candidates = {name for name in candidates if _is_formal_field(name)}
    return sorted(candidates)


def _text(value):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def _normalize_text(value):
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) >= 8 and len(text) % 2 == 0 and not text.isdigit():
        half = len(text) // 2
        if text[:half] == text[half:]:
            text = text[:half].strip()
    return text


def _decimal_text(value):
    raw = _text(value).replace(",", "").replace("￥", "").replace("¥", "").replace("%", "")
    if not raw:
        return ""
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return ""
    try:
        amount = Decimal(match.group(0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return ""
    return str(amount.normalize())


def _decimal_value(value):
    text_value = _decimal_text(value)
    if not text_value:
        return None
    try:
        return Decimal(text_value)
    except InvalidOperation:
        return None


def _state_text(value):
    text = _normalize_text(value)
    if not text:
        return ""
    state_map = {
        "0": "未提交",
        "1": "审核中",
        "2": "审核通过",
        "3": "审核驳回",
        "4": "已作废",
        "草稿": "未提交",
        "提交": "审核中",
        "已提交": "审核中",
        "审批中": "审核中",
        "批准": "审核通过",
        "已批准": "审核通过",
        "已审批": "审核通过",
        "已确认": "审核通过",
        "已完成": "审核通过",
        "已登记": "审核通过",
        "历史已确认": "审核通过",
        "legacy_confirmed": "审核通过",
        "approved": "审核通过",
        "done": "审核通过",
        "confirmed": "审核通过",
        "registered": "审核通过",
        "draft": "未提交",
        "cancel": "已作废",
        "已取消": "已作废",
    }
    return state_map.get(text, text)


def _attachment_presence(value):
    text = _text(value)
    if not text:
        return ""
    match = re.search(r"附件\((\d+)\)", text)
    if match:
        return "attachment:%s" % match.group(1)
    return "attachment:present"


def _quick_attachment_value(record, field_name):
    field = record._fields.get(field_name)
    if not field:
        return ""
    if field_name.startswith("p1_visible_"):
        for source_name in MODEL_LABEL_SOURCE_OVERRIDES.get(record._name, {}).get("附件", ()):
            value = _quick_attachment_value(record, source_name)
            if value:
                return value
        return ""
    value = record[field_name]
    if field.type in {"many2many", "one2many"}:
        return "附件(%s)" % len(value) if value else ""
    if not value:
        return ""
    return _text(value)


def _label_source_value(record, label):
    if label == "附件":
        for source_name in MODEL_LABEL_SOURCE_OVERRIDES.get(record._name, {}).get("附件", ()):
            value = _quick_attachment_value(record, source_name)
            if value:
                return value
        return ""
    for source_name in MODEL_LABEL_SOURCE_OVERRIDES.get(record._name, {}).get(label, ()):
        if source_name.startswith("p1_visible_"):
            continue
        value = _display_value(record, source_name, label)
        if value:
            return value
    for source_name, source_field in record._fields.items():
        if source_name.startswith(SOURCE_ONLY_PREFIXES):
            continue
        if source_field.string == label:
            value = _display_value(record, source_name, label)
            if value:
                return value
    return ""


def _display_value(record, field_name, label=""):
    field = record._fields.get(field_name)
    if not field:
        return ""
    if label == "附件":
        return _quick_attachment_value(record, field_name)
    if field_name.startswith("p1_visible_"):
        return _format_alias_value(record, field_name) or _label_source_value(record, label)
    return _format_alias_value(record, field_name)


def _normalized_values(value, field, label=""):
    text_value = _normalize_text(value)
    values = {text_value} if text_value else set()
    if label in {"单据状态", "状态", "开票状态", "付款状态"}:
        state_value = _state_text(value)
        if state_value:
            values.add(state_value)
    number_value = _decimal_text(value)
    if number_value:
        values.add(number_value)
    if field and field.type in {"date", "datetime"} and text_value:
        values.add(text_value[:10])
        values.add(text_value[:19])
    if label == "附件" or (field and field.type in {"many2many", "one2many"}):
        attachment_value = _attachment_presence(value)
        if attachment_value:
            values.add("attachment:present")
            values.add(attachment_value)
    return {item for item in values if item}


def _values_match(source_value, source_field, target_value, target_field, label):
    source_values = _normalized_values(source_value, source_field, label)
    target_values = _normalized_values(target_value, target_field, label)
    if not source_values:
        return True
    if label == "附件" and target_values and "attachment:present" in source_values:
        return True
    if label in {"结算说明/备注", "结算说明", "备注", "标题/结算内容", "结算内容"}:
        for source_text in source_values:
            if any(source_text in target_text for target_text in target_values):
                return True
    if label in {"付款金额", "实际付款金额"}:
        source_decimal = _decimal_value(source_value)
        target_decimal = _decimal_value(target_value)
        if source_decimal is not None and target_decimal is not None and abs(source_decimal) == abs(target_decimal):
            return True
        if source_decimal is not None and target_decimal is not None and abs(abs(source_decimal) - abs(target_decimal)) <= Decimal("0.01"):
            return True
    if label in {"收款单位", "实际收款单位", "供应商名称", "结算单位", "往来单位"}:
        stripped_source = re.sub(r"[（(][^（）()]+[）)]$", "", _normalize_text(source_value)).strip()
        stripped_target = re.sub(r"[（(][^（）()]+[）)]$", "", _normalize_text(target_value)).strip()
        stripped_source = re.sub(r"\s+(分包|材料|劳务|机械|租赁|其他)$", "", stripped_source).strip()
        stripped_target = re.sub(r"\s+(分包|材料|劳务|机械|租赁|其他)$", "", stripped_target).strip()
        if stripped_source and stripped_source == stripped_target:
            return True
    return bool(source_values & target_values)


def _field_has_values(records, field_name, label):
    for record in records:
        if _normalize_text(_display_value(record, field_name, label)):
            return True
    return False


def _field_should_check(model_fields, field_name):
    field = model_fields.get(field_name)
    if not field:
        return False
    if field_name in SKIP_FIELD_NAMES or field_name.endswith("_count"):
        return False
    if field.type in SKIP_FIELD_TYPES:
        return False
    return True


def _alignment_boundary_class(model_fields, field_name, label):
    """Classify a visible list field without weakening the data check itself.

    The product boundary is not "every visible list column must be editable on
    a formal form". Formal handling fields must be carried by product models;
    historical evidence, operational metadata, and computed summaries must stay
    visible and traceable without becoming writable business input.
    """
    field = model_fields.get(field_name)
    if field_name.startswith(("legacy_visible_", "accepted_visible_", "user_acceptance_")):
        return "historical_source_evidence"
    if label in NON_HANDLING_LABELS:
        return "operational_metadata"
    if field and getattr(field, "compute", None) and getattr(field, "readonly", False):
        return "computed_display"
    if field and getattr(field, "readonly", False) and field_name.startswith("p1_visible_"):
        return "p1_readonly_alias"
    if field_name.startswith("p1_visible_"):
        return "p1_product_alias"
    return "formal_product_field"


def _is_product_gap(model_fields, field_name, label):
    return _alignment_boundary_class(model_fields, field_name, label) in {
        "p1_product_alias",
        "formal_product_field",
    }


def _resolve_action(menu):
    action_id = int(menu.get("action_id") or 0)
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    action = Action.browse(action_id)
    if action.exists():
        return action, action_id
    menu_xmlid = menu.get("menu_xmlid") or menu.get("menu_key") or menu.get("page_key") or ""
    current_menu = env.ref(menu_xmlid, raise_if_not_found=False) if menu_xmlid else False  # noqa: F821
    if current_menu and current_menu.action and current_menu.action._name == "ir.actions.act_window":
        return current_menu.action.sudo(), current_menu.action.id
    return action, action_id


def _audit_menu(menu):
    action, action_id = _resolve_action(menu)
    row = {
        "group": menu.get("group_label") or "",
        "menu": menu.get("label") or menu.get("name") or "",
        "menu_xmlid": menu.get("menu_xmlid") or "",
        "action_id": action_id,
        "model": menu.get("res_model") or "",
        "domain_issue": "",
        "record_count": 0,
        "checked_records": 0,
        "checked_fields": 0,
        "formal_aligned_fields": 0,
        "readonly_source_only_fields": [],
        "unchecked_source_value_fields": [],
        "missing_formal_target_fields": [],
        "mismatch_fields": [],
        "mismatch_samples": [],
        "severity": "ok",
    }
    if not action.exists():
        row["severity"] = "blocker"
        row["domain_issue"] = "missing_action"
        return row

    action_data = action.read(["name", "res_model", "views", "domain"])[0]
    model_name = action_data.get("res_model") or row["model"]
    row["model"] = model_name
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    model_fields = Model._fields

    domain, domain_issue = _safe_domain(action)
    row["domain_issue"] = domain_issue
    row["record_count"] = Model.search_count(domain)
    search_kwargs = {"order": "id asc"}
    if RECORD_LIMIT > 0:
        search_kwargs["limit"] = RECORD_LIMIT
    records = Model.search(domain, **search_kwargs)
    row["checked_records"] = len(records)

    form_arch = _view_arch(model_name, "form", _action_view_id(action_data, "form"))
    tree_arch = _view_arch(model_name, "tree", _action_view_id(action_data, "tree"))
    form_fields = {item["name"] for item in _view_fields(form_arch)}
    tree_fields = _view_fields(tree_arch)

    field_rows = []
    for item in tree_fields:
        field_name = item["name"]
        label = item["label"] or model_fields.get(field_name) and model_fields[field_name].string or field_name
        if not _field_should_check(model_fields, field_name):
            continue
        candidates = _field_candidates(model_name, field_name, label, form_fields, model_fields)
        formal_candidates = [name for name in candidates if _is_formal_field(name)]
        source_values_seen = 0
        mismatches = 0
        matched = 0
        sample = None

        if not formal_candidates:
            readonly = field_name in form_fields or candidates
            row["readonly_source_only_fields"].append(
                {
                    "field": field_name,
                    "label": label,
                    "boundary_class": _alignment_boundary_class(model_fields, field_name, label),
                    "readonly_source_on_form": bool(readonly),
                }
            )
            if (
                _is_source_only_field(field_name)
                and _is_product_gap(model_fields, field_name, label)
                and _field_has_values(records, field_name, label)
            ):
                row["unchecked_source_value_fields"].append({"field": field_name, "label": label})
            continue

        if not _is_product_gap(model_fields, field_name, label):
            row["formal_aligned_fields"] += 1
            continue

        for record in records:
            source_value = _display_value(record, field_name, label)
            if not _normalize_text(source_value):
                continue
            source_values_seen += 1
            source_field = model_fields.get(field_name)
            candidate_values = []
            is_match = False
            for target_name in formal_candidates:
                target_value = _display_value(record, target_name, label)
                target_field = model_fields.get(target_name)
                candidate_values.append({"field": target_name, "value": _normalize_text(target_value)})
                if _values_match(source_value, source_field, target_value, target_field, label):
                    is_match = True
                    break
            if is_match:
                matched += 1
                continue
            mismatches += 1
            if sample is None:
                sample = {
                    "record_id": record.id,
                    "display_name": record.display_name,
                    "field": field_name,
                    "label": label,
                    "source": _normalize_text(source_value),
                    "targets": candidate_values,
                }

        if not source_values_seen:
            row["formal_aligned_fields"] += 1
            continue
        row["checked_fields"] += 1
        if mismatches:
            field_rows.append(
                {
                    "field": field_name,
                    "label": label,
                    "formal_candidates": formal_candidates,
                    "source_values": source_values_seen,
                    "matched": matched,
                    "mismatches": mismatches,
                    "sample": sample,
                }
            )
        else:
            row["formal_aligned_fields"] += 1

    row["mismatch_fields"] = [
        {k: v for k, v in item.items() if k != "sample"}
        for item in field_rows[:SAMPLE_LIMIT]
    ]
    row["mismatch_samples"] = [
        item["sample"] for item in field_rows if item.get("sample")
    ][:SAMPLE_LIMIT]
    row["missing_formal_target_fields"] = [
        item for item in row["readonly_source_only_fields"]
        if _is_product_gap(model_fields, item["field"], item["label"])
    ][:SAMPLE_LIMIT]

    if field_rows:
        row["severity"] = "mismatch"
    elif row["record_count"] and row["checked_records"] and row["unchecked_source_value_fields"] and not row["checked_fields"]:
        row["severity"] = "blocker"
        row["domain_issue"] = "source_values_without_formal_field_checks"
    elif row["missing_formal_target_fields"]:
        row["severity"] = "needs_formalization"
    return row


def _write_markdown(path, rows, summary):
    lines = [
        "# 用户确认菜单表单数据对齐审计",
        "",
        f"- 产品：`{PRODUCT_KEY}`",
        f"- 菜单数：{summary['menus']}",
        f"- 总记录数：{summary['record_count']}",
        f"- 已检查记录数：{summary['checked_records']}",
        f"- 已检查正式字段：{summary['checked_fields']}",
        f"- 数据不一致菜单：{summary['severity_counts'].get('mismatch', 0)}",
        f"- 仍需正式字段承接菜单：{summary['severity_counts'].get('needs_formalization', 0)}",
        f"- 产品字段缺口：{summary['product_gap_fields']}",
        f"- 非办理型展示字段：{summary['non_handling_display_fields']}",
        "",
        "| 分组 | 菜单 | 模型 | 记录 | 严重度 | 不一致字段 | 只读历史来源字段 |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        mismatch = ", ".join("%s(%s)" % (item["label"], item["mismatches"]) for item in row["mismatch_fields"][:6]) or "-"
        readonly = ", ".join(item["label"] for item in row["readonly_source_only_fields"][:8]) or "-"
        lines.append(
            "| {group} | {menu} | `{model}` | {records} | {severity} | {mismatch} | {readonly} |".format(
                group=row["group"],
                menu=row["menu"],
                model=row["model"],
                records=row["record_count"],
                severity=row["severity"],
                mismatch=mismatch,
                readonly=readonly,
            )
        )
    lines.extend(["", "## 差异示例", ""])
    for row in rows:
        if not row["mismatch_samples"]:
            continue
        lines.append("### %s / %s" % (row["group"], row["menu"]))
        for sample in row["mismatch_samples"][:5]:
            targets = "; ".join("%s=%s" % (item["field"], item["value"]) for item in sample["targets"])
            lines.append(
                "- 记录 `{record_id}` `{display_name}`，字段 `{label}`：验收值 `{source}`；正式字段 {targets}".format(
                    record_id=sample["record_id"],
                    display_name=sample["display_name"],
                    label=sample["label"],
                    source=sample["source"],
                    targets=targets or "-",
                )
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


baseline, baseline_path = _load_baseline()
menus = _menus_for_product(baseline)
rows = []
for index, menu in enumerate(menus, start=1):
    row = _audit_menu(menu)
    rows.append(row)
    print(
        json.dumps(
            {
                "progress": "%s/%s" % (index, len(menus)),
                "menu": row["menu"],
                "model": row["model"],
                "records": row["record_count"],
                "checked_records": row["checked_records"],
                "severity": row["severity"],
                "mismatch_fields": len(row["mismatch_fields"]),
                "readonly_source_only_fields": len(row["readonly_source_only_fields"]),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
severity_counts = Counter(row["severity"] for row in rows)
model_counts = Counter(row["model"] for row in rows)
readonly_source_only_field_details = [
    {
        "group": row["group"],
        "menu": row["menu"],
        "model": row["model"],
        "fields": row["readonly_source_only_fields"],
        "unchecked_source_value_fields": row["unchecked_source_value_fields"],
    }
    for row in rows
    if row["readonly_source_only_fields"]
]
readonly_boundary_counts = Counter(
    item.get("boundary_class") or "unknown"
    for row in rows
    for item in row["readonly_source_only_fields"]
)
product_gap_field_details = [
    {
        "group": row["group"],
        "menu": row["menu"],
        "model": row["model"],
        "fields": row["missing_formal_target_fields"],
    }
    for row in rows
    if row["missing_formal_target_fields"]
]
non_handling_display_field_details = [
    {
        "group": row["group"],
        "menu": row["menu"],
        "model": row["model"],
        "fields": [
            item for item in row["readonly_source_only_fields"]
            if not _is_product_gap(env[row["model"]]._fields, item["field"], item["label"])  # noqa: F821
        ],
    }
    for row in rows
    if any(
        not _is_product_gap(env[row["model"]]._fields, item["field"], item["label"])  # noqa: F821
        for item in row["readonly_source_only_fields"]
    )
]
summary = {
    "audit": "user_confirmed_form_data_alignment_audit",
    "baseline": str(baseline_path),
    "product_key": PRODUCT_KEY,
    "record_limit": RECORD_LIMIT,
    "menus": len(rows),
    "models": len(model_counts),
    "record_count": sum(row["record_count"] for row in rows),
    "checked_records": sum(row["checked_records"] for row in rows),
    "checked_fields": sum(row["checked_fields"] for row in rows),
    "mismatch_fields": sum(len(row["mismatch_fields"]) for row in rows),
    "readonly_source_only_fields": sum(len(row["readonly_source_only_fields"]) for row in rows),
    "readonly_boundary_counts": dict(readonly_boundary_counts),
    "product_gap_fields": sum(len(row["missing_formal_target_fields"]) for row in rows),
    "product_gap_field_details": product_gap_field_details[:SAMPLE_LIMIT],
    "non_handling_display_fields": sum(
        count
        for boundary, count in readonly_boundary_counts.items()
        if boundary not in {"p1_product_alias", "formal_product_field"}
    ),
    "non_handling_display_field_details": non_handling_display_field_details[:SAMPLE_LIMIT],
    "readonly_source_only_field_details": readonly_source_only_field_details[:SAMPLE_LIMIT],
    "severity_counts": dict(severity_counts),
    "status": "PASS" if not severity_counts.get("blocker") and not severity_counts.get("mismatch") else "FAIL",
}

out_dir = _output_dir()
(out_dir / "user_confirmed_form_data_alignment_audit.json").write_text(
    json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
_write_markdown(out_dir / "user_confirmed_form_data_alignment_audit.md", rows, summary)
print(json.dumps(summary, ensure_ascii=False))
