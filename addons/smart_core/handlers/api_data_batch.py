# -*- coding: utf-8 -*-

import logging
import base64
import csv
import io
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from odoo import fields
from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from .reason_codes import (
    REASON_CONFLICT,
    REASON_REPLAY_WINDOW_EXPIRED,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_WRITE_FAILED,
    batch_failure_meta,
)
from ..utils.idempotency import (
    find_latest_audit_entry,
    find_recent_audit_entry,
    normalize_request_id,
    replay_window_seconds,
    sha1_json,
)

_logger = logging.getLogger(__name__)


class ApiDataBatchHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data.batch"
    DESCRIPTION = "Batch update with per-record result details"
    VERSION = "0.1.0"
    ETAG_ENABLED = False

    ACTION_MAP = {
        "archive": {"active": False},
        "activate": {"active": True},
    }
    IDEMPOTENCY_WINDOW_SECONDS = 30

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code}

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_ids(self, params: Dict[str, Any]) -> List[int]:
        ids = params.get("ids") or []
        if isinstance(ids, list):
            values = []
            for raw in ids:
                try:
                    values.append(int(raw))
                except Exception:
                    continue
            return values
        try:
            return [int(ids)]
        except Exception:
            return []

    def _resolve_vals(self, params: Dict[str, Any]):
        action = str(params.get("action") or "").strip().lower()
        if action in self.ACTION_MAP:
            return action, dict(self.ACTION_MAP[action])
        if action == "assign":
            assignee_id = params.get("assignee_id")
            try:
                uid = int(assignee_id)
            except Exception:
                uid = 0
            if uid <= 0:
                return action, {}
            return action, {"user_id": uid}
        vals = params.get("vals") or params.get("values") or {}
        if isinstance(vals, dict) and vals:
            return action or "write", vals
        return action, {}

    def _get_int(self, params: Dict[str, Any], key: str, default: int):
        try:
            return int(params.get(key))
        except Exception:
            return default

    def _normalize_if_match_map(self, params: Dict[str, Any]) -> Dict[int, str]:
        raw = params.get("if_match_map") or {}
        if not isinstance(raw, dict):
            return {}
        normalized: Dict[int, str] = {}
        for key, value in raw.items():
            try:
                rid = int(key)
            except Exception:
                continue
            val = str(value or "").strip()
            if rid > 0 and val:
                normalized[rid] = val
        return normalized

    def _idempotency_fingerprint(self, *, model: str, action: str, ids: List[int], vals: Dict[str, Any], idem_key: str) -> str:
        payload = {
            "model": model,
            "action": action,
            "ids": list(sorted(ids)),
            "vals": vals,
            "idempotency_key": idem_key,
        }
        return sha1_json(payload)

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="API_DATA_BATCH_REPLAY_WINDOW_SEC",
        )

    def _find_idempotent_replay(self, *, model: str, idem_key: str, fingerprint: str):
        entry = find_recent_audit_entry(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key=idem_key,
            window_seconds=self._idempotency_window_seconds(),
            limit=20,
            extra_domain=[("model", "=", model)],
        )
        if not entry:
            return None
        payload = entry.get("payload") or {}
        if str(payload.get("idempotency_fingerprint") or "") != fingerprint:
            return None
        result = payload.get("result")
        if isinstance(result, dict):
            return result
        return None

    def _has_expired_replay_candidate(self, *, model: str, idem_key: str, fingerprint: str):
        entry = find_latest_audit_entry(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key=idem_key,
            limit=20,
            extra_domain=[("model", "=", model)],
        )
        if not entry:
            return False
        payload = entry.get("payload") or {}
        old_fingerprint = str(payload.get("idempotency_fingerprint") or "")
        return bool(old_fingerprint and old_fingerprint == fingerprint)

    def _write_batch_audit(self, *, trace_id: str, model: str, action: str, ids: List[int], vals: Dict[str, Any], idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.sudo().write_event(
                event_code="API_DATA_BATCH",
                model=model,
                res_id=0,
                action=action or "write",
                after={
                    "ids": ids,
                    "vals": vals,
                    "idempotency_key": idem_key,
                    "idempotency_fingerprint": idem_fingerprint,
                    "result": result,
                },
                reason="batch update",
                trace_id=trace_id or "",
                company_id=self.env.user.company_id.id if self.env.user and self.env.user.company_id else None,
            )
        except Exception:
            return

    def _build_failed_csv(self, model: str, action: str, failed_rows: List[Dict[str, Any]]):
        if not failed_rows:
            return {"file_name": "", "content_b64": "", "count": 0}
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["model", "action", "id", "reason_code", "retryable", "error_category", "message"])
        for row in failed_rows:
            writer.writerow([
                model,
                action,
                row.get("id") or "",
                row.get("reason_code") or "",
                bool(row.get("retryable")),
                row.get("error_category") or "",
                row.get("message") or "",
            ])
        raw = buf.getvalue().encode("utf-8-sig")
        b64 = base64.b64encode(raw).decode("ascii")
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return {
            "file_name": f"{model.replace('.', '_')}_{action}_failed_{stamp}.csv",
            "content_b64": b64,
            "count": len(failed_rows),
        }

    def _apply_failed_page(self, result: Dict[str, Any], *, offset: int, limit: int):
        all_rows = [item for item in (result.get("results") or []) if not item.get("ok")]
        total = len(all_rows)
        start = max(0, min(offset, total))
        page = all_rows[start:start + limit]
        enriched = dict(result)
        enriched["failed_total"] = total
        enriched["failed_page_offset"] = start
        enriched["failed_page_limit"] = limit
        enriched["failed_preview"] = page
        enriched["failed_truncated"] = max(0, total - (start + len(page)))
        enriched["failed_has_more"] = (start + len(page)) < total
        return enriched

    def _failed_reason_summary(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        counts = defaultdict(int)
        for row in rows or []:
            if row.get("ok"):
                continue
            code = str(row.get("reason_code") or "").strip() or "UNKNOWN"
            counts[code] += 1
        out = [{"reason_code": key, "count": int(value)} for key, value in counts.items()]
        out.sort(key=lambda item: item["count"], reverse=True)
        return out

    def _failed_retryable_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        retryable = 0
        non_retryable = 0
        for row in rows or []:
            if row.get("ok"):
                continue
            if bool(row.get("retryable")):
                retryable += 1
            else:
                non_retryable += 1
        return {"retryable": retryable, "non_retryable": non_retryable}

    def _normalize_result_rows(self, rows: List[Dict[str, Any]], *, trace_id: str) -> List[Dict[str, Any]]:
        normalized = []
        for raw in rows or []:
            row = dict(raw or {})
            reason_code = str(row.get("reason_code") or "").strip()
            ok = bool(row.get("ok"))
            if not ok and reason_code:
                row.update(batch_failure_meta(reason_code))
            row.setdefault("retryable", False)
            row.setdefault("error_category", "")
            row.setdefault("suggested_action", "")
            row["trace_id"] = str(row.get("trace_id") or trace_id)
            normalized.append(row)
        return normalized

    def _ensure_result_contract(self, result: Dict[str, Any], *, request_id: str, trace_id: str) -> Dict[str, Any]:
        data = dict(result or {})
        rows = self._normalize_result_rows(data.get("results") or [], trace_id=trace_id)
        data["results"] = rows
        data["request_id"] = str(data.get("request_id") or request_id)
        data["trace_id"] = str(data.get("trace_id") or trace_id)
        data["failed_retry_ids"] = [
            int(item.get("id") or 0)
            for item in rows
            if not item.get("ok") and bool(item.get("retryable")) and int(item.get("id") or 0) > 0
        ]
        data["failed_reason_summary"] = data.get("failed_reason_summary") or self._failed_reason_summary(rows)
        data["failed_retryable_summary"] = data.get("failed_retryable_summary") or self._failed_retryable_summary(rows)
        return data

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = str(params.get("model") or "").strip()
        ids = self._get_ids(params)
        action, vals = self._resolve_vals(params)
        request_id = normalize_request_id(params.get("request_id"), prefix="adb_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        if_match_map = self._normalize_if_match_map(params)
        preview_limit = self._get_int(params, "failed_preview_limit", 10)
        page_limit = self._get_int(params, "failed_limit", preview_limit)
        page_limit = max(1, min(page_limit, 200))
        page_offset = self._get_int(params, "failed_offset", 0)
        page_offset = max(0, page_offset)
        export_failed_csv = bool(params.get("export_failed_csv"))
        context = params.get("context") if isinstance(params.get("context"), dict) else {}

        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")
        if not ids:
            return self._err(400, "缺少参数 ids")
        if not vals:
            return self._err(400, "缺少有效的 action/vals")

        env_model = self.env[model].with_context(context)
        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = str(self.context.get("trace_id") or "")
        if not trace_id:
            trace_id = f"adb_{uuid4().hex[:12]}"

        safe_vals = {k: v for k, v in vals.items() if k in env_model._fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段")

        idempotency_fingerprint = self._idempotency_fingerprint(
            model=model,
            action=action or "write",
            ids=ids,
            vals=safe_vals,
            idem_key=idempotency_key,
        )
        replay = self._find_idempotent_replay(
            model=model,
            idem_key=idempotency_key,
            fingerprint=idempotency_fingerprint,
        )
        if replay:
            replay_data = self._ensure_result_contract(dict(replay), request_id=request_id, trace_id=trace_id)
            replay_data = self._apply_failed_page(replay_data, offset=page_offset, limit=page_limit)
            replay_data["idempotent_replay"] = True
            replay_data["replay_window_expired"] = False
            replay_data["idempotency_replay_reason_code"] = ""
            replay_data["idempotency_key"] = idempotency_key
            replay_data["idempotency_fingerprint"] = idempotency_fingerprint
            if export_failed_csv and replay_data.get("failed_total", 0) > 0 and not replay_data.get("failed_csv_content_b64"):
                failed_csv = self._build_failed_csv(model, action or "write", [item for item in replay_data.get("results") or [] if not item.get("ok")])
                replay_data["failed_csv_file_name"] = failed_csv.get("file_name")
                replay_data["failed_csv_content_b64"] = failed_csv.get("content_b64")
                replay_data["failed_csv_count"] = failed_csv.get("count")
            return {
                "ok": True,
                "data": replay_data,
                "meta": {
                    "trace_id": str(replay_data.get("trace_id") or trace_id),
                    "write_mode": "batch",
                    "source": "portal-shell",
                },
            }

        replay_window_expired = self._has_expired_replay_candidate(
            model=model,
            idem_key=idempotency_key,
            fingerprint=idempotency_fingerprint,
        )
        try:
            env_model.check_access_rights("write")
        except AccessError:
            return self._err(403, "无写入权限")

        results = []
        success = 0
        failed = 0
        for rec_id in ids:
            item = {
                "id": rec_id,
                "ok": False,
                "reason_code": "",
                "message": "",
                "retryable": False,
                "error_category": "",
                "suggested_action": "",
                "trace_id": trace_id,
            }
            rec = env_model.browse(rec_id).exists()
            if not rec:
                item["reason_code"] = REASON_NOT_FOUND
                item["message"] = "记录不存在"
                item.update(batch_failure_meta(REASON_NOT_FOUND))
                failed += 1
                results.append(item)
                continue
            try:
                rec.check_access_rule("write")
                if rec_id in if_match_map:
                    expected = if_match_map.get(rec_id, "")
                    current = rec.write_date and rec.write_date.strftime("%Y-%m-%d %H:%M:%S") or ""
                    if current and expected and current != expected:
                        item["reason_code"] = REASON_CONFLICT
                        item["message"] = "Record changed"
                        item.update(batch_failure_meta(REASON_CONFLICT))
                        failed += 1
                        results.append(item)
                        continue
                rec.write(safe_vals)
                item["ok"] = True
                item["reason_code"] = REASON_OK
                item["message"] = "updated"
                item.update(batch_failure_meta(REASON_OK))
                success += 1
            except AccessError:
                item["reason_code"] = REASON_PERMISSION_DENIED
                item["message"] = "无写入权限"
                item.update(batch_failure_meta(REASON_PERMISSION_DENIED))
                failed += 1
            except Exception as exc:
                _logger.warning("api.data.batch failed model=%s id=%s err=%s", model, rec_id, exc)
                item["reason_code"] = REASON_WRITE_FAILED
                item["message"] = str(exc)
                item.update(batch_failure_meta(REASON_WRITE_FAILED))
                failed += 1
            results.append(item)

        failed_retry_ids = [int(item.get("id") or 0) for item in results if not item.get("ok") and bool(item.get("retryable")) and int(item.get("id") or 0) > 0]
        data = {
            "model": model,
            "action": action or "write",
            "request_id": request_id,
            "trace_id": trace_id,
            "values": safe_vals,
            "requested_ids": ids,
            "succeeded": success,
            "failed": failed,
            "results": results,
            "failed_retry_ids": failed_retry_ids,
            "failed_reason_summary": self._failed_reason_summary(results),
            "failed_retryable_summary": self._failed_retryable_summary(results),
            "idempotency_key": idempotency_key,
            "idempotency_fingerprint": idempotency_fingerprint,
            "idempotent_replay": False,
            "replay_window_expired": bool(replay_window_expired),
            "idempotency_replay_reason_code": REASON_REPLAY_WINDOW_EXPIRED if replay_window_expired else "",
        }
        data = self._apply_failed_page(data, offset=page_offset, limit=page_limit)
        if export_failed_csv and failed > 0:
            failed_csv = self._build_failed_csv(model, action or "write", [item for item in results if not item.get("ok")])
            data["failed_csv_file_name"] = failed_csv.get("file_name")
            data["failed_csv_content_b64"] = failed_csv.get("content_b64")
            data["failed_csv_count"] = failed_csv.get("count")
        self._write_batch_audit(
            trace_id=trace_id,
            model=model,
            action=action or "write",
            ids=ids,
            vals=safe_vals,
            idem_key=idempotency_key,
            idem_fingerprint=idempotency_fingerprint,
            result=data,
        )
        meta = {"trace_id": trace_id, "write_mode": "batch", "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
