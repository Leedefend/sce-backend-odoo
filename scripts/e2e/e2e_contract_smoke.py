#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import time
from datetime import datetime
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


def _write_json(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=2)


def main():
    base_url = _get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or os.getenv("DB") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    out_dir = os.getenv("E2E_OUT_DIR")
    if not out_dir:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join("artifacts", "e2e", f"contract_smoke_{ts}")

    intent_url = f"{base_url}/api/v1/intent"

    # 1) login (anonymous intent)
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

    # 2) system.init
    init_payload = {"intent": "system.init", "params": {"db": db_name}}
    status, init_resp = _http_post_json(intent_url, init_payload, headers=auth_header)
    if status >= 400 or not init_resp.get("ok"):
        raise RuntimeError(f"system.init failed: {init_resp}")

    # 3) ui.contract (nav op)
    contract_payload = {"intent": "ui.contract", "params": {"db": db_name, "op": "nav"}}
    status, contract_resp = _http_post_json(
        intent_url, contract_payload, headers=auth_header
    )
    if status >= 400 or not contract_resp.get("ok"):
        raise RuntimeError(f"ui.contract failed: {contract_resp}")

    # 4) api.data list
    data_payload = {
        "intent": "api.data",
        "params": {"db": db_name, "model": "res.users", "fields": ["id", "name"], "limit": 1},
    }
    status, data_resp = _http_post_json(intent_url, data_payload, headers=auth_header)
    if status >= 400 or not data_resp.get("ok"):
        raise RuntimeError(f"api.data failed: {data_resp}")

    snapshot = {
        "meta": {
            "base_url": base_url,
            "db": db_name,
            "login": login,
            "captured_at": int(time.time()),
        },
        "login": login_resp,
        "system_init": init_resp,
        "ui_contract": contract_resp,
        "api_data": data_resp,
    }

    normalized = _normalize_obj(snapshot)

    raw_path = os.path.join(out_dir, "snapshot.raw.json")
    norm_path = os.path.join(out_dir, "snapshot.normalized.json")
    _write_json(raw_path, snapshot)
    _write_json(norm_path, normalized)

    print(f"[e2e] raw snapshot: {raw_path}")
    print(f"[e2e] normalized snapshot: {norm_path}")


if __name__ == "__main__":
    main()
