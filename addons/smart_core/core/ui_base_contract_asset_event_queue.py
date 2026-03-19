# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from typing import Any


QUEUE_KEY = "sc.ui_base_contract.asset.refresh.queue"
QUEUE_META_KEY = "sc.ui_base_contract.asset.refresh.queue.meta"
DEFAULT_MAX_QUEUE_SIZE = 500


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_scene_key(value: Any) -> str:
    key = _text(value).lower()
    if not key:
        return ""
    if "__pkg" in key:
        base = key.split("__pkg", 1)[0].strip()
        if base:
            return base
    return key


def _load_queue(config) -> list[str]:
    raw = _text(config.get_param(QUEUE_KEY) or "")
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    out: list[str] = []
    seen = set()
    for item in payload:
        key = _normalize_scene_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _save_queue(config, queue: list[str]) -> None:
    config.set_param(QUEUE_KEY, json.dumps(queue, ensure_ascii=False, separators=(",", ":")))


def _load_queue_meta(config) -> dict:
    raw = _text(config.get_param(QUEUE_META_KEY) or "")
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def enqueue_scene_keys(
    env,
    *,
    scene_keys: list[str] | None,
    reason: str = "event",
    max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
) -> dict:
    config = env["ir.config_parameter"].sudo()
    current = _load_queue(config)
    existing = set(current)
    added = 0
    for item in scene_keys or []:
        key = _normalize_scene_key(item)
        if not key or key in existing:
            continue
        current.append(key)
        existing.add(key)
        added += 1
    max_size = max(int(max_queue_size or 0), 1)
    if len(current) > max_size:
        current = current[-max_size:]
    _save_queue(config, current)
    meta = {
        "reason": _text(reason) or "event",
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "size": len(current),
        "added": int(added),
    }
    config.set_param(QUEUE_META_KEY, json.dumps(meta, ensure_ascii=False, separators=(",", ":")))
    return {
        "queue_size": len(current),
        "added_count": int(added),
        "reason": meta["reason"],
    }


def pop_scene_keys(env, *, limit: int = 50) -> dict:
    config = env["ir.config_parameter"].sudo()
    current = _load_queue(config)
    batch_size = max(int(limit or 0), 1)
    selected = current[:batch_size]
    remain = current[batch_size:]
    _save_queue(config, remain)
    meta = _load_queue_meta(config)
    meta.update(
        {
            "last_operation": "pop",
            "consumed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "popped_count": len(selected),
            "remaining_count": len(remain),
            "size": len(remain),
        }
    )
    config.set_param(QUEUE_META_KEY, json.dumps(meta, ensure_ascii=False, separators=(",", ":")))
    return {
        "scene_keys": list(selected),
        "popped_count": len(selected),
        "remaining_count": len(remain),
    }


def get_queue_metrics(env) -> dict:
    config = env["ir.config_parameter"].sudo()
    queue = _load_queue(config)
    meta = _load_queue_meta(config)
    return {
        "queue_size": len(queue),
        "updated_at": _text(meta.get("updated_at")),
        "reason": _text(meta.get("reason")),
        "added_count": int(meta.get("added") or 0),
        "last_operation": _text(meta.get("last_operation")),
        "consumed_at": _text(meta.get("consumed_at")),
        "popped_count": int(meta.get("popped_count") or 0),
        "remaining_count": len(queue),
    }
