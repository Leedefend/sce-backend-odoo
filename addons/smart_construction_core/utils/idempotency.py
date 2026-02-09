# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from datetime import timedelta

from odoo import fields


def normalize_request_id(raw_value, *, prefix="req"):
    value = str(raw_value or "").strip()
    if value:
        return value
    seed = str(fields.Datetime.now())
    return f"{prefix}_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"


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


def replay_window_seconds(default_seconds, *, env_key):
    raw = str(os.getenv(env_key, "")).strip()
    if raw:
        try:
            return max(0, int(raw))
        except Exception:
            pass
    return max(0, int(default_seconds))


def find_recent_audit_entry(env, *, event_code, idempotency_key, window_seconds, limit=20):
    if not idempotency_key:
        return None
    Audit = env.get("sc.audit.log")
    if not Audit:
        return None
    try:
        now = fields.Datetime.now()
        window_start = fields.Datetime.to_string(
            fields.Datetime.from_string(now) - timedelta(seconds=max(0, int(window_seconds)))
        )
        logs = Audit.sudo().search(
            [("event_code", "=", event_code), ("ts", ">=", window_start)],
            order="id desc",
            limit=max(1, int(limit)),
        )
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
