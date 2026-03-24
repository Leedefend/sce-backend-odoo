# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.scene_contract_builder import (
    build_release_surface_scene_contract_from_delivery_entry,
)
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService


class SceneService:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = SceneSnapshotService(env)

    def build_entries(self, *, policy: dict, scenes: list[dict]) -> list[dict]:
        scene_index = {}
        binding_map = (
            policy.get("scene_version_bindings") if isinstance(policy.get("scene_version_bindings"), dict) else {}
        )
        binding_diagnostics = (
            policy.get("scene_binding_diagnostics") if isinstance(policy.get("scene_binding_diagnostics"), dict) else {}
        )
        for item in scenes or []:
            if not isinstance(item, dict):
                continue
            scene_key = str(item.get("code") or item.get("key") or "").strip()
            if scene_key and scene_key not in scene_index:
                scene_index[scene_key] = item

        entries: list[dict] = []
        for row in policy.get("scenes") or []:
            if not isinstance(row, dict):
                continue
            scene_key = str(row.get("scene_key") or "").strip()
            if not scene_key:
                continue
            source = scene_index.get(scene_key) or {}
            target = source.get("target") if isinstance(source.get("target"), dict) else {}
            route = str(target.get("route") or row.get("route") or f"/s/{scene_key}").strip()
            label = str(
                row.get("label")
                or source.get("name")
                or source.get("title")
                or source.get("label")
                or scene_key
            ).strip()
            standard_contract = build_release_surface_scene_contract_from_delivery_entry(
                {
                    "scene_key": scene_key,
                    "label": label,
                    "route": route,
                    "product_key": str(row.get("product_key") or "").strip(),
                    "capability_key": str(row.get("capability_key") or "").strip(),
                    "requires_project_context": bool(row.get("requires_project_context", False)),
                    "state": "present" if source else "policy_only",
                }
            )
            snapshot_binding = binding_map.get(scene_key) if isinstance(binding_map.get(scene_key), dict) else {}
            snapshot, snapshot_diagnostics = self.snapshot_service.resolve_snapshot_with_diagnostics(
                scene_key=scene_key,
                product_key=str(row.get("product_key") or "").strip(),
                binding=snapshot_binding,
            )
            snapshot_contract = snapshot.get("contract_json") if isinstance(snapshot.get("contract_json"), dict) else {}
            entries.append(
                {
                    "scene_key": scene_key,
                    "label": label,
                    "route": route,
                    "product_key": str(row.get("product_key") or "").strip(),
                    "capability_key": str(row.get("capability_key") or "").strip(),
                    "requires_project_context": bool(row.get("requires_project_context", False)),
                    "state": "present" if source else "policy_only",
                    "source": "delivery_engine_v1",
                    "scene_contract_standard_v1": snapshot_contract or standard_contract,
                    "scene_asset_binding": {
                        "version": str(snapshot_binding.get("version") or "v1").strip() or "v1",
                        "channel": str(snapshot_binding.get("channel") or "stable").strip() or "stable",
                        "resolved": bool(snapshot),
                        "snapshot_id": int(snapshot.get("id") or 0),
                        "snapshot_state": str(snapshot.get("state") or snapshot_diagnostics.get("snapshot_state") or "").strip(),
                        "snapshot_fallback_reason": str(snapshot_diagnostics.get("snapshot_fallback_reason") or "").strip(),
                        "binding_allowed": bool(_binding_diag(binding_diagnostics, scene_key).get("binding_allowed", False)),
                    },
                }
            )
        return entries


def _binding_diag(diags: dict, scene_key: str) -> dict:
    row = diags.get(scene_key)
    return row if isinstance(row, dict) else {}
