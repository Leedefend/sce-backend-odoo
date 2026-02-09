# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_unlink.py
# Minimal unlink intent for portal relational MVP

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
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_SOURCE,
    failure_meta_for_reason,
)

_logger = logging.getLogger(__name__)


class ApiDataUnlinkHandler(BaseIntentHandler):
    """
    Intent: api.data.unlink
    - 限定 model=project.task
    - 返回删除 ids
    """

    INTENT_TYPE = "api.data.unlink"
    DESCRIPTION = "Portal Shell minimal unlink intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False
    IDEMPOTENCY_WINDOW_SECONDS = 120
    IDEMPOTENCY_EVENT_CODE = "API_DATA_UNLINK"

    ALLOWED_MODELS = {"project.task"}

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
            env_key="API_DATA_UNLINK_REPLAY_WINDOW_SEC",
        )

    def _idempotency_fingerprint(self, *, model: str, ids: List[int], dry_run: bool, idem_key: str):
        payload = {
            "intent": self.INTENT_TYPE,
            "model": str(model or ""),
            "ids": list(ids or []),
            "dry_run": bool(dry_run),
            "idempotency_key": str(idem_key or ""),
        }
        return build_idempotency_fingerprint(payload, normalize_id_keys=["ids"])

    def _write_idempotency_audit(self, *, trace_id: str, model: str, ids: List[int], idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.sudo().write_event(
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                model=model,
                res_id=0,
                action="unlink",
                after={
                    "idempotency_key": idem_key,
                    "idempotency_fingerprint": idem_fingerprint,
                    "result": result,
                    "ids": list(ids or []),
                },
                reason="api.data.unlink idempotency",
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

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_ids(self, params: Dict[str, Any]) -> List[int]:
        ids = params.get("ids") or params.get("record_ids") or []
        if isinstance(ids, list):
            return [int(v) for v in ids if v is not None]
        try:
            return [int(ids)]
        except Exception:
            return []

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = self._get_model(params)
        if not model:
            return self._err(400, "缺少参数 model", REASON_MISSING_PARAMS)
        if model not in self.ALLOWED_MODELS:
            return self._err(403, f"模型不允许删除: {model}", REASON_UNSUPPORTED_SOURCE)
        if model not in self.env:
            return self._err(404, f"未知模型: {model}", REASON_NOT_FOUND)

        ids = self._get_ids(params)
        dry_run = bool(params.get("dry_run"))
        if not ids:
            return self._err(400, "缺少参数 ids", REASON_MISSING_PARAMS)

        env_model = self.env[model]
        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""
        request_id = normalize_request_id(params.get("request_id"), prefix="adu_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        idempotency_fingerprint = self._idempotency_fingerprint(
            model=model,
            ids=ids,
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
                    "ids": ids,
                    "model": model,
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
                meta = {"trace_id": trace_id, "write_mode": "unlink", "source": "portal-shell"}
                return {"ok": True, "data": data, "meta": meta}

        recs = env_model.browse(ids).exists()
        if not recs:
            return self._err(404, "记录不存在", REASON_NOT_FOUND)

        try:
            env_model.check_access_rights("unlink")
            recs.check_access_rule("unlink")
            if not dry_run:
                recs.unlink()
        except AccessError as ae:
            _logger.warning("api.data.unlink AccessError on %s: %s", model, ae)
            return self._err(403, "无删除权限", REASON_PERMISSION_DENIED)
        except Exception as e:
            _logger.exception("api.data.unlink failed on %s", model)
            return self._err(500, str(e), REASON_SYSTEM_ERROR)

        data = {"ids": ids, "model": model, "dry_run": dry_run}
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
            ids=ids,
            idem_key=idempotency_key,
            idem_fingerprint=idempotency_fingerprint,
            result=data,
        )
        meta = {"trace_id": trace_id, "write_mode": "unlink", "source": "portal-shell"}
        return {"ok": True, "data": data, "meta": meta}
