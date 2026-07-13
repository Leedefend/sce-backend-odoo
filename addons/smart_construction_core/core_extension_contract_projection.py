# -*- coding: utf-8 -*-
import logging
from copy import deepcopy
from typing import Any

_logger = logging.getLogger(__name__)


def _sc_text(value) -> str:
    return str(value or "").strip()


def _sc_field_code(node: dict) -> str:
    return _sc_text(node.get("fieldCode") or node.get("name") or node.get("field"))


def _sc_set_project_label(node: dict, field_name: str, label: str) -> None:
    code = _sc_field_code(node)
    if code != field_name:
        return
    node["label"] = label
    node["string"] = label
    field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
    field_info["label"] = label
    field_info["string"] = label
    node["fieldInfo"] = field_info
    if isinstance(node.get("field_info"), dict):
        node["field_info"]["label"] = label
        node["field_info"]["string"] = label
    component_config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
    relation_entry = component_config.get("relationEntry") if isinstance(component_config.get("relationEntry"), dict) else {}
    ui_labels = relation_entry.get("ui_labels") if isinstance(relation_entry.get("ui_labels"), dict) else {}
    if ui_labels:
        ui_labels["dialog_title"] = "%s：搜索更多" % label
        relation_entry["ui_labels"] = ui_labels
        component_config["relationEntry"] = relation_entry
        node["componentConfig"] = component_config


def _sc_prune_and_label_project_nodes(value):
    if isinstance(value, list):
        out = []
        for item in value:
            pruned = _sc_prune_and_label_project_nodes(item)
            if pruned is not None:
                out.append(pruned)
        return out
    if not isinstance(value, dict):
        return value
    if _sc_field_code(value) == "user_id" or _sc_text(value.get("widgetId")) == "field.user_id":
        return None
    node = dict(value)
    for field_name, label in {
        "partner_id": "业主单位",
        "owner_id": "业主单位",
        "manager_id": "项目经理",
        "responsibility_ids": "项目责任分工",
        "collaborator_ids": "项目协作成员",
    }.items():
        _sc_set_project_label(node, field_name, label)
    for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"):
        if isinstance(node.get(key), list):
            node[key] = _sc_prune_and_label_project_nodes(node[key])
    return node


