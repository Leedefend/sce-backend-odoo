#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

NOISE_KEYS = {
    "trace_id",
    "server_time",
    "expires_at",
    "iat",
    "exp",
    "jti",
    "token",
}


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


def _normalize(obj):
    if isinstance(obj, dict):
        return {
            k: _normalize(v)
            for k, v in obj.items()
            if k not in NOISE_KEYS
        }
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj


def main():
    base_url = _get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    outdir = os.getenv("OUTDIR") or "/tmp/capability_smoke"
    os.makedirs(outdir, exist_ok=True)

    intent_url = f"{base_url}/api/v1/intent"
    search_url = f"{base_url}/api/capabilities/search?smoke=1&include_all=1"

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

    status, search_resp = _http_get_json(search_url, headers=auth_header)
    _require_ok(status, search_resp, "capabilities.search")
    data = search_resp.get("data") or {}
    capabilities = data.get("capabilities") or []
    if not capabilities:
        raise RuntimeError("capabilities.search returned empty list for smoke")

    for cap in capabilities:
        key = cap.get("key") or "unknown"
        intent = cap.get("intent")
        default_payload = cap.get("default_payload") or {}
        if not intent:
            raise RuntimeError(f"capability {key} missing intent")

        params = dict(default_payload)
        params.setdefault("db", db_name)
        status, resp = _http_post_json(
            intent_url,
            {"intent": intent, "params": params},
            headers=auth_header,
        )
        _require_ok(status, resp, f"capability {key} ({intent})")

        raw_path = os.path.join(outdir, f"{key}.raw.json")
        norm_path = os.path.join(outdir, f"{key}.normalized.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(resp, f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(norm_path, "w", encoding="utf-8") as f:
            json.dump(_normalize(resp), f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"[capability_smoke] PASS outdir={outdir}")


if __name__ == "__main__":
    main()
