# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def apply_released_scene_semantic_surface_bridge(
    payload: Dict[str, Any] | None,
    scene_contract: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    contract = dict(scene_contract or {})
    if not contract:
        return out

    governance = _as_dict(contract.get("governance"))
    parser_surface = _as_dict(governance.get("parser_semantic_surface"))
    page_surface = _as_dict(_as_dict(contract.get("page")).get("surface"))
    if not (parser_surface or page_surface):
        return out

    out["released_scene_semantic_surface"] = {
        "scene_key": _text(_as_dict(contract.get("identity")).get("scene_key")),
        "parser_semantic_surface": parser_surface,
        "page_surface": page_surface,
    }

    semantic_runtime = _as_dict(out.get("semantic_runtime"))
    if page_surface:
        semantic_runtime["view_type"] = _text(page_surface.get("view_type"))
        semantic_runtime["semantic_view"] = _as_dict(page_surface.get("semantic_view"))
        semantic_runtime["semantic_page"] = _as_dict(page_surface.get("semantic_page"))
    if parser_surface:
        semantic_runtime["parser_semantic_surface"] = parser_surface
    if semantic_runtime:
        out["semantic_runtime"] = semantic_runtime

    return out
