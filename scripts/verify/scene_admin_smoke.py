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
    scenes_url = f"{base_url}/api/scenes/my"
    pref_get_url = f"{base_url}/api/preferences/get"
    pref_set_url = f"{base_url}/api/preferences/set"
    export_url = f"{base_url}/api/scenes/export"

    # login (JWT)
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

    # scenes.my should be OK and non-empty
    status, scenes_resp = _http_get_json(scenes_url, headers=auth_header)
    _require_ok(status, scenes_resp, "scenes.my")
    scenes_data = scenes_resp.get("data") or {}
    scenes = scenes_data.get("scenes") or []
    if not scenes:
        raise RuntimeError("scenes.my returned empty list")
    default_scene = scenes_data.get("default_scene") or scenes[0].get("code")
    if not default_scene:
        raise RuntimeError("default_scene missing")

    # preference set/get should round-trip
    status, pref_set = _http_post_json(
        pref_set_url, {"default_scene": default_scene}, headers=auth_header
    )
    _require_ok(status, pref_set, "preferences.set")
    status, pref_get = _http_get_json(pref_get_url, headers=auth_header)
    _require_ok(status, pref_get, "preferences.get")
    pref_default = (pref_get.get("data") or {}).get("default_scene")
    if pref_default != default_scene:
        raise RuntimeError("preferences default_scene mismatch")

    # scenes.my should reflect default_scene
    status, scenes_resp2 = _http_get_json(scenes_url, headers=auth_header)
    _require_ok(status, scenes_resp2, "scenes.my (after pref)")
    if (scenes_resp2.get("data") or {}).get("default_scene") != default_scene:
        raise RuntimeError("scenes.my default_scene did not update")

    # export should be forbidden without auth
    status, export_noauth = _http_get_json(export_url)
    if status not in (401, 403):
        raise RuntimeError(f"export without auth should be 401/403, got {status}")

    # export with auth should succeed
    status, export_resp = _http_get_json(export_url, headers=auth_header)
    _require_ok(status, export_resp, "scenes.export")
    export_data = export_resp.get("data") or {}
    export_scenes = export_data.get("scenes") or []
    if not export_scenes:
        raise RuntimeError("scenes.export returned empty scenes")
    for scene in export_scenes:
        if "state" not in scene or "tiles" not in scene:
            raise RuntimeError("scenes.export scene missing state/tiles")

    print("[scene_admin_smoke] PASS")


if __name__ == "__main__":
    main()
