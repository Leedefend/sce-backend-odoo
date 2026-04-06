#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from capability_payload_v1_v2_diff_snapshot import build_diff
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url


class ProbeLoginError(RuntimeError):
    def __init__(self, message: str, attempts: List[Dict[str, Any]]):
        super().__init__(message)
        self.attempts = attempts


class LaneReadinessError(RuntimeError):
    def __init__(self, message: str, readiness: Dict[str, Any]):
        super().__init__(message)
        self.readiness = readiness


def _post_intent(
    intent_url: str,
    intent: str,
    params: Dict[str, Any],
    *,
    token: str | None,
    db_name: str,
    timeout_sec: int,
) -> Tuple[int, Dict[str, Any]]:
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Anonymous-Intent"] = "1"
    if db_name:
        headers["X-Odoo-DB"] = db_name
    body = json.dumps({"intent": intent, "params": params}, ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(intent_url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        req.add_header(key, value)

    retries = 2
    for attempt in range(1, retries + 1):
        try:
            with urlrequest.urlopen(req, timeout=max(1, int(timeout_sec))) as resp:
                text = resp.read().decode("utf-8")
                payload = json.loads(text or "{}")
                return int(resp.status), payload if isinstance(payload, dict) else {}
        except HTTPError as exc:
            text = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
            try:
                payload = json.loads(text or "{}")
            except Exception:
                payload = {"raw": text}
            return int(exc.code), payload if isinstance(payload, dict) else {}
        except (URLError, RemoteDisconnected, ConnectionResetError) as exc:
            if attempt >= retries:
                raise RuntimeError(f"HTTP request failed after retries: {exc}") from exc
            time.sleep(0.3 * attempt)

    raise RuntimeError("unreachable request state")


def _build_intent_candidates() -> List[str]:
    candidates: List[str] = []

    explicit = str(os.getenv("E2E_INTENT_URL") or "").strip()
    if explicit:
        candidates.append(explicit)

    base_url = str(os.getenv("E2E_BASE_URL") or get_base_url()).rstrip("/")
    if base_url:
        candidates.append(f"{base_url}/api/v1/intent")

    for host in ("localhost", "127.0.0.1"):
        for port in ("8069", "8070", "18080"):
            candidates.append(f"http://{host}:{port}/api/v1/intent")

    deduped: List[str] = []
    seen = set()
    for item in candidates:
        key = str(item).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def _login_with_probe(
    *,
    intent_candidates: List[str],
    db_name: str,
    login: str,
    password: str,
    timeout_sec: int,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    probe_attempts: List[Dict[str, Any]] = []

    for candidate in intent_candidates:
        candidate_url = candidate
        if db_name and "?db=" not in candidate_url:
            joiner = "&" if "?" in candidate_url else "?"
            candidate_url = f"{candidate_url}{joiner}db={db_name}"
        try:
            status, login_payload = _post_intent(
                candidate_url,
                "login",
                {"db": db_name, "login": login, "password": password},
                token=None,
                db_name=db_name,
                timeout_sec=timeout_sec,
            )
            token = _extract_token(login_payload)
            ok = status < 400 and bool(login_payload.get("ok")) and bool(token)
            probe_attempts.append(
                {
                    "intent_url": candidate_url,
                    "status": int(status),
                    "ok": bool(login_payload.get("ok")),
                    "token_present": bool(token),
                    "error": "",
                }
            )
            if ok:
                return candidate_url, token, probe_attempts
        except Exception as exc:
            probe_attempts.append(
                {
                    "intent_url": candidate_url,
                    "status": 0,
                    "ok": False,
                    "token_present": False,
                    "error": str(exc),
                }
            )

    raise ProbeLoginError("no intent endpoint accepted login", probe_attempts)


def _extract_token(login_resp: Dict[str, Any]) -> str:
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    if isinstance(data.get("session"), dict):
        token = str((data.get("session") or {}).get("token") or "").strip()
        if token:
            return token
    token = str(data.get("token") or "").strip()
    return token


def _normalize_capability_rows(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not isinstance(raw, dict):
        return []
    for key in ("items", "records", "capabilities", "list"):
        value = raw.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _extract_capabilities(system_init_resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = system_init_resp.get("data") if isinstance(system_init_resp.get("data"), dict) else {}
    rows = _normalize_capability_rows(data.get("capabilities"))
    if rows:
        return rows
    catalog = data.get("catalog") if isinstance(data.get("catalog"), dict) else {}
    rows = _normalize_capability_rows(catalog.get("capabilities"))
    if rows:
        return rows
    delivery_engine = data.get("delivery_engine_v1") if isinstance(data.get("delivery_engine_v1"), dict) else {}
    rows = _normalize_capability_rows(delivery_engine.get("capabilities"))
    if rows:
        return rows
    release_nav = data.get("release_navigation_v1") if isinstance(data.get("release_navigation_v1"), dict) else {}
    release_caps = release_nav.get("capabilities")
    rows = _normalize_capability_rows(release_caps)
    return rows


def _ensure_row_key(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        key = str(row.get("key") or "").strip()
        if not key:
            key = str(row.get("intent") or row.get("id") or "").strip()
        if not key:
            continue
        cloned = dict(row)
        cloned["key"] = key
        out.append(cloned)
    return out


def _upsert_toggle(
    intent_url: str,
    token: str,
    db_name: str,
    *,
    value: str,
    timeout_sec: int,
) -> str:
    key = "smart_core.capability_registry_query_v2_enabled"
    status, payload = _post_intent(
        intent_url,
        "api.data",
        {
            "op": "list",
            "model": "ir.config_parameter",
            "fields": ["id", "key", "value"],
            "domain": [["key", "=", key]],
            "limit": 1,
        },
        token=token,
        db_name=db_name,
        timeout_sec=timeout_sec,
    )
    require_ok(status, payload, "api.data(list ir.config_parameter)")
    records = ((payload.get("data") or {}) if isinstance(payload.get("data"), dict) else {}).get("records")
    rows = records if isinstance(records, list) else []
    if rows:
        row0 = rows[0] if isinstance(rows[0], dict) else {}
        current = str(row0.get("value") or "").strip()
        row_id = int(row0.get("id") or 0)
        status, write_payload = _post_intent(
            intent_url,
            "api.data",
            {
                "op": "write",
                "model": "ir.config_parameter",
                "ids": [row_id],
                "vals": {"value": str(value)},
            },
            token=token,
            db_name=db_name,
            timeout_sec=timeout_sec,
        )
        require_ok(status, write_payload, "api.data(write ir.config_parameter)")
        return current

    status, create_payload = _post_intent(
        intent_url,
        "api.data",
        {
            "op": "create",
            "model": "ir.config_parameter",
            "vals": {"key": key, "value": str(value)},
        },
        token=token,
        db_name=db_name,
        timeout_sec=timeout_sec,
    )
    require_ok(status, create_payload, "api.data(create ir.config_parameter)")
    return ""


def _capture_once(
    intent_url: str,
    token: str,
    db_name: str,
    timeout_sec: int,
) -> Dict[str, Any]:
    started = time.perf_counter()
    status, payload = _post_intent(
        intent_url,
        "system.init",
        {"with_preload": False, "contract_mode": "default"},
        token=token,
        db_name=db_name,
        timeout_sec=timeout_sec,
    )
    require_ok(status, payload, "system.init")
    rows = _ensure_row_key(_extract_capabilities(payload))
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "rows": rows,
        "count": len(rows),
        "elapsed_ms": elapsed_ms,
        "response": payload,
    }


def _list_records(
    intent_url: str,
    token: str,
    db_name: str,
    *,
    model: str,
    fields: List[str],
    domain: List[Any],
    limit: int,
    timeout_sec: int,
) -> List[Dict[str, Any]]:
    status, payload = _post_intent(
        intent_url,
        "api.data",
        {
            "op": "list",
            "model": model,
            "fields": fields,
            "domain": domain,
            "limit": int(limit),
        },
        token=token,
        db_name=db_name,
        timeout_sec=timeout_sec,
    )
    require_ok(status, payload, f"api.data(list {model})")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    records = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in records if isinstance(row, dict)]


def _check_lane_readiness(
    intent_url: str,
    token: str,
    db_name: str,
    *,
    timeout_sec: int,
) -> Dict[str, Any]:
    module_rows = _list_records(
        intent_url,
        token,
        db_name,
        model="ir.module.module",
        fields=["name", "state", "latest_version"],
        domain=[["name", "in", ["smart_core", "smart_construction_scene", "smart_construction_core"]]],
        limit=20,
        timeout_sec=timeout_sec,
    )
    module_by_name = {str(row.get("name") or "").strip(): row for row in module_rows}
    scene_state = str((module_by_name.get("smart_construction_scene") or {}).get("state") or "").strip()
    scene_installed = scene_state == "installed"

    capability_rows = _list_records(
        intent_url,
        token,
        db_name,
        model="sc.capability",
        fields=["id", "key"],
        domain=[],
        limit=500,
        timeout_sec=timeout_sec,
    )
    readiness = {
        "scene_module_state": scene_state,
        "scene_module_installed": scene_installed,
        "sc_capability_count": len(capability_rows),
        "sc_capability_non_empty": len(capability_rows) > 0,
        "module_rows": module_rows,
    }
    readiness["ready"] = bool(readiness["scene_module_installed"] and readiness["sc_capability_non_empty"])
    return readiness


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_capture(out_dir: Path, timeout_sec: int, *, require_lane_ready: bool) -> Dict[str, Any]:
    base_url = str(os.getenv("E2E_BASE_URL") or get_base_url()).rstrip("/")
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    intent_candidates = _build_intent_candidates()
    intent_url, token, probe_attempts = _login_with_probe(
        intent_candidates=intent_candidates,
        db_name=db_name,
        login=login,
        password=password,
        timeout_sec=timeout_sec,
    )
    lane_readiness = _check_lane_readiness(intent_url, token, db_name, timeout_sec=timeout_sec)
    if require_lane_ready and not bool(lane_readiness.get("ready")):
        raise LaneReadinessError("lane readiness check failed", lane_readiness)

    original_toggle = ""
    restore_error = ""
    capture_v1: Dict[str, Any] = {}
    capture_v2: Dict[str, Any] = {}
    try:
        original_toggle = _upsert_toggle(intent_url, token, db_name, value="0", timeout_sec=timeout_sec)
        capture_v1 = _capture_once(intent_url, token, db_name, timeout_sec)
        _upsert_toggle(intent_url, token, db_name, value="1", timeout_sec=timeout_sec)
        capture_v2 = _capture_once(intent_url, token, db_name, timeout_sec)
    finally:
        try:
            _upsert_toggle(intent_url, token, db_name, value=original_toggle or "0", timeout_sec=timeout_sec)
        except Exception as restore_exc:  # pragma: no cover
            restore_error = str(restore_exc)

    v1_path = out_dir / "capability_payload_v1.json"
    v2_path = out_dir / "capability_payload_v2.json"
    diff_path = out_dir / "capability_payload_v1_v2_diff_snapshot.json"
    raw_v1_path = out_dir / "system_init_raw_v1.json"
    raw_v2_path = out_dir / "system_init_raw_v2.json"

    _write_json(v1_path, capture_v1.get("rows") or [])
    _write_json(v2_path, capture_v2.get("rows") or [])
    _write_json(raw_v1_path, capture_v1.get("response") or {})
    _write_json(raw_v2_path, capture_v2.get("response") or {})

    diff_report = build_diff(capture_v1.get("rows") or [], capture_v2.get("rows") or [])
    _write_json(diff_path, diff_report)

    return {
        "env_status": "trusted",
        "base_url": base_url,
        "selected_intent_url": intent_url,
        "probe_attempts": probe_attempts,
        "lane_readiness": lane_readiness,
        "db_name": db_name,
        "login": login,
        "toggle_key": "smart_core.capability_registry_query_v2_enabled",
        "toggle_original_value": original_toggle,
        "toggle_restore_error": restore_error,
        "v1_count": int(capture_v1.get("count") or 0),
        "v2_count": int(capture_v2.get("count") or 0),
        "v1_elapsed_ms": int(capture_v1.get("elapsed_ms") or 0),
        "v2_elapsed_ms": int(capture_v2.get("elapsed_ms") or 0),
        "v1_payload": str(v1_path),
        "v2_payload": str(v2_path),
        "diff_report": str(diff_path),
        "raw_v1": str(raw_v1_path),
        "raw_v2": str(raw_v2_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture capability payload off/on snapshots in real environment.")
    parser.add_argument("--out-dir", default="artifacts/capability_payload_capture", help="output base directory")
    parser.add_argument("--request-timeout-sec", type=int, default=8, help="request timeout seconds")
    parser.add_argument(
        "--allow-env-unstable",
        action="store_true",
        help="emit ENV_UNSTABLE report instead of failing when runtime is unavailable",
    )
    parser.add_argument(
        "--require-lane-ready",
        action="store_true",
        help="require smart_construction_scene installed and non-empty sc.capability before capture",
    )
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = Path(args.out_dir) / ts
    latest_dir = Path(args.out_dir) / "latest"

    result: Dict[str, Any]
    probe_attempts: List[Dict[str, Any]] = []
    lane_readiness: Dict[str, Any] = {}
    try:
        result = _run_capture(
            out_dir,
            timeout_sec=max(1, int(args.request_timeout_sec)),
            require_lane_ready=bool(args.require_lane_ready),
        )
    except Exception as exc:
        if not args.allow_env_unstable:
            raise
        if isinstance(exc, ProbeLoginError):
            probe_attempts = exc.attempts
        if isinstance(exc, LaneReadinessError):
            lane_readiness = exc.readiness
        result = {
            "env_status": "ENV_UNSTABLE",
            "error": str(exc),
            "selected_intent_url": "",
            "probe_attempts": probe_attempts,
            "lane_readiness": lane_readiness,
            "v1_payload": "",
            "v2_payload": "",
            "diff_report": "",
        }
        _write_json(out_dir / "capture_error.json", {"error": str(exc)})

    result["timestamp"] = ts
    result["out_dir"] = str(out_dir)

    _write_json(out_dir / "capture_report.json", result)
    latest_dir.mkdir(parents=True, exist_ok=True)
    _write_json(latest_dir / "capture_report.json", result)

    print(str(out_dir / "capture_report.json"))
    print(str(latest_dir / "capture_report.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
