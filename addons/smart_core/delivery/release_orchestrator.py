# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields

from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .edition_release_snapshot_service import EditionReleaseSnapshotService


def _text(value: Any) -> str:
    return str(value or "").strip()


class ReleaseOrchestrator:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = EditionReleaseSnapshotService(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)

    def _action_model(self):
        return self.env["sc.release.action"].sudo()

    def _snapshot_model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

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
        try:
            with self.env.cr.savepoint():
                self._mark_running(action)
                result = self.promotion_service.promote_to_released(
                    int(snapshot_id),
                    replace_active=bool(replace_active),
                    state_reason="release_orchestrator_promoted",
                    promotion_note=_text(note) or "promoted by release orchestrator",
                )
            return self._mark_succeeded(
                action,
                result_snapshot_id=int(result.get("id") or 0),
                result_payload=result,
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": "promote_snapshot"},
            )
        except Exception as exc:
            return self._mark_failed(
                action,
                reason_code=str(exc),
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": "promote_snapshot", "error": str(exc)},
            )

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
        try:
            with self.env.cr.savepoint():
                self._mark_running(action)
                result = self.snapshot_service.rollback_to_snapshot(
                    product_key=product_key,
                    target_snapshot_id=target_snapshot_id,
                    note=_text(note) or "rollback by release orchestrator",
                )
            return self._mark_succeeded(
                action,
                result_snapshot_id=int(result.get("id") or 0),
                result_payload=result,
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": "rollback_snapshot"},
            )
        except Exception as exc:
            return self._mark_failed(
                action,
                reason_code=str(exc),
                diagnostics={"orchestrator": "release_orchestrator_v1", "operation": "rollback_snapshot", "error": str(exc)},
            )

    def list_actions(self, *, product_key: str | None = None) -> list[dict[str, Any]]:
        domain = [("active", "=", True)]
        if _text(product_key):
            domain.append(("product_key", "=", _text(product_key)))
        return [row.to_runtime_dict() for row in self._action_model().search(domain, order="requested_at desc, id desc")]
