#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json, http_get_json_with_headers, http_post_json


def _require_deprecation(payload: dict, *, label: str) -> None:
    dep = payload.get("deprecation") if isinstance(payload.get("deprecation"), dict) else {}
    if (dep.get("status") or "").strip().lower() != "deprecated":
        raise RuntimeError(f"{label} missing deprecation.status=deprecated")
    if not str(dep.get("replacement") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.replacement")
    sunset_date = str(dep.get("sunset_date") or "").strip()
    if sunset_date != "2026-04-30":
        raise RuntimeError(f"{label} invalid deprecation.sunset_date: {sunset_date}")


def _require_deprecation_headers(headers: dict, *, label: str) -> None:
    dep_header = str(headers.get("Deprecation") or headers.get("deprecation") or "").strip().lower()
    if dep_header != "true":
        raise RuntimeError(f"{label} missing Deprecation header=true")
    sunset_header = str(headers.get("Sunset") or headers.get("sunset") or "").strip()
    if not sunset_header:
        raise RuntimeError(f"{label} missing Sunset header")
    if "GMT" not in sunset_header:
        raise RuntimeError(f"{label} Sunset header must be GMT: {sunset_header}")
    link_header = str(headers.get("Link") or headers.get("link") or "").strip()
    if "successor-version" not in link_header or "/api/v1/intent" not in link_header:
        raise RuntimeError(f"{label} missing Link successor-version header")


def main():
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    intent_url = f"{base_url}/api/v1/intent"
    export_url = f"{base_url}/api/scenes/export?include_caps=1&pack_type=platform&vendor=local&channel=dev"
    publish_url = f"{base_url}/api/packs/publish"
    catalog_url = f"{base_url}/api/packs/catalog"
    install_url = f"{base_url}/api/packs/install"
    scenes_url = f"{base_url}/api/scenes/my"

    login_payload = {
        "intent": "login",
        "params": {"db": db_name, "login": login, "password": password},
    }
    status, login_resp = http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth_header = {"Authorization": f"Bearer {token}"}

    status, export_resp = http_get_json(export_url, headers=auth_header)
    require_ok(status, export_resp, "scenes.export")
    pack = export_resp.get("data") or {}
    pack_meta = pack.get("pack_meta") or {}
    pack_id = pack_meta.get("pack_id")
    if not pack_id:
        raise RuntimeError("export missing pack_id")

    status, publish_resp = http_post_json(publish_url, pack, headers=auth_header)
    require_ok(status, publish_resp, "packs.publish")

    status, catalog_resp = http_get_json(catalog_url, headers=auth_header)
    require_ok(status, catalog_resp, "packs.catalog")
    packs = (catalog_resp.get("data") or {}).get("packs") or []
    if pack_id not in [p.get("pack_id") for p in packs]:
        raise RuntimeError("catalog missing published pack_id")

    # dry_run install
    status, install_dry = http_post_json(
        install_url,
        {"pack_id": pack_id, "mode": "merge", "dry_run": True, "strict": True},
        headers=auth_header,
    )
    require_ok(status, install_dry, "packs.install dry_run")
    diff_v2 = (install_dry.get("data") or {}).get("diff_v2") or {}
    if not (diff_v2.get("creates") is not None and diff_v2.get("updates") is not None):
        raise RuntimeError("install dry_run missing diff_v2")

    # confirm install (merge)
    status, install_ok = http_post_json(
        install_url,
        {"pack_id": pack_id, "mode": "merge", "confirm": True, "strict": True},
        headers=auth_header,
    )
    require_ok(status, install_ok, "packs.install confirm")

    status, scenes_resp, scenes_headers = http_get_json_with_headers(scenes_url, headers=auth_header)
    require_ok(status, scenes_resp, "scenes.my")
    _require_deprecation(scenes_resp.get("data") or {}, label="scenes.my")
    _require_deprecation_headers(scenes_headers, label="scenes.my")

    print("[marketplace_smoke] PASS")


if __name__ == "__main__":
    main()
