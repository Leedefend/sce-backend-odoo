#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
import time
from datetime import datetime
from http.client import RemoteDisconnected
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from scene_legacy_contract import require_deprecation_headers, require_deprecation_payload  # noqa: E402


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


def _request_json(req: urlrequest.Request, *, retries: int = 3, backoff_sec: float = 0.5):
    attempt = 0
    while True:
        attempt += 1
        try:
            with urlrequest.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8") or "{}"
                return resp.status, json.loads(body), dict(resp.headers or {})
        except HTTPError as e:
            body = e.read().decode("utf-8") if hasattr(e, "read") else ""
            try:
                payload = json.loads(body or "{}")
            except Exception:
                payload = {"raw": body}
            return e.code, payload, dict(getattr(e, "headers", {}) or {})
        except (RemoteDisconnected, ConnectionResetError, URLError) as e:
            if attempt >= retries:
                raise RuntimeError(f"HTTP request failed after retries: {e}") from e
            time.sleep(backoff_sec * attempt)


def _http_post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    status, body, _ = _request_json(req)
    return status, body


def _http_get_json(url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
    req = urlrequest.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    return _request_json(req)


def _normalize_obj(obj):
    deny_keys = {
        "trace_id",
        "elapsed_ms",
        "expires_at",
        "token",
        "server_time",
        "timestamp",
        "generated_at",
        "__generated_at",
        "created_at",
        "write_date",
        "session_id",
        "captured_at",
    }
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in deny_keys:
                continue
            out[k] = _normalize_obj(v)
        return out
    if isinstance(obj, list):
        items = [_normalize_obj(v) for v in obj]
        return _sort_list(items)
    return obj


def _sort_list(items):
    if not items:
        return items
    if all(isinstance(x, (int, float, str)) for x in items):
        try:
            return sorted(items)
        except Exception:
            return items
    if all(isinstance(x, dict) for x in items):
        key_fields = ("id", "menu_id", "action_id", "key", "name", "model")

        def _key(d):
            for f in key_fields:
                if f in d and d[f] is not None:
                    return str(d[f])
            return json.dumps(d, sort_keys=True, ensure_ascii=False)

        try:
            return sorted(items, key=_key)
        except Exception:
            return items
    return items


def _write_snapshot(out_dir: str, name: str, payload: dict):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _cleanup_test_pack(import_url: str, headers: dict, payload: dict) -> None:
    _http_post_json(
        import_url,
        {
            "cleanup_test": True,
            "capabilities": payload.get("capabilities"),
            "scenes": payload.get("scenes"),
        },
        headers=headers,
    )


def main():
    base_url = _get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or os.getenv("DB") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    out_dir = os.getenv("E2E_OUT_DIR")
    if not out_dir:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join("artifacts", "e2e", f"scene_smoke_{ts}")

    intent_url = f"{base_url}/api/v1/intent"
    scenes_url = f"{base_url}/api/scenes/my"
    scenes_url_tests = f"{base_url}/api/scenes/my?include_tests=1"
    import_url = f"{base_url}/api/scenes/import"

    # login
    login_payload = {
        "intent": "login",
        "params": {"db": db_name, "login": login, "password": password},
    }
    status, login_resp = _http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    if status == 404:
        raise RuntimeError(
            f"intent endpoint not found at {intent_url} (smart_core not installed?)"
        )
    if not login_resp.get("ok"):
        raise RuntimeError(f"login failed: {login_resp}")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    auth_header = {"Authorization": f"Bearer {token}"}

    seed_payload = {
        "mode": "merge",
        "capabilities": [
            {
                "key": "scene.smoke.default",
                "name": "Scene Smoke Default",
                "intent": "system.init",
                "is_test": True,
            }
        ],
        "scenes": [
            {
                "code": "scene_smoke_default",
                "name": "Scene Smoke Default",
                "layout": "grid",
                "state": "published",
                "is_test": True,
                "tiles": [{"capability_key": "scene.smoke.default", "sequence": 10}],
            }
        ],
    }
    created_test = False
    try:
        # get scenes
        status, scenes_resp, scenes_headers = _http_get_json(scenes_url, headers=auth_header)
        if status >= 400 or not scenes_resp.get("ok"):
            raise RuntimeError(f"scenes.my failed: {scenes_resp}")
        scenes_data = scenes_resp.get("data") or {}
        scenes = scenes_data.get("scenes") or []
        if not scenes:
            status, seed_resp = _http_post_json(import_url, seed_payload, headers=auth_header)
            if status >= 400 or not seed_resp.get("ok"):
                raise RuntimeError(f"scenes.import seed failed: {seed_resp}")
            created_test = True
            status, scenes_resp, scenes_headers = _http_get_json(scenes_url_tests, headers=auth_header)
            if status >= 400 or not scenes_resp.get("ok"):
                raise RuntimeError(f"scenes.my (after seed) failed: {scenes_resp}")
            scenes_data = scenes_resp.get("data") or {}
            scenes = scenes_data.get("scenes") or []
            if not scenes:
                raise RuntimeError("scenes.my returned empty scenes list after seed")
        require_deprecation_payload(scenes_data, label="scenes.my")
        require_deprecation_headers(scenes_headers, label="scenes.my")
        default_code = scenes_data.get("default_scene")
        scene = next((s for s in scenes if s.get("code") == default_code), scenes[0])
        tiles = scene.get("tiles") or []
        if not tiles:
            raise RuntimeError("scene has no tiles")
        tile = tiles[0]
        intent = tile.get("intent")
        payload = tile.get("payload") or {}
        if not intent:
            raise RuntimeError("tile missing intent")
        if db_name and "db" not in payload:
            payload["db"] = db_name

        status, intent_resp = _http_post_json(
            intent_url, {"intent": intent, "params": payload}, headers=auth_header
        )
        if status >= 400 or not intent_resp.get("ok"):
            raise RuntimeError(f"scene tile intent failed: {intent_resp}")

        snapshot = {
            "meta": {
                "base_url": base_url,
                "db": db_name,
                "login": login,
                "captured_at": int(time.time()),
            },
            "scenes": scenes_resp,
            "tile_intent": {"intent": intent, "payload": payload},
            "tile_result": intent_resp,
        }
        raw_path = _write_snapshot(out_dir, "snapshot.raw.json", snapshot)
        normalized = _normalize_obj(snapshot)
        norm_path = _write_snapshot(out_dir, "snapshot.normalized.json", normalized)
        print(f"[e2e.scene] raw snapshot: {raw_path}")
        print(f"[e2e.scene] normalized snapshot: {norm_path}")
    finally:
        if created_test:
            _cleanup_test_pack(import_url, auth_header, seed_payload)


if __name__ == "__main__":
    main()
