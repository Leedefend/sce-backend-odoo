# -*- coding: utf-8 -*-
from odoo.addons.smart_core.utils.contract_governance import (
    apply_project_form_domain_override,
    register_contract_domain_override,
)


_PROJECT_INTAKE_SCENE_KEY = "projects.intake"
_PROJECT_INTAKE_STANDARD_ROUTE = "/s/project.management"
_PROJECT_INTAKE_STANDARD_MENU_XMLID = "smart_construction_core.menu_sc_project_initiation"
_PROJECT_INTAKE_QUICK_MENU_XMLID = "smart_construction_core.menu_sc_project_quick_create"


def _text(value):
    return str(value or "").strip()


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _is_project_intake_create_contract(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    head = _as_dict(data.get("head"))
    model = _text(head.get("model") or data.get("model"))
    render_profile = _text(head.get("render_profile") or data.get("render_profile")).lower()
    scene_key = _text(head.get("scene_key") or data.get("scene_key"))
    menu_xmlid = _text(head.get("menu_xmlid") or data.get("menu_xmlid"))
    return (
        model == "project.project"
        and render_profile == "create"
        and (
            scene_key == _PROJECT_INTAKE_SCENE_KEY
            or menu_xmlid in {
                _PROJECT_INTAKE_STANDARD_MENU_XMLID,
                _PROJECT_INTAKE_QUICK_MENU_XMLID,
            }
        )
    )


def _resolve_project_intake_mode(data: dict) -> str:
    head = _as_dict(data.get("head"))
    menu_xmlid = _text(head.get("menu_xmlid") or data.get("menu_xmlid"))
    if menu_xmlid == _PROJECT_INTAKE_QUICK_MENU_XMLID:
        return "quick"
    return "standard"


def _apply_project_intake_form_governance(data: dict, contract_mode: str) -> None:
    if contract_mode != "user":
        return
    if not _is_project_intake_create_contract(data):
        return
    intake_mode = _resolve_project_intake_mode(data)
    governance = _as_dict(data.get("form_governance"))
    governance.update(
        {
            "surface": "project_intake",
            "create_flow_mode": intake_mode,
            "autosave_scope": f"project_intake_{intake_mode}",
            "primary_action_label": "创建并进入项目驾驶舱" if intake_mode == "quick" else "创建项目",
            "post_create_target": {
                "intent": "project.dashboard.enter",
                "route": _PROJECT_INTAKE_STANDARD_ROUTE,
            },
        }
    )
    data["form_governance"] = governance


def _is_project_form_contract(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    model = _text(head.get("model") or data.get("model"))
    view_type = _text(head.get("view_type") or data.get("view_type")).lower()
    return model == "project.project" and (view_type == "form" or isinstance(views.get("form"), dict))


def _set_field_label(fields_map: dict, name: str, label: str) -> None:
    descriptor = _as_dict(fields_map.get(name))
    if not descriptor:
        return
    descriptor["string"] = label
    descriptor["label"] = label
    fields_map[name] = descriptor


def _hide_field(data: dict, fields_map: dict, name: str) -> None:
    descriptor = _as_dict(fields_map.get(name))
    if descriptor:
        descriptor["semantic_type"] = "technical"
        descriptor["surface_role"] = "hidden"
        descriptor["technical"] = True
        fields_map[name] = descriptor
    semantics = _as_dict(data.get("field_semantics"))
    semantics[name] = {
        "semantic_type": "technical",
        "surface_role": "hidden",
        "technical": True,
    }
    data["field_semantics"] = semantics
    visible_fields = data.get("visible_fields")
    if isinstance(visible_fields, list):
        data["visible_fields"] = [item for item in visible_fields if _text(item) != name]


def _layout_has_field(nodes, name: str) -> bool:
    if isinstance(nodes, list):
        return any(_layout_has_field(item, name) for item in nodes)
    if not isinstance(nodes, dict):
        return False
    if _text(nodes.get("name") or nodes.get("field")) == name:
        return True
    return any(
        _layout_has_field(nodes.get(key), name)
        for key in ("children", "tabs", "pages", "nodes", "items")
    )


def _append_project_responsibility_section(data: dict) -> None:
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return
    children = []
    if not _layout_has_field(layout, "responsibility_ids"):
        children.append({"type": "field", "name": "responsibility_ids", "string": "项目责任分工"})
    if not _layout_has_field(layout, "collaborator_ids"):
        children.append({"type": "field", "name": "collaborator_ids", "string": "项目协作成员"})
    if not children:
        return
    layout.append({
        "type": "group",
        "name": "sc_project_responsibility_collaboration",
        "title": "项目责任与协作",
        "children": children,
    })
    form["layout"] = layout
    views["form"] = form
    data["views"] = views


def _apply_project_ledger_form_surface_governance(data: dict, contract_mode: str) -> None:
    if contract_mode != "user" or not _is_project_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    _set_field_label(fields_map, "partner_id", "业主单位")
    _set_field_label(fields_map, "owner_id", "业主单位")
    _set_field_label(fields_map, "manager_id", "项目经理")
    _set_field_label(fields_map, "responsibility_ids", "项目责任分工")
    _set_field_label(fields_map, "collaborator_ids", "项目协作成员")
    _hide_field(data, fields_map, "user_id")
    data["fields"] = fields_map
    visible_fields = data.get("visible_fields")
    if isinstance(visible_fields, list):
        for name in ("responsibility_ids", "collaborator_ids"):
            if name in fields_map and name not in visible_fields:
                visible_fields.append(name)
        data["visible_fields"] = visible_fields
    _append_project_responsibility_section(data)


register_contract_domain_override(
    "smart_construction_core.project_form",
    apply_project_form_domain_override,
    priority=10,
)

register_contract_domain_override(
    "smart_construction_core.project_intake_form",
    _apply_project_intake_form_governance,
    priority=20,
)

register_contract_domain_override(
    "smart_construction_core.project_ledger_form_surface",
    _apply_project_ledger_form_surface_governance,
    priority=30,
)
