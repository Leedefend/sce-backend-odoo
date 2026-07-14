# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from odoo.addons.smart_construction_core import core_extension_contract_helpers as _contract_helpers

_sc_text = _contract_helpers.sc_text
_sc_collect_field_nodes = _contract_helpers.sc_collect_field_nodes
_sc_set_v2_container_tree = _contract_helpers.sc_set_v2_container_tree
_sc_set_v2_widget_status = _contract_helpers.sc_set_v2_widget_status
_sc_set_v2_governance_patch = _contract_helpers.sc_set_v2_governance_patch
_sc_replace_contract_content = _contract_helpers.sc_replace_contract_content
_sc_form_layout_governance = _contract_helpers.sc_form_layout_governance
_sc_apply_form_layout_governance_to_group = _contract_helpers.sc_apply_form_layout_governance_to_group

def normalize_construction_diary_form(contract: dict[str, Any], source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
    if model != "sc.construction.diary" or view_type != "form":
        return
    groups: list[tuple[str, list[str]]] = [
        ("项目与日志", ["project_id", "date_diary", "diary_type", "title"]),
        ("现场情况", ["weather", "construction_unit", "project_manager", "manpower_count", "attendance_equipment"]),
        ("施工内容", ["description", "material_inspection_note", "hidden_acceptance_note", "next_plan"]),
        ("质量安全", ["quality_name", "safety_note", "test_block_note", "design_change_note"]),
        ("办理信息", ["handler_name", "note"]),
    ]
    ordered_fields = [name for _title, names in groups for name in names]
    labels = {
        "date_diary": "日志日期",
        "diary_type": "日志类型",
        "title": "日志标题",
        "description": "今日施工内容",
        "material_inspection_note": "材料进场/送检",
        "hidden_acceptance_note": "隐蔽工程验收",
        "next_plan": "下步计划",
        "quality_name": "质量事项",
        "safety_note": "安全情况",
        "test_block_note": "试块制作",
        "design_change_note": "设计变更/技术核定",
        "handler_name": "经办人",
    }
    required = {"project_id", "date_diary", "diary_type"}
    readonly = {"name", "document_no", "source_origin", "state"}
    field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    existing: dict[str, dict[str, Any]] = {}
    _sc_collect_field_nodes(layout_contract.get("containerTree"), existing)

    def descriptor(name: str) -> dict[str, Any]:
        raw = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
        label = labels.get(name) or raw.get("string") or raw.get("label") or name
        return {
            "name": name,
            "label": label,
            "string": label,
            "type": raw.get("type") or raw.get("ttype") or "char",
            "required": name in required,
            "readonly": name in readonly or bool(raw.get("readonly")),
            "domain": raw.get("domain") if isinstance(raw.get("domain"), list) else [],
            "context": raw.get("context") if isinstance(raw.get("context"), dict) else {},
            **({"relation": raw.get("relation")} if raw.get("relation") else {}),
            **({"selection": raw.get("selection")} if isinstance(raw.get("selection"), list) else {}),
        }

    def normalize_node(name: str) -> dict[str, Any]:
        node = deepcopy(existing.get(name) or {"type": "field", "name": name, "children": [], "widgetList": []})
        info = descriptor(name)
        label = _sc_text(info.get("label")) or name
        node.update({"type": "field", "name": name, "string": label, "label": label, "widgetId": f"field.{name}"})
        node["fieldInfo"] = {**(node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}), **info}
        node["field_info"] = {**(node.get("field_info") if isinstance(node.get("field_info"), dict) else {}), **info}
        config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
        config.update({"fieldType": info.get("type"), "required": name in required, "readonly": bool(info.get("readonly"))})
        if info.get("selection"):
            config["selection"] = info.get("selection")
        if info.get("relation"):
            config["relation"] = info.get("relation")
        node["componentConfig"] = config
        return node

    container_tree: list[dict[str, Any]] = [{
        "type": "header",
        "name": "status",
        "children": [normalize_node("state")] if "state" in field_map or "state" in existing else [],
        "widgetList": [],
    }]
    for index, (title, names) in enumerate(groups, start=1):
        children = [normalize_node(name) for name in names if name in field_map or name in existing]
        if not children:
            continue
        container_tree.append({
            "type": "group",
            "name": "construction_diary_%s" % index,
            "string": title,
            "label": title,
            "children": children,
            "widgetList": [],
        })
    _sc_set_v2_container_tree(contract, container_tree)
    _sc_set_v2_widget_status(
        contract,
        [
            {
                "widgetId": f"field.{name}",
                "visible": True,
                "readonly": name in readonly,
                "required": name in required,
                "disabled": name in readonly,
                "auth": "readonly" if name in readonly else "edit",
            }
            for name in ["state"] + ordered_fields
        ],
    )
    _sc_set_v2_governance_patch(contract, "construction_diary_form", {
        "applied": True,
        "model": model,
        "visible_fields": ordered_fields,
        "hidden_reason": "construction_diary_handling_projection",
    })

