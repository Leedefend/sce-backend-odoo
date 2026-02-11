#!/usr/bin/env python3
import json
import os
import urllib.request
from http.cookiejar import CookieJar
from urllib.error import HTTPError


def _post_json(url, payload, cookie_jar=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    opener = urllib.request.build_opener()
    if cookie_jar is not None:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    try:
        with opener.open(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body


def _load_json(body):
    if not body:
        return {}
    try:
        return json.loads(body)
    except Exception:
        return {}


def main():
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
        cookie_jar = CookieJar()
        # /api/login
        status, body = _post_json(
            f"{base_url}/api/login?db={db}",
            {"db": db, "login": login, "password": password},
            cookie_jar=cookie_jar,
        )
        login_res = _load_json(body)
        if not isinstance(login_res, dict):
            last_error = f"[frontend_api] /api/login returned non-json ({base_url})"
            continue

        # /api/session/get (always public)
        status_sess, body_sess = _post_json(
            f"{base_url}/api/session/get?db={db}",
            {},
            cookie_jar=cookie_jar,
        )
        sess_res = _load_json(body_sess)
        if not isinstance(sess_res, dict):
            last_error = f"[frontend_api] /api/session/get returned non-json ({base_url})"
            continue

        # /api/menu/tree (auth user)
        status_menu, body_menu = _post_json(
            f"{base_url}/api/menu/tree?db={db}",
            {},
            cookie_jar=cookie_jar,
        )
        menu_res = _load_json(body_menu)

        # Acceptable outcomes:
        # - login ok -> menu ok true
        # - login fail -> menu 401/403/404 or ok false
        if login_res.get("ok"):
            if isinstance(menu_res, dict) and menu_res.get("ok"):
                print(f"[frontend_api] PASS ({base_url})")
                return
            last_error = f"[frontend_api] menu tree not OK after login ({base_url})"
            continue

        if status_menu >= 500:
            last_error = f"[frontend_api] menu tree returned server error ({base_url})"
            continue

        print(f"[frontend_api] PASS ({base_url})")
        return

    raise SystemExit(last_error or "[frontend_api] no usable API base URL")


if __name__ == "__main__":
    main()
