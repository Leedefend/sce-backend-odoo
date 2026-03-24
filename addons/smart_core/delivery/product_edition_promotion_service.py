# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields


def _text(value: Any) -> str:
    return str(value or "").strip()


class ProductEditionPromotionService:
    ALLOWED_TRANSITIONS = {
        "draft": {"ready"},
        "ready": {"preview", "stable"},
        "preview": {"stable", "deprecated"},
        "stable": {"deprecated"},
        "deprecated": set(),
    }

    def __init__(self, env):
        self.env = env

    def _model(self):
        return self.env["sc.product.policy"].sudo()

    def now(self):
        return fields.Datetime.now()

    def _load(self, product_key: str):
        rec = self._model().search([("product_key", "=", _text(product_key)), ("active", "=", True)], limit=1)
        if not rec:
            raise ValueError("PRODUCT_POLICY_NOT_FOUND")
        return rec

    def _assert_transition_allowed(self, *, current_state: str, target_state: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise ValueError(f"INVALID_POLICY_STATE_TRANSITION:{current_state}->{target_state}")

    def _validate_releaseable_scene_bindings(self, rec) -> None:
        from .product_policy_service import ProductPolicyService

        service = ProductPolicyService(self.env)
        payload = rec.to_runtime_dict()
        payload = service._sanitize_scene_version_bindings(payload)
        requested_bindings = rec.scene_version_bindings if isinstance(rec.scene_version_bindings, dict) else {}
        sanitized = payload.get("scene_version_bindings") if isinstance(payload.get("scene_version_bindings"), dict) else {}
        if not isinstance(requested_bindings, dict) or not requested_bindings:
            raise ValueError("SCENE_BINDINGS_MISSING")
        missing = sorted(set(requested_bindings.keys()) - set(sanitized.keys()))
        if missing:
            raise ValueError(f"SCENE_BINDINGS_NOT_RELEASEABLE:{','.join(missing)}")

    def _stable_conflicts(self, rec):
        return self._model().search(
            [
                ("base_product_key", "=", _text(rec.base_product_key)),
                ("state", "=", "stable"),
                ("active", "=", True),
                ("id", "!=", int(rec.id)),
            ]
        )

    def promote(
        self,
        *,
        product_key: str,
        target_state: str,
        replace_stable: bool = False,
        state_reason: str = "",
        promotion_note: str = "",
    ) -> dict[str, Any]:
        rec = self._load(product_key)
        current_state = _text(rec.state) or "draft"
        target = _text(target_state)
        self._assert_transition_allowed(current_state=current_state, target_state=target)
        if target in {"preview", "stable"}:
            self._validate_releaseable_scene_bindings(rec)
        if target == "stable":
            conflicts = self._stable_conflicts(rec)
            if conflicts and not replace_stable:
                raise ValueError("ACTIVE_STABLE_EDITION_CONFLICT")
            if conflicts and replace_stable:
                conflicts.write(
                    {
                        "state": "deprecated",
                        "deprecated_at": self.now(),
                        "state_reason": "replaced_by_new_stable_edition",
                    }
                )
            rec.write(
                {
                    "state": "stable",
                    "activated_at": self.now(),
                    "deprecated_at": False,
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_policy_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()
        if target == "deprecated":
            rec.write(
                {
                    "state": "deprecated",
                    "deprecated_at": self.now(),
                    "state_reason": state_reason,
                    "promotion_note": promotion_note,
                    "promoted_from_policy_id": int(rec.id),
                }
            )
            return rec.to_runtime_dict()
        rec.write(
            {
                "state": target,
                "state_reason": state_reason,
                "promotion_note": promotion_note,
                "promoted_from_policy_id": int(rec.id),
            }
        )
        return rec.to_runtime_dict()

    def promote_to_ready(self, product_key: str, **kwargs) -> dict[str, Any]:
        return self.promote(product_key=product_key, target_state="ready", **kwargs)

    def promote_to_preview(self, product_key: str, **kwargs) -> dict[str, Any]:
        return self.promote(product_key=product_key, target_state="preview", **kwargs)

    def promote_to_stable(self, product_key: str, **kwargs) -> dict[str, Any]:
        return self.promote(product_key=product_key, target_state="stable", **kwargs)

    def deprecate(self, product_key: str, **kwargs) -> dict[str, Any]:
        return self.promote(product_key=product_key, target_state="deprecated", **kwargs)

    def rollback_to_previous_stable(
        self,
        *,
        base_product_key: str,
        current_product_key: str,
        state_reason: str = "",
        promotion_note: str = "",
    ) -> dict[str, Any]:
        current = self._load(current_product_key)
        if _text(current.state) != "stable":
            raise ValueError("CURRENT_POLICY_NOT_STABLE")
        previous = self._model().search(
            [
                ("base_product_key", "=", _text(base_product_key)),
                ("state", "=", "deprecated"),
                ("active", "=", True),
                ("id", "!=", int(current.id)),
            ],
            order="deprecated_at desc, id desc",
            limit=1,
        )
        if not previous:
            raise ValueError("PREVIOUS_STABLE_NOT_FOUND")
        current.write(
            {
                "state": "deprecated",
                "deprecated_at": self.now(),
                "state_reason": state_reason or "rolled_back_to_previous_stable",
                "promotion_note": promotion_note,
            }
        )
        previous.write(
            {
                "state": "stable",
                "activated_at": self.now(),
                "deprecated_at": False,
                "state_reason": state_reason or "rollback_reactivated_previous_stable",
                "promotion_note": promotion_note,
                "promoted_from_policy_id": int(current.id),
            }
        )
        return previous.to_runtime_dict()
