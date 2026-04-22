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
