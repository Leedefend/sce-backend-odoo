# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from .scene_snapshot_service import SceneSnapshotService, _dict, _text


class ScenePromotionService:
    ALLOWED_TRANSITIONS = {
        "draft": {"ready"},
        "ready": {"beta", "stable"},
        "beta": {"stable"},
        "stable": {"deprecated"},
        "deprecated": set(),
    }

    def __init__(self, env):
        self.env = env
        self.snapshot_service = SceneSnapshotService(env)

    def _model(self):
        return self.env["sc.scene.snapshot"].sudo()

    def _load(self, snapshot_id: int):
        rec = self._model().browse(int(snapshot_id))
        if not rec.exists():
            raise ValueError("SNAPSHOT_NOT_FOUND")
        return rec

    def _validate_release_contract(self, rec) -> None:
        contract = rec.contract_json if isinstance(rec.contract_json, dict) else {}
        self.snapshot_service.validate_snapshot_contract(
            contract,
            scene_key=_text(rec.scene_key),
            product_key=_text(rec.product_key),
            capability_key=_text(rec.capability_key),
        )
        if not _text(rec.scene_key):
            raise ValueError("SCENE_KEY_MISSING")
        if not _text(rec.product_key):
            raise ValueError("PRODUCT_KEY_MISSING")
        if not _text(rec.capability_key):
            raise ValueError("CAPABILITY_KEY_MISSING")

    def _assert_transition_allowed(self, *, current_state: str, target_state: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise ValueError(f"INVALID_STATE_TRANSITION:{current_state}->{target_state}")

    def _active_stable_conflicts(self, rec) -> list:
        return self._model().search(
            [
                ("scene_key", "=", _text(rec.scene_key)),
                ("product_key", "=", _text(rec.product_key)),
                ("state", "=", "stable"),
                ("is_active", "=", True),
                ("active", "=", True),
                ("id", "!=", int(rec.id)),
            ]
        )

    def promote(
        self,
        *,
        snapshot_id: int,
        target_state: str,
        replace_active: bool = False,
        state_reason: str = "",
        promotion_note: str = "",
    ) -> dict[str, Any]:
        rec = self._load(snapshot_id)
        current_state = _text(rec.state) or "draft"
        target = _text(target_state)
        self._assert_transition_allowed(current_state=current_state, target_state=target)
        self._validate_release_contract(rec)

        if target == "stable":
            conflicts = self._active_stable_conflicts(rec)
            if conflicts and not replace_active:
                raise ValueError("ACTIVE_STABLE_CONFLICT")
            if conflicts and replace_active:
                conflicts.write(
                    {
                        "state": "deprecated",
                        "is_active": False,
                        "deprecated_at": self.snapshot_service.now(),
                        "state_reason": "replaced_by_new_stable",
                    }
                )
            rec.write(
                {
                    "state": "stable",
                    "is_active": True,
                    "activated_at": self.snapshot_service.now(),
                    "deprecated_at": False,
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_snapshot_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()

        if target == "deprecated":
            rec.write(
                {
                    "state": "deprecated",
                    "is_active": False,
                    "deprecated_at": self.snapshot_service.now(),
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_snapshot_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()

        rec.write(
            {
                "state": target,
                "is_active": False,
                "state_reason": state_reason,
                "promotion_note": promotion_note,
                "promoted_from_snapshot_id": int(rec.id),
            }
        )
        return rec.to_runtime_dict()

    def promote_to_ready(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="ready", **kwargs)

    def promote_to_beta(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="beta", **kwargs)

    def promote_to_stable(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="stable", **kwargs)

    def deprecate(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="deprecated", **kwargs)
