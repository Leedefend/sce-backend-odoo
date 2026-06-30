#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "project_task_action_smoke.json"
SEED_REPORT_PATH = ROOT / "artifacts" / "backend" / "project_task_action_seed.json"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8070").rstrip("/")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo"
LOGIN = os.getenv("ROLE_PM_LOGIN", "demo_role_pm")
PASSWORD = os.getenv("ROLE_PM_PASSWORD", "demo")
REQUEST_RETRY_MAX = max(5, int(os.getenv("PROJECT_TASK_ACTION_SMOKE_REQUEST_RETRY_MAX", "30")))
REQUEST_RETRY_SLEEP_SEC = max(1, int(os.getenv("PROJECT_TASK_ACTION_SMOKE_REQUEST_RETRY_SLEEP_SEC", "2")))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_intent(intent: str, params: dict, *, token: str | None = None, anonymous: bool = False) -> dict:
    payload = json.dumps({"intent": intent, "params": params}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Odoo-DB"] = DB_NAME
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    req = urllib.request.Request(f"{BASE_URL}/api/v1/intent", data=payload, headers=headers, method="POST")
    body = None
    last_err = None
    for _ in range(REQUEST_RETRY_MAX):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
            last_err = None
            break
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code in (502, 503, 504):
                last_err = exc
                time.sleep(REQUEST_RETRY_SLEEP_SEC)
                continue
            try:
                parsed = json.loads(raw or "{}")
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            return {"ok": False, "error": {"code": f"HTTP_{exc.code}", "message": raw[:300]}}
        except urllib.error.URLError as exc:
            last_err = exc
            time.sleep(REQUEST_RETRY_SLEEP_SEC)
    if body is None:
        return {"ok": False, "error": {"code": "REQUEST_FAILED", "message": str(last_err or "")}}
    try:
        parsed = json.loads(body or "{}")
    except Exception as exc:
        return {"ok": False, "error": {"code": "INVALID_JSON", "message": str(exc)}}
    return parsed if isinstance(parsed, dict) else {"ok": False, "error": {"code": "INVALID_RESPONSE"}}


def _reason(resp: dict) -> str:
    if bool(resp.get("ok")):
        data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
        return str(data.get("reason_code") or "OK")
    error = resp.get("error") if isinstance(resp.get("error"), dict) else {}
    return str(error.get("reason_code") or error.get("code") or "")


def _records(resp: dict) -> list[dict]:
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _as_id(value) -> int:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return int(value or 0)
    except Exception:
        return 0


def _login() -> str:
    resp = _request_intent("login", {"db": DB_NAME, "login": LOGIN, "password": PASSWORD}, anonymous=True)
    if not resp.get("ok"):
        raise AssertionError(f"login failed: {resp.get('error')}")
    token = str(((resp.get("data") or {}).get("token") or "")).strip()
    if not token:
        raise AssertionError("login token missing")
    return token


def _list_projects(token: str) -> list[dict]:
    resp = _request_intent(
        "api.data",
        {
            "op": "list",
            "model": "project.project",
            "fields": ["id", "name", "write_date"],
            "limit": 20,
            "order": "write_date desc,id desc",
        },
        token=token,
    )
    if not resp.get("ok"):
        raise AssertionError(f"project list failed: {resp.get('error')}")
    return _records(resp)


def _create_task(token: str, project_id: int) -> tuple[int, dict]:
    resp = _request_intent(
        "api.data",
        {
            "op": "create",
            "model": "project.task",
            "vals": {
                "name": f"Delivery action smoke {_utc_now()}",
                "project_id": int(project_id),
            },
            "current_project_id": int(project_id),
            "context": {"current_project_id": int(project_id), "default_project_id": int(project_id)},
        },
        token=token,
    )
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return _as_id(data.get("id") or data.get("record_id") or data.get("res_id")), resp


def _pick_existing_task(token: str, project_id: int) -> tuple[int, dict]:
    resp = _request_intent(
        "api.data",
        {
            "op": "list",
            "model": "project.task",
            "fields": ["id", "name", "project_id", "sc_state"],
            "domain": [["project_id", "=", int(project_id)]],
            "limit": 10,
            "order": "write_date desc,id desc",
            "current_project_id": int(project_id),
        },
        token=token,
    )
    rows = _records(resp) if resp.get("ok") else []
    return (_as_id(rows[0].get("id")) if rows else 0), resp


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_seed() -> dict:
    if not SEED_REPORT_PATH.exists():
        return {}
    try:
        payload = json.loads(SEED_REPORT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    steps: list[dict] = []
    token = _login()
    steps.append({"step": "login.pm", "ok": True})

    seed = _load_seed()
    seed_ok = bool(seed.get("ok")) and _as_id(seed.get("project_id")) > 0 and _as_id(seed.get("task_id")) > 0
    task_auto_created = False
    if seed_ok:
        project_id = _as_id(seed.get("project_id"))
        task_id = _as_id(seed.get("task_id"))
        steps.append({"step": "load_seed", "ok": True, "project_id": project_id, "task_id": task_id})
    else:
        projects = _list_projects(token)
        if not projects:
            raise AssertionError("no project.project rows visible to PM role")
        project_id = _as_id(projects[0].get("id"))
        steps.append({"step": "select_project", "ok": project_id > 0, "project_id": project_id})

        task_id, create_resp = _create_task(token, project_id)
        task_auto_created = task_id > 0 and bool(create_resp.get("ok"))
        steps.append(
            {
                "step": "api.data.create.project.task",
                "ok": task_auto_created,
                "reason_code": _reason(create_resp),
                "task_id": task_id,
            }
        )
    if task_id <= 0:
        task_id, task_list_resp = _pick_existing_task(token, project_id)
        steps.append(
            {
                "step": "api.data.list.project.task",
                "ok": task_id > 0,
                "reason_code": _reason(task_list_resp),
                "task_id": task_id,
            }
        )
    if task_id <= 0:
        raise AssertionError("no project.task available for project execution smoke")

    enter_resp = _request_intent(
        "project.execution.enter",
        {"project_id": project_id, "current_project_id": project_id},
        token=token,
    )
    steps.append({"step": "project.execution.enter", "ok": bool(enter_resp.get("ok")), "reason_code": _reason(enter_resp)})
    if not enter_resp.get("ok"):
        raise AssertionError(f"project.execution.enter failed: {enter_resp.get('error')}")

    block_results = {}
    for block_key in ("execution_tasks", "next_actions"):
        block_resp = _request_intent(
            "project.execution.block.fetch",
            {"project_id": project_id, "current_project_id": project_id, "block_key": block_key},
            token=token,
        )
        data = block_resp.get("data") if isinstance(block_resp.get("data"), dict) else {}
        block_results[block_key] = {
            "ok": bool(block_resp.get("ok")),
            "reason_code": _reason(block_resp),
            "state": str(data.get("state") or ""),
            "block_type": str(data.get("block_type") or ""),
            "summary": data.get("data", {}).get("summary") if isinstance(data.get("data"), dict) else {},
        }
        steps.append({"step": f"project.execution.block.fetch.{block_key}", **block_results[block_key]})
        if not block_resp.get("ok"):
            raise AssertionError(f"project.execution.block.fetch[{block_key}] failed: {block_resp.get('error')}")

    advance_resp = _request_intent(
        "project.execution.advance",
        {
            "project_id": project_id,
            "current_project_id": project_id,
            "task_id": task_id,
            "request_id": f"project_task_action_smoke_{project_id}_{task_id}_{int(time.time())}",
        },
        token=token,
    )
    advance_data = advance_resp.get("data") if isinstance(advance_resp.get("data"), dict) else {}
    advance_ok = bool(advance_resp.get("ok")) and str(advance_data.get("result") or "") == "success"
    steps.append(
        {
            "step": "project.execution.advance",
            "ok": advance_ok,
            "reason_code": _reason(advance_resp),
            "result": str(advance_data.get("result") or ""),
            "from_state": str(advance_data.get("from_state") or ""),
            "to_state": str(advance_data.get("to_state") or ""),
        }
    )

    refresh_resp = _request_intent(
        "project.execution.block.fetch",
        {"project_id": project_id, "current_project_id": project_id, "block_key": "execution_tasks"},
        token=token,
    )
    steps.append(
        {
            "step": "project.execution.block.fetch.execution_tasks.after_advance",
            "ok": bool(refresh_resp.get("ok")),
            "reason_code": _reason(refresh_resp),
        }
    )

    payload = {
        "generated_at_utc": _utc_now(),
        "ok": advance_ok and bool(refresh_resp.get("ok")),
        "db": DB_NAME,
        "base_url": BASE_URL,
        "login": LOGIN,
        "project_id": project_id,
        "task_id": task_id,
        "task_auto_created": task_auto_created,
        "blocks": block_results,
        "steps": steps,
    }
    _write_report(payload)
    print(REPORT_PATH)
    if not payload["ok"]:
        print("[project_task_action_smoke] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print("[project_task_action_smoke] PASS")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        payload = {"generated_at_utc": _utc_now(), "ok": False, "error": str(exc)}
        _write_report(payload)
        print(REPORT_PATH)
        print(f"[project_task_action_smoke] FAIL: {exc}")
        raise SystemExit(1)