def general_contract_tax_contract(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(contract, dict):
        return
    model = _sc_text(
        contract.get("model")
        or (source_contract or {}).get("model")
        or ((contract.get("head") or {}).get("model") if isinstance(contract.get("head"), dict) else "")
    )
    field_map = contract.get("fields") if isinstance(contract.get("fields"), dict) else {}
    source_fields = (source_contract or {}).get("fields") if isinstance((source_contract or {}).get("fields"), dict) else {}
    if model != "sc.general.contract" or ("tax_id" not in field_map and "tax_id" not in source_fields):
        return

    def is_tax_rate_node(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        name = _sc_text(value.get("name") or value.get("field") or value.get("fieldCode"))
        widget_id = _sc_text(value.get("widgetId") or value.get("id"))
        return name == "tax_rate" or widget_id == "field.tax_rate"

    def is_tax_id_node(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        name = _sc_text(value.get("name") or value.get("field") or value.get("fieldCode"))
        widget_id = _sc_text(value.get("widgetId") or value.get("id"))
        return name == "tax_id" or widget_id == "field.tax_id"

    tax_field = field_map.get("tax_id") if isinstance(field_map.get("tax_id"), dict) else {}
    if not tax_field and isinstance(source_fields.get("tax_id"), dict):
        tax_field = source_fields.get("tax_id") or {}

    def tax_id_field_node(source_node: dict[str, Any]) -> dict[str, Any]:
        role = source_node.get("formStructureRole") if isinstance(source_node.get("formStructureRole"), dict) else {
            "role": "amount",
            "slot": "amount_progress",
            "group": "amounts",
        }
        descriptor = dict(tax_field or {})
        descriptor.update({"name": "tax_id", "label": "税率", "string": "税率", "type": "many2one", "widget": "many2one"})
        return {
            "type": "field",
            "name": "tax_id",
            "formStructureRole": role,
            "string": "税率",
            "label": "税率",
            "fieldInfo": descriptor,
            "widget": "many2one",
            "componentKey": "sc.input.many2one",
            "componentConfig": {"readonly": False, "required": False, "fieldType": "many2one"},
            "widgetId": "field.tax_id",
            "field_info": descriptor,
            "children": [],
            "widgetList": [],
        }

    def is_form_field_node(value: dict[str, Any]) -> bool:
        return _sc_text(value.get("type")) == "field" or isinstance(value.get("fieldInfo"), dict) or isinstance(value.get("field_info"), dict)

    def clean(value: Any):
        if isinstance(value, list):
            return [item for item in (clean(item) for item in value) if item is not None]
        if isinstance(value, dict):
            if is_tax_rate_node(value):
                return tax_id_field_node(value) if is_form_field_node(value) else None
            copied = {}
            for key, item in value.items():
                if key == "tax_rate":
                    continue
                copied[key] = clean(item)
            return copied
        return value

    cleaned = clean(contract)
    if isinstance(cleaned, dict):
        _sc_replace_contract_content(contract, cleaned)

    status_contract = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
    tax_status_rows = [
        row for row in widget_status
        if isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.tax_id"
    ]
    if not tax_status_rows:
        tax_status_rows = [{"widgetId": "field.tax_id", "visible": True, "readonly": False, "required": False, "disabled": False, "auth": "edit"}]
        widget_status.extend(tax_status_rows)
    for row in tax_status_rows:
        row["visible"] = True
        row["readonly"] = False
        row["disabled"] = False
        row["auth"] = "edit"
    if widget_status:
        _sc_set_v2_widget_status(contract, [
            row for row in widget_status
            if not (isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.tax_rate")
        ])

    def has_tax_id_layout_node(value: Any) -> bool:
        if is_tax_id_node(value) and (_sc_text((value or {}).get("type")) == "field" or isinstance((value or {}).get("fieldInfo"), dict) or isinstance((value or {}).get("field_info"), dict)):
            return True
        if isinstance(value, list):
            return any(has_tax_id_layout_node(item) for item in value)
        if isinstance(value, dict):
            return any(has_tax_id_layout_node(item) for item in value.values())
        return False

    if has_tax_id_layout_node(contract):
        return
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
    if not container_tree:
        return
    target_field_names = {"contract_amount", "amount_total", "amount_untaxed", "settlement_amount"}

    def append_after_amount_node(rows: list[Any]) -> bool:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            name = _sc_text(row.get("name") or row.get("field") or row.get("fieldCode"))
            widget_id = _sc_text(row.get("widgetId"))
            if name in target_field_names or widget_id in {f"field.{name}" for name in target_field_names}:
                rows.insert(index + 1, tax_id_field_node(row))
                return True
            for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
                children = row.get(key)
                if isinstance(children, list) and append_after_amount_node(children):
                    return True
        return False

    if append_after_amount_node(container_tree):
        _sc_set_v2_container_tree(contract, container_tree)

def normalize_general_contract_company_form(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(contract, dict):
        return
    model = _sc_text(
        contract.get("model")
        or (source_contract or {}).get("model")
        or ((contract.get("pageInfo") or {}).get("model") if isinstance(contract.get("pageInfo"), dict) else "")
        or ((contract.get("head") or {}).get("model") if isinstance(contract.get("head"), dict) else "")
    )
    view_type = _sc_text(
        contract.get("viewType")
        or ((contract.get("pageInfo") or {}).get("viewType") if isinstance(contract.get("pageInfo"), dict) else "")
        or (source_contract or {}).get("view_type")
    ).lower()
    if model != "sc.general.contract" or view_type != "form":
        return
    groups: list[tuple[str, list[str]]] = [
        ("合同基本信息", ["contract_name", "contract_no", "contract_type", "contract_direction", "project_id"]),
        ("合同方", ["partner_id", "partner_name_text", "credit_code", "contact_name", "contact_phone", "engineering_address", "bank_name", "bank_account"]),
        ("金额与条款", ["amount_total", "tax_id", "amount_untaxed", "currency_id", "payment_terms", "special_condition"]),
        ("签署与履约", ["contract_date", "expected_sign_date", "completion_date", "signing_place", "pricing_mode", "union_mode", "subcontract_mode"]),
        ("办理信息", ["applicant_name", "applicant_department", "handler_id", "purchase_engineer", "note"]),
    ]
    ordered_fields = [name for _title, names in groups for name in names]
    visible = set(ordered_fields)
    governance = _sc_form_layout_governance(source_contract)
    hidden_field_names = {_sc_text(item) for item in (governance.get("hidden_field_names") or []) if _sc_text(item)}
    visible.difference_update(hidden_field_names)
    labels = {
        "project_id": "关联项目",
        "partner_name_text": "合同方",
        "amount_total": "合同金额",
        "expected_sign_date": "预计签订日期",
        "signing_place": "签订地点",
        "subcontract_mode": "分包类型",
    }
    required = {"contract_name", "amount_total"}
    readonly = {"contract_no"}
    field_map = (source_contract or {}).get("fields") if isinstance((source_contract or {}).get("fields"), dict) else {}
    existing: dict[str, dict[str, Any]] = {}
    _sc_collect_field_nodes((contract.get("layoutContract") or {}).get("containerTree") if isinstance(contract.get("layoutContract"), dict) else [], existing)

    def descriptor(name: str) -> dict[str, Any]:
        raw = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
        label = labels.get(name) or raw.get("string") or raw.get("label") or name
        return {
            "name": name,
            "label": label,
            "string": label,
            "type": raw.get("type") or raw.get("ttype") or "char",
            "required": name in required or bool(raw.get("required")),
            "readonly": name in readonly or bool(raw.get("readonly")),
            "domain": raw.get("domain") if isinstance(raw.get("domain"), list) else [],
            "context": raw.get("context") if isinstance(raw.get("context"), dict) else {},
            **({"relation": raw.get("relation")} if raw.get("relation") else {}),
            **({"selection": raw.get("selection")} if isinstance(raw.get("selection"), list) else {}),
        }

    def normalize_node(name: str) -> dict[str, Any]:
        node = deepcopy(existing.get(name) or {"type": "field", "name": name, "children": [], "widgetList": []})
        info = descriptor(name)
        label = _sc_text(info.get("label")) or name
        node.update({"type": "field", "name": name, "string": label, "label": label, "widgetId": f"field.{name}"})
        node["fieldInfo"] = {**(node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}), **info}
        node["field_info"] = {**(node.get("field_info") if isinstance(node.get("field_info"), dict) else {}), **info}
        config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
        config.update({"fieldType": info.get("type"), "required": name in required, "readonly": bool(info.get("readonly"))})
        if info.get("selection"):
            config["selection"] = info.get("selection")
        if info.get("relation"):
            config["relation"] = info.get("relation")
        node["componentConfig"] = config
        return node

    container_tree: list[dict[str, Any]] = [{"type": "header", "name": "status", "children": [normalize_node("state")] if "state" in existing else [], "widgetList": []}]
    for index, (title, names) in enumerate(groups, start=1):
        children = [normalize_node(name) for name in names if name in visible and (name in field_map or name in existing)]
        if not children:
            continue
        group_node = {"type": "group", "name": "general_contract_%s" % index, "string": title, "label": title, "children": children, "widgetList": []}
        _sc_apply_form_layout_governance_to_group(group_node, title, source_contract=source_contract)
        container_tree.append(group_node)
    _sc_set_v2_container_tree(contract, container_tree)
    _sc_set_v2_widget_status(contract, [
        {
            "widgetId": f"field.{name}",
            "visible": True,
            "readonly": name in readonly,
            "required": name in required,
            "disabled": name in readonly,
            "auth": "readonly" if name in readonly else "edit",
        }
        for name in ["state"] + ordered_fields
        if name == "state" or name in visible
    ])
    _sc_set_v2_governance_patch(contract, "general_contract_company_form", {
        "applied": True,
        "model": model,
        "visible_fields": ordered_fields,
        "hidden_reason": "company_general_contract_handling_projection",
    })

    def replace_amount_label(value: Any) -> Any:
        if isinstance(value, str):
            return "合同金额" if value == "最终合同价" else value
        if isinstance(value, list):
            return [replace_amount_label(item) for item in value]
        if isinstance(value, dict):
            return {key: replace_amount_label(item) for key, item in value.items()}
        return value

    replaced = replace_amount_label(contract)
    if isinstance(replaced, dict):
        _sc_replace_contract_content(contract, replaced)

def model_specific_form_contract_policy(payload: dict[str, Any] | None) -> dict[str, list[str]] | None:
    safe_payload = payload if isinstance(payload, dict) else {}
    model = _sc_text(safe_payload.get("model"))
    fields_map = safe_payload.get("fields") if isinstance(safe_payload.get("fields"), dict) else {}
    if model == "sc.general.contract" and "tax_id" in fields_map and "tax_rate" in fields_map:
        return {"remove_fields": ["tax_rate"]}
    return None

def form_field_aliases(payload: dict[str, Any] | None) -> dict[str, str] | None:
    safe_payload = payload if isinstance(payload, dict) else {}
    model = _sc_text(safe_payload.get("model"))
    source = safe_payload.get("source_contract") if isinstance(safe_payload.get("source_contract"), dict) else {}
    fields_map = source.get("fields") if isinstance(source.get("fields"), dict) else {}
    if model == "sc.general.contract" and "tax_id" in fields_map:
        return {"tax_rate": "tax_id"}
    return None
