# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from odoo import fields

from .delivery_engine import DeliveryEngine
from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .product_policy_service import ProductPolicyService


FREEZE_SURFACE_CONTRACT_VERSION = "edition_freeze_surface_v1"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class EditionReleaseSnapshotService:
    def __init__(self, env):
        self.env = env
        self.policy_service = ProductPolicyService(env)
        self.delivery_engine = DeliveryEngine(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)

    def _model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

    def now(self):
        return fields.Datetime.now()

    def _freeze_role_code(self, policy: dict[str, Any], explicit_role_code: str = "") -> str:
        if _text(explicit_role_code):
            return _text(explicit_role_code)
        allowed = policy.get("allowed_role_codes") if isinstance(policy.get("allowed_role_codes"), list) else []
        for item in allowed:
            value = _text(item)
            if value:
                return value
        return "pm"

    def _default_requested_role_code(
        self,
        *,
        requested_product_key: str,
        explicit_role_code: str = "",
    ) -> str:
        if _text(explicit_role_code):
            return _text(explicit_role_code)
        rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", _text(requested_product_key)), ("active", "=", True)], limit=1)
        if rec and isinstance(rec.allowed_role_codes, list):
            for item in rec.allowed_role_codes:
                value = _text(item)
                if value:
                    return value
        return "pm"

    def build_freeze_surface(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        role_code: str = "",
    ) -> dict[str, Any]:
        requested_product_key, requested_base_product_key, requested_edition_key = self.policy_service.resolve_policy_identity(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
        )
        requested_role_code = self._default_requested_role_code(
            requested_product_key=requested_product_key,
            explicit_role_code=role_code,
        )
        policy = self.policy_service.get_policy(
            product_key=requested_product_key,
            edition_key=requested_edition_key,
            base_product_key=requested_base_product_key,
            role_code=requested_role_code,
            enforce_release=True,
            enforce_access=True,
        )
        freeze_role_code = self._freeze_role_code(policy, explicit_role_code=requested_role_code)
        delivery = self.delivery_engine.build(
            data={"role_surface": {"role_code": freeze_role_code}, "scenes": [], "capabilities": []},
            product_key=requested_product_key,
            edition_key=requested_edition_key,
            base_product_key=requested_base_product_key,
        )
        resolved_policy = _dict(policy)
        resolved_delivery = _dict(delivery)
        effective_product_key = _text(resolved_delivery.get("product_key")) or _text(resolved_policy.get("product_key"))
        effective_base_product_key = _text(resolved_delivery.get("base_product_key")) or _text(resolved_policy.get("base_product_key"))
        effective_edition_key = _text(resolved_delivery.get("edition_key")) or _text(resolved_policy.get("edition_key"))
        policy_rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", effective_product_key), ("active", "=", True)], limit=1)
        declared_scene_bindings = (
            deepcopy(policy_rec.scene_version_bindings)
            if policy_rec and isinstance(policy_rec.scene_version_bindings, dict)
            else deepcopy(_dict(resolved_policy.get("scene_version_bindings")))
        )
        identity = {
            "product_key": effective_product_key,
            "base_product_key": effective_base_product_key,
            "edition_key": effective_edition_key,
            "label": _text(resolved_policy.get("label")),
            "version": _text(resolved_policy.get("version")) or "v1",
            "channel": "preview" if effective_edition_key == "preview" else "stable",
        }
        runtime_meta = {
            "requested": {
                "product_key": requested_product_key,
                "base_product_key": requested_base_product_key,
                "edition_key": requested_edition_key,
                "role_code": freeze_role_code,
            },
            "effective": {
                "product_key": effective_product_key,
                "base_product_key": effective_base_product_key,
                "edition_key": effective_edition_key,
                "role_code": freeze_role_code,
            },
            "edition_diagnostics": _dict(resolved_policy.get("edition_diagnostics")),
            "delivery_engine_meta": _dict(resolved_delivery.get("meta")),
        }
        snapshot = {
            "contract_version": FREEZE_SURFACE_CONTRACT_VERSION,
            "identity": identity,
            "policy": {
                "product_key": effective_product_key,
                "base_product_key": effective_base_product_key,
                "edition_key": effective_edition_key,
                "state": _text(resolved_policy.get("state")),
                "access_level": _text(resolved_policy.get("access_level")),
                "allowed_role_codes": deepcopy(_list(resolved_policy.get("allowed_role_codes"))),
                "label": _text(resolved_policy.get("label")),
                "version": _text(resolved_policy.get("version")) or "v1",
            },
            "nav": deepcopy(_list(resolved_delivery.get("nav"))),
            "capabilities": deepcopy(_list(resolved_delivery.get("capabilities"))),
            "scenes": deepcopy(_list(resolved_delivery.get("scenes"))),
            "scene_version_bindings": declared_scene_bindings,
            "resolved_scene_version_bindings": deepcopy(_dict(resolved_policy.get("scene_version_bindings"))),
            "scene_binding_diagnostics": deepcopy(_dict(resolved_policy.get("scene_binding_diagnostics"))),
            "runtime_meta": runtime_meta,
        }
        return snapshot

    def _lineage_meta(self, rec) -> dict[str, Any]:
        runtime = rec.snapshot_json if isinstance(rec.snapshot_json, dict) else {}
        runtime_meta = _dict(runtime.get("runtime_meta"))
        return {
            "snapshot_id": int(rec.id),
            "product_key": _text(rec.product_key),
            "base_product_key": _text(rec.base_product_key),
            "edition_key": _text(rec.edition_key),
            "version": _text(rec.version) or "v1",
            "channel": _text(rec.channel) or "stable",
            "state": _text(rec.state) or "candidate",
            "is_active": bool(rec.is_active),
            "released_at": rec.released_at.isoformat() if rec.released_at else "",
            "approved_at": rec.approved_at.isoformat() if rec.approved_at else "",
            "frozen_at": rec.frozen_at.isoformat() if rec.frozen_at else "",
            "state_reason": _text(rec.state_reason),
            "promotion_note": _text(rec.promotion_note),
            "promoted_from_snapshot_id": int(rec.promoted_from_snapshot_id.id) if rec.promoted_from_snapshot_id else 0,
            "rollback_target_snapshot_id": int(rec.rollback_target_snapshot_id.id) if rec.rollback_target_snapshot_id else 0,
            "replaced_by_snapshot_id": int(rec.replaced_by_snapshot_id.id) if rec.replaced_by_snapshot_id else 0,
            "effective_runtime": _dict(runtime_meta.get("effective")),
        }

    def freeze_release_surface(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        version: str = "v1",
        role_code: str = "",
        note: str = "",
        replace_active: bool = True,
    ) -> dict[str, Any]:
        payload = self.build_freeze_surface(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
            role_code=role_code,
        )
        identity = _dict(payload.get("identity"))
        resolved_product_key = _text(identity.get("product_key"))
        resolved_base_product_key = _text(identity.get("base_product_key")) or "construction"
        resolved_edition_key = _text(identity.get("edition_key")) or "standard"
        resolved_version = _text(version) or _text(identity.get("version")) or "v1"
        channel = _text(identity.get("channel")) or ("preview" if resolved_edition_key == "preview" else "stable")
        label = _text(identity.get("label")) or resolved_product_key
        now = self.now()
        model = self._model()
        current_active = model.search(
            [("product_key", "=", resolved_product_key), ("is_active", "=", True), ("active", "=", True)],
            order="activated_at desc, id desc",
            limit=1,
        )
        target = model.search(
            [("product_key", "=", resolved_product_key), ("version", "=", resolved_version), ("active", "=", True)],
            limit=1,
        )
        rollback_target_id = int(current_active.id) if current_active and (not target or int(current_active.id) != int(target.id)) else False
        policy_rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", resolved_product_key), ("active", "=", True)], limit=1)
        values = {
            "state": "candidate",
            "product_key": resolved_product_key,
            "base_product_key": resolved_base_product_key,
            "edition_key": resolved_edition_key,
            "label": label,
            "version": resolved_version,
            "channel": channel,
            "frozen_at": now,
            "approved_at": False,
            "released_at": False,
            "activated_at": False,
            "superseded_at": False,
            "source_policy_id": int(policy_rec.id) if policy_rec else False,
            "promoted_from_snapshot_id": False,
            "rollback_target_snapshot_id": rollback_target_id or False,
            "replaced_by_snapshot_id": False,
            "snapshot_json": payload,
            "meta_json": {
                "freeze_context": {
                    "requested_product_key": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("product_key")),
                    "requested_edition_key": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("edition_key")),
                    "effective_product_key": _text(_dict(_dict(payload.get("runtime_meta")).get("effective")).get("product_key")),
                    "effective_edition_key": _text(_dict(_dict(payload.get("runtime_meta")).get("effective")).get("edition_key")),
                    "role_code": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("role_code")),
                },
                "rollback_basis_available": bool(rollback_target_id),
            },
            "state_reason": "frozen_release_surface_candidate",
            "promotion_note": "",
            "note": _text(note) or "frozen from edition delivery surface",
            "is_active": False,
        }
        if target:
            target.write(values)
            rec = target
        else:
            rec = model.create(values)
        self.promotion_service.promote_to_approved(
            int(rec.id),
            state_reason="freeze_surface_approved",
            promotion_note="approved by freeze service",
        )
        if replace_active:
            return self.promotion_service.promote_to_released(
                int(rec.id),
                replace_active=True,
                state_reason="freeze_surface_released",
                promotion_note="released by freeze service",
            )
        return rec.to_runtime_dict()

    def list_snapshots(self, *, product_key: str | None = None) -> list[dict[str, Any]]:
        domain = [("active", "=", True)]
        if _text(product_key):
            domain.append(("product_key", "=", _text(product_key)))
        return [row.to_runtime_dict() for row in self._model().search(domain, order="product_key asc, version desc, id desc")]

    def resolve_active_snapshot(self, *, product_key: str) -> dict[str, Any]:
        rec = self._model().search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="activated_at desc, id desc",
            limit=1,
        )
        return rec.to_runtime_dict() if rec else {}

    def resolve_active_snapshot_lineage(self, *, product_key: str) -> dict[str, Any]:
        rec = self._model().search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        return self._lineage_meta(rec) if rec else {}

    def rollback_to_snapshot(self, *, product_key: str, target_snapshot_id: int | None = None, note: str = "") -> dict[str, Any]:
        current = self._model().search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        if not current:
            raise ValueError("ACTIVE_RELEASE_SNAPSHOT_NOT_FOUND")
        target = self._model().browse(int(target_snapshot_id)) if target_snapshot_id else current.rollback_target_snapshot_id
        if not target or not target.exists():
            raise ValueError("ROLLBACK_TARGET_NOT_FOUND")
        if _text(target.product_key) != _text(product_key):
            raise ValueError("ROLLBACK_TARGET_PRODUCT_MISMATCH")
        if _text(target.state) not in {"approved", "released", "superseded"}:
            raise ValueError("ROLLBACK_TARGET_NOT_RELEASEABLE")
        now = self.now()
        current.write(
            {
                "state": "superseded",
                "is_active": False,
                "superseded_at": now,
                "state_reason": "rolled_back_to_previous_released_snapshot",
                "promotion_note": _text(note) or "rolled back to previous release snapshot",
            }
        )
        target.write(
            {
                "state": "released",
                "is_active": True,
                "released_at": target.released_at or now,
                "activated_at": now,
                "superseded_at": False,
                "state_reason": "rollback_reactivated_released_snapshot",
                "promotion_note": _text(note) or "rollback reactivated previous release snapshot",
                "replaced_by_snapshot_id": False,
            }
        )
        return target.to_runtime_dict()
