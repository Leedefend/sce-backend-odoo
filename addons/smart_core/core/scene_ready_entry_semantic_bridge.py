# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def apply_scene_ready_entry_semantic_bridge(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    out = dict(payload or {})
    meta = _as_dict(out.get("meta"))
    parser_surface = _as_dict(meta.get("parser_semantic_surface"))
    if not parser_surface:
        return out

    view_semantics = _as_dict(parser_surface.get("view_semantics"))
    semantic_page = _as_dict(parser_surface.get("semantic_page"))
    parser_contract = _as_dict(parser_surface.get("parser_contract"))
    surface = _as_dict(out.get("surface"))
    render_hints = _as_dict(out.get("render_hints"))

    if parser_surface:
        out["parser_semantic_surface"] = parser_surface
    if view_semantics:
        out["semantic_view"] = {
            "source_view": _text(view_semantics.get("source_view")),
            "capability_flags": _as_dict(view_semantics.get("capability_flags")),
            "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
        }
        if not _as_dict(surface.get("semantic_view")):
            surface["semantic_view"] = dict(out["semantic_view"])
    if semantic_page:
        out["semantic_page"] = semantic_page
        render_hints.setdefault("semantic_page", semantic_page)
    if parser_contract:
        out["view_type"] = _text(parser_contract.get("view_type"))

    if surface:
        out["surface"] = surface
    if render_hints:
        out["render_hints"] = render_hints
    return out
