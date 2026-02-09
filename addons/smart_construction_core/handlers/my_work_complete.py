# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
import json
from uuid import uuid4

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError
from odoo.addons.smart_construction_core.handlers.reason_codes import (
    REASON_DONE,
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_PARTIAL_FAILED,
    REASON_REPLAY_WINDOW_EXPIRED,
    failure_meta_for_reason,
    my_work_failure_meta_for_exception,
)
from odoo.addons.smart_core.utils.idempotency import (
    find_latest_audit_entry,
    find_recent_audit_entry,
    ids_summary,
    normalize_ids_for_fingerprint,
    normalize_request_id,
    replay_window_seconds,
    sha1_json,
)


class MyWorkCompleteHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.complete"
    DESCRIPTION = "Complete a todo item from my-work list"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        source = str(params.get("source") or "").strip()
        item_id = params.get("id")
        note = str(params.get("note") or "").strip()
        try:
            activity_id = _coerce_activity_id(item_id)
            _complete_activity(self.env, source=source, activity_id=activity_id, note=note)
            data = {
                "id": activity_id,
                "source": source,
                "success": True,
                "reason_code": REASON_DONE,
                "message": "待办已完成",
                "retryable": False,
                "error_category": "",
                "suggested_action": "",
                "done_at": fields.Datetime.now(),
            }
        except Exception as exc:
            activity_id = _safe_int(item_id)
            failed_meta = my_work_failure_meta_for_exception(exc)
            data = {
                "id": activity_id,
                "source": source,
                "success": False,
                "reason_code": failed_meta["reason_code"],
                "message": str(exc) or "完成待办失败",
                "retryable": bool(failed_meta["retryable"]),
                "error_category": failed_meta["error_category"],
                "suggested_action": failed_meta["suggested_action"],
                "done_at": fields.Datetime.now(),
            }

        return {
            "ok": True,
            "data": data,
            "meta": {"intent": self.INTENT_TYPE},
        }


class MyWorkCompleteBatchHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.complete_batch"
    DESCRIPTION = "Complete multiple todo items from my-work list"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    IDEMPOTENCY_WINDOW_SECONDS = 120
    AUDIT_MAX_PAYLOAD_BYTES = 16 * 1024
    AUDIT_IDS_SAMPLE_LIMIT = 20

    def _idempotency_fingerprint(self, *, source, ids, note, idem_key):
        payload = {
            "intent": self.INTENT_TYPE,
            "db": self.env.cr.dbname,
            "user_id": int(self.env.user.id or 0),
            "company_id": int(self.env.user.company_id.id or 0) if self.env.user and self.env.user.company_id else 0,
            "source": source,
            "ids": normalize_ids_for_fingerprint(ids),
            "note": note or "",
            "idempotency_key": idem_key,
        }
        return sha1_json(payload)

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="MY_WORK_BATCH_REPLAY_WINDOW_SEC",
        )

    def _find_recent_idempotency_entry(self, *, idem_key):
        return find_recent_audit_entry(
            self.env,
            event_code="MY_WORK_COMPLETE_BATCH",
            idempotency_key=idem_key,
            window_seconds=self._idempotency_window_seconds(),
            limit=20,
        )

    def _has_expired_replay_candidate(self, *, idem_key, fingerprint):
        entry = find_latest_audit_entry(
            self.env,
            event_code="MY_WORK_COMPLETE_BATCH",
            idempotency_key=idem_key,
            limit=20,
        )
        if not entry:
            return False
        payload = entry.get("payload") or {}
        old_fingerprint = str(payload.get("idempotency_fingerprint") or "")
        return bool(old_fingerprint and old_fingerprint == fingerprint)

    def _idempotency_conflict_response(self, *, request_id, idempotency_key, trace_id):
        failure_meta = failure_meta_for_reason(REASON_IDEMPOTENCY_CONFLICT)
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
            "data": {
                "request_id": request_id,
                "idempotency_key": idempotency_key,
                "idempotent_replay": False,
                "replay_window_expired": False,
                "idempotency_replay_reason_code": "",
                "trace_id": trace_id,
            },
            "meta": {"intent": self.INTENT_TYPE},
        }

    def _to_dt(self, value):
        if not value:
            return None
        if isinstance(value, str):
            try:
                return fields.Datetime.from_string(value)
            except Exception:
                return None
        return value

    def _ids_summary(self, rows):
        return ids_summary(rows, sample_limit=self.AUDIT_IDS_SAMPLE_LIMIT)

    def _build_audit_payload(self, *, source, ids, note, idem_key, idem_fingerprint, result, trace_id, duration_ms):
        payload = {
            "source": source,
            "idempotency_key": idem_key,
            "idempotency_fingerprint": idem_fingerprint,
            "trace_id": trace_id,
            "duration_ms": int(duration_ms),
            "input_summary": {
                "ids": self._ids_summary(ids),
                "note_len": len(note or ""),
            },
            "result_summary": {
                "success": bool(result.get("success")),
                "reason_code": str(result.get("reason_code") or ""),
                "done_count": int(result.get("done_count") or 0),
                "failed_count": int(result.get("failed_count") or 0),
                "failed_reason_summary": result.get("failed_reason_summary") or [],
                "failed_retryable_summary": result.get("failed_retryable_summary") or {},
                "completed_ids": self._ids_summary(result.get("completed_ids") or []),
                "failed_ids": self._ids_summary([(row or {}).get("id") for row in (result.get("failed_items") or [])]),
            },
            "replay_result": result,
        }
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        if len(raw.encode("utf-8")) <= self.AUDIT_MAX_PAYLOAD_BYTES:
            return payload
        compact_result = dict(result)
        compact_result.pop("completed_ids", None)
        compact_result.pop("failed_items", None)
        compact_result["result_truncated"] = True
        payload["replay_result"] = compact_result
        payload["result_summary"]["payload_truncated"] = True
        return payload

    def _write_batch_audit(self, *, trace_id, source, ids, note, idem_key, idem_fingerprint, result, duration_ms):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            after_payload = self._build_audit_payload(
                source=source,
                ids=ids,
                note=note,
                idem_key=idem_key,
                idem_fingerprint=idem_fingerprint,
                result=result,
                trace_id=trace_id,
                duration_ms=duration_ms,
            )
            Audit.sudo().write_event(
                event_code="MY_WORK_COMPLETE_BATCH",
                model="mail.activity",
                res_id=0,
                action="complete_batch",
                after=after_payload,
                reason="my-work batch completion",
                trace_id=trace_id or "",
                company_id=self.env.user.company_id.id if self.env.user and self.env.user.company_id else None,
            )
        except Exception:
            return

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        source = str(params.get("source") or "").strip()
        ids = params.get("ids") if isinstance(params.get("ids"), list) else []
        note = str(params.get("note") or "").strip()
        started = fields.Datetime.now()
        request_id = normalize_request_id(params.get("request_id"), prefix="mw_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        idempotency_fingerprint = self._idempotency_fingerprint(
            source=source, ids=ids, note=note, idem_key=idempotency_key
        )
        trace_id = f"mw_batch_{uuid4().hex[:12]}"
        if not ids:
            raise UserError("缺少待办 ID 列表")
        entry = self._find_recent_idempotency_entry(idem_key=idempotency_key)
        if entry:
            payload = entry.get("payload") or {}
            old_fingerprint = str(payload.get("idempotency_fingerprint") or "")
            if old_fingerprint and old_fingerprint != idempotency_fingerprint:
                return self._idempotency_conflict_response(
                    request_id=request_id,
                    idempotency_key=idempotency_key,
                    trace_id=trace_id,
                )
            replay = payload.get("replay_result") or {}
            replay_data = dict(replay or {})
            replay_data["idempotent_replay"] = True
            replay_data["request_id"] = str(replay_data.get("request_id") or request_id)
            replay_data["idempotency_key"] = idempotency_key
            replay_data["idempotency_fingerprint"] = idempotency_fingerprint
            replay_data["trace_id"] = str(replay_data.get("trace_id") or trace_id)
            ts = self._to_dt(entry.get("ts"))
            now_dt = fields.Datetime.from_string(fields.Datetime.now())
            replay_age_ms = 0
            if ts:
                replay_age_ms = max(0, int((now_dt - ts).total_seconds() * 1000))
            replay_data["replay_from_audit_id"] = int(entry.get("audit_id") or 0)
            replay_data["replay_original_trace_id"] = str(entry.get("trace_id") or "")
            replay_data["replay_age_ms"] = replay_age_ms
            replay_data["replay_window_expired"] = False
            replay_data["idempotency_replay_reason_code"] = ""
            return {"ok": True, "data": replay_data, "meta": {"intent": self.INTENT_TYPE}}

        replay_window_expired = self._has_expired_replay_candidate(
            idem_key=idempotency_key,
            fingerprint=idempotency_fingerprint,
        )
        completed = []
        failed = []
        reason_counter = defaultdict(int)
        for raw_id in ids:
            try:
                activity_id = _coerce_activity_id(raw_id)
                _complete_activity(self.env, source=source, activity_id=activity_id, note=note)
                completed.append(activity_id)
            except Exception as exc:
                failed_meta = my_work_failure_meta_for_exception(exc)
                reason_code = failed_meta["reason_code"]
                reason_counter[reason_code] += 1
                failed.append({
                    "id": _safe_int(raw_id),
                    "reason_code": reason_code,
                    "message": str(exc) or "failed",
                    "retryable": bool(failed_meta["retryable"]),
                    "error_category": failed_meta["error_category"],
                    "suggested_action": failed_meta["suggested_action"],
                    "trace_id": trace_id,
                })

        ok = len(failed) == 0
        failed_retry_ids = [int(item.get("id") or 0) for item in failed if bool(item.get("retryable")) and int(item.get("id") or 0) > 0]
        data = {
            "source": source,
            "request_id": request_id,
            "idempotency_key": idempotency_key,
            "idempotency_fingerprint": idempotency_fingerprint,
            "idempotent_replay": False,
            "replay_window_expired": bool(replay_window_expired),
            "idempotency_replay_reason_code": REASON_REPLAY_WINDOW_EXPIRED if replay_window_expired else "",
            "trace_id": trace_id,
            "success": ok,
            "reason_code": REASON_DONE if ok else REASON_PARTIAL_FAILED,
            "message": "批量完成成功" if ok else "部分待办完成失败",
            "done_count": len(completed),
            "failed_count": len(failed),
            "completed_ids": completed,
            "failed_items": failed,
            "failed_retry_ids": failed_retry_ids,
            "failed_reason_summary": _reason_summary(reason_counter),
            "failed_retryable_summary": _retryable_summary(failed),
            "done_at": fields.Datetime.now(),
        }
        duration_ms = int(
            (
                fields.Datetime.from_string(fields.Datetime.now())
                - fields.Datetime.from_string(started)
            ).total_seconds()
            * 1000
        )
        self._write_batch_audit(
            trace_id=trace_id,
            source=source,
            ids=ids,
            note=note,
            idem_key=idempotency_key,
            idem_fingerprint=idempotency_fingerprint,
            result=data,
            duration_ms=duration_ms,
        )
        return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE}}


