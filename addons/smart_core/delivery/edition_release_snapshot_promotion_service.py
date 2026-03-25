# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields


def _text(value: Any) -> str:
    return str(value or "").strip()


class EditionReleaseSnapshotPromotionService:
    ALLOWED_TRANSITIONS = {
        "candidate": {"approved", "released"},
        "approved": {"released"},
        "released": {"superseded"},
        "superseded": set(),
    }

    def __init__(self, env):
        self.env = env

    def _model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

    def now(self):
        return fields.Datetime.now()

    def _load(self, snapshot_id: int):
        rec = self._model().browse(int(snapshot_id))
        if not rec.exists() or not rec.active:
            raise ValueError("EDITION_RELEASE_SNAPSHOT_NOT_FOUND")
        return rec

    def _assert_transition_allowed(self, *, current_state: str, target_state: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise ValueError(f"INVALID_RELEASE_SNAPSHOT_TRANSITION:{current_state}->{target_state}")

    def _active_released_conflicts(self, rec):
        return self._model().search(
            [
                ("product_key", "=", _text(rec.product_key)),
                ("state", "=", "released"),
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
        current_state = _text(rec.state) or "candidate"
        target = _text(target_state)
        self._assert_transition_allowed(current_state=current_state, target_state=target)
        now = self.now()
        if target == "approved":
            rec.write(
                {
                    "state": "approved",
                    "approved_at": now,
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_snapshot_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()
        if target == "released":
            conflicts = self._active_released_conflicts(rec)
            if conflicts and not replace_active:
                raise ValueError("ACTIVE_RELEASED_SNAPSHOT_CONFLICT")
            if conflicts and replace_active:
                conflicts.write(
                    {
                        "state": "superseded",
                        "is_active": False,
                        "superseded_at": now,
                        "state_reason": "replaced_by_new_released_snapshot",
                        "replaced_by_snapshot_id": int(rec.id),
                    }
                )
            rec.write(
                {
                    "state": "released",
                    "is_active": True,
                    "approved_at": rec.approved_at or now,
                    "released_at": now,
                    "activated_at": now,
                    "superseded_at": False,
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_snapshot_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()
        if target == "superseded":
            rec.write(
                {
                    "state": "superseded",
                    "is_active": False,
                    "superseded_at": now,
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_snapshot_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()
        raise ValueError(f"UNSUPPORTED_RELEASE_SNAPSHOT_TARGET:{target}")

    def promote_to_approved(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="approved", **kwargs)

    def promote_to_released(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="released", **kwargs)

    def supersede(self, snapshot_id: int, **kwargs) -> dict[str, Any]:
        return self.promote(snapshot_id=snapshot_id, target_state="superseded", **kwargs)
