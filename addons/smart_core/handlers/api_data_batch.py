# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import base64
import csv
import io
from datetime import datetime
from datetime import timedelta
from typing import Any, Dict, List

from odoo import fields
from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler

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
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _find_idempotent_replay(self, *, model: str, idem_key: str, fingerprint: str):
        if not idem_key:
            return None
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return None
        try:
            now = fields.Datetime.now()
            window_start = fields.Datetime.to_string(
                fields.Datetime.from_string(now) - timedelta(seconds=self.IDEMPOTENCY_WINDOW_SECONDS)
            )
            logs = Audit.sudo().search([
                ("event_code", "=", "API_DATA_BATCH"),
                ("model", "=", model),
                ("ts", ">=", window_start),
            ], order="id desc", limit=20)
            for log in logs:
                after_raw = log.after_json or ""
                if not after_raw:
                    continue
                try:
                    after_payload = json.loads(after_raw)
                except Exception:
                    continue
                if str(after_payload.get("idempotency_key") or "") != idem_key:
                    continue
                if str(after_payload.get("idempotency_fingerprint") or "") != fingerprint:
                    continue
                result = after_payload.get("result")
                if isinstance(result, dict):
                    return result
            return None
        except Exception:
            return None

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
        writer.writerow(["model", "action", "id", "reason_code", "message"])
        for row in failed_rows:
            writer.writerow([
                model,
                action,
                row.get("id") or "",
                row.get("reason_code") or "",
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

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = str(params.get("model") or "").strip()
        ids = self._get_ids(params)
        action, vals = self._resolve_vals(params)
        idempotency_key = str(params.get("idempotency_key") or "").strip()
        if_match_map = self._normalize_if_match_map(params)
        preview_limit = self._get_int(params, "failed_preview_limit", 10)
        preview_limit = max(1, min(preview_limit, 200))
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
            replay_data = dict(replay)
            replay_data["idempotent_replay"] = True
            replay_data["idempotency_key"] = idempotency_key
            replay_data["idempotency_fingerprint"] = idempotency_fingerprint
            return {"ok": True, "data": replay_data, "meta": {"trace_id": trace_id, "write_mode": "batch", "source": "portal-shell"}}

        try:
            env_model.check_access_rights("write")
        except AccessError:
            return self._err(403, "无写入权限")

        results = []
        success = 0
        failed = 0
        for rec_id in ids:
            item = {"id": rec_id, "ok": False, "reason_code": "", "message": ""}
            rec = env_model.browse(rec_id).exists()
            if not rec:
                item["reason_code"] = "NOT_FOUND"
                item["message"] = "记录不存在"
                failed += 1
                results.append(item)
                continue
            try:
                rec.check_access_rule("write")
                if rec_id in if_match_map:
                    expected = if_match_map.get(rec_id, "")
                    current = rec.write_date and rec.write_date.strftime("%Y-%m-%d %H:%M:%S") or ""
                    if current and expected and current != expected:
                        item["reason_code"] = "CONFLICT"
                        item["message"] = "Record changed"
                        failed += 1
                        results.append(item)
                        continue
                rec.write(safe_vals)
                item["ok"] = True
                item["reason_code"] = "OK"
                item["message"] = "updated"
                success += 1
            except AccessError:
                item["reason_code"] = "PERMISSION_DENIED"
                item["message"] = "无写入权限"
                failed += 1
            except Exception as exc:
                _logger.warning("api.data.batch failed model=%s id=%s err=%s", model, rec_id, exc)
                item["reason_code"] = "WRITE_FAILED"
                item["message"] = str(exc)
                failed += 1
            results.append(item)

        data = {
            "model": model,
            "action": action or "write",
            "values": safe_vals,
            "requested_ids": ids,
            "succeeded": success,
            "failed": failed,
            "results": results,
            "failed_preview": [item for item in results if not item.get("ok")][:preview_limit],
            "failed_truncated": max(0, failed - min(failed, preview_limit)),
            "idempotency_key": idempotency_key,
            "idempotency_fingerprint": idempotency_fingerprint,
            "idempotent_replay": False,
        }
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
