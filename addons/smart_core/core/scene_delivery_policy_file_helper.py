# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any, Callable


def surface_policy_default_file(
    env=None,
    *,
    hook: Callable[[Any, str, Any], Any] | None = None,
    default_file: str,
) -> str:
    payload = hook(env, "smart_core_surface_policy_file_default", env) if callable(hook) else None
    value = str(payload or "").strip()
    return value or default_file


def resolve_policy_file_path(
    env=None,
    *,
    default_file_resolver: Callable[[Any], str],
) -> str | None:
    explicit = str(os.environ.get("SCENE_DELIVERY_POLICY_FILE") or "").strip()
    rel_path = explicit or default_file_resolver(env)
    candidates = [
        rel_path,
        os.path.join("/mnt/e/sc-backend-odoo", rel_path),
        os.path.join("/mnt/extra-addons", rel_path),
        os.path.join("/mnt/addons_external", rel_path),
        os.path.join("/mnt/odoo", rel_path),
        os.path.join("/mnt", rel_path),
    ]
    for item in candidates:
        if item and os.path.isfile(item):
            return item
    return None


def load_surface_policy_payload_from_file(
    env=None,
    *,
    cache: dict[str, Any],
    default_file_resolver: Callable[[Any], str],
) -> dict:
    path = resolve_policy_file_path(env, default_file_resolver=default_file_resolver)
    if not path:
        return {}
    try:
        mtime = float(os.path.getmtime(path))
    except Exception:
        mtime = -1.0
    cached_path = str(cache.get("path") or "")
    cached_mtime = float(cache.get("mtime") or -1.0)
    if cached_path == path and cached_mtime == mtime:
        cached_payload = cache.get("payload")
        return cached_payload if isinstance(cached_payload, dict) else {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.loads(handle.read() or "{}")
    except Exception:
        return {}
    normalized = payload if isinstance(payload, dict) else {}
    cache["path"] = path
    cache["mtime"] = mtime
    cache["payload"] = normalized
    return normalized


def resolve_default_surface_from_file(
    env=None,
    *,
    payload_loader: Callable[[Any], dict],
    normalize_surface: Callable[[Any], str],
) -> str:
    payload = payload_loader(env)
    raw = payload.get("default_surface") if isinstance(payload, dict) else ""
    value = normalize_surface(raw)
    return value if value and value != "default" else ""
