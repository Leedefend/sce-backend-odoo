# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from odoo.addons.smart_core.utils.contract_governance import is_truthy


class SceneRuntimeOrchestrator:
    def __init__(self, logger):
        self._logger = logger

    def execute(
        self,
        *,
        runtime_ctx,
        scene_normalizer,
        scene_drift_engine,
        auto_degrade_engine,
    ):
        env = runtime_ctx.env
        user = runtime_ctx.user
        params = runtime_ctx.params
        data = runtime_ctx.data
        nav_tree = runtime_ctx.nav_tree
        scene_channel = runtime_ctx.scene_channel
        rollback_active = runtime_ctx.rollback_active
        trace_id = runtime_ctx.trace_id
        diagnostics_collector = runtime_ctx.diagnostics_collector
        scene_diagnostics = runtime_ctx.scene_diagnostics
        load_scene_contract_fn = runtime_ctx.load_scene_contract_fn
        load_scenes_fallback_fn = runtime_ctx.load_scenes_fallback_fn
        merge_missing_scenes_fn = runtime_ctx.merge_missing_scenes_fn
        append_resolve_error_fn = runtime_ctx.append_resolve_error_fn

        contract_payload, contract_ref = load_scene_contract_fn(env, scene_channel, rollback_active)
        data["scene_contract_ref"] = contract_ref
        if rollback_active:
            scene_diagnostics["rollback_ref"] = contract_ref
        if contract_payload:
            data["scenes"] = contract_payload.get("scenes") or []
            data["scene_version"] = contract_payload.get("scene_version") or data.get("scene_version")
            data["schema_version"] = contract_payload.get("schema_version") or data.get("schema_version")
            scene_diagnostics["scene_version"] = data.get("scene_version")
            scene_diagnostics["schema_version"] = data.get("schema_version")
            scene_diagnostics["loaded_from"] = "contract"
            data["scenes"] = merge_missing_scenes_fn(
                env, data.get("scenes"), scene_diagnostics["normalize_warnings"]
            )
        else:
            t_load_start = time.time()
            scene_source = load_scenes_fallback_fn(env, drift=scene_diagnostics["drift"], logger=self._logger)
            scene_diagnostics["loaded_from"] = scene_source.get("loaded_from") or "fallback"
            scene_diagnostics["timings"]["load_ms"] = int((time.time() - t_load_start) * 1000)
            scenes_payload = scene_source.get("scenes") if isinstance(scene_source.get("scenes"), list) else []
            if scenes_payload:
                data["scenes"] = scenes_payload
                data["scene_version"] = scene_source.get("scene_version") or data.get("scene_version")
                data["schema_version"] = scene_source.get("schema_version") or data.get("schema_version")
                scene_diagnostics["scene_version"] = data.get("scene_version")
                scene_diagnostics["schema_version"] = data.get("schema_version")

        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        t_norm_start = time.time()
        scene_normalizer.normalize_structure(
            scenes_payload,
            nav_tree,
            data.get("capabilities"),
            scene_diagnostics,
        )
        scene_diagnostics["timings"]["normalize_ms"] = int((time.time() - t_norm_start) * 1000)
        nav_targets = scene_normalizer.index_nav_scene_targets(nav_tree)
        t_resolve_start = time.time()
        scene_normalizer.resolve_targets(
            env,
            scenes_payload,
            nav_tree,
            scene_diagnostics,
            nav_targets=nav_targets,
        )
        scene_drift_engine.evaluate(scenes_payload, scene_diagnostics)
        scene_diagnostics["timings"]["resolve_ms"] = int((time.time() - t_resolve_start) * 1000)

        if is_truthy(params.get("scene_inject_critical_error")) and diagnostics_collector.diagnostics_enabled(env):
            append_resolve_error_fn(
                scene_diagnostics["resolve_errors"],
                scene_key="projects.list",
                kind="target",
                code="TEST_CRITICAL_INJECTED",
                ref="smart_construction_scene.test.injected",
                message="injected critical resolve error for auto-degrade smoke",
                severity="critical",
            )

        auto_degrade = auto_degrade_engine.evaluate(
            env,
            scene_diagnostics,
            user,
            trace_id,
            scene_channel,
        )
        scene_diagnostics["auto_degrade"] = auto_degrade
        if auto_degrade.get("triggered"):
            action_taken = auto_degrade.get("action_taken") or "rollback_pinned"
            scene_channel = "stable"
            rollback_active = action_taken == "rollback_pinned"
            data["scene_channel"] = scene_channel
            data["scene_contract_ref"] = "stable/PINNED.json" if rollback_active else "stable/LATEST.json"
            scene_diagnostics["rollback_active"] = bool(rollback_active)
            scene_diagnostics["rollback_ref"] = data["scene_contract_ref"] if rollback_active else None

            degraded_payload, degraded_ref = load_scene_contract_fn(env, scene_channel, rollback_active)
            data["scene_contract_ref"] = degraded_ref
            if rollback_active:
                scene_diagnostics["rollback_ref"] = degraded_ref
            if degraded_payload:
                data["scenes"] = degraded_payload.get("scenes") or []
                data["scene_version"] = degraded_payload.get("scene_version") or data.get("scene_version")
                data["schema_version"] = degraded_payload.get("schema_version") or data.get("schema_version")
                scene_diagnostics["scene_version"] = data.get("scene_version")
                scene_diagnostics["schema_version"] = data.get("schema_version")
                scene_diagnostics["loaded_from"] = "contract"
                scene_diagnostics["resolve_errors"] = []
                scene_diagnostics["drift"] = []
                scene_diagnostics["normalize_warnings"] = []
                data["scenes"] = merge_missing_scenes_fn(
                    env, data.get("scenes"), scene_diagnostics["normalize_warnings"]
                )
                t_norm2 = time.time()
                scene_normalizer.normalize_structure(
                    data["scenes"],
                    nav_tree,
                    data.get("capabilities"),
                    scene_diagnostics,
                )
                scene_diagnostics["timings"]["normalize_after_degrade_ms"] = int((time.time() - t_norm2) * 1000)
                t_resolve2 = time.time()
                scene_normalizer.resolve_targets(
                    env,
                    data["scenes"],
                    nav_tree,
                    scene_diagnostics,
                    nav_targets=nav_targets,
                )
                scene_drift_engine.evaluate(data["scenes"], scene_diagnostics)
                scene_diagnostics["timings"]["resolve_after_degrade_ms"] = int((time.time() - t_resolve2) * 1000)

        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else scenes_payload
        data["scenes"] = scenes_payload
        runtime_ctx.data = data
        runtime_ctx.scene_channel = scene_channel
        runtime_ctx.rollback_active = rollback_active
        runtime_ctx.scene_diagnostics = scene_diagnostics
        return runtime_ctx
