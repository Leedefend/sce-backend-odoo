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
    for item in payload:
        key = _text(item)
        if key:
            out.append(key)
    return out


def _save_queue(config, queue: list[str]) -> None:
    config.set_param(QUEUE_KEY, json.dumps(queue, ensure_ascii=False, separators=(",", ":")))


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
        key = _text(item)
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
    return {
        "scene_keys": list(selected),
        "popped_count": len(selected),
        "remaining_count": len(remain),
    }

