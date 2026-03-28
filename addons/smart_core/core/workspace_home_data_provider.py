# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .workspace_home_provider_defaults import (
    build_default_role_focus_config,
    build_default_v1_data_sources,
    build_default_v1_focus_map,
    build_default_v1_page_profile,
    build_default_v1_state_schema,
    to_text,
)

_PROVIDER = None


def _to_text(value: Any) -> str:
    return to_text(value)


def _load_industry_provider():
    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER
    addons_root = Path(__file__).resolve().parents[2]
    for provider_path in sorted(addons_root.glob("*/profiles/workspace_home_scene_content.py")):
        try:
            module_key = provider_path.parts[-3]
            module_name = f"{module_key}_workspace_home_scene_content"
            spec = spec_from_file_location(module_name, provider_path)
            if spec is None or spec.loader is None:
                continue
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            _PROVIDER = module
            return module
        except Exception:
            continue
    _PROVIDER = False
    return None


def _call_provider(name: str, fallback: Any, *args: Any) -> Any:
    provider = _load_industry_provider()
    if provider is None:
        return fallback
    fn = getattr(provider, name, None)
    if callable(fn):
        try:
            return fn(*args)
        except Exception:
            return fallback
    return fallback


def build_today_actions(ready_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _call_provider("build_today_actions", [], ready_caps)


def build_advice_items(locked_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    default = [{
        "id": "stable",
        "level": "green",
        "tone": "success",
        "progress": "completed",
        "title": "当前整体运行稳定",
        "description": "能力面运行正常，建议优先处理今日关键动作。",
        "action_label": "",
    }]
    return _call_provider("build_advice_items", default, locked_caps)


def build_role_focus_config(role_code: str) -> Dict[str, Any]:
    default = build_default_role_focus_config()
    return _call_provider("build_role_focus_config", default, role_code)


def build_v1_focus_map() -> Dict[str, List[str]]:
    default = build_default_v1_focus_map()
    return _call_provider("build_v1_focus_map", default)


def build_v1_page_profile(role_code: str) -> Dict[str, Any]:
    default = build_default_v1_page_profile(role_code)
    return _call_provider("build_v1_page_profile", default, role_code)


def build_v1_data_sources() -> Dict[str, Dict[str, Any]]:
    default = build_default_v1_data_sources()
    return _call_provider("build_v1_data_sources", default)


def build_legacy_blocks(role_code: str) -> List[Dict[str, Any]]:
    return _call_provider("build_legacy_blocks", [], role_code)


def build_v1_zones(role_code: str, audience: List[str], zone_rank: Dict[str, int]) -> List[Dict[str, Any]]:
    return _call_provider("build_v1_zones", [], role_code, audience, zone_rank)


def build_v1_state_schema() -> Dict[str, Dict[str, str]]:
    default = build_default_v1_state_schema()
    return _call_provider("build_v1_state_schema", default)
