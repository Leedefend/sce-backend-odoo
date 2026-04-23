# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def apply_runtime_page_parser_semantic_bridge(
    page_payload: Dict[str, Any] | None,
    *,
    page_key: str = "",
) -> Dict[str, Any]:
    page = dict(page_payload or {})
    orchestration = _as_dict(page.get("page_orchestration_v1"))
    meta = _as_dict(orchestration.get("meta"))
    surface = _as_dict(meta.get("parser_semantic_surface"))
    if not surface:
        return page

    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))

    runtime_context = _as_dict(page.get("runtime_context"))
    runtime_context["page_key"] = _text(page_key)
    if parser_contract:
        runtime_context["view_type"] = _text(parser_contract.get("view_type"))
    if view_semantics:
        runtime_context["semantic_source_view"] = _text(view_semantics.get("source_view"))
    page["runtime_context"] = runtime_context
    page["runtime_semantic_surface"] = surface

    render_hints = _as_dict(orchestration.get("render_hints"))
    if view_semantics:
        render_hints["runtime_semantic_view"] = {
            "source_view": _text(view_semantics.get("source_view")),
            "capability_flags": _as_dict(view_semantics.get("capability_flags")),
            "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
        }
    if semantic_page:
        render_hints["runtime_semantic_page"] = semantic_page
    if render_hints:
        orchestration["render_hints"] = render_hints

    page_ctx = _as_dict(_as_dict(orchestration.get("page")).get("context"))
    if parser_contract:
        page_ctx.setdefault("view_type", _text(parser_contract.get("view_type")))
    if view_semantics:
        page_ctx.setdefault("semantic_source_view", _text(view_semantics.get("source_view")))
    page_node = _as_dict(orchestration.get("page"))
    if page_ctx:
        page_node["context"] = page_ctx
    orchestration["page"] = page_node

    page["page_orchestration_v1"] = orchestration
    return page
