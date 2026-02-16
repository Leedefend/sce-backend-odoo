#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
import urllib.request
from urllib.error import HTTPError

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _post_json(
    url: str,
    payload: dict,
    *,
    cookie_jar: CookieJar,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        try:
            data = json.loads(body or "{}")
        except Exception:
            data = {"raw": body}
        return exc.code, data


def _session_auth(base_url: str, db_name: str, login: str, password: str) -> CookieJar:
    jar = CookieJar()
    status, body = _post_json(
        f"{base_url}/web/session/authenticate",
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"db": db_name, "login": login, "password": password},
            "id": 1,
        },
        cookie_jar=jar,
    )
    result = body.get("result") if isinstance(body, dict) else {}
    if status >= 400 or not isinstance(result, dict) or not result.get("uid"):
        raise RuntimeError(f"admin session auth failed: status={status}")
    return jar


def _call_kw(
    base_url: str,
    cookie_jar: CookieJar,
    model: str,
    method: str,
    args: list[Any],
    kwargs: dict[str, Any] | None = None,
) -> Any:
    status, body = _post_json(
        f"{base_url}/web/dataset/call_kw/{model}/{method}",
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            },
            "id": 1,
        },
        cookie_jar=cookie_jar,
    )
    if status >= 400:
        raise RuntimeError(f"call_kw failed: {model}.{method} status={status}")
    if not isinstance(body, dict):
        raise RuntimeError(f"call_kw invalid response: {model}.{method}")
    if body.get("error"):
        raise RuntimeError(f"call_kw error: {model}.{method} -> {body.get('error')}")
    return body.get("result")


def _xmlid_to_group_id(base_url: str, cookie_jar: CookieJar, xmlid: str) -> int:
    module, _, name = xmlid.partition(".")
    rows = _call_kw(
        base_url,
        cookie_jar,
        "ir.model.data",
        "search_read",
        [[("model", "=", "res.groups"), ("module", "=", module), ("name", "=", name)]],
        {"fields": ["res_id"], "limit": 1},
    )
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"group xmlid not found: {xmlid}")
    group_id = int((rows[0] or {}).get("res_id") or 0)
    if group_id <= 0:
        raise RuntimeError(f"group xmlid has invalid res_id: {xmlid}")
    return group_id


def _ensure_user(
    base_url: str,
    cookie_jar: CookieJar,
    fixture: dict,
    fixture_password: str,
) -> tuple[int, list[str]]:
    login = str(fixture.get("login") or "").strip()
    name = str(fixture.get("name") or login).strip()
    role = str(fixture.get("role") or login).strip()
    groups_xmlids = [str(x).strip() for x in (fixture.get("groups_xmlids") or []) if str(x).strip()]
    if not login or not groups_xmlids:
        raise RuntimeError(f"invalid fixture config: role={role} login={login}")
    group_ids = [_xmlid_to_group_id(base_url, cookie_jar, xmlid) for xmlid in groups_xmlids]
    rows = _call_kw(
        base_url,
        cookie_jar,
        "res.users",
        "search_read",
        [[("login", "=", login)]],
        {"fields": ["id"], "limit": 1},
    )
    values = {
        "name": name,
        "login": login,
        "password": fixture_password,
        "active": True,
        "groups_id": [(6, 0, sorted(set(group_ids)))],
    }
    if isinstance(rows, list) and rows:
        user_id = int((rows[0] or {}).get("id") or 0)
        if user_id <= 0:
            raise RuntimeError(f"invalid user id for login={login}")
        _call_kw(base_url, cookie_jar, "res.users", "write", [[user_id], values], {})
        return user_id, groups_xmlids
    user_id = int(_call_kw(base_url, cookie_jar, "res.users", "create", [values], {}) or 0)
    if user_id <= 0:
        raise RuntimeError(f"failed to create fixture user: {login}")
    return user_id, groups_xmlids


def _intent_login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, f"login({login})")
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login}) missing token")
    return token


