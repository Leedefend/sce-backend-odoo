# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy


def sc_text(value) -> str:
    return str(value or "").strip()


def sc_field_code(node: dict) -> str:
    return sc_text(node.get("fieldCode") or node.get("name") or node.get("field"))


def sc_set_project_label(node: dict, field_name: str, label: str) -> None:
    code = sc_field_code(node)
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


def sc_prune_and_label_project_nodes(value):
    if isinstance(value, list):
        out = []
        for item in value:
            pruned = sc_prune_and_label_project_nodes(item)
            if pruned is not None:
                out.append(pruned)
        return out
    if not isinstance(value, dict):
        return value
    if sc_field_code(value) == "user_id" or sc_text(value.get("widgetId")) == "field.user_id":
        return None
    node = dict(value)
    for field_name, label in {
        "partner_id": "业主单位",
        "owner_id": "业主单位",
        "manager_id": "项目经理",
        "responsibility_ids": "项目责任分工",
        "collaborator_ids": "项目协作成员",
    }.items():
        sc_set_project_label(node, field_name, label)
    for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"):
        if isinstance(node.get(key), list):
            node[key] = sc_prune_and_label_project_nodes(node[key])
    return node


def sc_project_field_widget(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
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


def sc_project_field_node(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
    widget = sc_project_field_widget(field_name, label, field_type, relation=relation)
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


def sc_node_has_field(value, field_name: str) -> bool:
    if isinstance(value, list):
        return any(sc_node_has_field(item, field_name) for item in value)
    if not isinstance(value, dict):
        return False
    if sc_field_code(value) == field_name:
        return True
    return any(sc_node_has_field(value.get(key), field_name) for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"))


def sc_append_project_responsibility_group(contract: dict, *, include_collaborators: bool) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    if not tree:
        return
    children = []
    if not sc_node_has_field(tree, "responsibility_ids"):
        children.append(sc_project_field_node("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"))
    if include_collaborators and not sc_node_has_field(tree, "collaborator_ids"):
        children.append(sc_project_field_node("collaborator_ids", "项目协作成员", "many2many", relation="res.users"))
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
            sc_project_field_widget("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"),
            *(
                [sc_project_field_widget("collaborator_ids", "项目协作成员", "many2many", relation="res.users")]
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
    widget_status = [row for row in status.get("widgetStatus", []) if isinstance(row, dict) and sc_text(row.get("widgetId")) != "field.user_id"]
    field_names = ["responsibility_ids"]
    if include_collaborators:
        field_names.append("collaborator_ids")
    for field_name in field_names:
        widget_id = "field.%s" % field_name
        if not any(sc_text(row.get("widgetId")) == widget_id for row in widget_status):
            widget_status.append({"widgetId": widget_id, "visible": True, "readonly": False, "required": False, "disabled": False, "auth": "edit"})
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status
