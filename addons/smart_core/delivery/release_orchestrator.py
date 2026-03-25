# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields

from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .edition_release_snapshot_service import EditionReleaseSnapshotService
from .release_approval_policy_service import ReleaseApprovalPolicyService


def _text(value: Any) -> str:
    return str(value or "").strip()


class ReleaseOrchestrator:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = EditionReleaseSnapshotService(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)
        self.approval_policy_service = ReleaseApprovalPolicyService(env)

    def _action_model(self):
        return self.env["sc.release.action"].sudo()

    def _snapshot_model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

    def _load_action(self, action_id: int):
        rec = self._action_model().browse(int(action_id))
        if not rec.exists() or not rec.active:
            raise ValueError("RELEASE_ACTION_NOT_FOUND")
        return rec

    def now(self):
        return fields.Datetime.now()

    def _release_identity(self, *, product_key: str) -> dict[str, str]:
        product = _text(product_key)
        if "." in product:
            base_product_key, edition_key = product.split(".", 1)
        else:
            base_product_key, edition_key = "construction", "standard"
        return {
            "product_key": product,
            "base_product_key": _text(base_product_key) or "construction",
            "edition_key": _text(edition_key) or "standard",
        }

    def _active_released_snapshot(self, *, product_key: str):
        return self._snapshot_model().search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )

    def _create_action(
        self,
        *,
        action_type: str,
        product_key: str,
        target_snapshot_id: int | None,
        note: str,
        request_payload: dict[str, Any],
    ):
        identity = self._release_identity(product_key=product_key)
        active = self._active_released_snapshot(product_key=identity["product_key"])
        policy_fields = self.approval_policy_service.build_action_policy(
            action_type=action_type,
            product_key=identity["product_key"],
            user=self.env.user,
        )
        return self._action_model().create(
            {
                "name": f"{action_type}:{identity['product_key']}",
                "action_type": action_type,
                "state": "pending",
                "product_key": identity["product_key"],
                "base_product_key": identity["base_product_key"],
                "edition_key": identity["edition_key"],
                "requested_by_user_id": int(self.env.user.id) if self.env.user else False,
                "requested_at": self.now(),
                "source_snapshot_id": int(active.id) if active else False,
                "target_snapshot_id": int(target_snapshot_id or 0) or False,
                "note": _text(note),
                "request_payload_json": request_payload if isinstance(request_payload, dict) else {},
                "result_payload_json": {"status": "pending"},
                "diagnostics_json": {"orchestrator": "release_orchestrator_v1", "status": "pending"},
                **policy_fields,
            }
        )

    def _mark_running(self, action) -> None:
        action.write({"state": "running", "executed_at": self.now()})

    def _mark_succeeded(self, action, *, result_snapshot_id: int | None, result_payload: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
        action.write(
            {
                "state": "succeeded",
                "completed_at": self.now(),
                "result_snapshot_id": int(result_snapshot_id or 0) or False,
                "reason_code": "OK",
                "result_payload_json": result_payload if isinstance(result_payload, dict) else {},
                "diagnostics_json": diagnostics if isinstance(diagnostics, dict) else {},
            }
        )
        return action.to_runtime_dict()

    def _mark_failed(self, action, *, reason_code: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
        action.write(
            {
                "state": "failed",
                "completed_at": self.now(),
                "reason_code": _text(reason_code),
                "diagnostics_json": diagnostics if isinstance(diagnostics, dict) else {},
            }
        )
        return action.to_runtime_dict()

    def _mark_pending_approval(self, action, *, diagnostics: dict[str, Any]) -> dict[str, Any]:
        merged_diagnostics = dict(action.diagnostics_json or {}) if isinstance(action.diagnostics_json, dict) else {}
        merged_diagnostics.update(diagnostics if isinstance(diagnostics, dict) else {})
        action.write(
            {
                "state": "pending",
                "reason_code": "APPROVAL_REQUIRED",
                "diagnostics_json": merged_diagnostics,
            }
        )
        return action.to_runtime_dict()

    def approve_action(self, *, action_id: int, note: str = "") -> dict[str, Any]:
        action = self._load_action(action_id)
        return self.approval_policy_service.approve_action(action=action, user=self.env.user, note=note, auto=False)

    def execute_action(self, *, action_id: int) -> dict[str, Any]:
        action = self._load_action(action_id)
        if _text(action.state) == "succeeded":
            return action.to_runtime_dict()

        executor_allowed, executor_reason, executor_diag = self.approval_policy_service.can_execute(action=action, user=self.env.user)
        if not executor_allowed:
            return self._mark_failed(
                action,
                reason_code=executor_reason,
                diagnostics={"orchestrator": "release_orchestrator_v1", "approval": executor_diag},
            )

        if bool(action.approval_required) and _text(action.approval_state) != "approved":
            allow_self_approval = bool((action.policy_snapshot_json or {}).get("allow_self_approval")) if isinstance(action.policy_snapshot_json, dict) else False
            if allow_self_approval:
                approver_allowed, _, _ = self.approval_policy_service.can_approve(action=action, user=self.env.user)
                if approver_allowed:
                    self.approval_policy_service.approve_action(action=action, user=self.env.user, note="auto approval during orchestration", auto=True)
            if _text(action.approval_state) != "approved":
                return self._mark_pending_approval(
                    action,
                    diagnostics={"orchestrator": "release_orchestrator_v1", "approval_state": _text(action.approval_state)},
                )

        request_payload = action.request_payload_json if isinstance(action.request_payload_json, dict) else {}
        try:
            with self.env.cr.savepoint():
                self._mark_running(action)
                if _text(action.action_type) == "promote_snapshot":
                    result = self.promotion_service.promote_to_released(
                        int(request_payload.get("snapshot_id") or action.target_snapshot_id.id or 0),
                        replace_active=bool(request_payload.get("replace_active", True)),
                        state_reason="release_orchestrator_promoted",
                        promotion_note=_text(action.note) or "promoted by release orchestrator",
                    )
                elif _text(action.action_type) == "rollback_snapshot":
                    result = self.snapshot_service.rollback_to_snapshot(
                        product_key=_text(action.product_key),
                        target_snapshot_id=int(request_payload.get("target_snapshot_id") or action.target_snapshot_id.id or 0) or None,
                        note=_text(action.note) or "rollback by release orchestrator",
                    )
                else:
                    raise ValueError(f"UNSUPPORTED_RELEASE_ACTION_TYPE:{_text(action.action_type)}")
            return self._mark_succeeded(
                action,
                result_snapshot_id=int(result.get("id") or 0),
                result_payload=result,
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": _text(action.action_type)},
            )
        except Exception as exc:
            return self._mark_failed(
                action,
                reason_code=str(exc),
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": _text(action.action_type), "error": str(exc)},
            )

    def promote_snapshot(
        self,
        *,
        product_key: str,
        snapshot_id: int,
        note: str = "",
        replace_active: bool = True,
    ) -> dict[str, Any]:
        action = self._create_action(
            action_type="promote_snapshot",
            product_key=product_key,
            target_snapshot_id=snapshot_id,
            note=note,
            request_payload={
                "snapshot_id": int(snapshot_id),
                "replace_active": bool(replace_active),
                "note": _text(note),
            },
        )
        return self.execute_action(action_id=int(action.id))

    def rollback_snapshot(
        self,
        *,
        product_key: str,
        target_snapshot_id: int | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        action = self._create_action(
            action_type="rollback_snapshot",
            product_key=product_key,
            target_snapshot_id=target_snapshot_id,
            note=note,
            request_payload={
                "target_snapshot_id": int(target_snapshot_id or 0) or 0,
                "note": _text(note),
            },
        )
        return self.execute_action(action_id=int(action.id))

    def list_actions(self, *, product_key: str | None = None) -> list[dict[str, Any]]:
        domain = [("active", "=", True)]
        if _text(product_key):
            domain.append(("product_key", "=", _text(product_key)))
        return [row.to_runtime_dict() for row in self._action_model().search(domain, order="requested_at desc, id desc")]
