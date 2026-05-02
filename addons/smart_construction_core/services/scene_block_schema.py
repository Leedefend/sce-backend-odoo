# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


CONTRACT_SCHEMA_VERSION = "scene_contract_v1"
ALLOWED_BLOCK_TYPES = {
    "metric_card",
    "shortcut_grid",
    "todo_list",
    "warning_list",
    "native_view_ref",
}

BLOCK_SCHEMA = {
    "metric_card": {"required": ["key", "type", "title", "value", "target"]},
    "shortcut_grid": {"required": ["key", "type", "title", "items"]},
    "todo_list": {"required": ["key", "type", "title", "items"]},
    "warning_list": {"required": ["key", "type", "title", "items"]},
    "native_view_ref": {"required": ["key", "type", "title", "model", "view_mode", "target"]},
}


def text(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def action_target(*, action_xmlid: str = "", intent: str = "", params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if action_xmlid:
        return {"type": "action", "action_xmlid": text(action_xmlid)}
    if intent:
        return {"type": "intent", "intent": text(intent), "params": dict(params or {})}
    return {"type": "none"}


def metric_card(key: str, title: str, value: Any, *, subtitle: str = "", tone: str = "neutral", target=None) -> Dict[str, Any]:
    return {
        "key": text(key),
        "type": "metric_card",
        "title": text(title),
        "value": value,
        "subtitle": text(subtitle),
        "tone": text(tone) or "neutral",
        "target": target or {"type": "none"},
    }


def shortcut_grid(key: str, title: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "key": text(key),
        "type": "shortcut_grid",
        "title": text(title),
        "items": [row for row in list(items or []) if isinstance(row, dict)],
    }


def todo_list(key: str, title: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "key": text(key),
        "type": "todo_list",
        "title": text(title),
        "items": [row for row in list(items or []) if isinstance(row, dict)],
        "empty_text": "暂无待办",
    }


def warning_list(key: str, title: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "key": text(key),
        "type": "warning_list",
        "title": text(title),
        "items": [row for row in list(items or []) if isinstance(row, dict)],
        "empty_text": "暂无预警",
    }


def native_view_ref(
    key: str,
    title: str,
    *,
    action_xmlid: str,
    model: str,
    view_mode: str,
    count: int = 0,
    summary: str = "",
) -> Dict[str, Any]:
    return {
        "key": text(key),
        "type": "native_view_ref",
        "title": text(title),
        "model": text(model),
        "view_mode": text(view_mode),
        "count": as_int(count),
        "summary": text(summary),
        "target": action_target(action_xmlid=action_xmlid),
    }


def guard_contract_shape(contract: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("scene contract must be a dict")
    contract.setdefault("schema_version", CONTRACT_SCHEMA_VERSION)
    scene = contract.get("scene")
    page = contract.get("page")
    if not isinstance(scene, dict) or not text(scene.get("key")):
        raise ValueError("scene contract requires scene.key")
    if not isinstance(page, dict):
        raise ValueError("scene contract requires page")
    blocks = page.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("scene contract requires page.blocks")
    seen = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValueError("scene block must be a dict")
        key = text(block.get("key")) or f"block_{index + 1}"
        block["key"] = key
        if key in seen:
            raise ValueError("scene block key must be unique")
        seen.add(key)
        block_type = text(block.get("type"))
        if block_type not in ALLOWED_BLOCK_TYPES:
            raise ValueError("unsupported scene block type: %s" % block_type)
        required = BLOCK_SCHEMA.get(block_type, {}).get("required") or []
        missing = [field for field in required if field not in block]
        if missing:
            raise ValueError("scene block %s missing fields: %s" % (key, ", ".join(missing)))
    return contract


def build_contract(*, scene_key: str, title: str, blocks: List[Dict[str, Any]], subtitle: str = "") -> Dict[str, Any]:
    return guard_contract_shape(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "scene": {
                "key": text(scene_key),
                "title": text(title),
                "subtitle": text(subtitle),
            },
            "page": {
                "layout": "block_grid",
                "blocks": list(blocks or []),
            },
            "block_schema": {
                "version": "block_schema_v1",
                "types": BLOCK_SCHEMA,
            },
        }
    )
