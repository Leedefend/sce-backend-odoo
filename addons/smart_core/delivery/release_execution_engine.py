# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields

from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .edition_release_snapshot_service import EditionReleaseSnapshotService
from .release_approval_policy_service import ReleaseApprovalPolicyService


RELEASE_EXECUTION_PROTOCOL_VERSION = "release_execution_protocol_v1"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class ReleaseExecutionEngine:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = EditionReleaseSnapshotService(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)
        self.approval_policy_service = ReleaseApprovalPolicyService(env)

    def now(self):
        return fields.Datetime.now()

    def _ts(self) -> str:
        value = self.now()
        return value.isoformat() if value else ""

    def _run(self, *, action, operation: str) -> dict[str, Any]:
        return {
            "contract_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
            "operation": _text(operation),
            "action_id": int(action.id or 0),
            "action_type": _text(action.action_type),
            "product_key": _text(action.product_key),
            "started_at": self._ts(),
            "completed_at": "",
            "state": "running",
            "reason_code": "",
            "steps": [],
        }

    def _step(self, *, key: str, label: str, state: str, reason_code: str = "", details: dict[str, Any] | None = None) -> dict[str, Any]:
        timestamp = self._ts()
        return {
            "key": _text(key),
            "label": _text(label),
            "state": _text(state) or "running",
            "reason_code": _text(reason_code),
            "started_at": timestamp,
            "completed_at": timestamp,
            "details": details if isinstance(details, dict) else {},
        }

    def _finish(self, run: dict[str, Any], *, state: str, reason_code: str = "") -> dict[str, Any]:
        run["state"] = _text(state) or "succeeded"
        run["reason_code"] = _text(reason_code)
        run["completed_at"] = self._ts()
        return run

    def run_approval(self, *, action, user, note: str = "", auto: bool = False) -> dict[str, Any]:
        run = self._run(action=action, operation="approve_action")
        allowed, reason_code, diagnostics = self.approval_policy_service.can_approve(action=action, user=user)
        run["steps"].append(
            self._step(
                key="approver_gate",
                label="Approver Gate",
                state="succeeded" if allowed else "failed",
                reason_code="OK" if allowed else reason_code,
                details=diagnostics,
            )
        )
        if not allowed:
            return self._finish(run, state="failed", reason_code=reason_code)

        self.approval_policy_service.approve_action(action=action, user=user, note=note, auto=auto)
        run["steps"].append(
            self._step(
                key="approval_apply",
                label="Apply Approval",
                state="succeeded",
                reason_code="OK",
                details={
                    "approval_state": _text(action.approval_state),
                    "approved_by_user_id": int(action.approved_by_user_id.id) if action.approved_by_user_id else 0,
                    "approval_mode": "auto" if auto else "manual",
                },
            )
        )
        return self._finish(run, state="succeeded", reason_code="OK")

    def execute_release_action(self, *, action, user) -> dict[str, Any]:
        run = self._run(action=action, operation=_text(action.action_type))
        executor_allowed, executor_reason, executor_diag = self.approval_policy_service.can_execute(action=action, user=user)
        run["steps"].append(
            self._step(
                key="executor_gate",
                label="Executor Gate",
                state="succeeded" if executor_allowed else "failed",
                reason_code="OK" if executor_allowed else executor_reason,
                details=executor_diag,
            )
        )
        if not executor_allowed:
            return {
                "status": "failed",
                "reason_code": executor_reason,
                "trace_run": self._finish(run, state="failed", reason_code=executor_reason),
                "diagnostics": {"approval": executor_diag},
            }

        approval_details = {"approval_required": bool(action.approval_required), "approval_state": _text(action.approval_state)}
        if bool(action.approval_required) and _text(action.approval_state) != "approved":
            allow_self_approval = bool((_dict(action.policy_snapshot_json)).get("allow_self_approval"))
            if allow_self_approval:
                approver_allowed, _, _ = self.approval_policy_service.can_approve(action=action, user=user)
                if approver_allowed:
                    approval_run = self.run_approval(action=action, user=user, note="auto approval during execution protocol", auto=True)
                    run["steps"].extend(list(approval_run.get("steps") or []))
                    approval_details["approval_state"] = _text(action.approval_state)
            if _text(action.approval_state) != "approved":
                run["steps"].append(
                    self._step(
                        key="approval_gate",
                        label="Approval Gate",
                        state="pending",
                        reason_code="APPROVAL_REQUIRED",
                        details=approval_details,
                    )
                )
                return {
                    "status": "pending_approval",
                    "reason_code": "APPROVAL_REQUIRED",
                    "trace_run": self._finish(run, state="pending", reason_code="APPROVAL_REQUIRED"),
                    "diagnostics": {"approval_state": _text(action.approval_state)},
                }

        run["steps"].append(
            self._step(
                key="approval_gate",
                label="Approval Gate",
                state="succeeded",
                reason_code="OK",
                details={"approval_state": _text(action.approval_state) or "not_required"},
            )
        )
        request_payload = action.request_payload_json if isinstance(action.request_payload_json, dict) else {}
        try:
            if _text(action.action_type) == "promote_snapshot":
                result = self.promotion_service.promote_to_released(
                    int(request_payload.get("snapshot_id") or action.target_snapshot_id.id or 0),
                    replace_active=bool(request_payload.get("replace_active", True)),
                    state_reason="release_execution_protocol_promoted",
                    promotion_note=_text(action.note) or "promoted by release execution protocol",
                )
            elif _text(action.action_type) == "rollback_snapshot":
                result = self.snapshot_service.rollback_to_snapshot(
                    product_key=_text(action.product_key),
                    target_snapshot_id=int(request_payload.get("target_snapshot_id") or action.target_snapshot_id.id or 0) or None,
                    note=_text(action.note) or "rollback by release execution protocol",
                )
            else:
                raise ValueError(f"UNSUPPORTED_RELEASE_ACTION_TYPE:{_text(action.action_type)}")
        except Exception as exc:
            run["steps"].append(
                self._step(
                    key="operation_execute",
                    label="Execute Operation",
                    state="failed",
                    reason_code=str(exc),
                    details={"operation": _text(action.action_type), "error": str(exc)},
                )
            )
            return {
                "status": "failed",
                "reason_code": str(exc),
                "trace_run": self._finish(run, state="failed", reason_code=str(exc)),
                "diagnostics": {"operation": _text(action.action_type), "error": str(exc)},
            }

        run["steps"].append(
            self._step(
                key="operation_execute",
                label="Execute Operation",
                state="succeeded",
                reason_code="OK",
                details={"operation": _text(action.action_type), "result_snapshot_id": int(result.get("id") or 0)},
            )
        )
        return {
            "status": "succeeded",
            "reason_code": "OK",
            "result": result,
            "trace_run": self._finish(run, state="succeeded", reason_code="OK"),
            "diagnostics": {"operation": _text(action.action_type)},
        }
