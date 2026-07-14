# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

try:
    from .contract_governance_capabilities import _normalized_tags_for_item
    from .contract_governance_registry import _SCENE_SEMANTIC_PROFILE_REGISTRY
except ImportError:
    base = Path(__file__).parent
    registry_spec = importlib.util.spec_from_file_location(
        "contract_governance_registry",
        base / "contract_governance_registry.py",
    )
    capabilities_spec = importlib.util.spec_from_file_location(
        "contract_governance_capabilities",
        base / "contract_governance_capabilities.py",
    )
    if registry_spec is None or registry_spec.loader is None or capabilities_spec is None or capabilities_spec.loader is None:
        raise
    registry = importlib.util.module_from_spec(registry_spec)
    registry_spec.loader.exec_module(registry)
    capabilities = importlib.util.module_from_spec(capabilities_spec)
    capabilities_spec.loader.exec_module(capabilities)
    _SCENE_SEMANTIC_PROFILE_REGISTRY = registry._SCENE_SEMANTIC_PROFILE_REGISTRY
    _normalized_tags_for_item = capabilities._normalized_tags_for_item


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _normalize_scene_list_profile(item: dict) -> dict:
    raw = item.get("list_profile")
    profile = dict(raw) if isinstance(raw, dict) else {}
    columns = profile.get("columns") if isinstance(profile.get("columns"), list) else []
    hidden = profile.get("hidden_columns") if isinstance(profile.get("hidden_columns"), list) else []
    row_primary = _safe_text(profile.get("row_primary"))
    row_secondary = _safe_text(profile.get("row_secondary"))
    primary_field = _safe_text(profile.get("primary_field"), row_primary or (columns[0] if columns else "name"))
    status_field = _safe_text(profile.get("status_field"), "lifecycle_state")
    urgency_score = int(profile.get("urgency_score") or 0)
    highlight_rule = profile.get("highlight_rule") if isinstance(profile.get("highlight_rule"), dict) else {}
    if not highlight_rule:
        highlight_rule = {
            "overdue": {"field": "end_date", "operator": "lt_today", "level": "danger"},
            "at_risk": {"field": status_field, "operator": "in", "value": ["paused", "closing"], "level": "warning"},
        }
    profile["columns"] = columns
    profile["hidden_columns"] = sorted({str(col).strip() for col in hidden if str(col).strip()})
    profile["row_primary"] = row_primary
    profile["row_secondary"] = row_secondary
    profile["primary_field"] = primary_field
    profile["status_field"] = status_field
    profile["urgency_score"] = urgency_score
    profile["highlight_rule"] = highlight_rule
    return profile


def _derive_scene_meta(item: dict) -> dict:
    code = _safe_text(item.get("code") or item.get("key")).lower()
    purpose = "Business work"
    for profile in _SCENE_SEMANTIC_PROFILE_REGISTRY:
        prefixes = profile.get("code_prefixes") if isinstance(profile, dict) else ()
        contains = profile.get("code_contains") if isinstance(profile, dict) else ()
        if (prefixes and code.startswith(tuple(prefixes))) or (
            contains and any(marker in code for marker in contains)
        ):
            purpose = _safe_text(profile.get("purpose"), purpose)
            break

    access = item.get("access") if isinstance(item.get("access"), dict) else {}
    required_caps = access.get("required_capabilities") if isinstance(access.get("required_capabilities"), list) else []
    is_allowed = bool(access.get("allowed", True))
    is_default = bool(item.get("is_default"))
    base_score = 80
    if is_default:
        base_score += 10
    if not is_allowed:
        base_score -= 30
    base_score -= min(30, len(required_caps) * 5)
    role_relevance_score = max(0, min(100, base_score))

    tiles = item.get("tiles") if isinstance(item.get("tiles"), list) else []
    action_labels: list[str] = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        label = _safe_text(tile.get("title") or tile.get("subtitle") or tile.get("key"))
        if label and label not in action_labels:
            action_labels.append(label)
    core_action = action_labels[0] if action_labels else "进入场景"
    priority_actions = action_labels[:3]
    return {
        "purpose": purpose,
        "core_action": core_action,
        "priority_actions": priority_actions,
        "role_relevance_score": role_relevance_score,
    }


def normalize_scenes(scenes: list) -> list[dict]:
    out: list[dict] = []
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        item = dict(scene)
        code = _safe_text(item.get("code") or item.get("key"))
        item["code"] = code or item.get("code")
        item["key"] = _safe_text(item.get("key"), code)
        item["name"] = _safe_text(item.get("name"), code or "未命名场景")
        item["list_profile"] = _normalize_scene_list_profile(item)
        item["scene_meta"] = _derive_scene_meta(item)
        item["tags"] = _normalized_tags_for_item(item)
        out.append(item)
    return out
