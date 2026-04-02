#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import time
from pathlib import Path
from datetime import datetime
from http.client import RemoteDisconnected
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2]
GROUPED_SNAPSHOT_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "e2e_grouped_rows_signature.json"


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
    attempt = 0
    while True:
        attempt += 1
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
        except (RemoteDisconnected, ConnectionResetError, URLError) as e:
            if attempt >= 3:
                raise RuntimeError(f"HTTP request failed after retries: {e}") from e
            time.sleep(0.5 * attempt)


def _assert_error(resp: dict, code: str):
    if resp.get("ok") is not False:
        raise RuntimeError(f"expected error envelope, got ok={resp.get('ok')} resp={resp}")
    err = resp.get("error") or {}
    if err.get("code") != code:
        raise RuntimeError(
            f"error code mismatch: expected {code}, got {err.get('code')} resp={resp}"
        )
    meta = resp.get("meta") or {}
    if not meta.get("trace_id"):
        raise RuntimeError("missing meta.trace_id in error response")


def _assert_scene_trace(resp: dict, *, label: str):
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    scene_trace = meta.get("scene_trace") if isinstance(meta.get("scene_trace"), dict) else {}
    if not scene_trace:
        raise RuntimeError(f"{label} missing meta.scene_trace")
    for key in ("scene_source", "scene_contract_ref", "scene_channel", "channel_selector", "channel_source_ref"):
        if not str(scene_trace.get(key) or "").strip():
            raise RuntimeError(f"{label} missing meta.scene_trace.{key}")


def _extract_login_token(login_resp: dict) -> str:
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


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


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_path(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=2)


