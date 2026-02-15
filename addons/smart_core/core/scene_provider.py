# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Callable


SCENE_CHANNELS = {"stable", "beta", "dev"}


def _normalize_scene_channel(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip().lower()
    return raw if raw in SCENE_CHANNELS else None


def resolve_scene_channel(
    env,
    user,
    params: dict | None,
    *,
    get_header: Callable[[str], str | None] | None = None,
) -> tuple[str, str, str]:
    channel = None
    selector = "default"
    source_ref = "default"
    if isinstance(params, dict):
        channel = _normalize_scene_channel(params.get("scene_channel") or params.get("channel"))
        if channel:
            selector = "param"
            source_ref = "param:scene_channel"
            return channel, selector, source_ref
    header_val = _normalize_scene_channel(get_header("X-Scene-Channel") if callable(get_header) else None)
    if header_val:
        return header_val, "param", "header:X-Scene-Channel"

    try:
        config = env["ir.config_parameter"].sudo()
        user_val = None
        if user and user.id:
            user_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.user.{user.id}") or "")
        if user_val:
            return user_val, "user", f"user_id={user.id}"

        company_id = user.company_id.id if user and user.company_id else None
        if company_id:
            company_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.company.{company_id}") or "")
            if company_val:
                return company_val, "company", f"company_id={company_id}"

        default_val = _normalize_scene_channel(config.get_param("sc.scene.channel.default") or "")
        if default_val:
            return default_val, "config", "sc.scene.channel.default"
    except Exception:
        pass

    env_val = _normalize_scene_channel(os.environ.get("SCENE_CHANNEL"))
    if env_val:
        return env_val, "env", "SCENE_CHANNEL"

    return "stable", selector, source_ref


def _resolve_scene_contract_path(rel_path: str) -> str | None:
    roots = [
        os.environ.get("SCENE_CONTRACT_ROOT"),
        "/mnt/extra-addons",
        "/mnt/addons_external",
        "/mnt/odoo",
        "/mnt/e/sc-backend-odoo",
        "/mnt",
    ]
    for root in roots:
        if not root:
            continue
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            return candidate
    return None


def load_scene_contract(env, scene_channel: str, use_pinned: bool, *, logger=None) -> tuple[dict | None, str]:
    if use_pinned:
        ref = "stable/PINNED.json"
        try:
            param = env["ir.config_parameter"].sudo().get_param("sc.scene.contract.pinned")
            if param:
                return json.loads(param), ref
        except Exception:
            pass
        rel_path = "docs/contract/exports/scenes/stable/PINNED.json"
    else:
        rel_path = f"docs/contract/exports/scenes/{scene_channel}/LATEST.json"
        ref = f"{scene_channel}/LATEST.json"
    path = _resolve_scene_contract_path(rel_path)
    if not path:
        return None, ref
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), ref
    except Exception as exc:
        if logger is not None:
            try:
                logger.warning("scene contract load failed: %s (%s)", path, exc)
            except Exception:
                pass
        return None, ref


def merge_missing_scenes_from_registry(env, scenes, warnings):
    try:
        from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs
    except Exception:
        return scenes
    current = [scene for scene in (scenes or []) if isinstance(scene, dict)]
    existing = {
        str(scene.get("code") or scene.get("key") or "").strip()
        for scene in current
        if isinstance(scene, dict)
    }
    existing = {code for code in existing if code}
    registry_scenes = load_scene_configs(env) or []
    appended = []
    for scene in registry_scenes:
        if not isinstance(scene, dict):
            continue
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code or code in existing:
            continue
        item = dict(scene)
        target = item.get("target")
        if isinstance(target, dict):
            item["target"] = dict(target)
        current.append(item)
        existing.add(code)
        appended.append(code)
    if appended and isinstance(warnings, list):
        warnings.append({
            "code": "SCENE_FALLBACK_MERGED",
            "severity": "info",
            "scene_key": "",
            "message": "missing scenes merged from registry fallback",
            "field": "scenes",
            "reason": "contract_gap",
            "count": len(appended),
            "scene_codes": appended[:20],
        })
    return current

