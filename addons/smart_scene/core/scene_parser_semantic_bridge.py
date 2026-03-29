# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _coalesce_consumer_runtime(
    *,
    surface: Dict[str, Any],
    diagnostics: Dict[str, Any],
    contract_v1: Dict[str, Any],
) -> Dict[str, Any]:
    if _as_dict(surface.get("consumer_runtime")):
        return _as_dict(surface.get("consumer_runtime"))

    if _as_dict(diagnostics.get("consumer_runtime")):
        return _as_dict(diagnostics.get("consumer_runtime"))

    consumer_semantics = _as_dict(diagnostics.get("consumer_semantics"))
    if _as_dict(consumer_semantics.get("runtime")):
        return _as_dict(consumer_semantics.get("runtime"))

    contract_v1_diagnostics = _as_dict(contract_v1.get("diagnostics"))
    if _as_dict(contract_v1_diagnostics.get("consumer_runtime")):
        return _as_dict(contract_v1_diagnostics.get("consumer_runtime"))

    contract_v1_consumer_semantics = _as_dict(contract_v1_diagnostics.get("consumer_semantics"))
    if _as_dict(contract_v1_consumer_semantics.get("runtime")):
        return _as_dict(contract_v1_consumer_semantics.get("runtime"))

    return {}


def _build_consumer_runtime_assertions(
    *,
    consumer_runtime: Dict[str, Any],
    semantic_runtime_state: Dict[str, Any],
) -> Dict[str, Any]:
    runtime_page_status = _text(semantic_runtime_state.get("page_status"))
    consumer_page_status = _text(consumer_runtime.get("runtime_page_status") or consumer_runtime.get("page_status"))
    runtime_current_state = _text(semantic_runtime_state.get("current_state"))
    consumer_current_state = _text(consumer_runtime.get("current_state"))

    return {
        "consumer_runtime_present": bool(consumer_runtime),
        "semantic_runtime_state_present": bool(semantic_runtime_state),
        "page_status_aligned": (not runtime_page_status) or runtime_page_status == consumer_page_status,
        "current_state_aligned": (not runtime_current_state) or runtime_current_state == consumer_current_state,
    }


def apply_scene_parser_semantic_bridge(
    contract: Dict[str, Any] | None,
    semantic_surface: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(contract or {})
    surface = dict(semantic_surface or {})
    if not surface:
        return out

    diagnostics = _as_dict(out.get("diagnostics"))
    contract_v1 = _as_dict(out.get("scene_contract_v1"))

    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    native_view = _as_dict(surface.get("native_view"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    search_surface = _as_dict(surface.get("search_surface"))
    permission_surface = _as_dict(surface.get("permission_surface"))
    workflow_surface = _as_dict(surface.get("workflow_surface"))
    validation_surface = _as_dict(surface.get("validation_surface"))
    semantic_runtime_state = _as_dict(surface.get("semantic_runtime_state"))
    consumer_runtime = _coalesce_consumer_runtime(
        surface=surface,
        diagnostics=diagnostics,
        contract_v1=contract_v1,
    )
    consumer_runtime_assertions = _build_consumer_runtime_assertions(
        consumer_runtime=consumer_runtime,
        semantic_runtime_state=semantic_runtime_state,
    )
    if not (
        parser_contract
        or view_semantics
        or native_view
        or semantic_page
        or search_surface
        or permission_surface
        or workflow_surface
        or validation_surface
        or semantic_runtime_state
        or consumer_runtime
    ):
        return out

    page = _as_dict(out.get("page"))
    page_surface = _as_dict(page.get("surface"))
    if parser_contract:
        page_surface["view_type"] = _text(parser_contract.get("view_type"))
    elif not _text(page_surface.get("view_type")) and _text(page.get("view_type")):
        page_surface["view_type"] = _text(page.get("view_type"))
    if view_semantics:
        page_surface["semantic_view"] = {
            "source_view": _text(view_semantics.get("source_view")),
            "capability_flags": _as_dict(view_semantics.get("capability_flags")),
            "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
        }
    if semantic_page:
        page_surface["semantic_page"] = semantic_page
    if page_surface:
        page["surface"] = page_surface
        out["page"] = page

    diagnostics["parser_semantic_surface"] = {
        "parser_contract": parser_contract,
        "view_semantics": view_semantics,
        "native_view": native_view,
        "semantic_page": semantic_page,
        "search_surface": search_surface,
        "permission_surface": permission_surface,
        "workflow_surface": workflow_surface,
        "validation_surface": validation_surface,
        "semantic_runtime_state": semantic_runtime_state,
        "consumer_runtime": consumer_runtime,
        "consumer_runtime_assertions": consumer_runtime_assertions,
    }
    if semantic_runtime_state:
        diagnostics["semantic_runtime_state"] = semantic_runtime_state
    if consumer_runtime:
        diagnostics["consumer_runtime"] = consumer_runtime
    diagnostics["consumer_runtime_assertions"] = consumer_runtime_assertions
    out["diagnostics"] = diagnostics

    if contract_v1:
        contract_v1["page"] = _as_dict(out.get("page"))
        contract_v1["diagnostics"] = diagnostics
        out["scene_contract_v1"] = contract_v1

    return out