def _coerce_activity_id(item_id):
    if not item_id:
        raise UserError("缺少待办 ID")
    try:
        return int(item_id)
    except Exception:
        raise UserError("待办 ID 无效")


def _complete_activity(env, *, source, activity_id, note):
    if source != "mail.activity":
        raise UserError("仅支持完成 mail.activity 类型待办")
    Activity = env["mail.activity"]
    activity = Activity.browse(activity_id).exists()
    if not activity:
        raise UserError("待办不存在")
    if activity.user_id.id != env.user.id and not env.user.has_group("base.group_system"):
        raise AccessError("只能完成分配给自己的待办")
    feedback = note or "Completed from my-work."
    activity.action_feedback(feedback=feedback)


def _safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def _reason_code_for_exception(exc):
    return _failure_meta_for_exception(exc)["reason_code"]


def _failure_meta_for_exception(exc):
    # Keep this compatibility wrapper for existing imports in tests and handlers.
    return my_work_failure_meta_for_exception(exc)


def _reason_summary(counter_map):
    rows = [{"reason_code": key, "count": int(value)} for key, value in counter_map.items()]
    rows.sort(key=lambda row: row["count"], reverse=True)
    return rows


def _retryable_summary(failed_items):
    retryable = 0
    non_retryable = 0
    for item in failed_items or []:
        if bool(item.get("retryable")):
            retryable += 1
        else:
            non_retryable += 1
    return {"retryable": retryable, "non_retryable": non_retryable}
