# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import hashlib
import os
from typing import Any

from odoo.addons.smart_core.core.ui_base_contract_canonicalizer import canonicalize_ui_base_contract


ASSET_MODEL = "sc.ui.base.contract.asset"
CONTRACT_KIND_UI_BASE = "ui_base"
ASSET_TABLE = "sc_ui_base_contract_asset"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_payload(payload: dict | None) -> dict:
    return canonicalize_ui_base_contract(payload if isinstance(payload, dict) else {})


def _parse_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return canonicalize_ui_base_contract(parsed if isinstance(parsed, dict) else {})


def _scope_domain(*, scene_key: str, role_code: str | None, company_id: int | None, status: str = "active") -> list:
    domain = [
        ("contract_kind", "=", CONTRACT_KIND_UI_BASE),
        ("scene_key", "=", _text(scene_key)),
        ("status", "=", _text(status) or "active"),
    ]
    if role_code:
        domain.append(("role_code", "=", _text(role_code)))
    else:
        domain.append(("role_code", "=", False))
    if company_id:
        domain.append(("company_id", "=", int(company_id)))
    else:
        domain.append(("company_id", "=", False))
    return domain


def _asset_model(env):
    try:
        if ASSET_MODEL not in env:
            return None
        return env[ASSET_MODEL].sudo()
    except Exception:
        return None


def _asset_table_available(env) -> bool:
    try:
        if env is None or env.cr is None:
            return False
        env.cr.execute("SELECT to_regclass(%s)", [ASSET_TABLE])
        row = env.cr.fetchone()
        return bool(row and row[0])
    except Exception:
        return False


def _runtime_env() -> str:
    return _text(os.environ.get("ENV") or "dev").lower() or "dev"


def _should_auto_refresh_missing_assets(env) -> bool:
    override = _text(os.environ.get("SC_UI_BASE_ASSET_AUTO_REFRESH_MISSING"))
    if override:
        return override.lower() in {"1", "true", "yes", "on"}
    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.ui_base_contract_asset.auto_refresh_missing") if env is not None else ""
    except Exception:
        raw = ""
    if _text(raw):
        return _text(raw).lower() in {"1", "true", "yes", "on"}
    return _runtime_env() in {"dev", "test"}


def _auto_refresh_missing_assets(
    env,
    *,
    scene_keys: list[str],
    scene_rows: list[dict] | None = None,
    role_code: str | None,
    company_id: int | None,
) -> None:
    if not scene_keys:
        return
    try:
        from odoo.addons.smart_core.core.ui_base_contract_asset_producer import refresh_ui_base_contract_assets

        refresh_ui_base_contract_assets(
            env,
            scene_keys=scene_keys,
            scene_rows=scene_rows,
            limit=max(len(scene_keys), 1),
            role_code=role_code,
            company_id=company_id,
            source_type="runtime_intent",
            code_version="auto-refresh-missing-v1",
        )
    except Exception:
        return


def _build_runtime_contract_fallback(env, *, action_id: int) -> dict:
    if int(action_id or 0) <= 0:
        return {}
    try:
        from odoo.addons.smart_core.core.ui_base_contract_asset_producer import _build_runtime_ui_base_contract

        payload = _build_runtime_ui_base_contract(env, action_id=int(action_id))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _resolve_scene_action_id(env, scene: dict) -> int:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    action_id = _safe_int(target.get("action_id"), 0)
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


def _is_canonical_scene_root(scene: dict) -> bool:
    payload = scene if isinstance(scene, dict) else {}
    scene_key = _text(payload.get("code") or payload.get("key"))
    if not scene_key:
        return False
    target = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    route = _text(target.get("route"))
    action_xmlid = _text(target.get("action_xmlid"))
    model = _text(target.get("model"))
    record_id = _safe_int(target.get("record_id"), 0)
    action_id = _safe_int(target.get("action_id"), 0)
    return (
        route == f"/s/{scene_key}"
        and action_id <= 0
        and not action_xmlid
        and not model
        and record_id <= 0
    )


def _asset_is_stale_for_scene(asset: dict | None, scene: dict) -> bool:
    payload = asset if isinstance(asset, dict) else {}
    if not payload:
        return False
    if not _is_canonical_scene_root(scene):
        return False
    source_ref = _text(payload.get("source_ref"))
    return source_ref.startswith("action:")


def _minimal_ui_base_contract(scene_key: str) -> dict:
    return {
        "model": "res.partner",
        "views": {"tree": {"fields": ["name"]}},
        "fields": {"name": {"type": "char"}},
        "search": {"fields": ["name"]},
    }


