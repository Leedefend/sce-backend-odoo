#!/usr/bin/env python3
import json
import os
import urllib.request
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
    base_url = os.environ.get("FRONTEND_API_BASE_URL", "http://localhost:8070").rstrip("/")
    lang = os.environ.get("FRONTEND_API_LANG", "en").strip("/")
    if lang:
        base_url = f"{base_url}/{lang}"
    db = os.environ.get("DB_NAME", "sc_demo")
    login = os.environ.get("FRONTEND_API_LOGIN", "admin")
    password = os.environ.get("FRONTEND_API_PASSWORD", "admin")

    # /api/login
    status, body = _post_json(
        f"{base_url}/api/login?db={db}",
        {"db": db, "login": login, "password": password},
    )
    login_res = _load_json(body)
    if not isinstance(login_res, dict):
        raise SystemExit("[frontend_api] /api/login returned non-json")

    # /api/session/get (always public)
    status_sess, body_sess = _post_json(f"{base_url}/api/session/get?db={db}", {})
    sess_res = _load_json(body_sess)
    if not isinstance(sess_res, dict):
        raise SystemExit("[frontend_api] /api/session/get returned non-json")

    # /api/menu/tree (auth user)
    status_menu, body_menu = _post_json(f"{base_url}/api/menu/tree?db={db}", {})
    menu_res = _load_json(body_menu)

    # Acceptable outcomes:
    # - login ok -> menu ok true
    # - login fail -> menu 401/403/404 or ok false
    if login_res.get("ok"):
        if not (isinstance(menu_res, dict) and menu_res.get("ok")):
            raise SystemExit("[frontend_api] menu tree not OK after login")
    else:
        if status_menu >= 500:
            raise SystemExit("[frontend_api] menu tree returned server error")

    print("[frontend_api] PASS")


if __name__ == "__main__":
    main()
