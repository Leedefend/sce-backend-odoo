# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def apply_workspace_home_parser_semantic_bridge(
    payload: Dict[str, Any] | None,
    source: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    raw = dict(source or {})

    parser_contract = _as_dict(raw.get("parser_contract"))
    view_semantics = _as_dict(raw.get("view_semantics"))
    native_view = _as_dict(raw.get("native_view"))
    semantic_page = _as_dict(raw.get("semantic_page"))

    if not (parser_contract or view_semantics or native_view or semantic_page):
        return out

    surface = {
        "parser_contract": parser_contract,
        "view_semantics": view_semantics,
        "native_view": native_view,
        "semantic_page": semantic_page,
    }

    diagnostics = _as_dict(out.get("diagnostics"))
    diagnostics["parser_semantic_surface"] = surface
    out["diagnostics"] = diagnostics

    layout = _as_dict(out.get("layout"))
    if parser_contract:
        layout.setdefault("view_type", _text(parser_contract.get("view_type")))
    if view_semantics:
        layout["semantic_view"] = {
            "source_view": _text(view_semantics.get("source_view")),
            "capability_flags": _as_dict(view_semantics.get("capability_flags")),
            "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
        }
    if semantic_page:
        layout["semantic_page"] = semantic_page
    if layout:
        out["layout"] = layout

    orchestration = _as_dict(out.get("page_orchestration_v1"))
    if orchestration:
        page = _as_dict(orchestration.get("page"))
        page_context = _as_dict(page.get("context"))
        if parser_contract:
            page_context.setdefault("view_type", _text(parser_contract.get("view_type")))
        if view_semantics:
            page_context.setdefault("semantic_source_view", _text(view_semantics.get("source_view")))
        if page_context:
            page["context"] = page_context
        if page:
            orchestration["page"] = page

        render_hints = _as_dict(orchestration.get("render_hints"))
        if view_semantics:
            render_hints["semantic_view"] = {
                "source_view": _text(view_semantics.get("source_view")),
                "capability_flags": _as_dict(view_semantics.get("capability_flags")),
                "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
            }
        if semantic_page:
            render_hints["semantic_page"] = semantic_page
        if render_hints:
            orchestration["render_hints"] = render_hints

        meta = _as_dict(orchestration.get("meta"))
        meta["parser_semantic_surface"] = surface
        orchestration["meta"] = meta

        out["page_orchestration_v1"] = orchestration

    return out
