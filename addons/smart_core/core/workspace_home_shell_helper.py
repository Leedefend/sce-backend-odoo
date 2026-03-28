# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


DEFAULT_WORKSPACE_SCENE_ALIASES = {
    "default": "workspace.home",
    "dashboard": "workspace.home",
    "project_list": "workspace.list",
    "project_management": "workspace.management",
    "execution": "workspace.execution",
    "operation_overview": "workspace.overview",
    "risk_center": "workspace.risk",
    "task_center": "workspace.tasks",
    "cost_center": "workspace.cost",
    "finance_center": "workspace.finance",
}


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def build_workspace_scene_aliases(provider: Any = None) -> Dict[str, str]:
    if provider is not None:
        fn = getattr(provider, "build_scene_aliases", None)
        if callable(fn):
            try:
                payload = fn()
            except Exception:
                payload = None
            if isinstance(payload, dict):
                out = {
                    _to_text(key).lower(): _to_text(value)
                    for key, value in payload.items()
                    if _to_text(key) and _to_text(value)
                }
                if out:
                    return out
    return dict(DEFAULT_WORKSPACE_SCENE_ALIASES)


def resolve_workspace_scene(name: Any, aliases: Dict[str, str] | None = None) -> str:
    resolved_aliases = aliases if isinstance(aliases, dict) and aliases else dict(DEFAULT_WORKSPACE_SCENE_ALIASES)
    key = _to_text(name).lower()
    return _to_text(resolved_aliases.get(key) or resolved_aliases.get("default") or "workspace.home") or "workspace.home"


def resolve_workspace_keyword_overrides(data: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    direct_payload = data.get("workspace_keyword_overrides")
    if isinstance(direct_payload, dict):
        return direct_payload
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    ext_payload = ext_facts.get("workspace_keyword_overrides")
    if isinstance(ext_payload, dict):
        return ext_payload
    return {}


def merge_workspace_mapping_overrides(defaults: Dict[str, str], provider: Any = None, *, override_builder: str) -> Dict[str, str]:
    out = dict(defaults or {})
    if provider is None:
        return out
    fn = getattr(provider, override_builder, None)
    if not callable(fn):
        return out
    try:
        payload = fn()
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return out
    for key, value in payload.items():
        normalized_key = _to_text(key)
        normalized_value = _to_text(value)
        if normalized_key and normalized_value:
            out[normalized_key] = normalized_value
    return out