def _scope_hash(*, scene_key: str, role_code: str | None, company_id: int | None, contract_kind: str = CONTRACT_KIND_UI_BASE) -> str:
    raw = "|".join(
        [
            _text(contract_kind) or CONTRACT_KIND_UI_BASE,
            _text(scene_key),
            _text(role_code),
            str(int(company_id or 0)),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _search_one(env, *, scene_key: str, role_code: str | None, company_id: int | None) -> dict:
    model = _asset_model(env)
    if model is None or not _asset_table_available(env):
        return {}
    with env.cr.savepoint():
        try:
            rec = model.search(_scope_domain(scene_key=scene_key, role_code=role_code, company_id=company_id), limit=1)
        except Exception:
            return {}
    if not rec:
        return {}
    return {
        "id": int(rec.id),
        "contract_kind": _text(rec.contract_kind),
        "scene_key": _text(rec.scene_key),
        "role_code": _text(rec.role_code),
        "company_id": int(rec.company_id.id) if rec.company_id else None,
        "scope_hash": _text(rec.scope_hash),
        "source_type": _text(rec.source_type),
        "asset_version": _text(rec.asset_version),
        "asset_hash": _text(rec.asset_hash),
        "source_ref": _text(rec.source_ref),
        "code_version": _text(rec.code_version),
        "generated_at": _text(rec.generated_at),
        "payload": _parse_payload(rec.payload_json),
        "write_date": _text(rec.write_date),
    }


def get_latest_asset(
    env,
    *,
    scene_key: str,
    role_code: str | None = None,
    company_id: int | None = None,
) -> dict:
    key = _text(scene_key)
    if not key:
        return {}
    role = _text(role_code)
    cid = int(company_id or 0) or None
    candidate_scopes = [
        (role or None, cid),
        (None, cid),
        (role or None, None),
        (None, None),
    ]
    for scoped_role, scoped_company in candidate_scopes:
        data = _search_one(env, scene_key=key, role_code=scoped_role, company_id=scoped_company)
        if data:
            return data
    return {}


def build_scene_asset_map(
    env,
    *,
    scene_keys: list[str] | None,
    role_code: str | None = None,
    company_id: int | None = None,
) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in scene_keys or []:
        key = _text(item)
        if not key or key in out:
            continue
        data = get_latest_asset(env, scene_key=key, role_code=role_code, company_id=company_id)
        if data:
            out[key] = data
    return out


def upsert_asset(
    env,
    *,
    scene_key: str,
    payload: dict | None,
    role_code: str | None = None,
    company_id: int | None = None,
    asset_version: str = "v1",
    asset_hash: str | None = None,
    source_ref: str | None = None,
    source_type: str = "runtime_intent",
    code_version: str | None = None,
    status: str = "active",
) -> dict:
    model = _asset_model(env)
    key = _text(scene_key)
    if model is None or not key or not _asset_table_available(env):
        return {}

    role = _text(role_code)
    company = int(company_id or 0) or None
    version = _text(asset_version) or "v1"
    state = _text(status) or "active"
    payload_body = _normalize_payload(payload)
    scope_hash = _scope_hash(scene_key=key, role_code=role or None, company_id=company)
    vals = {
        "name": f"{key}@{version}",
        "contract_kind": CONTRACT_KIND_UI_BASE,
        "scene_key": key,
        "role_code": role or False,
        "company_id": company or False,
        "scope_hash": scope_hash,
        "source_type": _text(source_type) or "runtime_intent",
        "status": state,
        "asset_version": version,
        "asset_hash": _text(asset_hash),
        "source_ref": _text(source_ref),
        "code_version": _text(code_version),
        "payload_json": json.dumps(payload_body, ensure_ascii=False, separators=(",", ":")),
    }
    with env.cr.savepoint():
        try:
            rec = model.search(
                [
                    ("contract_kind", "=", CONTRACT_KIND_UI_BASE),
                    ("scene_key", "=", key),
                    ("role_code", "=", role or False),
                    ("company_id", "=", company or False),
                    ("asset_version", "=", version),
                ],
                limit=1,
            )
        except Exception:
            return {}
    if state == "active":
        active_domain = [
            ("contract_kind", "=", CONTRACT_KIND_UI_BASE),
            ("scene_key", "=", key),
            ("role_code", "=", role or False),
            ("company_id", "=", company or False),
            ("status", "=", "active"),
        ]
        if rec:
            active_domain.append(("id", "!=", rec.id))
        with env.cr.savepoint():
            try:
                existing_active = model.search(active_domain)
            except Exception:
                return {}
        if existing_active:
            existing_active.write({"status": "archived"})
    if rec:
        rec.write(vals)
    else:
        rec = model.create(vals)
    return get_latest_asset(env, scene_key=key, role_code=role or None, company_id=company)


def bind_scene_assets(
    env,
    *,
    scenes: list[dict] | None,
    role_code: str | None = None,
    company_id: int | None = None,
) -> dict:
    rows = [item for item in (scenes or []) if isinstance(item, dict)]
    scene_keys: list[str] = []
    for row in rows:
        key = _text(row.get("code") or row.get("key"))
        if key:
            scene_keys.append(key)
    assets = build_scene_asset_map(
        env,
        scene_keys=scene_keys,
        role_code=role_code,
        company_id=company_id,
    )

    fallback_bind_limit = 10
    fallback_bound = 0

    def _bind_with_assets(
        asset_map: dict[str, dict],
        *,
        allow_runtime_fallback: bool,
    ) -> tuple[list[dict], int, int, list[str]]:
        nonlocal fallback_bound
        bound = 0
        missing = 0
        missing_keys: list[str] = []
        bound_rows: list[dict] = []
        for row in rows:
            scene_key = _text(row.get("code") or row.get("key"))
            entry = dict(row)
            asset = asset_map.get(scene_key) if scene_key else {}
            asset_usable = isinstance(asset, dict) and asset and not _asset_is_stale_for_scene(asset, entry)
            if scene_key and asset_usable:
                asset = asset_map.get(scene_key) or {}
                if not isinstance(entry.get("ui_base_contract"), dict):
                    entry["ui_base_contract"] = asset.get("payload") or {}
                entry["ui_base_contract_ref"] = {
                    "asset_id": asset.get("id"),
                    "asset_version": asset.get("asset_version"),
                    "asset_hash": asset.get("asset_hash"),
                    "source_ref": asset.get("source_ref"),
                }
                bound += 1
            elif scene_key:
                if allow_runtime_fallback:
                    payload = {}
                    action_id = _resolve_scene_action_id(env, entry)
                    if fallback_bound < fallback_bind_limit:
                        payload = _build_runtime_contract_fallback(env, action_id=action_id)
                    if isinstance(payload, dict) and payload:
                        entry["ui_base_contract"] = payload
                        entry["ui_base_contract_ref"] = {
                            "asset_id": None,
                            "asset_version": "runtime-fallback",
                            "asset_hash": "",
                            "source_ref": f"action:{action_id}",
                        }
                        bound += 1
                        fallback_bound += 1
                    else:
                        minimal = _minimal_ui_base_contract(scene_key)
                        if minimal:
                            entry["ui_base_contract"] = minimal
                            entry["ui_base_contract_ref"] = {
                                "asset_id": None,
                                "asset_version": "runtime-minimal",
                                "asset_hash": "",
                                "source_ref": f"scene:{scene_key}",
                            }
                            bound += 1
                        else:
                            missing += 1
                            missing_keys.append(scene_key)
                else:
                    missing += 1
                    missing_keys.append(scene_key)
            bound_rows.append(entry)
        return bound_rows, bound, missing, missing_keys

    enriched, bound_count, missing_count, missing_keys = _bind_with_assets(
        assets,
        allow_runtime_fallback=False,
    )

    if missing_count > 0 and _should_auto_refresh_missing_assets(env):
        _auto_refresh_missing_assets(
            env,
            scene_keys=missing_keys,
            scene_rows=[row for row in rows if _text(row.get("code") or row.get("key")) in set(missing_keys)],
            role_code=role_code,
            company_id=company_id,
        )
        refreshed_assets = build_scene_asset_map(
            env,
            scene_keys=scene_keys,
            role_code=role_code,
            company_id=company_id,
        )
        enriched, bound_count, missing_count, _ = _bind_with_assets(
            refreshed_assets,
            allow_runtime_fallback=True,
        )
        assets = refreshed_assets
    else:
        enriched, bound_count, missing_count, _ = _bind_with_assets(
            assets,
            allow_runtime_fallback=True,
        )

    return {
        "scenes": enriched,
        "asset_scene_count": len(assets),
        "bound_scene_count": bound_count,
        "missing_scene_count": missing_count,
    }
