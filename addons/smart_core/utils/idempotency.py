# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from datetime import timedelta
from uuid import uuid4

from odoo import fields
from .reason_codes import REASON_IDEMPOTENCY_CONFLICT, failure_meta_for_reason


def normalize_request_id(raw_value, *, prefix="req"):
    value = str(raw_value or "").strip()
    if value:
        return value
    return f"{prefix}_{uuid4().hex[:12]}"


def normalize_ids_for_fingerprint(values):
    normalized = []
    for raw_id in values or []:
        token = str(raw_id or "").strip()
        if not token:
            continue
        try:
            normalized.append(int(token))
        except Exception:
            normalized.append(f"raw:{token}")
    return list(sorted(normalized, key=lambda item: str(item)))


def sha1_json(payload):
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def build_idempotency_fingerprint(payload, *, normalize_id_keys=None):
    data = dict(payload or {})
    for key in normalize_id_keys or []:
        data[key] = normalize_ids_for_fingerprint(data.get(key) or [])
    return sha1_json(data)


def replay_window_seconds(default_seconds, *, env_key):
    raw = str(os.getenv(env_key, "")).strip()
    if raw:
        try:
            return max(0, int(raw))
        except Exception:
            pass
    return max(0, int(default_seconds))


def _find_audit_entry(env, *, event_code, idempotency_key, limit=20, extra_domain=None):
    if not idempotency_key:
        return None
    Audit = env.get("sc.audit.log")
    if not Audit:
        return None
    try:
        domain = [("event_code", "=", event_code)]
        if extra_domain:
            domain.extend(list(extra_domain))
        logs = Audit.sudo().search(domain, order="id desc", limit=max(1, int(limit)))
        for log in logs:
            after_raw = log.after_json or ""
            if not after_raw:
                continue
            try:
                payload = json.loads(after_raw)
            except Exception:
                continue
            if str(payload.get("idempotency_key") or "") != str(idempotency_key):
                continue
            return {
                "audit_id": int(log.id or 0),
                "trace_id": str(log.trace_id or ""),
                "ts": log.ts,
                "payload": payload,
            }
    except Exception:
        return None
    return None


def find_recent_audit_entry(env, *, event_code, idempotency_key, window_seconds, limit=20, extra_domain=None):
    now = fields.Datetime.now()
    window_start = fields.Datetime.to_string(
        fields.Datetime.from_string(now) - timedelta(seconds=max(0, int(window_seconds)))
    )
    domain = [("ts", ">=", window_start)]
    if extra_domain:
        domain.extend(list(extra_domain))
    return _find_audit_entry(
        env,
        event_code=event_code,
        idempotency_key=idempotency_key,
        limit=limit,
        extra_domain=domain,
    )


def find_latest_audit_entry(env, *, event_code, idempotency_key, limit=20, extra_domain=None):
    return _find_audit_entry(
        env,
        event_code=event_code,
        idempotency_key=idempotency_key,
        limit=limit,
        extra_domain=extra_domain,
    )


def ids_summary(rows, *, sample_limit=20):
    normalized = []
    for value in rows or []:
        token = str(value or "").strip()
        if not token:
            continue
        try:
            normalized.append(int(token))
        except Exception:
            continue
    sample = normalized[: max(1, int(sample_limit))]
    payload = "|".join(sorted([str(x) for x in normalized]))
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest() if payload else ""
    return {"count": len(normalized), "sample": sample, "hash": digest}


def build_idempotency_conflict_response(
    *,
    intent_type,
    request_id,
    idempotency_key,
    trace_id,
    include_replay_evidence=False,
):
    failure_meta = failure_meta_for_reason(REASON_IDEMPOTENCY_CONFLICT)
    data = {
        "request_id": request_id,
        "idempotency_key": idempotency_key,
        "idempotent_replay": False,
        "replay_window_expired": False,
        "idempotency_replay_reason_code": "",
        "trace_id": trace_id,
    }
    if include_replay_evidence:
        data.update({
            "replay_from_audit_id": 0,
            "replay_original_trace_id": "",
            "replay_age_ms": 0,
        })
    return {
        "ok": False,
        "code": 409,
        "error": {
            "code": 409,
            "message": "idempotency key payload mismatch",
            "reason_code": REASON_IDEMPOTENCY_CONFLICT,
            "retryable": bool(failure_meta.get("retryable")),
            "error_category": str(failure_meta.get("error_category") or ""),
            "suggested_action": str(failure_meta.get("suggested_action") or ""),
        },
        "data": data,
        "meta": {"intent": str(intent_type or "")},
    }


def enrich_replay_contract(
    data,
    *,
    idempotent_replay=False,
    replay_window_expired=False,
    replay_reason_code="",
    replay_entry=None,
    include_replay_evidence=False,
):
    payload = dict(data or {})
    payload["idempotent_replay"] = bool(idempotent_replay)
    payload["replay_window_expired"] = bool(replay_window_expired)
    payload["idempotency_replay_reason_code"] = str(replay_reason_code or "")
    if include_replay_evidence:
        payload["replay_from_audit_id"] = 0
        payload["replay_original_trace_id"] = ""
        payload["replay_age_ms"] = 0
        if idempotent_replay and isinstance(replay_entry, dict):
            payload["replay_from_audit_id"] = int(replay_entry.get("audit_id") or 0)
            payload["replay_original_trace_id"] = str(replay_entry.get("trace_id") or "")
            ts = replay_entry.get("ts")
            if isinstance(ts, str):
                try:
                    ts = fields.Datetime.from_string(ts)
                except Exception:
                    ts = None
            now_dt = fields.Datetime.from_string(fields.Datetime.now())
            if ts:
                payload["replay_age_ms"] = max(0, int((now_dt - ts).total_seconds() * 1000))
    return payload
