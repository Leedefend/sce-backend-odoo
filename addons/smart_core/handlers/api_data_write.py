# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_write.py
# v0.6: Minimal write intent (create/update) for project.project

import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..utils.idempotency import (
    apply_idempotency_identity,
    build_idempotency_conflict_response,
    build_idempotency_fingerprint,
    find_recent_audit_entry,
    normalize_request_id,
    replay_window_seconds,
)
from ..utils.reason_codes import (
    REASON_CONFLICT,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_SOURCE,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)

_logger = logging.getLogger(__name__)


class ApiDataWriteHandler(BaseIntentHandler):
    """
    Intent: api.data.create / api.data.write
    - 限定 model=project.project
    - 字段白名单写入
    - 返回固定写入契约
    """

    INTENT_TYPE = "api.data.create"
    ALIASES = ["api.data.write"]
    DESCRIPTION = "Portal Shell v0.6 minimal write intent (create/update)"
    VERSION = "0.6.0"
    ETAG_ENABLED = False
    IDEMPOTENCY_WINDOW_SECONDS = 120
    IDEMPOTENCY_EVENT_CODE = "API_DATA_WRITE"

    ALLOWED_MODELS = {
        "project.project": {"name", "description", "date_start"},
        "project.task": {"name", "description", "date_deadline", "project_id"},
    }

    def _err(self, code: int, message: str, reason_code: str):
        return {
            "ok": False,
            "error": {
                "code": reason_code,
                "message": message,
                "reason_code": reason_code,
                **failure_meta_for_reason(reason_code),
            },
            "code": code,
        }

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="API_DATA_WRITE_REPLAY_WINDOW_SEC",
        )

    def _idempotency_fingerprint(self, *, intent: str, model: str, record_id: int, vals: Dict[str, Any], dry_run: bool, idem_key: str):
        payload = {
            "intent": str(intent or ""),
            "model": str(model or ""),
            "record_id": int(record_id or 0),
            "vals": dict(vals or {}),
            "dry_run": bool(dry_run),
            "idempotency_key": str(idem_key or ""),
        }
        return build_idempotency_fingerprint(payload)

    def _write_idempotency_audit(self, *, trace_id: str, model: str, res_id: int, action: str, idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.sudo().write_event(
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                model=model,
                res_id=int(res_id or 0),
                action=action or "write",
                after={
                    "idempotency_key": idem_key,
                    "idempotency_fingerprint": idem_fingerprint,
                    "result": result,
                },
                reason="api.data.write idempotency",
                trace_id=trace_id or "",
                company_id=self.env.user.company_id.id if self.env.user and self.env.user.company_id else None,
            )
        except Exception:
            return

    def _idempotency_conflict_response(self, *, request_id: str, idempotency_key: str, idempotency_fingerprint: str, trace_id: str):
        result = build_idempotency_conflict_response(
            intent_type=self.INTENT_TYPE,
            request_id=request_id,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            include_replay_evidence=False,
        )
        data = result.setdefault("data", {})
        data["idempotency_fingerprint"] = str(idempotency_fingerprint or "")
        data["replay_supported"] = False
        meta = result.setdefault("meta", {})
        meta["trace_id"] = str(trace_id or "")
        return result

    def _with_idempotency_contract(self, data: Dict[str, Any], *, request_id: str, idempotency_key: str, idempotency_fingerprint: str, trace_id: str, deduplicated: bool):
        contract = apply_idempotency_identity(
            data,
            request_id=request_id,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            trace_id=trace_id,
        )
        contract["idempotent_replay"] = False
        contract["replay_supported"] = False
        contract["replay_window_expired"] = False
        contract["idempotency_replay_reason_code"] = ""
        contract["idempotency_deduplicated"] = bool(deduplicated)
        return contract

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = params.get("context")
        return ctx if isinstance(ctx, dict) else {}

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_vals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vals = params.get("vals") or params.get("values") or {}
        return vals if isinstance(vals, dict) else {}

    def _get_if_match(self, params: Dict[str, Any]) -> str:
        return str(params.get("if_match") or params.get("ifMatch") or params.get("write_date") or "").strip()

    def _get_id(self, params: Dict[str, Any]) -> int:
        for key in ("id", "record_id"):
            if key in params:
                try:
                    return int(params.get(key))
                except Exception:
                    return 0
        ids = params.get("ids")
        if isinstance(ids, list) and ids:
            try:
                return int(ids[0])
            except Exception:
                return 0
        return 0

    def _filter_vals(self, vals: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in vals.items() if k in self.ALLOWED_FIELDS}

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        intent = (payload.get("intent") or "").strip().lower()
        model = self._get_model(params)

        if not model:
            return self._err(400, "缺少参数 model", REASON_MISSING_PARAMS)
        allowed_fields = self.ALLOWED_MODELS.get(model)
        if not allowed_fields:
            return self._err(403, f"模型不允许写入: {model}", REASON_UNSUPPORTED_SOURCE)
        if model not in self.env:
            return self._err(404, f"未知模型: {model}", REASON_NOT_FOUND)

        vals = self._get_vals(params)
        dry_run = bool(params.get("dry_run"))
        if not vals:
            return self._err(400, "缺少参数 vals", REASON_MISSING_PARAMS)

        illegal_fields = sorted(set(vals.keys()) - allowed_fields)
        if illegal_fields:
            return self._err(400, f"字段不允许写入: {', '.join(illegal_fields)}", REASON_USER_ERROR)

        safe_vals = {k: v for k, v in vals.items() if k in allowed_fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段", REASON_USER_ERROR)

        context = self._get_context(params)
        env_model = self.env[model].with_context(context)

        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""
        request_id = normalize_request_id(params.get("request_id"), prefix="adw_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id

        if intent == "api.data.write":
            record_id = self._get_id(params)
            if not record_id:
                return self._err(400, "缺少参数 id", REASON_MISSING_PARAMS)

            rec = env_model.browse(record_id).exists()
            if not rec:
                return self._err(404, "记录不存在", REASON_NOT_FOUND)

            idempotency_fingerprint = self._idempotency_fingerprint(
                intent=intent,
                model=model,
                record_id=record_id,
                vals=safe_vals,
                dry_run=dry_run,
                idem_key=idempotency_key,
            )
            recent_entry = find_recent_audit_entry(
                self.env,
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                idempotency_key=idempotency_key,
                window_seconds=self._idempotency_window_seconds(),
                limit=20,
                extra_domain=[("model", "=", model)],
            )
            if recent_entry:
                payload_after = recent_entry.get("payload") or {}
                recent_fingerprint = str(payload_after.get("idempotency_fingerprint") or "")
                if recent_fingerprint and recent_fingerprint != idempotency_fingerprint:
                    return self._idempotency_conflict_response(
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                    )
                if recent_fingerprint and recent_fingerprint == idempotency_fingerprint:
                    replay_result = payload_after.get("result")
                    base_data = replay_result if isinstance(replay_result, dict) else {
                        "id": rec.id,
                        "model": model,
                        "written_fields": sorted(safe_vals.keys()),
                        "values": safe_vals,
                        "dry_run": dry_run,
                    }
                    data = self._with_idempotency_contract(
                        base_data,
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                        deduplicated=True,
                    )
                    meta = {"trace_id": trace_id, "write_mode": "update", "source": "portal-shell"}
                    return {"ok": True, "data": data, "meta": meta}

            try:
                if_match = self._get_if_match(params)
                if if_match:
                    current = rec.write_date and rec.write_date.strftime("%Y-%m-%d %H:%M:%S") or ""
                    if current and current != if_match:
                        return self._err(409, "Record changed", REASON_CONFLICT)
                env_model.check_access_rights("write")
                rec.check_access_rule("write")
                if not dry_run:
                    rec.write(safe_vals)
            except AccessError as ae:
                _logger.warning("api.data.write AccessError on %s: %s", model, ae)
                return self._err(403, "无写入权限", REASON_PERMISSION_DENIED)
            except Exception as e:
                _logger.exception("api.data.write failed on %s", model)
                return self._err(500, str(e), REASON_SYSTEM_ERROR)

            data = {
                "id": rec.id,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
                "dry_run": dry_run,
            }
            data = self._with_idempotency_contract(
                data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                deduplicated=False,
            )
            self._write_idempotency_audit(
                trace_id=trace_id,
                model=model,
                res_id=rec.id,
                action="write",
                idem_key=idempotency_key,
                idem_fingerprint=idempotency_fingerprint,
                result=data,
            )
            meta = {"trace_id": trace_id, "write_mode": "update", "source": "portal-shell"}
            return {"ok": True, "data": data, "meta": meta}

        if intent == "api.data.create":
            idempotency_fingerprint = self._idempotency_fingerprint(
                intent=intent,
                model=model,
                record_id=0,
                vals=safe_vals,
                dry_run=dry_run,
                idem_key=idempotency_key,
            )
            recent_entry = find_recent_audit_entry(
                self.env,
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                idempotency_key=idempotency_key,
                window_seconds=self._idempotency_window_seconds(),
                limit=20,
                extra_domain=[("model", "=", model)],
            )
            if recent_entry:
                payload_after = recent_entry.get("payload") or {}
                recent_fingerprint = str(payload_after.get("idempotency_fingerprint") or "")
                if recent_fingerprint and recent_fingerprint != idempotency_fingerprint:
                    return self._idempotency_conflict_response(
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                    )
                if recent_fingerprint and recent_fingerprint == idempotency_fingerprint:
                    replay_result = payload_after.get("result")
                    base_data = replay_result if isinstance(replay_result, dict) else {
                        "id": 0,
                        "model": model,
                        "written_fields": sorted(safe_vals.keys()),
                        "values": safe_vals,
                        "dry_run": dry_run,
                    }
                    data = self._with_idempotency_contract(
                        base_data,
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                        deduplicated=True,
                    )
                    meta = {"trace_id": trace_id, "write_mode": "create", "source": "portal-shell"}
                    return {"ok": True, "data": data, "meta": meta}

            try:
                env_model.check_access_rights("create")
                rec = env_model.create(safe_vals) if not dry_run else None
            except AccessError as ae:
                _logger.warning("api.data.create AccessError on %s: %s", model, ae)
                return self._err(403, "无创建权限", REASON_PERMISSION_DENIED)
            except Exception as e:
                _logger.exception("api.data.create failed on %s", model)
                return self._err(500, str(e), REASON_SYSTEM_ERROR)

            data = {
                "id": rec.id if rec else 0,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
                "dry_run": dry_run,
            }
            data = self._with_idempotency_contract(
                data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                deduplicated=False,
            )
            self._write_idempotency_audit(
                trace_id=trace_id,
                model=model,
                res_id=rec.id if rec else 0,
                action="create",
                idem_key=idempotency_key,
                idem_fingerprint=idempotency_fingerprint,
                result=data,
            )
            meta = {"trace_id": trace_id, "write_mode": "create", "source": "portal-shell"}
            return {"ok": True, "data": data, "meta": meta}

        return self._err(400, f"未知写入意图: {intent}", REASON_UNSUPPORTED_SOURCE)
