#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


def _load_env_value_from_file(env_path: str, key: str) -> str | None:
    if not env_path or not os.path.isfile(env_path):
        return None
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _get_base_url() -> str:
    base = os.getenv("E2E_BASE_URL", "").strip()
    if base:
        return base.rstrip("/")
    port = os.getenv("ODOO_PORT")
    if not port:
        env_file = os.getenv("ENV_FILE") or os.path.join(os.getcwd(), ".env")
        port = _load_env_value_from_file(env_file, "ODOO_PORT")
    if not port:
        port = "8070"
    return f"http://localhost:{port}"


def _http_post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body or "{}")
        except Exception:
            return e.code, {"raw": body}
    except URLError as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def _http_get_json(url: str, headers: dict | None = None) -> tuple[int, dict]:
    req = urlrequest.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body or "{}")
        except Exception:
            return e.code, {"raw": body}
    except URLError as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def _require_ok(status: int, payload: dict, label: str):
    if status >= 400 or not payload.get("ok"):
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def main():
    base_url = _get_base_url()
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
    status, login_resp = _http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    _require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth_header = {"Authorization": f"Bearer {token}"}

    status, export_resp = _http_get_json(export_url, headers=auth_header)
    _require_ok(status, export_resp, "scenes.export")
    pack = export_resp.get("data") or {}
    pack_meta = pack.get("pack_meta") or {}
    pack_id = pack_meta.get("pack_id")
    if not pack_id:
        raise RuntimeError("export missing pack_id")

    status, publish_resp = _http_post_json(publish_url, pack, headers=auth_header)
    _require_ok(status, publish_resp, "packs.publish")

    status, catalog_resp = _http_get_json(catalog_url, headers=auth_header)
    _require_ok(status, catalog_resp, "packs.catalog")
    packs = (catalog_resp.get("data") or {}).get("packs") or []
    if pack_id not in [p.get("pack_id") for p in packs]:
        raise RuntimeError("catalog missing published pack_id")

    # dry_run install
    status, install_dry = _http_post_json(
        install_url,
        {"pack_id": pack_id, "mode": "merge", "dry_run": True, "strict": True},
        headers=auth_header,
    )
    _require_ok(status, install_dry, "packs.install dry_run")
    diff_v2 = (install_dry.get("data") or {}).get("diff_v2") or {}
    if not (diff_v2.get("creates") is not None and diff_v2.get("updates") is not None):
        raise RuntimeError("install dry_run missing diff_v2")

    # confirm install (merge)
    status, install_ok = _http_post_json(
        install_url,
        {"pack_id": pack_id, "mode": "merge", "confirm": True, "strict": True},
        headers=auth_header,
    )
    _require_ok(status, install_ok, "packs.install confirm")

    status, scenes_resp = _http_get_json(scenes_url, headers=auth_header)
    _require_ok(status, scenes_resp, "scenes.my")

    print("[marketplace_smoke] PASS")


if __name__ == "__main__":
    main()
