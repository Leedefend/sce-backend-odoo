# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from uuid import uuid4

from odoo.exceptions import AccessError
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.project_context import (
    project_scope_denied_response,
)
try:
    from odoo.addons.smart_core.core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - standalone boundary-test fallback
    from odoo.addons.smart_core.core.project_context import record_in_project_scope, selected_project_id_from_context

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_project_id_from_context(params, context))
from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
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

    SOURCE_AUTHORITY = {
        "kind": "payment_request_action_availability_projection",
        "authorities": [
            "payment.request",
            "tier.review",
            "res.groups",
            "ir.model.access",
            "ir.rule",
            "odoo.orm",
        ],
        "projection_only": True,
        "runtime_carrier": "payment_request_available_actions_contract",
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
        groups = self.env.user.groups_id
        ext = groups.get_external_id() or {}
        return {str(xmlid).strip() for xmlid in ext.values() if str(xmlid or "").strip()}

    def _reason_from_exception(self, exc: Exception) -> str:
        match = re.search(r"\[SC_GUARD:([A-Z0-9_]+)\]", str(exc or ""))
        if match:
            return str(match.group(1) or "").strip().upper() or REASON_BUSINESS_RULE_FAILED
        return REASON_BUSINESS_RULE_FAILED

    def _evaluate_prerequisites(self, record, action_key: str) -> tuple[bool, str]:
        key = str(action_key or "").strip()
        if key == "submit":
            if not record.contract_id:
                return False, REASON_MISSING_PARAMS
            if record.contract_id and str(record.contract_id.state or "") == "cancel":
                return False, REASON_BUSINESS_RULE_FAILED
            advisories = record._collect_payment_advisories("submit") if hasattr(record, "_collect_payment_advisories") else []
            blocking = [item for item in advisories if item.get("force_block_enabled")]
            if blocking:
                return False, str(blocking[0].get("reason_code") or REASON_BUSINESS_RULE_FAILED)
            return True, REASON_OK
        if key == "approve":
            validation_status = str(record.validation_status or "").strip()
            no_tier_review = validation_status in ("", "no") and not record.review_ids
            if validation_status not in ("waiting", "pending", "validated") and not no_tier_review:
                return False, REASON_BUSINESS_RULE_FAILED
            advisories = record._collect_payment_advisories("approve") if hasattr(record, "_collect_payment_advisories") else []
            blocking = [item for item in advisories if item.get("force_block_enabled")]
            if blocking:
                return False, str(blocking[0].get("reason_code") or REASON_BUSINESS_RULE_FAILED)
            return True, REASON_OK
        if key == "reject":
            return True, REASON_OK
        if key == "done":
            if str(record.validation_status or "") != "validated":
                return False, REASON_BUSINESS_RULE_FAILED
            if str(record.state or "") != "approved":
                return False, REASON_BUSINESS_RULE_FAILED
            advisories = record._collect_payment_advisories("done") if hasattr(record, "_collect_payment_advisories") else []
            blocking = [item for item in advisories if item.get("force_block_enabled")]
            if blocking:
                return False, str(blocking[0].get("reason_code") or REASON_BUSINESS_RULE_FAILED)
            return True, REASON_OK
        return False, REASON_BUSINESS_RULE_FAILED

    def _advisories_for_action(self, record, action_key: str) -> list[dict]:
        key = str(action_key or "").strip()
        if key not in {"submit", "approve", "done"} or not hasattr(record, "_collect_payment_advisories"):
            return []
        try:
            return list(record._collect_payment_advisories(key) or [])
        except Exception:
            return []

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
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id, "source_authority": self.SOURCE_AUTHORITY},
        }

    def _action_entry(self, record, spec: dict, *, user_group_xmlids: set[str] | None = None) -> dict:
        state = str(record.state or "")
        action_key = str(spec.get("key") or "")
        method_name = str(spec.get("method") or "")
        fn = getattr(record, method_name, None)
        method_ok = callable(fn)
        state_ok = state in set(spec.get("allowed_states") or [])
        advisories = self._advisories_for_action(record, action_key)
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
        warning_message = ""
        advisory_reason_codes = [
            str(item.get("reason_code") or "").strip()
            for item in advisories
            if str(item.get("reason_code") or "").strip()
        ]
        if allowed and advisories:
            warning_message = "\n".join(
                str(item.get("message") or item.get("reason_code") or "").strip()
                for item in advisories
                if str(item.get("message") or item.get("reason_code") or "").strip()
            )
            suggested_action = str(advisories[0].get("suggested_action") or "")
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
            "warning_message": warning_message,
            "advisory_warnings": advisories,
            "advisory_reason_codes": advisory_reason_codes,
            "force_block_available": bool(advisories),
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

        PaymentRequest = self.env["payment.request"]
        if not PaymentRequest.check_access_rights("read", raise_exception=False):
            return self._error(
                reason_code=REASON_PERMISSION_DENIED,
                message="permission denied",
                trace_id=trace_id,
                code=403,
            )
        record = PaymentRequest.browse(payment_request_id).exists()
        if not record:
            return self._error(
                reason_code=REASON_NOT_FOUND,
                message="payment request not found",
                trace_id=trace_id,
                code=404,
            )
        try:
            record.check_access_rule("read")
        except AccessError:
            return self._error(
                reason_code=REASON_PERMISSION_DENIED,
                message="permission denied",
                trace_id=trace_id,
                code=403,
            )
        in_scope, scope_meta = record_in_business_scope(
            PaymentRequest,
            payment_request_id,
            params,
            self.context if isinstance(self.context, dict) else {},
        )
        if not in_scope:
            return project_scope_denied_response(scope_meta)

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
            "meta": {"intent": self.INTENT_TYPE, "trace_id": trace_id, "source_authority": self.SOURCE_AUTHORITY},
        }
