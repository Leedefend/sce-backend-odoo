# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from odoo.addons.smart_core.core.scene_contract_builder import (
    SCENE_CONTRACT_STANDARD_VERSION,
    build_release_surface_scene_contract_from_delivery_entry,
)
from odoo.addons.smart_core.delivery.product_policy_service import ProductPolicyService


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _policy_row_by_scene(policy: dict[str, Any], scene_key: str) -> dict[str, Any]:
    for row in policy.get("scenes") or []:
        if not isinstance(row, dict):
            continue
        if _text(row.get("scene_key")) == scene_key:
            return row
    return {}


class SceneSnapshotService:
    def __init__(self, env):
        self.env = env
        self.policy_service = ProductPolicyService(env)

    def _model(self):
        return self.env["sc.scene.snapshot"].sudo()

    def _normalize_contract(self, contract: dict[str, Any], *, scene_key: str, product_key: str, capability_key: str) -> dict[str, Any]:
        payload = deepcopy(_dict(contract))
        payload["contract_version"] = SCENE_CONTRACT_STANDARD_VERSION
        identity = _dict(payload.get("identity"))
        identity["scene_key"] = scene_key
        identity["product_key"] = product_key
        identity["capability"] = capability_key
        identity["version"] = _text(identity.get("version")) or "v1"
        payload["identity"] = identity

        governance = _dict(payload.get("governance"))
        governance["contract_version"] = SCENE_CONTRACT_STANDARD_VERSION
        governance["policy_match"] = True
        governance["released"] = True
        payload["governance"] = governance
        return payload

    def freeze_policy_surface(self, *, product_key: str, version: str = "v1", channel: str = "stable") -> list[dict[str, Any]]:
        policy = self.policy_service.get_policy(product_key=product_key)
        rows: list[dict[str, Any]] = []
        for entry in policy.get("scenes") or []:
            if not isinstance(entry, dict):
                continue
            scene_key = _text(entry.get("scene_key"))
            if not scene_key:
                continue
            capability_key = _text(entry.get("capability_key"))
            contract = build_release_surface_scene_contract_from_delivery_entry(entry)
            normalized = self._normalize_contract(
                contract,
                scene_key=scene_key,
                product_key=_text(entry.get("product_key")),
                capability_key=capability_key,
            )
            identity = _dict(normalized.get("identity"))
            identity["version"] = _text(version) or "v1"
            normalized["identity"] = identity
            governance = _dict(normalized.get("governance"))
            governance["diagnostics_ref"] = "scene_snapshot.freeze_policy_surface"
            normalized["governance"] = governance
            rows.append(
                self.upsert_snapshot(
                    scene_key=scene_key,
                    product_key=_text(entry.get("product_key")),
                    capability_key=capability_key,
                    label=_text(entry.get("label")),
                    route=_text(entry.get("route")),
                    version=version,
                    channel=channel,
                    contract=normalized,
                    source_type="release_surface",
                    source_ref=f"{product_key}:{scene_key}",
                    note="frozen from delivery policy surface",
                    meta={
                        "binding_scope": "released_surface",
                        "policy_product_key": product_key,
                    },
                )
            )
        return rows

    def upsert_snapshot(
        self,
        *,
        scene_key: str,
        product_key: str,
        capability_key: str,
        label: str,
        route: str,
        version: str,
        channel: str,
        contract: dict[str, Any],
        source_type: str,
        source_ref: str,
        note: str = "",
        meta: dict[str, Any] | None = None,
        cloned_from_snapshot_id: int | None = None,
    ) -> dict[str, Any]:
        model = self._model()
        rec = model.search(
            [
                ("scene_key", "=", scene_key),
                ("product_key", "=", product_key),
                ("version", "=", version),
                ("channel", "=", channel),
            ],
            limit=1,
        )
        values = {
            "scene_key": scene_key,
            "product_key": product_key,
            "capability_key": capability_key,
            "label": label,
            "route": route,
            "version": version,
            "channel": channel,
            "is_active": True,
            "source_type": source_type,
            "source_ref": source_ref,
            "source_contract_version": SCENE_CONTRACT_STANDARD_VERSION,
            "contract_json": self._normalize_contract(contract, scene_key=scene_key, product_key=product_key, capability_key=capability_key),
            "meta_json": meta or {},
            "note": note,
        }
        if cloned_from_snapshot_id:
            values["cloned_from_snapshot_id"] = int(cloned_from_snapshot_id)
        if rec:
            rec.write(values)
            target = rec
        else:
            target = model.create(values)
        return target.to_runtime_dict()

    def list_snapshots(self, *, product_key: str | None = None, scene_key: str | None = None) -> list[dict[str, Any]]:
        domain = [("active", "=", True)]
        if _text(product_key):
            domain.append(("product_key", "=", _text(product_key)))
        if _text(scene_key):
            domain.append(("scene_key", "=", _text(scene_key)))
        return [rec.to_runtime_dict() for rec in self._model().search(domain)]

    def resolve_snapshot(
        self,
        *,
        scene_key: str,
        product_key: str,
        binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bind = _dict(binding)
        version = _text(bind.get("version")) or "v1"
        channel = _text(bind.get("channel")) or "stable"
        rec = self._model().search(
            [
                ("scene_key", "=", scene_key),
                ("product_key", "=", product_key),
                ("version", "=", version),
                ("channel", "=", channel),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            limit=1,
        )
        return rec.to_runtime_dict() if rec else {}

    def clone_snapshot(
        self,
        *,
        source_scene_key: str,
        source_product_key: str,
        source_version: str,
        source_channel: str,
        target_scene_key: str | None = None,
        target_product_key: str | None = None,
        target_capability_key: str | None = None,
        target_version: str,
        target_channel: str,
        target_label: str | None = None,
        target_route: str | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        rec = self._model().search(
            [
                ("scene_key", "=", source_scene_key),
                ("product_key", "=", source_product_key),
                ("version", "=", source_version),
                ("channel", "=", source_channel),
                ("active", "=", True),
            ],
            limit=1,
        )
        if not rec:
            raise ValueError(f"source snapshot not found: {source_product_key}/{source_scene_key}@{source_version}:{source_channel}")
        source = rec.to_runtime_dict()
        contract = deepcopy(_dict(source.get("contract_json")))
        scene_key = _text(target_scene_key) or _text(source.get("scene_key"))
        product_key = _text(target_product_key) or _text(source.get("product_key"))
        capability_key = _text(target_capability_key) or _text(source.get("capability_key"))
        label = _text(target_label) or _text(source.get("label"))
        route = _text(target_route) or _text(source.get("route"))
        contract = self._normalize_contract(contract, scene_key=scene_key, product_key=product_key, capability_key=capability_key)
        identity = _dict(contract.get("identity"))
        identity["version"] = _text(target_version) or "v1"
        if label:
            identity["title"] = label
        contract["identity"] = identity
        target = _dict(contract.get("target"))
        target["route"] = route
        target["openable"] = bool(route)
        contract["target"] = target
        governance = _dict(contract.get("governance"))
        governance["diagnostics_ref"] = "scene_snapshot.clone"
        contract["governance"] = governance
        return self.upsert_snapshot(
            scene_key=scene_key,
            product_key=product_key,
            capability_key=capability_key,
            label=label,
            route=route,
            version=_text(target_version) or "v1",
            channel=_text(target_channel) or "stable",
            contract=contract,
            source_type="scene_snapshot_clone",
            source_ref=f"{source_product_key}:{source_scene_key}@{source_version}:{source_channel}",
            note=note or "cloned from existing scene snapshot",
            meta={
                "cloned_from": {
                    "scene_key": source_scene_key,
                    "product_key": source_product_key,
                    "version": source_version,
                    "channel": source_channel,
                }
            },
            cloned_from_snapshot_id=int(source.get("id") or 0) or None,
        )

    def build_policy_binding_map(self, *, product_key: str) -> dict[str, dict[str, Any]]:
        policy = self.policy_service.get_policy(product_key=product_key)
        bindings = policy.get("scene_version_bindings") if isinstance(policy.get("scene_version_bindings"), dict) else {}
        out: dict[str, dict[str, Any]] = {}
        for scene_key, row in bindings.items():
            key = _text(scene_key)
            value = _dict(row)
            if not key:
                continue
            out[key] = {
                "version": _text(value.get("version")) or "v1",
                "channel": _text(value.get("channel")) or "stable",
            }
        return out
