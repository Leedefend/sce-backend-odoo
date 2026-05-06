# -*- coding: utf-8 -*-
"""Normalize raw Odoo/native page payloads before the Lite adapter.

This module is intentionally side-effect free. It does not import the Lite
adapter, does not register an Odoo model, and does not touch public intents.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from .source_authority import build_source_authority_contract

SUPPORTED_CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}
SOURCE_KIND = "unified_page_contract_lite_source_normalizer"
SOURCE_AUTHORITIES = ("legacy_ui_contract", "native_page_payload", "semantic_page")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier=SOURCE_KIND,
    )

SUPPORTED_VIEW_TYPES = {"form", "tree", "list", "kanban", "search", "gantt", "popup", "combine"}
SUPPORTED_RENDER_PROFILES = {"create", "edit", "readonly", "search", "list"}


def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _client_type(value: Any) -> str:
    raw = _text(value, "web_pc")
    return raw if raw in SUPPORTED_CLIENT_TYPES else "web_pc"


def _view_type(value: Any) -> str:
    raw = _text(value, "form").split(",")[0].strip().lower() or "form"
    return raw if raw in SUPPORTED_VIEW_TYPES else "form"


def _render_profile(value: Any, view_type: str) -> str:
    raw = _text(value)
    if raw in SUPPORTED_RENDER_PROFILES:
        return raw
    if view_type in {"search", "list"}:
        return view_type
    return "edit"


def _semantic_page(raw: Dict[str, Any], head: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    semantic_page = deepcopy(_dict(raw.get("semantic_page") or _dict(meta.get("semantic_page"))))
    model = _text(semantic_page.get("model") or head.get("model") or raw.get("model"), "unknown.model")
    view_type = _view_type(semantic_page.get("view_type") or head.get("view_type") or raw.get("view_type"))
    semantic_page["model"] = model
    semantic_page["view_type"] = view_type
    return semantic_page


def normalize_lite_contract_source(raw_source: Dict[str, Any]) -> Dict[str, Any]:
    """Return Batch-7 normalized contract source shape from a raw source payload."""

    raw = _dict(raw_source)
    head = _dict(raw.get("head"))
    meta = _dict(raw.get("meta"))
    semantic_page = _semantic_page(raw, head, meta)
    model = _text(semantic_page.get("model"), "unknown.model")
    view_type = _view_type(semantic_page.get("view_type"))
    page_id = _text(raw.get("page_id") or head.get("page_id"), f"{model}.{view_type}")
    scene_key = _text(raw.get("scene_key") or head.get("scene_key"), page_id)
    normalized = {
        "page_id": page_id,
        "scene_key": scene_key,
        "client_type": _client_type(raw.get("client_type") or head.get("client_type")),
        "semantic_page": semantic_page,
        "fields": deepcopy(_dict(raw.get("fields"))),
    }

    etag = _text(raw.get("etag") or head.get("etag"))
    if etag:
        normalized["etag"] = etag
    trace_id = _text(raw.get("trace_id") or head.get("trace_id"))
    if trace_id:
        normalized["trace_id"] = trace_id
    normalized["render_profile"] = _render_profile(raw.get("render_profile") or head.get("render_profile"), view_type)

    optional_mappings = (
        ("field_policies", "field_policies"),
        ("action_policies", "action_policies"),
        ("access_policy", "access_policy"),
        ("modifiers", "modifiers"),
        ("field_modifiers", "field_modifiers"),
        ("onchange_fields", "onchange_fields"),
    )
    for raw_key, normalized_key in optional_mappings:
        if raw_key in raw:
            normalized[normalized_key] = deepcopy(raw.get(raw_key))

    normalized["record"] = deepcopy(_dict(raw.get("record") or raw.get("values") or raw.get("mainData")))
    normalized["relation_rows"] = deepcopy(_dict(raw.get("relation_rows") or raw.get("relationData")))
    normalized["dict_data"] = deepcopy(_dict(raw.get("dict_data") or raw.get("dictData") or raw.get("options")))
    return normalized
