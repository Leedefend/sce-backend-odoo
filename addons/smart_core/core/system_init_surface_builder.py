# -*- coding: utf-8 -*-
from __future__ import annotations

class SystemInitSurfaceBuilder:
    @staticmethod
    def apply(
        *,
        data: dict,
        contract_mode: str,
        scene_diagnostics: dict,
        capability_surface_engine,
        identity_resolver,
        user_groups_xmlids: list,
        nav_tree: list,
        scene_diagnostics_builder,
        build_capability_groups_fn,
        apply_contract_governance_fn,
    ) -> tuple[dict, dict]:
        pre_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        pre_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        data = apply_contract_governance_fn(data, contract_mode)
        data["capability_groups"] = build_capability_groups_fn(data.get("capabilities") or [])
        data["capability_surface_summary"] = capability_surface_engine.build_summary(
            data.get("capabilities") or [],
            data.get("capability_groups") or [],
        )
        post_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        post_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        scene_diagnostics["governance"] = scene_diagnostics_builder.governance(
            contract_mode=contract_mode,
            before_scene_count=pre_governance_scene_count,
            before_capability_count=pre_governance_capability_count,
            after_scene_count=post_governance_scene_count,
            after_capability_count=post_governance_capability_count,
        )
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        scene_keys_latest = {
            (s.get("code") or s.get("key"))
            for s in scenes_payload
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        data["role_surface"] = identity_resolver.build_role_surface(user_groups_xmlids, nav_tree, scene_keys_latest)
        data["role_surface_map"] = identity_resolver.build_role_surface_map_payload()
        return data, scene_diagnostics
