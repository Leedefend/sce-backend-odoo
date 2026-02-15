#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import urllib.request
from http.cookiejar import CookieJar
from urllib.error import HTTPError


def _post_json(url: str, payload: dict, *, cookie_jar: CookieJar, headers: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body, dict(resp.headers.items())
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body, dict(e.headers.items()) if e.headers else {}


def _load_json(body: str) -> dict:
    if not body:
        return {}
    try:
        return json.loads(body)
    except Exception:
        return {}


def _extract_etag(headers: dict) -> str:
    etag = headers.get("ETag") or headers.get("etag") or ""
    return str(etag).strip().strip('"')


def _session_login(base_url: str, db: str, login: str, password: str, cookie_jar: CookieJar) -> bool:
    status, body, _ = _post_json(
        f"{base_url}/api/login?db={db}",
        {"db": db, "login": login, "password": password},
        cookie_jar=cookie_jar,
    )
    login_res = _load_json(body)
    if status < 400 and isinstance(login_res, dict) and login_res.get("ok"):
        return True

    # Fallback: standard Odoo session auth
    status, body, _ = _post_json(
        f"{base_url}/web/session/authenticate",
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"db": db, "login": login, "password": password},
        },
        cookie_jar=cookie_jar,
    )
    auth_res = _load_json(body)
    if status >= 400:
        return False
    result = auth_res.get("result") if isinstance(auth_res, dict) else {}
    return bool(isinstance(result, dict) and result.get("uid"))


def _run_one(base_url: str, db: str, login: str, password: str) -> bool:
    cookie_jar = CookieJar()
    if not _session_login(base_url, db, login, password, cookie_jar):
        return False

    contract_url = f"{base_url}/api/contract/get"
    payload_user = {"subject": "model", "model": "project.project", "view_type": "tree", "contract_mode": "user"}
    payload_hud = {"subject": "model", "model": "project.project", "view_type": "tree", "contract_mode": "hud"}

    status_u1, body_u1, hdr_u1 = _post_json(contract_url, payload_user, cookie_jar=cookie_jar)
    if status_u1 >= 400:
        raise RuntimeError(f"user contract call failed: status={status_u1} body={body_u1}")
    res_u1 = _load_json(body_u1)
    meta_u1 = res_u1.get("meta") if isinstance(res_u1.get("meta"), dict) else {}
    if meta_u1.get("contract_mode") != "user":
        raise RuntimeError(f"user contract_mode mismatch: {meta_u1.get('contract_mode')}")
    etag_u = _extract_etag(hdr_u1) or str(meta_u1.get("etag") or "").strip()
    if not etag_u:
        raise RuntimeError("missing user ETag")

    status_h1, body_h1, hdr_h1 = _post_json(contract_url, payload_hud, cookie_jar=cookie_jar)
    if status_h1 >= 400:
        raise RuntimeError(f"hud contract call failed: status={status_h1} body={body_h1}")
    res_h1 = _load_json(body_h1)
    meta_h1 = res_h1.get("meta") if isinstance(res_h1.get("meta"), dict) else {}
    if meta_h1.get("contract_mode") != "hud":
        raise RuntimeError(f"hud contract_mode mismatch: {meta_h1.get('contract_mode')}")
    etag_h = _extract_etag(hdr_h1) or str(meta_h1.get("etag") or "").strip()
    if not etag_h:
        raise RuntimeError("missing hud ETag")
    if etag_h == etag_u:
        raise RuntimeError("user/hud ETag must be different")

    status_u304, body_u304, _ = _post_json(
        contract_url,
        payload_user,
        cookie_jar=cookie_jar,
        headers={"If-None-Match": etag_u},
    )
    if status_u304 != 304:
        raise RuntimeError(f"user 304 expected, got status={status_u304} body={body_u304}")

    status_h304, body_h304, _ = _post_json(
        contract_url,
        payload_hud,
        cookie_jar=cookie_jar,
        headers={"If-None-Match": etag_h},
    )
    if status_h304 != 304:
        raise RuntimeError(f"hud 304 expected, got status={status_h304} body={body_h304}")

    return True


def main() -> None:
    raw_base_url = os.environ.get("FRONTEND_API_BASE_URL", "http://localhost:8070").rstrip("/")
    lang = os.environ.get("FRONTEND_API_LANG", "").strip("/")
    db = os.environ.get("DB_NAME", "sc_demo")
    login = os.environ.get("FRONTEND_API_LOGIN", "admin")
    password = os.environ.get("FRONTEND_API_PASSWORD", "admin")
    base_urls = []
    if lang:
        base_urls.append(f"{raw_base_url}/{lang}")
    base_urls.append(raw_base_url)

    last_error = None
    for base_url in base_urls:
        try:
            if _run_one(base_url, db, login, password):
                print(f"[contract_api_mode_smoke] PASS ({base_url})")
                return
        except Exception as exc:  # pragma: no cover
            last_error = f"{base_url}: {exc}"
            continue

    raise SystemExit(last_error or "[contract_api_mode_smoke] no usable API base URL")


if __name__ == "__main__":
    main()