def _run_journey_intent(intent_url: str, token: str, intent: str) -> tuple[bool, str]:
    intent = str(intent or "").strip()
    if not intent:
        return False, "empty_intent"
    params = {}
    if intent == "ui.contract":
        params = {"op": "model", "model": "project.project", "view_type": "tree", "contract_mode": "user"}
    elif intent == "system.init":
        params = {"contract_mode": "user"}
    status, resp = http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = bool(status < 400 and isinstance(resp, dict) and resp.get("ok") is True)
    if ok:
        return True, "ok"
    reason = "intent_failed"
    if isinstance(resp, dict):
        meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
        reason = str(meta.get("reason_code") or resp.get("message") or reason)
    return False, reason


def _system_init_capability_count(intent_url: str, token: str) -> int:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "system.init user")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    caps = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    return len(caps)


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[role_capability_floor_prod_like] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    if len(fixtures) < 6:
        print("[role_capability_floor_prod_like] FAIL")
        print("baseline fixtures must include >= 6 roles")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    admin_login = str(os.getenv("E2E_ADMIN_LOGIN") or os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_ADMIN_PASSWORD") or os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    journey_defaults = [str(x).strip() for x in (baseline.get("journey_intents") or ["system.init", "ui.contract"]) if str(x).strip()]
    max_errors = int(baseline.get("max_errors") or 0)

    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "role_capability_floor_prod_like.json"
    artifact_md = artifacts_dir / "role_capability_floor_prod_like.md"

    errors: list[str] = []
    rows: list[dict] = []
    try:
        admin_session = _session_auth(base_url, db_name, admin_login, admin_password)
    except Exception as exc:
        print("[role_capability_floor_prod_like] FAIL")
        print(f"admin session setup failed: {exc}")
        return 1

    for fixture in fixtures:
        role = str(fixture.get("role") or fixture.get("login") or "").strip()
        login = str(fixture.get("login") or "").strip()
        if not role or not login:
            errors.append(f"invalid fixture row: role={role!r} login={login!r}")
            continue
        row = {
            "role": role,
            "login": login,
            "ok": False,
            "user_id": 0,
            "groups_xmlids": [],
            "capability_count": 0,
            "journey": [],
            "failure_reason": "",
        }
        try:
            user_id, groups_xmlids = _ensure_user(base_url, admin_session, fixture, fixture_password)
            token = _intent_login(intent_url, db_name, login, fixture_password)
            cap_count = _system_init_capability_count(intent_url, token)
            min_caps = int(fixture.get("min_capabilities") or 0)
            if cap_count < min_caps:
                raise RuntimeError(f"capability floor not met: {cap_count} < {min_caps}")
            journey = []
            intents = [str(x).strip() for x in (fixture.get("journey_intents") or journey_defaults) if str(x).strip()]
            for intent in intents:
                ok, reason = _run_journey_intent(intent_url, token, intent)
                journey.append({"intent": intent, "ok": ok, "reason": reason})
                if not ok:
                    raise RuntimeError(f"journey intent failed: {intent} ({reason})")
            row.update(
                {
                    "ok": True,
                    "user_id": user_id,
                    "groups_xmlids": groups_xmlids,
                    "capability_count": cap_count,
                    "journey": journey,
                }
            )
        except Exception as exc:
            row["failure_reason"] = str(exc)
            errors.append(f"{role}: {exc}")
        rows.append(row)

    report = {
        "ok": len(errors) <= max_errors,
        "summary": {
            "fixture_count": len(fixtures),
            "passed_fixture_count": sum(1 for row in rows if row.get("ok")),
            "failed_fixture_count": sum(1 for row in rows if not row.get("ok")),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "roles": rows,
        "errors": errors,
    }

    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Role Capability Floor Prod-Like",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- fixture_count: {report['summary']['fixture_count']}",
        f"- passed_fixture_count: {report['summary']['passed_fixture_count']}",
        f"- failed_fixture_count: {report['summary']['failed_fixture_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['role']} ({row['login']}): {'PASS' if row.get('ok') else 'FAIL'} "
            f"capabilities={row.get('capability_count')} reason={row.get('failure_reason') or 'ok'}"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors[:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[role_capability_floor_prod_like] FAIL")
        return 1
    print("[role_capability_floor_prod_like] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
