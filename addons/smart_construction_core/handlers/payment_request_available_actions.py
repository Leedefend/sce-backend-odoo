# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    failure_meta_for_reason,
)


class PaymentRequestAvailableActionsHandler(BaseIntentHandler):
    INTENT_TYPE = "payment.request.available_actions"
    DESCRIPTION = "Describe available payment request actions for current user"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    _ACTION_SPECS = [
        {
            "key": "submit",
            "label": "提交",
            "intent": "payment.request.submit",
            "method": "action_submit",
            "allowed_states": {"draft"},
            "delivery_priority": 10,
        },
        {
            "key": "approve",
            "label": "审批",
            "intent": "payment.request.approve",
            "method": "action_approve",
            "allowed_states": {"submit"},
            "delivery_priority": 20,
        },
        {
            "key": "reject",
            "label": "驳回",
            "intent": "payment.request.reject",
            "method": "action_on_tier_rejected",
            "allowed_states": {"submit"},
            "required_params": ["reason"],
            "delivery_priority": 30,
        },
        {
            "key": "done",
            "label": "完成",
            "intent": "payment.request.done",
            "method": "action_done",
            "allowed_states": {"approved"},
            "delivery_priority": 40,
        },
    ]
    _EXECUTE_INTENT = "payment.request.execute"
    _NEXT_STATE_HINT = {
        "submit": "submit",
        "approve": "approved",
        "reject": "draft",
        "done": "done",
    }
    _ACTION_ROLE_HINTS = {
        "submit": {
            "required_role_key": "finance",
            "required_role_label": "财务",
            "required_group_xmlid": "smart_construction_custom.group_sc_role_finance",
            "handoff_hint": "请由财务提交申请后进入审批链路。",
        },
        "approve": {
            "required_role_key": "executive",
            "required_role_label": "管理层",
            "required_group_xmlid": "smart_construction_custom.group_sc_role_executive",
            "handoff_hint": "请由管理层执行审批决策。",
        },
        "reject": {
            "required_role_key": "executive",
            "required_role_label": "管理层",
            "required_group_xmlid": "smart_construction_custom.group_sc_role_executive",
            "handoff_hint": "请由管理层执行驳回并填写原因。",
        },
        "done": {
            "required_role_key": "finance",
            "required_role_label": "财务",
            "required_group_xmlid": "smart_construction_custom.group_sc_role_finance",
            "handoff_hint": "审批完成后由财务确认办结。",
        },
    }

    def _current_user_group_xmlids(self) -> set[str]:
        groups = self.env.user.sudo().groups_id
        ext = groups.get_external_id() or {}
        return {str(xmlid).strip() for xmlid in ext.values() if str(xmlid or "").strip()}

    def _evaluate_prerequisites(self, record, action_key: str) -> tuple[bool, str]:
        key = str(action_key or "").strip()
        if key == "submit":
            if int(record._get_attachment_count() or 0) <= 0:
                return False, "PAYMENT_ATTACHMENTS_REQUIRED"
            if not record.contract_id:
                return False, REASON_MISSING_PARAMS
            if record.contract_id and str(record.contract_id.state or "") == "cancel":
                return False, REASON_BUSINESS_RULE_FAILED
            return True, REASON_OK
        if key == "approve":
            if str(record.validation_status or "") != "validated":
                return False, REASON_BUSINESS_RULE_FAILED
            return True, REASON_OK
        if key == "reject":
            return True, REASON_OK
        if key == "done":
            if str(record.validation_status or "") != "validated":
                return False, REASON_BUSINESS_RULE_FAILED
            if str(record.state or "") != "approved":
                return False, REASON_BUSINESS_RULE_FAILED
            if not bool(record.is_fully_paid):
                return False, REASON_BUSINESS_RULE_FAILED
            return True, REASON_OK
        return False, REASON_BUSINESS_RULE_FAILED

    def _trace_id(self) -> str:
        if isinstance(self.context, dict):
            value = str(self.context.get("trace_id") or "").strip()
            if value:
                return value
        return f"pay_req_actions_{uuid4().hex[:12]}"

    def _error(self, *, reason_code: str, message: str, trace_id: str, code: int):
        return {
            "ok": False,
            "data": {
                "success": False,
                "reason_code": reason_code,
                "message": str(message or ""),
            },
            "error": {
                "code": reason_code,
                "reason_code": reason_code,
                "message": str(message or ""),
                **failure_meta_for_reason(reason_code),
            },
            "code": int(code),
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id},
        }

    def _action_entry(self, record, spec: dict, *, user_group_xmlids: set[str] | None = None) -> dict:
        state = str(record.state or "")
        action_key = str(spec.get("key") or "")
        method_name = str(spec.get("method") or "")
        fn = getattr(record, method_name, None)
        method_ok = callable(fn)
        state_ok = state in set(spec.get("allowed_states") or [])
        precheck_ok, precheck_reason = self._evaluate_prerequisites(record, action_key)
        allowed = bool(method_ok and state_ok and precheck_ok)
        if allowed:
            reason_code = REASON_OK
        elif not method_ok or not state_ok:
            reason_code = REASON_BUSINESS_RULE_FAILED
        else:
            reason_code = precheck_reason or REASON_BUSINESS_RULE_FAILED
        reason_meta = failure_meta_for_reason(reason_code)
        blocked_message = ""
        suggested_action = ""
        if not allowed:
            blocked_message = str(reason_meta.get("message") or reason_code)
            suggested_action = str(reason_meta.get("suggested_action") or "")
        execute_payload = {
            "id": int(record.id or 0),
            "action": action_key,
        }
        required_params = list(spec.get("required_params") or [])
        role_hint = self._ACTION_ROLE_HINTS.get(action_key) or {}
        required_group_xmlid = str(role_hint.get("required_group_xmlid") or "")
        actor_matches_required_role = bool(required_group_xmlid and required_group_xmlid in (user_group_xmlids or set()))
        handoff_required = bool(required_group_xmlid and not actor_matches_required_role)
        return {
            "key": action_key,
            "label": str(spec.get("label") or ""),
            "intent": str(spec.get("intent") or ""),
            "method": method_name,
            "required_params": required_params,
            "allowed": allowed,
            "reason_code": reason_code,
            "state_required": sorted(list(spec.get("allowed_states") or [])),
            "current_state": state,
            "next_state_hint": self._NEXT_STATE_HINT.get(action_key, ""),
            "allowed_by_state": bool(state_ok),
            "allowed_by_method": bool(method_ok),
            "allowed_by_precheck": bool(precheck_ok),
            "execute_intent": self._EXECUTE_INTENT,
            "execute_params": execute_payload,
            "idempotency_required": True,
            "requires_reason": "reason" in required_params,
            "blocked_message": blocked_message,
            "suggested_action": suggested_action,
            "required_role_key": str(role_hint.get("required_role_key") or ""),
            "required_role_label": str(role_hint.get("required_role_label") or ""),
            "required_group_xmlid": required_group_xmlid,
            "handoff_hint": str(role_hint.get("handoff_hint") or ""),
            "actor_matches_required_role": actor_matches_required_role,
            "handoff_required": handoff_required,
            "delivery_priority": int(spec.get("delivery_priority") or 100),
        }

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}

        trace_id = self._trace_id()
        raw_id = params.get("id") or params.get("payment_request_id") or params.get("res_id")
        try:
            payment_request_id = int(raw_id)
        except Exception:
            payment_request_id = 0
        if payment_request_id <= 0:
            return self._error(
                reason_code=REASON_MISSING_PARAMS,
                message="missing id/payment_request_id",
                trace_id=trace_id,
                code=400,
            )

        record = self.env["payment.request"].browse(payment_request_id).exists()
        if not record:
            return self._error(
                reason_code=REASON_NOT_FOUND,
                message="payment request not found",
                trace_id=trace_id,
                code=404,
            )

        user_group_xmlids = self._current_user_group_xmlids()
        actions = [self._action_entry(record, spec, user_group_xmlids=user_group_xmlids) for spec in self._ACTION_SPECS]
        primary_action_key = ""
        for item in actions:
            if bool(item.get("allowed")):
                primary_action_key = str(item.get("key") or "")
                break
        return {
            "ok": True,
            "data": {
                "success": True,
                "reason_code": REASON_OK,
                "payment_request": {
                    "id": int(record.id),
                    "name": str(record.name or ""),
                    "state": str(record.state or ""),
                    "type": str(record.type or ""),
                },
                "actions": actions,
                "primary_action_key": primary_action_key,
            },
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id},
        }
