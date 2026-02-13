# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_REPLAY_WINDOW_EXPIRED,
    REASON_SYSTEM_ERROR,
    failure_meta_for_reason,
)
from odoo.addons.smart_core.utils.idempotency import (
    apply_idempotency_identity,
    build_idempotency_conflict_response,
    build_idempotency_fingerprint,
    enrich_replay_contract,
    normalize_request_id,
    replay_window_seconds,
    resolve_idempotency_decision,
)
from odoo.exceptions import AccessError, UserError


class _BasePaymentApprovalHandler(BaseIntentHandler):
    ETAG_ENABLED = False
    IDEMPOTENCY_WINDOW_SECONDS = 120
    AUDIT_EVENT_CODE = ""
    ACTION_METHOD = ""
    ACTION_NAME = ""

    def _trace_id(self) -> str:
        if isinstance(self.context, dict):
            return str(self.context.get("trace_id") or "")
        return ""

    def _request_identity(self, params: dict) -> tuple[str, str, str]:
        request_id = normalize_request_id(params.get("request_id"), prefix="pay_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        trace_id = self._trace_id() or f"pay_req_{uuid4().hex[:12]}"
        return request_id, idempotency_key, trace_id

    def _idempotency_window_seconds(self) -> int:
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="PAYMENT_REQUEST_APPROVAL_REPLAY_WINDOW_SEC",
        )

    def _idempotency_fingerprint(self, *, payment_request_id: int, idempotency_key: str) -> str:
        payload = {
            "intent": self.INTENT_TYPE,
            "event_code": self.AUDIT_EVENT_CODE,
            "action": self.ACTION_NAME,
            "method": self.ACTION_METHOD,
            "db": self.env.cr.dbname,
            "user_id": int(self.env.user.id or 0),
            "company_id": int(self.env.user.company_id.id or 0) if self.env.user and self.env.user.company_id else 0,
            "payment_request_id": int(payment_request_id or 0),
            "idempotency_key": str(idempotency_key or ""),
        }
        return build_idempotency_fingerprint(payload)

    def _error_response(
        self,
        *,
        reason_code: str,
        message: str,
        request_id: str,
        idempotency_key: str,
        idempotency_fingerprint: str,
        trace_id: str,
        status_code: int,
    ):
        data = {
            "success": False,
            "reason_code": reason_code,
            "message": str(message or ""),
            "status_code": int(status_code),
            "intent_action": self.ACTION_NAME,
        }
        data = apply_idempotency_identity(
            data,
            request_id=request_id,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            trace_id=trace_id,
        )
        data = enrich_replay_contract(
            data,
            idempotent_replay=False,
            replay_window_expired=False,
            replay_reason_code="",
            include_replay_evidence=True,
        )
        return {
            "ok": False,
            "data": data,
            "error": {
                "code": reason_code,
                "reason_code": reason_code,
                "message": str(message or ""),
                **failure_meta_for_reason(reason_code),
            },
            "code": int(status_code),
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id},
        }

    def _conflict_response(self, *, request_id: str, idempotency_key: str, idempotency_fingerprint: str, trace_id: str):
        payload = build_idempotency_conflict_response(
            intent_type=self.INTENT_TYPE,
            request_id=request_id,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            include_replay_evidence=True,
        )
        data = payload.setdefault("data", {})
        data["idempotency_fingerprint"] = str(idempotency_fingerprint or "")
        data["intent_action"] = self.ACTION_NAME
        payload.setdefault("meta", {})["trace_id"] = trace_id
        return payload

    def _write_audit(self, *, payment_request_id: int, trace_id: str, idempotency_key: str, idempotency_fingerprint: str, result: dict):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.sudo().write_event(
                event_code=self.AUDIT_EVENT_CODE,
                model="payment.request",
                res_id=int(payment_request_id or 0),
                action=self.ACTION_NAME,
                after={
                    "idempotency_key": str(idempotency_key or ""),
                    "idempotency_fingerprint": str(idempotency_fingerprint or ""),
                    "replay_result": result,
                },
                reason="payment request approval intent",
                trace_id=str(trace_id or ""),
                company_id=self.env.user.company_id.id if self.env.user and self.env.user.company_id else None,
            )
        except Exception:
            return

    def _build_success_data(self, payment_request, action_result, *, replay_window_expired: bool) -> dict:
        reason_code = REASON_REPLAY_WINDOW_EXPIRED if replay_window_expired else REASON_OK
        success_data = {
            "success": True,
            "reason_code": reason_code,
            "message": "request accepted" if not replay_window_expired else "request accepted after replay window",
            "intent_action": self.ACTION_NAME,
            "payment_request": {
                "id": int(payment_request.id),
                "name": str(payment_request.name or ""),
                "state": str(payment_request.state or ""),
                "type": str(payment_request.type or ""),
                "amount": float(payment_request.amount or 0.0),
                "currency_id": int(payment_request.currency_id.id or 0) if payment_request.currency_id else 0,
                "project_id": int(payment_request.project_id.id or 0) if payment_request.project_id else 0,
            },
            "action_result": action_result if isinstance(action_result, dict) else {},
        }
        if replay_window_expired:
            success_data["replay_window_reason_code"] = REASON_REPLAY_WINDOW_EXPIRED
        return success_data

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        raw_id = params.get("id") or params.get("payment_request_id") or params.get("res_id")
        try:
            payment_request_id = int(raw_id)
        except Exception:
            payment_request_id = 0

        request_id, idempotency_key, trace_id = self._request_identity(params)
        idempotency_fingerprint = self._idempotency_fingerprint(
            payment_request_id=payment_request_id,
            idempotency_key=idempotency_key,
        )

        if payment_request_id <= 0:
            return self._error_response(
                reason_code=REASON_MISSING_PARAMS,
                message="missing id/payment_request_id",
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                status_code=400,
            )

        payment_request = self.env["payment.request"].browse(payment_request_id).exists()
        if not payment_request:
            return self._error_response(
                reason_code=REASON_NOT_FOUND,
                message="payment request not found",
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                status_code=404,
            )

        decision = resolve_idempotency_decision(
            self.env,
            event_code=self.AUDIT_EVENT_CODE,
            idempotency_key=idempotency_key,
            fingerprint=idempotency_fingerprint,
            window_seconds=self._idempotency_window_seconds(),
            replay_payload_key="replay_result",
            limit=20,
            recent_extra_domain=[
                ("model", "=", "payment.request"),
                ("res_id", "=", int(payment_request_id)),
                ("action", "=", self.ACTION_NAME),
            ],
        )

        if decision.get("conflict"):
            return self._conflict_response(
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
            )

        replay_payload = decision.get("replay_payload") or {}
        replay_entry = decision.get("replay_entry") or {}
        if replay_payload:
            replay_data = dict(replay_payload)
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
            return {"ok": True, "data": replay_data, "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id}}

        replay_window_expired = bool(decision.get("replay_window_expired"))

        try:
            method = getattr(payment_request, self.ACTION_METHOD)
            action_result = method()
            data = self._build_success_data(
                payment_request,
                action_result,
                replay_window_expired=replay_window_expired,
            )
            data = apply_idempotency_identity(
                data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
            )
            data = enrich_replay_contract(
                data,
                idempotent_replay=False,
                replay_window_expired=replay_window_expired,
                replay_reason_code=REASON_REPLAY_WINDOW_EXPIRED if replay_window_expired else "",
                include_replay_evidence=True,
            )
            self._write_audit(
                payment_request_id=payment_request_id,
                trace_id=trace_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                result=data,
            )
            return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id}}
        except AccessError as exc:
            return self._error_response(
                reason_code=REASON_PERMISSION_DENIED,
                message=str(exc) or "permission denied",
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                status_code=403,
            )
        except UserError as exc:
            return self._error_response(
                reason_code=REASON_BUSINESS_RULE_FAILED,
                message=str(exc) or "business rule failed",
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                status_code=400,
            )
        except Exception:
            return self._error_response(
                reason_code=REASON_SYSTEM_ERROR,
                message="payment request approval intent failed",
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                status_code=500,
            )


class PaymentRequestSubmitHandler(_BasePaymentApprovalHandler):
    INTENT_TYPE = "payment.request.submit"
    DESCRIPTION = "Submit payment request via canonical intent contract"
    VERSION = "1.0.0"
    AUDIT_EVENT_CODE = "PAYMENT_REQUEST_SUBMIT_INTENT"
    ACTION_METHOD = "action_submit"
    ACTION_NAME = "submit"


class PaymentRequestApproveHandler(_BasePaymentApprovalHandler):
    INTENT_TYPE = "payment.request.approve"
    DESCRIPTION = "Approve payment request via canonical intent contract"
    VERSION = "1.0.0"
    AUDIT_EVENT_CODE = "PAYMENT_REQUEST_APPROVE_INTENT"
    ACTION_METHOD = "action_approve"
    ACTION_NAME = "approve"
