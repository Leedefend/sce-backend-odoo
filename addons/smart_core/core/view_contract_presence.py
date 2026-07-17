# -*- coding: utf-8 -*-
"""Authoritative view-presence checks for business configuration contracts."""

from __future__ import annotations

from typing import Any


def normalize_contract_view_type(view_type: Any) -> str:
    normalized = str(view_type or "").strip()
    return "tree" if normalized == "list" else normalized


def _value(contract: Any, key: str, default: Any = None) -> Any:
    if isinstance(contract, dict):
        return contract.get(key, default)
    return getattr(contract, key, default)


def _view_spec(contract: Any, requested_view_type: str) -> Any:
    payload = _value(contract, "contract_json", {})
    if not isinstance(payload, dict):
        return None
    orchestration = payload.get("view_orchestration")
    if not isinstance(orchestration, dict):
        return None
    views = orchestration.get("views")
    if not isinstance(views, dict):
        return None
    if requested_view_type == "tree":
        if "tree" in views:
            return views.get("tree")
        if "list" in views:
            return views.get("list")
        return None
    if requested_view_type not in views:
        return None
    return views.get(requested_view_type)


def contract_contributes_view(contract: Any, requested_view_type: Any) -> bool:
    """Return whether an effective contract contributes a valid requested view.

    A dedicated contract and a generic contract both need a corresponding
    object-valued ``view_orchestration.views`` node.  Empty view objects and
    empty arrays inside a view remain explicit configuration.  Lifecycle
    filtering is repeated here so callers cannot accidentally treat a draft,
    inactive, or superseded record as an effective contribution.  Change-set
    preview projections are the only non-published runtime input accepted.
    """

    requested = normalize_contract_view_type(requested_view_type)
    if not requested:
        return False
    if _value(contract, "active", True) is False:
        return False
    status = str(_value(contract, "status", "") or "").strip()
    source_kind = str(_value(contract, "source_kind", "") or "").strip()
    is_preview = status == "preview" or source_kind == "change_set_preview"
    if status and status != "published" and not is_preview:
        return False
    declared = normalize_contract_view_type(_value(contract, "view_type", ""))
    if declared and declared != requested:
        return False
    return isinstance(_view_spec(contract, requested), dict)
