# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from typing import Any

from odoo import api

from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.core.ui_base_contract_canonicalizer import canonicalize_ui_base_contract
from odoo.addons.smart_core.core.ui_base_contract_asset_repository import upsert_asset


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _asset_hash(payload: dict) -> str:
    raw = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _asset_version(payload_hash: str) -> str:
    digest = _text(payload_hash)
    return f"h-{digest[:12]}" if digest else "v1"


def _scene_action_id(env, scene: dict) -> int:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    try:
        action_id = int(target.get("action_id") or 0)
    except Exception:
        action_id = 0
    if action_id > 0:
        return action_id
    action_xmlid = _text(target.get("action_xmlid"))
    if not action_xmlid:
        return 0
    try:
        rec = env.ref(action_xmlid, raise_if_not_found=False)
    except Exception:
        rec = None
    try:
        return int(rec.id) if rec else 0
    except Exception:
        return 0


def _load_scene_rows(env) -> tuple[list[dict], str]:
    try:
        from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs, has_db_scenes
    except Exception:
        return [], "fallback"
    try:
        payload = load_scene_configs(env) or []
        rows = payload if isinstance(payload, list) else []
        source = "db" if has_db_scenes(env) else "fallback"
        return rows, source
    except Exception:
        return [], "fallback"


def _build_runtime_ui_base_contract(env, *, action_id: int) -> dict:
    if int(action_id or 0) <= 0:
        return {}
    dispatch_ctx = api.Environment(env.cr, env.user.id, dict(env.context or {}))
    payload, _versions = ActionDispatcher(env, dispatch_ctx).dispatch(
        {
            "subject": "action",
            "action_id": int(action_id),
            "with_data": False,
        }
    )
    contract_service = ContractService(env)
    finalized = contract_service.finalize_contract(
        {
            "ok": True,
            "data": _as_dict(payload),
            "meta": {"subject": "asset.ui_base", "action_id": int(action_id)},
        }
    )
    data = finalized.get("data") if isinstance(finalized, dict) else {}
    return canonicalize_ui_base_contract(_as_dict(data))


def _build_scene_minimal_ui_base_contract(scene_key: str, scene: dict) -> dict:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    model = _text(target.get("model")) or "project.project"
    payload = {
        "model": model,
        "views": {"tree": {"fields": ["name"]}},
        "fields": {"name": {"type": "char"}},
        "search": {"fields": ["name"]},
    }
    key = _text(scene_key)
    if key == "projects.intake":
        payload["views"] = {"form": {"fields": ["name", "partner_id", "date_start"]}}
        payload["validator"] = {"required": ["name"]}
    return canonicalize_ui_base_contract(payload)


def refresh_ui_base_contract_assets(
    env,
    *,
    scene_keys: list[str] | None = None,
    limit: int = 50,
    role_code: str | None = None,
    company_id: int | None = None,
    source_type: str = "precompile",
    code_version: str | None = None,
) -> dict:
    requested_keys = {_text(item) for item in (scene_keys or []) if _text(item)}
    rows, scene_source = _load_scene_rows(env)
    produced = 0
    skipped = 0
    failed = 0
    for scene in rows:
        if produced >= max(int(limit or 0), 1):
            break
        if not isinstance(scene, dict):
            skipped += 1
            continue
        scene_key = _text(scene.get("code") or scene.get("key"))
        if not scene_key:
            skipped += 1
            continue
        if requested_keys and scene_key not in requested_keys:
            skipped += 1
            continue
        action_id = _scene_action_id(env, scene)
        try:
            source_ref = ""
            if action_id > 0:
                payload = _build_runtime_ui_base_contract(env, action_id=action_id)
                source_ref = f"action:{action_id}"
            else:
                payload = _build_scene_minimal_ui_base_contract(scene_key, scene)
                source_ref = f"scene:{scene_key}:minimal"
            digest = _asset_hash(payload)
            upsert_asset(
                env,
                scene_key=scene_key,
                payload=payload,
                role_code=role_code,
                company_id=company_id,
                asset_version=_asset_version(digest),
                asset_hash=digest,
                source_ref=source_ref,
                source_type=source_type,
                code_version=_text(code_version),
                status="active",
            )
            produced += 1
        except Exception:
            failed += 1
    return {
        "requested_scene_count": len(requested_keys),
        "produced_count": produced,
        "skipped_count": skipped,
        "failed_count": failed,
        "scene_source": _text(scene_source),
    }
