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
        self._load_scenes(runtime_ctx=runtime_ctx)
        nav_targets = self._normalize_and_resolve(
            runtime_ctx=runtime_ctx,
            scene_normalizer=scene_normalizer,
            scene_drift_engine=scene_drift_engine,
            timing_prefix="",
        )
        self._inject_critical_error(runtime_ctx=runtime_ctx)
        self._evaluate_auto_degrade(
            runtime_ctx=runtime_ctx,
            scene_normalizer=scene_normalizer,
            scene_drift_engine=scene_drift_engine,
            auto_degrade_engine=auto_degrade_engine,
            nav_targets=nav_targets,
        )
        scenes_payload = (
            runtime_ctx.data.get("scenes")
            if isinstance(runtime_ctx.data.get("scenes"), list)
            else []
        )
        runtime_ctx.data["scenes"] = scenes_payload
        return runtime_ctx

    def _load_scenes(self, *, runtime_ctx):
        env = runtime_ctx.env
        data = runtime_ctx.data
        scene_channel = runtime_ctx.scene_channel
        rollback_active = runtime_ctx.rollback_active
        scene_diagnostics = runtime_ctx.scene_diagnostics

        contract_payload, contract_ref = runtime_ctx.load_scene_contract_fn(
            env, scene_channel, rollback_active
        )
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
            data["scenes"] = runtime_ctx.merge_missing_scenes_fn(
                env, data.get("scenes"), scene_diagnostics["normalize_warnings"]
            )
            return

        t_load_start = time.time()
        scene_source = runtime_ctx.load_scenes_fallback_fn(
            env,
            drift=scene_diagnostics["drift"],
            logger=self._logger,
        )
        scene_diagnostics["loaded_from"] = scene_source.get("loaded_from") or "fallback"
        scene_diagnostics["timings"]["load_ms"] = int((time.time() - t_load_start) * 1000)
        scenes_payload = scene_source.get("scenes") if isinstance(scene_source.get("scenes"), list) else []
        if scenes_payload:
            data["scenes"] = scenes_payload
            data["scene_version"] = scene_source.get("scene_version") or data.get("scene_version")
            data["schema_version"] = scene_source.get("schema_version") or data.get("schema_version")
            scene_diagnostics["scene_version"] = data.get("scene_version")
            scene_diagnostics["schema_version"] = data.get("schema_version")

    def _normalize_and_resolve(
        self,
        *,
        runtime_ctx,
        scene_normalizer,
        scene_drift_engine,
        timing_prefix: str,
    ):
        env = runtime_ctx.env
        data = runtime_ctx.data
        nav_tree = runtime_ctx.nav_tree
        scene_diagnostics = runtime_ctx.scene_diagnostics
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []

        norm_timing_key = f"{timing_prefix}normalize_ms"
        resolve_timing_key = f"{timing_prefix}resolve_ms"

        t_norm_start = time.time()
        scene_normalizer.normalize_structure(
            scenes_payload,
            nav_tree,
            data.get("capabilities"),
            scene_diagnostics,
        )
        scene_diagnostics["timings"][norm_timing_key] = int((time.time() - t_norm_start) * 1000)

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
        scene_diagnostics["timings"][resolve_timing_key] = int((time.time() - t_resolve_start) * 1000)
        return nav_targets

    def _inject_critical_error(self, *, runtime_ctx):
        if not is_truthy(runtime_ctx.params.get("scene_inject_critical_error")):
            return
        if not runtime_ctx.diagnostics_collector.diagnostics_enabled(runtime_ctx.env):
            return
        runtime_ctx.append_resolve_error_fn(
            runtime_ctx.scene_diagnostics["resolve_errors"],
            scene_key="workspace.home",
            kind="target",
            code="TEST_CRITICAL_INJECTED",
            ref="smart_scene.test.injected",
            message="injected critical resolve error for auto-degrade smoke",
            severity="critical",
        )

    def _evaluate_auto_degrade(
        self,
        *,
        runtime_ctx,
        scene_normalizer,
        scene_drift_engine,
        auto_degrade_engine,
        nav_targets,
    ):
        env = runtime_ctx.env
        data = runtime_ctx.data
        scene_diagnostics = runtime_ctx.scene_diagnostics

        auto_degrade = auto_degrade_engine.evaluate(
            env,
            scene_diagnostics,
            runtime_ctx.user,
            runtime_ctx.trace_id,
            runtime_ctx.scene_channel,
        )
        scene_diagnostics["auto_degrade"] = auto_degrade
        if not auto_degrade.get("triggered"):
            return

        action_taken = auto_degrade.get("action_taken") or "rollback_pinned"
        runtime_ctx.scene_channel = "stable"
        runtime_ctx.rollback_active = action_taken == "rollback_pinned"
        data["scene_channel"] = runtime_ctx.scene_channel
        data["scene_contract_ref"] = (
            "stable/PINNED.json" if runtime_ctx.rollback_active else "stable/LATEST.json"
        )
        scene_diagnostics["rollback_active"] = bool(runtime_ctx.rollback_active)
        scene_diagnostics["rollback_ref"] = (
            data["scene_contract_ref"] if runtime_ctx.rollback_active else None
        )

        degraded_payload, degraded_ref = runtime_ctx.load_scene_contract_fn(
            env,
            runtime_ctx.scene_channel,
            runtime_ctx.rollback_active,
        )
        data["scene_contract_ref"] = degraded_ref
        if runtime_ctx.rollback_active:
            scene_diagnostics["rollback_ref"] = degraded_ref
        if not degraded_payload:
            return

        data["scenes"] = degraded_payload.get("scenes") or []
        data["scene_version"] = degraded_payload.get("scene_version") or data.get("scene_version")
        data["schema_version"] = degraded_payload.get("schema_version") or data.get("schema_version")
        scene_diagnostics["scene_version"] = data.get("scene_version")
        scene_diagnostics["schema_version"] = data.get("schema_version")
        scene_diagnostics["loaded_from"] = "contract"
        scene_diagnostics["resolve_errors"] = []
        scene_diagnostics["drift"] = []
        scene_diagnostics["normalize_warnings"] = []
        data["scenes"] = runtime_ctx.merge_missing_scenes_fn(
            env, data.get("scenes"), scene_diagnostics["normalize_warnings"]
        )

        self._normalize_and_resolve(
            runtime_ctx=runtime_ctx,
            scene_normalizer=scene_normalizer,
            scene_drift_engine=scene_drift_engine,
            timing_prefix="after_degrade_",
        )
        timings = scene_diagnostics["timings"]
        timings["normalize_after_degrade_ms"] = timings.pop("after_degrade_normalize_ms", 0)
        timings["resolve_after_degrade_ms"] = timings.pop("after_degrade_resolve_ms", 0)
