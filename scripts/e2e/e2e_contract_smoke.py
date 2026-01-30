#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from urllib.error import HTTPError


def _post_json(url, payload, headers=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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


IGNORE_KEYS = {
    "trace_id",
    "elapsed_ms",
    "etag",
    "token",
    "expires_at",
}


def _normalize(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in IGNORE_KEYS:
                continue
            if k == "meta":
                continue
            out[k] = _normalize(v)
        return out
    if isinstance(obj, list):
        return [_normalize(x) for x in obj]
    return obj


def run_once(base_url, db, login, password, action_xmlid):
    intent_url = f"{base_url}/api/v1/intent?db={db}"
    # login
    login_payload = {
        "intent": "login",
        "params": {"login": login, "password": password, "db": db},
    }
    status, body = _post_json(
        intent_url,
        login_payload,
        headers={"X-Anonymous-Intent": "true"},
    )
    login_res = _load_json(body)
    if status >= 400 or not login_res.get("data", {}).get("token"):
        raise SystemExit(f"[e2e] login failed: status={status} body={body}")

    token = login_res["data"]["token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # system.init
    sys_payload = {"intent": "system.init", "params": {}}
    _, body = _post_json(intent_url, sys_payload, headers=auth_header)
    sys_res = _load_json(body)

    # resolve action id via ir.model.data
    data_payload = {
        "intent": "api.data",
        "params": {
            "op": "list",
            "model": "ir.model.data",
            "domain": [
                ["module", "=", action_xmlid.split(".")[0]],
                ["name", "=", action_xmlid.split(".")[1]],
            ],
            "fields": ["res_id"],
            "limit": 1,
        },
    }
    _, body = _post_json(intent_url, data_payload, headers=auth_header)
    data_res = _load_json(body)
    rows = (data_res.get("data") or {}).get("records") or (data_res.get("data") or {}).get("rows") or []
    action_id = rows[0].get("res_id") if rows else None
    if not action_id:
        raise SystemExit("[e2e] failed to resolve action_id from ir.model.data")

    # ui.contract
    contract_payload = {"intent": "ui.contract", "params": {"op": "action_open", "action_id": action_id}}
    _, body = _post_json(intent_url, contract_payload, headers=auth_header)
    contract_res = _load_json(body)

    # api.data list
    list_payload = {
        "intent": "api.data",
        "params": {
            "op": "list",
            "model": "project.project",
            "fields": ["id", "name"],
            "limit": 1,
        },
    }
    _, body = _post_json(intent_url, list_payload, headers=auth_header)
    list_res = _load_json(body)

    return {
        "login": _normalize(login_res),
        "system_init": _normalize(sys_res),
        "ui_contract": _normalize(contract_res),
        "api_data": _normalize(list_res),
    }


def main():
    base_url = os.environ.get("E2E_BASE_URL", "http://localhost:8070").rstrip("/")
    lang = os.environ.get("E2E_LANG", "en").strip("/")
    if lang:
        base_url = f"{base_url}/{lang}"
    db = os.environ.get("DB_NAME", "sc_demo")
    login = os.environ.get("E2E_LOGIN", "admin")
    password = os.environ.get("E2E_PASSWORD", "admin")
    action_xmlid = os.environ.get(
        "E2E_ACTION_XMLID",
        "smart_construction_core.action_sc_project_kanban_lifecycle",
    )
    outdir = os.environ.get("E2E_OUTDIR", "artifacts/e2e")
    os.makedirs(outdir, exist_ok=True)

    run1 = run_once(base_url, db, login, password, action_xmlid)
    time.sleep(1)
    run2 = run_once(base_url, db, login, password, action_xmlid)

    with open(os.path.join(outdir, "contract_smoke_run1.json"), "w", encoding="utf-8") as f:
        json.dump(run1, f, ensure_ascii=False, indent=2)
    with open(os.path.join(outdir, "contract_smoke_run2.json"), "w", encoding="utf-8") as f:
        json.dump(run2, f, ensure_ascii=False, indent=2)

    if run1 != run2:
        raise SystemExit("[e2e] snapshot drift detected")

    print("[e2e] PASS")


if __name__ == "__main__":
    main()
