# -*- coding: utf-8 -*-

import logging
import base64
import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import apply_business_scope_domain
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import apply_project_scope_domain
    try:
        from ..core.project_context import selected_record_context_id_from_context
    except ImportError:  # pragma: no cover - compatibility for older lightweight boundary tests
        from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context

    def apply_business_scope_domain(env_model, domain, params=None, context=None):
        return apply_project_scope_domain(env_model, domain, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_bool, parse_non_negative_int, parse_positive_int
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
    apply_idempotency_identity,
    build_idempotency_fingerprint,
    build_idempotency_conflict_response,
    enrich_replay_contract,
    normalize_request_id,
    resolve_idempotency_decision,
    replay_window_seconds,
)

_logger = logging.getLogger(__name__)


class ApiDataBatchHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data.batch"
    DESCRIPTION = "Batch update with per-record result details"
    VERSION = "0.1.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "odoo_orm_batch_write_proxy"
    SOURCE_AUTHORITIES = ("odoo.orm", "ir.model.access", "ir.rule", "ir.model.fields")

    ACTION_MAP = {
        "archive": {"active": False},
        "activate": {"active": True},
    }
    IDEMPOTENCY_WINDOW_SECONDS = 30

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code}

    def _record_scope_denied(self, message: str, scope_meta: Dict[str, Any]):
        return {
            "ok": False,
            "error": {
                "code": 403,
                "message": message,
                "kind": "permission",
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            },
            "code": 403,
        }

    def _project_scope_denied(self, message: str, scope_meta: Dict[str, Any]):
        return self._record_scope_denied(message, scope_meta)

    def _source_authority_contract(self, model: str, action: str) -> Dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model or ""),
            "action": str(action or "write"),
            "proxy_only": True,
        }

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            if isinstance(payload.get("context"), dict):
                params.setdefault("context", {}).update(payload.get("context") or {})
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_ids(self, params: Dict[str, Any]) -> List[int]:
        ids, _error = self._read_ids(params)
        return ids

    def _read_ids(self, params: Dict[str, Any]):
        ids = params.get("ids") or []
        if isinstance(ids, list):
            values = []
            for raw in ids:
                try:
                    value = int(raw)
                except Exception:
                    return [], self._err(400, "ids 无效")
                if value <= 0:
                    return [], self._err(400, "ids 无效")
                values.append(value)
            return values, None
        try:
            value = int(ids)
        except Exception:
            return [], self._err(400, "ids 无效")
        if value <= 0:
            return [], self._err(400, "ids 无效")
        return [value], None

    def _resolve_vals(self, params: Dict[str, Any]):
        action = str(params.get("action") or "").strip().lower()
        if action in self.ACTION_MAP:
            return action, dict(self.ACTION_MAP[action]), None
        if action == "assign":
            uid, uid_error = parse_positive_int(params.get("assignee_id"))
            if uid_error:
                return action, {}, self._err(400, "assignee_id 无效")
            return action, {"user_id": uid}, None
        vals = params.get("vals") or params.get("values") or {}
        if isinstance(vals, dict) and vals:
            return action or "write", vals, None
        return action, {}, None

    def _read_positive_param(self, params: Dict[str, Any], key: str, default: int):
        value, error = parse_positive_int(params.get(key), allow_empty=True)
        if error:
            return 0, self._err(400, f"{key} 无效")
        return value or default, None

    def _read_non_negative_param(self, params: Dict[str, Any], key: str, default: int):
        value, error = parse_non_negative_int(params.get(key), allow_empty=True)
        if error:
            return 0, self._err(400, f"{key} 无效")
        return default if value is None else value, None

    def _request_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = dict(params.get("context") or {}) if isinstance(params.get("context"), dict) else {}
        company_id, company_error = parse_positive_int(params.get("company_id"), allow_empty=True)
        if not company_error and company_id:
            ctx["allowed_company_ids"] = [company_id]
            ctx["company_id"] = company_id
        project_id, project_error = parse_positive_int(
            params.get("current_project_id") or params.get("project_id"),
            allow_empty=True,
        )
        if not project_error and project_id:
            ctx["current_project_id"] = project_id
            ctx.setdefault("default_project_id", project_id)
        operation_strategy = str(params.get("operation_strategy") or params.get("operationStrategy") or "").strip()
        if operation_strategy:
            ctx["operation_strategy"] = operation_strategy
        return ctx

    def _normalize_if_match_map(self, params: Dict[str, Any]):
        raw = params.get("if_match_map") or {}
        if not isinstance(raw, dict):
            return {}, self._err(400, "if_match_map 无效")
        normalized: Dict[int, str] = {}
        for key, value in raw.items():
            rid, rid_error = parse_positive_int(key)
            if rid_error:
                return {}, self._err(400, "if_match_map 无效")
            val = str(value or "").strip()
            if not val:
                return {}, self._err(400, "if_match_map 无效")
            normalized[rid] = val
        return normalized, None

    def _idempotency_fingerprint(self, *, model: str, action: str, ids: List[int], vals: Dict[str, Any], idem_key: str) -> str:
        payload = {
            "model": model,
            "action": action,
            "ids": ids,
            "vals": vals,
            "idempotency_key": idem_key,
        }
        return build_idempotency_fingerprint(payload, normalize_id_keys=["ids"])

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="API_DATA_BATCH_REPLAY_WINDOW_SEC",
        )

    def _idempotency_conflict_response(self, *, request_id, idempotency_key, trace_id):
        return build_idempotency_conflict_response(
            intent_type=self.INTENT_TYPE,
            request_id=request_id,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            include_replay_evidence=True,
        )

    def _write_batch_audit(self, *, trace_id: str, model: str, action: str, ids: List[int], vals: Dict[str, Any], idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.write_event(
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
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
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
        ids, ids_error = self._read_ids(params)
        if ids_error:
            return ids_error
        action, vals, vals_error = self._resolve_vals(params)
        if vals_error:
            return vals_error
        request_id = normalize_request_id(params.get("request_id"), prefix="adb_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        if_match_map, if_match_map_error = self._normalize_if_match_map(params)
        if if_match_map_error:
            return if_match_map_error
        preview_limit, preview_limit_error = self._read_positive_param(params, "failed_preview_limit", 10)
        if preview_limit_error:
            return preview_limit_error
        page_limit, page_limit_error = self._read_positive_param(params, "failed_limit", preview_limit)
        if page_limit_error:
            return page_limit_error
        page_limit = max(1, min(page_limit, 200))
        page_offset, page_offset_error = self._read_non_negative_param(params, "failed_offset", 0)
        if page_offset_error:
            return page_offset_error
        export_failed_csv = parse_bool(params.get("export_failed_csv"), False)
        context = self._request_context(params)

        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")
        if not ids:
            return self._err(400, "缺少参数 ids")
        if not vals:
            return self._err(400, "缺少有效的 action/vals")

        env_model = self.env[model].with_context(context)
        scoped_domain, project_scope_meta = apply_business_scope_domain(env_model, [("id", "in", ids)], params, context)
        if project_scope_meta.get("applied"):
            allowed_count = env_model.search_count(scoped_domain)
            if int(allowed_count or 0) != len(set(ids)):
                return self._record_scope_denied("当前记录上下文不允许批量修改其他记录的数据", project_scope_meta)
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
        decision = resolve_idempotency_decision(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key=idempotency_key,
            fingerprint=idempotency_fingerprint,
            window_seconds=self._idempotency_window_seconds(),
            replay_payload_key="result",
            limit=20,
            recent_extra_domain=[("model", "=", model)],
        )
        if decision.get("conflict"):
            return self._idempotency_conflict_response(
                request_id=request_id,
                idempotency_key=idempotency_key,
                trace_id=trace_id,
            )
        replay_payload = decision.get("replay_payload") or {}
        replay_entry = decision.get("replay_entry") or {}
        if replay_payload:
            replay_data = self._ensure_result_contract(dict(replay_payload), request_id=request_id, trace_id=trace_id)
            replay_data = self._apply_failed_page(replay_data, offset=page_offset, limit=page_limit)
            replay_data = apply_idempotency_identity(
                replay_data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
            )
            replay_data = enrich_replay_contract(
                replay_data,
                idempotent_replay=True,
                replay_window_expired=False,
                replay_reason_code="",
                replay_entry=replay_entry,
                include_replay_evidence=True,
            )
            if export_failed_csv and replay_data.get("failed_total", 0) > 0 and not replay_data.get("failed_csv_content_b64"):
                failed_csv = self._build_failed_csv(model, action or "write", [item for item in replay_data.get("results") or [] if not item.get("ok")])
                replay_data["failed_csv_file_name"] = failed_csv.get("file_name")
                replay_data["failed_csv_content_b64"] = failed_csv.get("content_b64")
                replay_data["failed_csv_count"] = failed_csv.get("count")
            replay_data.setdefault("project_scope", project_scope_meta)
            replay_data.setdefault("record_scope", project_scope_meta)
            return {
                "ok": True,
                "data": replay_data,
                "meta": {
                    "trace_id": str(replay_data.get("trace_id") or trace_id),
                    "write_mode": "batch",
                    "source": "portal-shell",
                    "source_authority": self._source_authority_contract(model, action or "write"),
                    "project_scope": project_scope_meta,
                    "record_scope": project_scope_meta,
                },
        }

        replay_window_expired = bool(decision.get("replay_window_expired"))
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
        data = apply_idempotency_identity(
            {
                "model": model,
                "action": action or "write",
                "values": safe_vals,
                "requested_ids": ids,
                "succeeded": success,
                "failed": failed,
                "results": results,
                "failed_retry_ids": failed_retry_ids,
                "failed_reason_summary": self._failed_reason_summary(results),
                "failed_retryable_summary": self._failed_retryable_summary(results),
                "project_scope": project_scope_meta,
                "record_scope": project_scope_meta,
            },
            request_id=request_id,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            trace_id=trace_id,
        )
        data = enrich_replay_contract(data,
            idempotent_replay=False,
            replay_window_expired=bool(replay_window_expired),
            replay_reason_code=REASON_REPLAY_WINDOW_EXPIRED if replay_window_expired else "",
            include_replay_evidence=True,
        )
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
        meta = {
            "trace_id": trace_id,
            "write_mode": "batch",
            "source": "portal-shell",
            "source_authority": self._source_authority_contract(model, action or "write"),
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return {"ok": True, "data": data, "meta": meta}
