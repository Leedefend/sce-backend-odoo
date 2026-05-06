# -*- coding: utf-8 -*-
"""Normalize raw onchange/x2many payloads into Lite patch source shape.

This module is intentionally side-effect free. It does not register Odoo
objects and does not call delivery handlers.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .source_authority import build_source_authority_contract

SOURCE_KIND = "unified_page_contract_lite_patch_normalizer"
SOURCE_AUTHORITIES = ("onchange_payload", "x2many_patch_payload", "lite_patch_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier=SOURCE_KIND,
    )


def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _normalize_line_patch(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "field": _text(row.get("field") or row.get("relation_field")),
        "row_key": _text(row.get("row_key") or row.get("key") or row.get("virtual_id") or row.get("row_id")),
        "row_id": row.get("row_id") if isinstance(row.get("row_id"), int) else 0,
        "patch": deepcopy(_dict(row.get("patch") or row.get("values") or row.get("value"))),
        "modifiers_patch": deepcopy(_dict(row.get("modifiers_patch") or row.get("modifiers"))),
        "warnings": deepcopy(_list(row.get("warnings"))),
        "row_state": _text(row.get("row_state") or row.get("state"), "keep"),
        "command_hint": deepcopy(_list(row.get("command_hint") or row.get("command"))),
    }


def normalize_lite_patch_source(raw_patch: Dict[str, Any]) -> Dict[str, Any]:
    """Return Batch-7 normalized patch source shape from raw onchange payload."""

    raw = _dict(raw_patch)
    patch = deepcopy(_dict(raw.get("patch") or raw.get("value") or raw.get("values")))
    modifiers_patch = deepcopy(_dict(raw.get("modifiers_patch") or raw.get("modifiers")))
    button_status_patch = raw.get("button_status_patch")
    if button_status_patch is None:
        button_status_patch = raw.get("button_status") or raw.get("buttons")

    raw_line_patches = raw.get("line_patches")
    if raw_line_patches is None:
        raw_line_patches = raw.get("x2many_patches") or raw.get("x2many_changes") or raw.get("relation_patches")
    line_patches = [
        _normalize_line_patch(row)
        for row in _list(raw_line_patches)
        if isinstance(row, dict) and _text(row.get("field") or row.get("relation_field"))
    ]

    normalized = {
        "schema_version": "v1",
        "patch": patch,
        "modifiers_patch": modifiers_patch,
        "line_patches": line_patches,
        "warnings": deepcopy(_list(raw.get("warnings") or raw.get("warning"))),
        "applied_fields": deepcopy(_list(raw.get("applied_fields") or raw.get("changed_fields"))),
    }
    if isinstance(button_status_patch, (dict, list)):
        normalized["button_status_patch"] = deepcopy(button_status_patch)
    return normalized
