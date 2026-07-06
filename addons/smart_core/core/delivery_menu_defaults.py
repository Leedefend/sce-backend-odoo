# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib
from typing import Any, Dict

from .navigation_entry_target import normalize_entry_target
from .source_authority import build_source_authority_contract

SOURCE_KIND = "delivery_menu_default_projection"
SOURCE_AUTHORITIES = ("delivery_engine_v1", "release_surface_menu_payload")
NO_BUSINESS_FACT_AUTHORITY = True
_CURRENT_RECORD_SCOPE_MODELS: set[str] = set()
_CURRENT_PROJECT_SCOPE_MODELS = _CURRENT_RECORD_SCOPE_MODELS


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        synthetic_navigation_only=True,
    )


def synthetic_menu_id(key: str, base: int = 900_000_000, span: int = 50_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def register_current_record_scope_model(model_name: str) -> None:
    model = str(model_name or "").strip()
    if model:
        _CURRENT_RECORD_SCOPE_MODELS.add(model)


def register_current_project_scope_model(model_name: str) -> None:
    register_current_record_scope_model(model_name)


def _record_scope_policy(menu: Dict[str, Any]) -> str:
    explicit = str(menu.get("record_scope_policy") or menu.get("project_scope_policy") or "").strip().lower()
    if explicit in {"current_record", "current_project"}:
        return "current_record"
    if explicit in {"global", "exempt"}:
        return explicit
    model = str(
        menu.get("model")
        or menu.get("res_model")
        or menu.get("integration_model")
        or menu.get("fact_model")
        or ""
    ).strip()
    if model in _CURRENT_RECORD_SCOPE_MODELS:
        return "current_record"
    intent = str(menu.get("entry_intent") or "").strip()
    if intent in {"query", "master_data", "analysis", "config"}:
        return "global"
    if intent in {"handling", "source_fact"}:
        return "current_record"
    required = menu.get("required_relationships")
    if isinstance(required, list) and any(str(item or "").strip() == "project_id" for item in required):
        return "current_record"
    return ""


def _project_scope_policy(menu: Dict[str, Any]) -> str:
    policy = _record_scope_policy(menu)
    if policy == "current_record":
        return "current_project"
    return policy


def build_delivery_menu_child(menu: Dict[str, Any]) -> Dict[str, Any] | None:
    key = str(menu.get("menu_key") or "").strip()
    label = str(menu.get("label") or "").strip()
    route = str(menu.get("route") or "").strip()
    menu_id = menu.get("menu_id")
    action_id = menu.get("action_id")
    model = str(menu.get("model") or "").strip()
    scene_key = str(menu.get("scene_key") or "").strip()
    if not key or not label:
        return None
    if not (route or menu_id or action_id or model or scene_key):
        return None
    meta = {
        "action_type": "delivery.engine",
        "menu_key": key,
        "product_key": str(menu.get("product_key") or "").strip(),
        "capability_key": str(menu.get("capability_key") or "").strip(),
        "source": "delivery_engine_v1",
        "default_source_authority": source_authority_contract(),
    }
    if route:
        meta["route"] = route
    if scene_key:
        meta["scene_key"] = scene_key
    if menu_id:
        meta["menu_id"] = menu_id
    action_xmlid = str(menu.get("action_xmlid") or "").strip()
    if action_id:
        meta["action_id"] = action_id
    if action_xmlid:
        meta["action_xmlid"] = action_xmlid
    if model:
        meta["model"] = model
    view_modes = menu.get("view_modes")
    if isinstance(view_modes, list) and view_modes:
        meta["view_modes"] = view_modes
    record_scope_policy = _record_scope_policy(menu)
    if record_scope_policy:
        meta["record_scope_policy"] = record_scope_policy
        meta["project_scope_policy"] = "current_project" if record_scope_policy == "current_record" else record_scope_policy
    release_state = str(menu.get("release_state") or "").strip()
    if release_state:
        meta["release_state"] = release_state
    menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
    if menu_xmlid:
        meta["menu_xmlid"] = menu_xmlid
    scene_source = str(menu.get("scene_source") or "").strip()
    if scene_source:
        meta["scene_source"] = scene_source
    delivery_bucket = str(menu.get("delivery_bucket") or "").strip()
    if delivery_bucket:
        meta["delivery_bucket"] = delivery_bucket
    for meta_key in (
        "product_domain",
        "product_domain_label",
        "entry_intent",
        "entry_intent_label",
        "fact_model",
        "disposition_policy",
        "integration_target",
        "default_business_category_code",
        "allowed_business_category_codes",
        "required_relationships",
        "locked_data_policy",
        "productization_source",
        "business_entry_contract_version",
        "entry_target_policy",
        "integration_action_id",
        "integration_action_xmlid",
        "integration_view_modes",
        "integration_entry_target",
        "integration_model",
        "record_scope_policy",
        "project_scope_policy",
    ):
        value = menu.get(meta_key)
        if value not in (None, "", []):
            if meta_key == "record_scope_policy":
                normalized = _record_scope_policy({meta_key: value})
                if normalized:
                    meta["record_scope_policy"] = normalized
                    meta["project_scope_policy"] = "current_project" if normalized == "current_record" else normalized
            elif meta_key == "project_scope_policy":
                normalized = _project_scope_policy({meta_key: value})
                if normalized:
                    meta["project_scope_policy"] = normalized
                    meta.setdefault("record_scope_policy", "current_record" if normalized == "current_project" else normalized)
            else:
                meta[meta_key] = value
    entry_target = normalize_entry_target(
        entry_target=menu.get("entry_target"),
        scene_key=scene_key,
        route=route,
        menu_id=menu_id,
        action_id=action_id,
        model=model,
        view_modes=view_modes,
    )
    if entry_target:
        meta["entry_target"] = entry_target
    source_authority = menu.get("source_authority")
    if isinstance(source_authority, dict) and source_authority:
        meta["source_authority"] = source_authority
    node = {
        "key": key,
        "label": label,
        "title": label,
        "menu_id": int(menu_id) if isinstance(menu_id, int) and menu_id > 0 else synthetic_menu_id(key),
        "children": [],
        "meta": meta,
    }
    for field, value in (
        ("route", route),
        ("scene_key", scene_key),
        ("action_id", action_id),
        ("model", model),
        ("view_modes", view_modes if isinstance(view_modes, list) else []),
        ("entry_target", entry_target),
    ):
        if value not in (None, "", []):
            node[field] = value
    try:
        sequence = int(menu.get("sequence") or 0)
    except Exception:
        sequence = 0
    if sequence > 0:
        node["sequence"] = sequence
    return node


def build_delivery_menu_group(group_key: str, group_label: str, children: list[dict]) -> Dict[str, Any]:
    meta = {
        "group_key": group_key,
        "source": "delivery_engine_v1",
        "default_source_authority": source_authority_contract(),
    }
    if children and any(((child.get("meta") or {}).get("release_state") == "preview") for child in children if isinstance(child, dict)):
        meta["release_state"] = "preview"
    return {
        "key": f"group:{group_key}",
        "label": group_label,
        "title": group_label,
        "menu_id": synthetic_menu_id(f"group:{group_key}", base=881_000_000, span=10_000_000),
        "children": children,
        "meta": meta,
    }


def build_delivery_menu_root(group_nodes: list[dict], role_code: str) -> Dict[str, Any]:
    return {
        "key": "root:delivery_engine",
        "label": "产品发布面",
        "title": "产品发布面",
        "menu_id": synthetic_menu_id("root:delivery_engine", base=880_000_000, span=10_000_000),
        "children": group_nodes,
        "meta": {
            "source": "delivery_engine_v1",
            "role_code": role_code,
            "default_source_authority": source_authority_contract(),
        },
    }
