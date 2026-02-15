#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import time
from http.client import RemoteDisconnected
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


def load_env_value_from_file(env_path: str, key: str) -> str | None:
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


def get_base_url() -> str:
    base = os.getenv("E2E_BASE_URL", "").strip()
    if base:
        return base.rstrip("/")
    port = os.getenv("ODOO_PORT")
    if not port:
        env_file = os.getenv("ENV_FILE") or os.path.join(os.getcwd(), ".env")
        port = load_env_value_from_file(env_file, "ODOO_PORT")
    if not port:
        port = "8070"
    return f"http://localhost:{port}"


def _request_json(
    req: urlrequest.Request,
    *,
    retries: int = 3,
    backoff_sec: float = 0.5,
) -> tuple[int, dict, dict]:
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


def http_post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    status, body, _ = _request_json(req)
    return status, body


def http_get_json(url: str, headers: dict | None = None) -> tuple[int, dict]:
    status, payload, _ = http_get_json_with_headers(url, headers=headers)
    return status, payload


def http_get_json_with_headers(url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
    req = urlrequest.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    return _request_json(req)