def _unwrap_intent_data(resp: dict) -> tuple[dict, dict]:
    payload = resp.get("data")
    meta = resp.get("meta")
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        data_nested = payload.get("data")
        meta_nested = payload.get("meta")
        return (
            data_nested if isinstance(data_nested, dict) else {},
            meta_nested if isinstance(meta_nested, dict) else (meta if isinstance(meta, dict) else {}),
        )
    return (
        payload if isinstance(payload, dict) else {},
        meta if isinstance(meta, dict) else {},
    )


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _build_grouped_semantic_signature(
    data: dict,
    *,
    request_model: str,
    request_group_by: str,
    request_page_limit: int,
    request_offset: int,
) -> dict:
    grouped_rows = data.get("grouped_rows") if isinstance(data.get("grouped_rows"), list) else []
    group_paging = data.get("group_paging") if isinstance(data.get("group_paging"), dict) else {}
    window_identity = (
        group_paging.get("window_identity")
        if isinstance(group_paging.get("window_identity"), dict)
        else {}
    )
    first_group = grouped_rows[0] if grouped_rows and isinstance(grouped_rows[0], dict) else {}
    has_first_group = bool(first_group)

    page_limit = max(1, _to_int(first_group.get("page_limit"), request_page_limit))
    requested_offset = max(0, _to_int(request_offset, 0))
    normalized_request_offset = (requested_offset // page_limit) * page_limit
    page_offset = max(0, _to_int(first_group.get("page_offset"), normalized_request_offset))
    page_offset = (page_offset // page_limit) * page_limit

    count = max(0, _to_int(first_group.get("count"), 0))
    range_start = page_offset + 1 if count > 0 else 0
    range_end = min(count, page_offset + page_limit) if count > 0 else 0
    page_window = first_group.get("page_window") if isinstance(first_group.get("page_window"), dict) else {}
    page_window_start = max(0, _to_int(page_window.get("start"), _to_int(first_group.get("page_range_start"), range_start)))
    page_window_end = max(0, _to_int(page_window.get("end"), _to_int(first_group.get("page_range_end"), range_end)))
    page_window_matches_range = (not has_first_group) or (page_window_start == range_start and page_window_end == range_end)

    supports_group_key = has_first_group and isinstance(first_group.get("group_key"), str) and bool(str(first_group.get("group_key")).strip())
    supports_page_flags = (
        has_first_group
        and isinstance(first_group.get("page_has_prev"), bool)
        and isinstance(first_group.get("page_has_next"), bool)
    )
    supports_page_window = (
        has_first_group
        and isinstance(first_group.get("page_window"), dict)
        and isinstance(page_window.get("start"), (int, float))
        and isinstance(page_window.get("end"), (int, float))
    )
    supports_window_identity = isinstance(group_paging.get("window_identity"), dict)
    window_key = str(group_paging.get("window_key") or "").strip()
    identity_key = str(window_identity.get("key") or "").strip()
    supports_window_key = bool(window_key or identity_key)
    identity_model = str(window_identity.get("model") or "").strip()
    identity_group_by_field = str(window_identity.get("group_by_field") or "").strip()
    supports_window_identity_model = bool(identity_model) and identity_model == str(request_model or "").strip()
    supports_window_identity_group_by = bool(identity_group_by_field) and identity_group_by_field == str(request_group_by or "").strip()
    identity_version = str(window_identity.get("version") or "").strip()
    identity_algo = str(window_identity.get("algo") or "").strip().lower()
    supports_window_identity_algo = bool(identity_algo) and identity_algo == "sha1"
    identity_window_id = str(window_identity.get("window_id") or group_paging.get("window_id") or "").strip()
    identity_window_digest = str(window_identity.get("window_digest") or group_paging.get("window_digest") or "").strip()
    tuple_key_expected = (
        f"{identity_version or 'v1'}:{identity_algo or 'sha1'}:{identity_window_id or '-'}:{identity_window_digest or '-'}"
    )
    supports_window_identity_key_tuple = bool(identity_key or window_key) and (identity_key or window_key) == tuple_key_expected
    identity_prev_offset = window_identity.get("prev_group_offset")
    identity_next_offset = window_identity.get("next_group_offset")
    identity_has_more = window_identity.get("has_more")
    flat_prev_offset = group_paging.get("prev_group_offset")
    flat_next_offset = group_paging.get("next_group_offset")
    flat_has_more = group_paging.get("has_more")
    supports_window_nav_match = (
        (
            identity_prev_offset is None
            or _to_int(identity_prev_offset, 0) == _to_int(flat_prev_offset, 0)
        )
        and (
            identity_next_offset is None
            or _to_int(identity_next_offset, 0) == _to_int(flat_next_offset, 0)
        )
        and (
            identity_has_more is None
            or bool(identity_has_more) == bool(flat_has_more)
        )
    )

    group_count = max(0, _to_int(group_paging.get("group_count"), 0))
    window_start = max(0, _to_int(group_paging.get("window_start"), 0))
    window_end = max(0, _to_int(group_paging.get("window_end"), 0))
    identity_window_span = window_identity.get("window_span")
    has_identity_window_span = isinstance(identity_window_span, (int, float))
    expected_window_span = max(0, window_end - window_start + 1) if group_count > 0 else 0
    window_span_matches_range = (
        (not has_identity_window_span)
        or (max(0, _to_int(identity_window_span, 0)) == expected_window_span)
    )
    supports_window_span = has_identity_window_span and bool(window_span_matches_range)

    request_offset_matches_observed = (not has_first_group) or (normalized_request_offset == page_offset)
    signature = {
        "supports_group_key": bool(supports_group_key),
        "supports_page_flags": bool(supports_page_flags),
        "supports_page_window": bool(supports_page_window),
        "supports_window_identity": bool(supports_window_identity),
        "supports_window_key": bool(supports_window_key),
        "supports_window_identity_model": bool(supports_window_identity_model),
        "supports_window_identity_group_by": bool(supports_window_identity_group_by),
        "supports_window_identity_algo": bool(supports_window_identity_algo),
        "supports_window_identity_key_tuple": bool(supports_window_identity_key_tuple),
        "supports_window_nav_match": bool(supports_window_nav_match),
        "supports_window_span": bool(supports_window_span),
        "window_span_matches_range": bool(window_span_matches_range),
        "request_offset_matches_observed": bool(request_offset_matches_observed),
        "page_window_matches_range": bool(page_window_matches_range),
    }
    signature["consistency_score"] = sum(1 for key in signature if signature.get(key) is True)
    return signature


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
    token = _extract_login_token(login_resp)
    if not token:
        raise RuntimeError("login response missing token")

    auth_header = {"Authorization": f"Bearer {token}"}

    # 1.1) negative: call system.init without token
    status, init_noauth = _http_post_json(
        intent_url, {"intent": "system.init", "params": {"db": db_name}}
    )
    if status < 400:
        raise RuntimeError("system.init without token should fail")
    _assert_error(init_noauth, "AUTH_REQUIRED")

    # 2) system.init
    init_payload = {"intent": "system.init", "params": {"db": db_name}}
    status, init_resp = _http_post_json(intent_url, init_payload, headers=auth_header)
    if status >= 400 or not init_resp.get("ok"):
        raise RuntimeError(f"system.init failed: {init_resp}")
    _assert_scene_trace(init_resp, label="system.init")

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

    # 4.1) api.data grouped_rows across key domains (project/contract/cost/risk)
    grouped_cases = [
        {"case": "project_grouped", "model": "project.project", "group_by": "lifecycle_state"},
        {"case": "task_grouped", "model": "project.task", "group_by": "stage_id"},
        {"case": "contract_grouped", "model": "construction.contract", "group_by": "create_uid"},
        {"case": "cost_grouped", "model": "project.cost.ledger", "group_by": "create_uid"},
        {"case": "risk_grouped", "model": "payment.request", "group_by": "create_uid"},
    ]
    grouped_responses: list[dict] = []
    grouped_signature_cases: list[dict] = []
    for item in grouped_cases:
        grouped_payload = {
            "intent": "api.data",
            "params": {
                "db": db_name,
                "op": "list",
                "model": item["model"],
                "fields": ["id", "name"],
                "group_by": item["group_by"],
                "group_sample_limit": 3,
                "limit": 12,
                "offset": 0,
            },
        }
        status, grouped_resp = _http_post_json(intent_url, grouped_payload, headers=auth_header)
        if status >= 400 or not grouped_resp.get("ok"):
            err = grouped_resp.get("error") if isinstance(grouped_resp.get("error"), dict) else {}
            err_code = str(err.get("code") or "")
            if err_code == "PERMISSION_DENIED":
                grouped_responses.append(
                    {
                        "case": item["case"],
                        "request": grouped_payload,
                        "response": grouped_resp,
                        "skipped": True,
                        "skip_reason": "PERMISSION_DENIED",
                    }
                )
                grouped_signature_cases.append(
                    {
                        "case": item["case"],
                        "model": item["model"],
                        "group_by": item["group_by"],
                        "status": "skipped",
                        "reason": "PERMISSION_DENIED",
                        "meta_group_by": None,
                        "has_group_summary": False,
                        "has_grouped_rows": False,
                        "supports_group_key": False,
                        "supports_page_flags": False,
                        "supports_page_window": False,
                        "supports_window_identity": False,
                        "supports_window_key": False,
                        "supports_window_identity_model": False,
                        "supports_window_identity_group_by": False,
                        "supports_window_identity_algo": False,
                        "supports_window_identity_key_tuple": False,
                        "supports_window_nav_match": False,
                        "supports_window_span": False,
                        "window_span_matches_range": False,
                        "request_offset_matches_observed": False,
                        "page_window_matches_range": False,
                        "consistency_score": 0,
                        "response_keys": [],
                    }
                )
                continue
            raise RuntimeError(f"grouped api.data failed for {item['case']}: {grouped_resp}")
        data, meta = _unwrap_intent_data(grouped_resp)
        grouped_semantic = _build_grouped_semantic_signature(
            data,
            request_model=item["model"],
            request_group_by=item["group_by"],
            request_page_limit=int(grouped_payload["params"].get("group_sample_limit") or 3),
            request_offset=int(grouped_payload["params"].get("offset") or 0),
        )
        grouped_responses.append({"case": item["case"], "request": grouped_payload, "response": grouped_resp})
        grouped_signature_cases.append(
            {
                "case": item["case"],
                "model": item["model"],
                "group_by": item["group_by"],
                "status": "ok",
                "reason": "",
                "meta_group_by": meta.get("group_by"),
                "has_group_summary": isinstance(data.get("group_summary"), list),
                "has_grouped_rows": isinstance(data.get("grouped_rows"), list),
                "supports_group_key": grouped_semantic["supports_group_key"],
                "supports_page_flags": grouped_semantic["supports_page_flags"],
                "supports_page_window": grouped_semantic["supports_page_window"],
                "supports_window_identity": grouped_semantic["supports_window_identity"],
                "supports_window_key": grouped_semantic["supports_window_key"],
                "supports_window_identity_model": grouped_semantic["supports_window_identity_model"],
                "supports_window_identity_group_by": grouped_semantic["supports_window_identity_group_by"],
                "supports_window_identity_algo": grouped_semantic["supports_window_identity_algo"],
                "supports_window_identity_key_tuple": grouped_semantic["supports_window_identity_key_tuple"],
                "supports_window_nav_match": grouped_semantic["supports_window_nav_match"],
                "supports_window_span": grouped_semantic["supports_window_span"],
                "window_span_matches_range": grouped_semantic["window_span_matches_range"],
                "request_offset_matches_observed": grouped_semantic["request_offset_matches_observed"],
                "page_window_matches_range": grouped_semantic["page_window_matches_range"],
                "consistency_score": grouped_semantic["consistency_score"],
                "response_keys": sorted(
                    [key for key in ("records", "next_offset", "group_summary", "grouped_rows") if key in data]
                ),
            }
        )

    grouped_signature = _normalize_obj(
        {
            "version": "v0.4",
            "grouped_cases": sorted(grouped_signature_cases, key=lambda row: row.get("case") or ""),
        }
    )
    update_grouped_snapshot = os.getenv("E2E_GROUPED_SNAPSHOT_UPDATE") == "1"
    if update_grouped_snapshot:
        _write_json_path(GROUPED_SNAPSHOT_BASELINE, grouped_signature)
        print(f"[e2e] grouped snapshot updated: {GROUPED_SNAPSHOT_BASELINE}")
    else:
        if not GROUPED_SNAPSHOT_BASELINE.exists():
            raise RuntimeError(
                f"grouped snapshot baseline missing: {GROUPED_SNAPSHOT_BASELINE}. "
                f"Run with E2E_GROUPED_SNAPSHOT_UPDATE=1 to create baseline."
            )
        baseline = _normalize_obj(_read_json(GROUPED_SNAPSHOT_BASELINE))
        if baseline != grouped_signature:
            current_path = os.path.join(out_dir, "grouped_signature.current.json")
            baseline_path = os.path.join(out_dir, "grouped_signature.baseline.json")
            _write_json(current_path, grouped_signature)
            _write_json(baseline_path, baseline)
            raise RuntimeError(
                "grouped_rows e2e snapshot mismatch "
                f"(current={current_path}, baseline={baseline_path})"
            )

    # 5) logout and verify revoked token
    status, logout_resp = _http_post_json(
        intent_url, {"intent": "auth.logout", "params": {"db": db_name}}, headers=auth_header
    )
    if status >= 400 or not logout_resp.get("ok"):
        raise RuntimeError(f"logout failed: {logout_resp}")

    status, init_revoked = _http_post_json(
        intent_url, {"intent": "system.init", "params": {"db": db_name}}, headers=auth_header
    )
    if status < 400:
        raise RuntimeError("system.init with revoked token should fail")
    _assert_error(init_revoked, "AUTH_REQUIRED")

    snapshot = {
        "meta": {
            "base_url": base_url,
            "db": db_name,
            "login": login,
            "captured_at": int(time.time()),
        },
        "login": login_resp,
        "system_init_noauth": init_noauth,
        "system_init": init_resp,
        "ui_contract": contract_resp,
        "api_data": data_resp,
        "api_data_grouped": grouped_responses,
        "api_data_grouped_signature": grouped_signature,
        "logout": logout_resp,
        "system_init_revoked": init_revoked,
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
