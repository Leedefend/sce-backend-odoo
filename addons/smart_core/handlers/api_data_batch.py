# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, List

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

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = str(params.get("model") or "").strip()
        ids = self._get_ids(params)
        action, vals = self._resolve_vals(params)
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
        }
        meta = {"trace_id": trace_id, "write_mode": "batch", "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
