#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json, http_post_json


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

    status, scenes_resp = http_get_json(scenes_url, headers=auth_header)
    require_ok(status, scenes_resp, "scenes.my")

    print("[marketplace_smoke] PASS")


if __name__ == "__main__":
    main()
