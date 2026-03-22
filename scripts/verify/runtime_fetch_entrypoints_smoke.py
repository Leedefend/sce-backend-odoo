#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "runtime_fetch_entrypoints_smoke.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _post(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict[str, Any] | None = None,
    *,
    db_name: str = "",
) -> tuple[int, dict[str, Any]]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {"checks": {}}

    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
    if status >= 400 or login_resp.get("ok") is not True:
        errors.append(f"login failed: status={status}")
    token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
    token = str(token or "").strip()
    if not token:
        errors.append("login token missing")

    if token:
        status, init_resp = _post(intent_url, token, "system.init", {"with_preload": False, "contract_mode": "default"}, db_name=db_name)
        if status >= 400 or init_resp.get("ok") is not True:
            errors.append(f"system.init failed: status={status}")
        init_data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        init_meta = init_data.get("init_meta") if isinstance(init_data.get("init_meta"), dict) else {}
        scene_subset = init_meta.get("scene_subset") if isinstance(init_meta.get("scene_subset"), list) else []
        default_route = init_data.get("default_route") if isinstance(init_data.get("default_route"), dict) else {}
        landing_scene_key = str(default_route.get("scene_key") or "workspace.home").strip() or "workspace.home"

        status, page_resp = _post(intent_url, token, "page.contract", {"page_key": "home"}, db_name=db_name)
        if status >= 400 or page_resp.get("ok") is not True:
            errors.append(
                f"page.contract(home) failed: status={status} code={((page_resp.get('error') or {}) if isinstance(page_resp.get('error'), dict) else {}).get('code')} message={((page_resp.get('error') or {}) if isinstance(page_resp.get('error'), dict) else {}).get('message')}"
            )
        page_data = page_resp.get("data") if isinstance(page_resp.get("data"), dict) else {}
        page_contract = page_data.get("page_contract") if isinstance(page_data.get("page_contract"), dict) else {}
        if not page_contract:
            errors.append("page.contract(home) missing page_contract")
        if "pages" in page_data:
            errors.append("page.contract(home) must not return pages wrapper")
        page_orchestration = page_contract.get("page_orchestration_v1") if isinstance(page_contract.get("page_orchestration_v1"), dict) else {}
        if not page_orchestration:
            errors.append("page.contract(home) missing page_orchestration_v1")

        status, catalog_resp = _post(intent_url, token, "scene.catalog", {}, db_name=db_name)
        if status >= 400 or catalog_resp.get("ok") is not True:
            errors.append(f"scene.catalog failed: status={status}")
        catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
        scenes = catalog_data.get("scenes") if isinstance(catalog_data.get("scenes"), list) else []
        if not scenes:
            errors.append("scene.catalog returned empty scenes")
        scene_codes = {str(row.get("code") or "").strip() for row in scenes if isinstance(row, dict)}
        if landing_scene_key and landing_scene_key not in scene_codes:
            errors.append(f"scene.catalog missing landing scene: {landing_scene_key}")
        if scene_subset:
            subset_hit = bool(scene_codes & {str(item or "").strip() for item in scene_subset if str(item or "").strip()})
            if not subset_hit:
                errors.append("scene.catalog does not overlap boot scene_subset")

        status, detail_resp = _post(intent_url, token, "scene.detail", {"scene_key": landing_scene_key}, db_name=db_name)
        if status >= 400 or detail_resp.get("ok") is not True:
            errors.append(f"scene.detail({landing_scene_key}) failed: status={status}")
        detail_data = detail_resp.get("data") if isinstance(detail_resp.get("data"), dict) else {}
        detail_scene = detail_data.get("scene") if isinstance(detail_data.get("scene"), dict) else {}
        if str(detail_scene.get("code") or "").strip() != landing_scene_key:
            errors.append("scene.detail returned mismatched scene code")

        status, collections_resp = _post(intent_url, token, "workspace.collections", {}, db_name=db_name)
        if status >= 400 or collections_resp.get("ok") is not True:
            errors.append(
                f"workspace.collections failed: status={status} code={((collections_resp.get('error') or {}) if isinstance(collections_resp.get('error'), dict) else {}).get('code')} message={((collections_resp.get('error') or {}) if isinstance(collections_resp.get('error'), dict) else {}).get('message')}"
            )
        collections_data = collections_resp.get("data") if isinstance(collections_resp.get("data"), dict) else {}
        collections = collections_data.get("collections") if isinstance(collections_data.get("collections"), dict) else {}
        if "workspace_home" in collections_data or "page_contracts" in collections_data:
            errors.append("workspace.collections must not leak preload/runtime page payloads")
        reported_keys = collections_data.get("keys") if isinstance(collections_data.get("keys"), list) else []
        if sorted([str(key) for key in collections.keys()]) != sorted([str(key) for key in reported_keys]):
            errors.append("workspace.collections keys payload mismatch")

        report["checks"] = {
            "landing_scene_key": landing_scene_key,
            "scene_subset_count": len(scene_subset),
            "page_contract_keys": sorted(list(page_contract.keys())),
            "catalog_count": len(scenes),
            "collections_keys": sorted(list(collections.keys())),
        }

    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    _write_json(OUT_JSON, report)

    if errors:
        print("[runtime_fetch_entrypoints_smoke] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[runtime_fetch_entrypoints_smoke] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _write_json(OUT_JSON, {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]})
        print("[runtime_fetch_entrypoints_smoke] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
