# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import hashlib
from typing import Any


ASSET_MODEL = "sc.ui.base.contract.asset"
CONTRACT_KIND_UI_BASE = "ui_base"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_payload(payload: dict | None) -> dict:
    return payload if isinstance(payload, dict) else {}


def _parse_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
    if model is None:
        return {}
    rec = model.search(_scope_domain(scene_key=scene_key, role_code=role_code, company_id=company_id), limit=1)
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
    if model is None or not key:
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
        existing_active = model.search(active_domain)
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

    bound_count = 0
    missing_count = 0
    enriched: list[dict] = []
    for row in rows:
        scene_key = _text(row.get("code") or row.get("key"))
        entry = dict(row)
        if scene_key and isinstance(assets.get(scene_key), dict):
            asset = assets.get(scene_key) or {}
            if not isinstance(entry.get("ui_base_contract"), dict):
                entry["ui_base_contract"] = asset.get("payload") or {}
            entry["ui_base_contract_ref"] = {
                "asset_id": asset.get("id"),
                "asset_version": asset.get("asset_version"),
                "asset_hash": asset.get("asset_hash"),
                "source_ref": asset.get("source_ref"),
            }
            bound_count += 1
        elif scene_key:
            missing_count += 1
        enriched.append(entry)

    return {
        "scenes": enriched,
        "asset_scene_count": len(assets),
        "bound_scene_count": bound_count,
        "missing_scene_count": missing_count,
    }