def _sc_project_field_widget(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
    config = {"fieldType": field_type}
    if relation:
        config["relation"] = relation
    return {
        "widgetId": "field.%s" % field_name,
        "widgetType": "table" if field_type in {"one2many", "many2many"} else "select",
        "fieldCode": field_name,
        "label": label,
        "span": 12,
        "componentKey": "sc.table.data" if field_type in {"one2many", "many2many"} else "sc.select.remote",
        "capabilities": [],
        "componentConfig": config,
    }


def _sc_project_field_node(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
    widget = _sc_project_field_widget(field_name, label, field_type, relation=relation)
    return {
        "type": "field",
        "name": field_name,
        "string": label,
        "label": label,
        "fieldInfo": {
            "name": field_name,
            "label": label,
            "string": label,
            "type": field_type,
            "relation": relation,
            "widget": widget["widgetType"],
        },
        "field_info": {
            "name": field_name,
            "label": label,
            "string": label,
            "type": field_type,
            "relation": relation,
            "widget": widget["widgetType"],
        },
        "widget": widget["widgetType"],
        "componentKey": widget["componentKey"],
        "componentConfig": deepcopy(widget["componentConfig"]),
        "widgetId": widget["widgetId"],
    }


def _sc_node_has_field(value, field_name: str) -> bool:
    if isinstance(value, list):
        return any(_sc_node_has_field(item, field_name) for item in value)
    if not isinstance(value, dict):
        return False
    if _sc_field_code(value) == field_name:
        return True
    return any(_sc_node_has_field(value.get(key), field_name) for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"))


def _sc_append_project_responsibility_group(contract: dict, *, include_collaborators: bool) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    if not tree:
        return
    children = []
    if not _sc_node_has_field(tree, "responsibility_ids"):
        children.append(_sc_project_field_node("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"))
    if include_collaborators and not _sc_node_has_field(tree, "collaborator_ids"):
        children.append(_sc_project_field_node("collaborator_ids", "项目协作成员", "many2many", relation="res.users"))
    if not children:
        return
    group = {
        "type": "group",
        "name": "sc_project_responsibility_collaboration",
        "containerId": "sc_project_responsibility_collaboration",
        "containerType": "group",
        "string": "项目责任与协作",
        "label": "项目责任与协作",
        "children": children,
        "widgetList": [
            _sc_project_field_widget("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"),
            *(
                [_sc_project_field_widget("collaborator_ids", "项目协作成员", "many2many", relation="res.users")]
                if include_collaborators else []
            ),
        ],
    }
    target = tree[0] if isinstance(tree[0], dict) else None
    if target is None:
        return
    if isinstance(target.get("children"), list):
        target["children"].append(group)
    else:
        tree.append(group)
    layout["containerTree"] = tree
    registry = layout.get("componentRegistry") if isinstance(layout.get("componentRegistry"), dict) else {}
    registry["sc.table.data"] = {"componentKey": "sc.table.data"}
    layout["componentRegistry"] = registry
    contract["layoutContract"] = layout
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    widget_status = [row for row in status.get("widgetStatus", []) if isinstance(row, dict) and _sc_text(row.get("widgetId")) != "field.user_id"]
    field_names = ["responsibility_ids"]
    if include_collaborators:
        field_names.append("collaborator_ids")
    for field_name in field_names:
        widget_id = "field.%s" % field_name
        if not any(_sc_text(row.get("widgetId")) == widget_id for row in widget_status):
            widget_status.append({"widgetId": widget_id, "visible": True, "readonly": False, "required": False, "disabled": False, "auth": "edit"})
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status


def smart_core_finalize_unified_page_contract_v2(env, contract, context):
    if not isinstance(contract, dict):
        return None
    context = context if isinstance(context, dict) else {}
    source = context.get("source_contract") if isinstance(context.get("source_contract"), dict) else {}
    head = source.get("head") if isinstance(source.get("head"), dict) else {}
    model = _sc_text(source.get("model") or head.get("model"))
    view_type = _sc_text(source.get("view_type") or head.get("view_type") or (context or {}).get("view_type")).lower()
    render_profile = _sc_text(source.get("render_profile") or head.get("render_profile") or (((context or {}).get("meta") or {}).get("params") or {}).get("render_profile")).lower()
    out = deepcopy(contract)
    _sc_inject_workflow_contract(env, out, source, model=model, view_type=view_type)
    _sc_normalize_construction_diary_form(out, source, model=model, view_type=view_type)
    if model != "project.project" or view_type != "form":
        return out if out != contract else None
    layout = out.get("layoutContract") if isinstance(out.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    layout["containerTree"] = _sc_prune_and_label_project_nodes(tree)
    out["layoutContract"] = layout
    status = out.get("statusContract") if isinstance(out.get("statusContract"), dict) else {}
    if isinstance(status.get("widgetStatus"), list):
        status["widgetStatus"] = [
            row for row in status["widgetStatus"]
            if not (isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.user_id")
        ]
        out["statusContract"] = status
    _sc_append_project_responsibility_group(out, include_collaborators=render_profile != "create")
    return out


def smart_core_normalize_projected_contract_data(env, data, context):
    del env, context
    if not isinstance(data, dict):
        return None
    out = deepcopy(data)
    _sc_general_contract_tax_contract(out)
    return out if out != data else None


def smart_core_normalize_unified_page_contract_v2(env, contract, context):
    del env
    if not isinstance(contract, dict):
        return None
    source = (context or {}).get("source_contract") if isinstance(context, dict) else {}
    source = source if isinstance(source, dict) else {}
    out = deepcopy(contract)
    _sc_general_contract_tax_contract(out, source_contract=source)
    _sc_normalize_general_contract_company_form(out, source_contract=source)
    return out if out != contract else None


def _sc_field_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    return _sc_text(node.get("name") or node.get("field") or node.get("fieldCode"))


def _sc_collect_field_nodes(nodes: Any, existing: dict[str, dict[str, Any]]) -> None:
    if isinstance(nodes, list):
        for item in nodes:
            _sc_collect_field_nodes(item, existing)
        return
    if not isinstance(nodes, dict):
        return
    if _sc_text(nodes.get("type")) == "field":
        name = _sc_field_name(nodes)
        if name and name not in existing:
            existing[name] = deepcopy(nodes)
    for key in ("children", "widgetList", "pages", "tabs", "nodes", "items", "containerTree"):
        _sc_collect_field_nodes(nodes.get(key), existing)


def _sc_set_v2_container_tree(contract: dict[str, Any], container_tree: list[Any]) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    layout["containerTree"] = container_tree
    contract["layoutContract"] = layout
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["containerTree"] = container_tree
    contract["runtimeContract"] = runtime


def _sc_set_v2_widget_status(contract: dict[str, Any], widget_status: list[dict[str, Any]]) -> None:
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["widgetStatus"] = widget_status
    contract["runtimeContract"] = runtime


def _sc_set_v2_governance_patch(contract: dict[str, Any], key: str, patch: dict[str, Any]) -> None:
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    patches = runtime.get("governancePatches") if isinstance(runtime.get("governancePatches"), dict) else {}
    patches[key] = patch
    runtime["governancePatches"] = patches
    contract["runtimeContract"] = runtime
    meta = contract.get("meta") if isinstance(contract.get("meta"), dict) else {}
    meta_patches = meta.get("governance_patches") if isinstance(meta.get("governance_patches"), dict) else {}
    meta_patches[key] = patch
    meta["governance_patches"] = meta_patches
    contract["meta"] = meta


def _sc_normalize_construction_diary_form(contract: dict[str, Any], source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
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


def _sc_replace_contract_content(contract: dict[str, Any], replacement: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not isinstance(replacement, dict):
        return
    contract.clear()
    contract.update(replacement)


def _sc_general_contract_tax_contract(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
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


def _sc_form_layout_governance(source_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(source_contract, dict):
        return {}
    profile = source_contract.get("business_operation_profile")
    governance = profile.get("form_structure_governance") if isinstance(profile, dict) else {}
    return governance if isinstance(governance, dict) else {}


def _sc_form_layout_columns_from_governance(governance: dict[str, Any] | None, title: str = "") -> int:
    if not isinstance(governance, dict):
        return 0
    group_columns = governance.get("group_columns") if isinstance(governance.get("group_columns"), dict) else {}
    key = _sc_text(title)
    try:
        columns = int(group_columns.get(key) or 0) if key else 0
    except (TypeError, ValueError):
        columns = 0
    if columns <= 0:
        try:
            columns = int(governance.get("form_columns") or 0)
        except (TypeError, ValueError):
            columns = 0
    return columns if columns > 0 else 0


def _sc_apply_form_layout_governance_to_group(node: dict[str, Any], title: str = "", *, source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(node, dict):
        return
    resolved_title = _sc_text(title or node.get("string") or node.get("label") or node.get("title") or node.get("name"))
    columns = _sc_form_layout_columns_from_governance(_sc_form_layout_governance(source_contract), resolved_title)
    if columns <= 0:
        return
    node["cols"] = columns
    node["columns"] = columns
    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
    attrs["col"] = str(columns)
    node["attributes"] = attrs


def _sc_normalize_general_contract_company_form(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
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


def _sc_inject_workflow_contract(env, contract, source, *, model, view_type):
    if view_type != "form" or not model:
        return
    if env is None or not getattr(env, "registry", None):
        return
    record_id = (
        source.get("record_id")
        or source.get("recordId")
        or ((source.get("head") or {}).get("record_id") if isinstance(source.get("head"), dict) else None)
    )
    try:
        record_id = int(record_id or 0)
    except Exception:
        record_id = 0
    if record_id <= 0:
        return
    try:
        if model not in env.registry:
            return
        record = env[model].browse(record_id).exists()
        if not record:
            return
        workflow_contract = env["sc.workflow.contract.service"].describe_record(record)
    except Exception:
        _logger.exception("Failed to inject workflow contract for %s,%s", model, record_id)
        return
    if not isinstance(workflow_contract, dict) or not workflow_contract:
        return
    contract["workflowContract"] = workflow_contract
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["workflowContract"] = workflow_contract
    contract["runtimeContract"] = runtime
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    global_status = status.get("globalStatus") if isinstance(status.get("globalStatus"), dict) else {}
    editability = _sc_text(workflow_contract.get("editability"))
    if editability in {"readonly", "locked"}:
        global_status["pageAuth"] = "read"
    elif editability == "editable":
        global_status["pageAuth"] = "edit"
    global_status["workflowPhase"] = workflow_contract.get("businessPhase")
    global_status["approvalPhase"] = workflow_contract.get("approvalPhase")
    status["globalStatus"] = global_status
    contract["statusContract"] = status

