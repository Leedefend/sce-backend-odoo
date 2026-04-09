# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields

from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .edition_release_snapshot_service import EditionReleaseSnapshotService
from .release_approval_policy_service import ReleaseApprovalPolicyService
from .release_execution_engine import RELEASE_EXECUTION_PROTOCOL_VERSION, ReleaseExecutionEngine
from .release_operator_write_model_service import RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class ReleaseOrchestrator:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = EditionReleaseSnapshotService(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)
        self.approval_policy_service = ReleaseApprovalPolicyService(env)
        self.execution_engine = ReleaseExecutionEngine(env)

    def _action_model(self):
        return self.env["sc.release.action"]

    def _snapshot_model(self):
        return self.env["sc.edition.release.snapshot"]

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
                "execution_protocol_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
                "execution_trace_json": {"contract_version": RELEASE_EXECUTION_PROTOCOL_VERSION, "runs": []},
                **policy_fields,
            }
        )

    def _append_trace_run(self, action, trace_run: dict[str, Any] | None = None) -> dict[str, Any]:
        current = action.execution_trace_json if isinstance(action.execution_trace_json, dict) else {}
        runs = list(current.get("runs") or []) if isinstance(current.get("runs"), list) else []
        if isinstance(trace_run, dict) and trace_run:
            runs.append(trace_run)
        merged = {
            "contract_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
            "runs": runs,
        }
        action.write({"execution_protocol_version": RELEASE_EXECUTION_PROTOCOL_VERSION, "execution_trace_json": merged})
        return merged

    def _mark_running(self, action, *, trace_run: dict[str, Any] | None = None) -> None:
        values = {"state": "running", "executed_at": self.now()}
        if isinstance(trace_run, dict) and trace_run:
            current = action.execution_trace_json if isinstance(action.execution_trace_json, dict) else {}
            runs = list(current.get("runs") or []) if isinstance(current.get("runs"), list) else []
            values["execution_protocol_version"] = RELEASE_EXECUTION_PROTOCOL_VERSION
            values["execution_trace_json"] = {"contract_version": RELEASE_EXECUTION_PROTOCOL_VERSION, "runs": runs + [trace_run]}
        action.write(values)

    def _mark_succeeded(self, action, *, result_snapshot_id: int | None, result_payload: dict[str, Any], diagnostics: dict[str, Any], trace_run: dict[str, Any] | None = None) -> dict[str, Any]:
        trace_payload = self._append_trace_run(action, trace_run)
        action.write(
            {
                "state": "succeeded",
                "completed_at": self.now(),
                "result_snapshot_id": int(result_snapshot_id or 0) or False,
                "reason_code": "OK",
                "result_payload_json": result_payload if isinstance(result_payload, dict) else {},
                "diagnostics_json": diagnostics if isinstance(diagnostics, dict) else {},
                "execution_protocol_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
                "execution_trace_json": trace_payload,
            }
        )
        return action.to_runtime_dict()

    def _mark_failed(self, action, *, reason_code: str, diagnostics: dict[str, Any], trace_run: dict[str, Any] | None = None) -> dict[str, Any]:
        trace_payload = self._append_trace_run(action, trace_run)
        action.write(
            {
                "state": "failed",
                "completed_at": self.now(),
                "reason_code": _text(reason_code),
                "diagnostics_json": diagnostics if isinstance(diagnostics, dict) else {},
                "execution_protocol_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
                "execution_trace_json": trace_payload,
            }
        )
        return action.to_runtime_dict()

    def _mark_pending_approval(self, action, *, diagnostics: dict[str, Any], trace_run: dict[str, Any] | None = None) -> dict[str, Any]:
        trace_payload = self._append_trace_run(action, trace_run)
        merged_diagnostics = dict(action.diagnostics_json or {}) if isinstance(action.diagnostics_json, dict) else {}
        merged_diagnostics.update(diagnostics if isinstance(diagnostics, dict) else {})
        action.write(
            {
                "state": "pending",
                "reason_code": "APPROVAL_REQUIRED",
                "diagnostics_json": merged_diagnostics,
                "execution_protocol_version": RELEASE_EXECUTION_PROTOCOL_VERSION,
                "execution_trace_json": trace_payload,
            }
        )
        return action.to_runtime_dict()

    def approve_action(self, *, action_id: int, note: str = "") -> dict[str, Any]:
        action = self._load_action(action_id)
        run = self.execution_engine.run_approval(action=action, user=self.env.user, note=note, auto=False)
        self._append_trace_run(action, run)
        if _text(run.get("state")) != "succeeded":
            raise ValueError(_text(run.get("reason_code")) or "RELEASE_APPROVAL_FAILED")
        return action.to_runtime_dict()

    def approve_and_execute_action(self, *, action_id: int, note: str = "") -> dict[str, Any]:
        self.approve_action(action_id=action_id, note=note)
        return self.execute_action(action_id=action_id)

    def execute_action(self, *, action_id: int) -> dict[str, Any]:
        action = self._load_action(action_id)
        if _text(action.state) == "succeeded":
            return action.to_runtime_dict()
        with self.env.cr.savepoint():
            outcome = self.execution_engine.execute_release_action(action=action, user=self.env.user)
            trace_run = outcome.get("trace_run") if isinstance(outcome.get("trace_run"), dict) else {}
            status = _text(outcome.get("status"))
            diagnostics = {"orchestrator": "release_orchestrator_v1", **(_dict(outcome.get("diagnostics")))}
            if status == "pending_approval":
                return self._mark_pending_approval(action, diagnostics=diagnostics, trace_run=trace_run)
            if status == "failed":
                return self._mark_failed(
                    action,
                    reason_code=_text(outcome.get("reason_code")) or "RELEASE_EXECUTION_FAILED",
                    diagnostics=diagnostics,
                    trace_run=trace_run,
                )
            result = outcome.get("result") if isinstance(outcome.get("result"), dict) else {}
            self._mark_running(action)
            return self._mark_succeeded(
                action,
                result_snapshot_id=int(result.get("id") or 0),
                result_payload=result,
                diagnostics=diagnostics,
                trace_run=trace_run,
            )

    def submit_write_model(self, write_model: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = write_model if isinstance(write_model, dict) else {}
        if _text(payload.get("contract_version")) != RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION:
            raise ValueError("RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_DRIFT")
        operation = _text(payload.get("operation"))
        identity = payload.get("identity") if isinstance(payload.get("identity"), dict) else {}
        model_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        product_key = _text(identity.get("product_key"))
        note = _text(model_payload.get("note"))
        if operation == "promote_snapshot":
            return self.promote_snapshot(
                product_key=product_key,
                snapshot_id=int(model_payload.get("snapshot_id") or 0),
                note=note,
                replace_active=bool(model_payload.get("replace_active", True)),
            )
        if operation == "approve_action":
            action_id = int(model_payload.get("action_id") or 0)
            approved = self.approve_action(action_id=action_id, note=note)
            if bool(model_payload.get("execute_after_approval", True)):
                return self.execute_action(action_id=action_id)
            return approved
        if operation == "rollback_snapshot":
            return self.rollback_snapshot(
                product_key=product_key,
                target_snapshot_id=int(model_payload.get("target_snapshot_id") or 0) or None,
                note=note,
            )
        raise ValueError(f"UNSUPPORTED_RELEASE_OPERATOR_WRITE_OPERATION:{operation}")

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
