# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import List, Tuple

from .capability_group_defaults import (
    DEFAULT_CAPABILITY_GROUPS,
    default_group_meta,
    default_group_order_map,
    infer_group_key,
)
from odoo.addons.smart_core.app_config_engine.capability.projection.capability_list_projection import (
    build_capability_list_projection,
)
from odoo.addons.smart_core.app_config_engine.capability.services.capability_registry_service import (
    CapabilityRegistryService,
)
from .capability_contribution_loader import (
    collect_capability_contributions,
    collect_capability_group_contributions,
)


def _default_group_meta(group_key: str) -> dict:
    return default_group_meta(group_key)


def _infer_group_key(capability_key: str) -> str:
    return infer_group_key(capability_key)


def _capability_legacy_fallback_enabled(env) -> bool:
    try:
        raw = env["ir.config_parameter"].sudo().get_param("smart_core.capability_legacy_fallback_enabled", "0")
    except Exception:
        return False
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def build_capability_groups(capabilities: List[dict]) -> List[dict]:
    grouped: dict[str, dict] = {}
    for idx, cap in enumerate(capabilities or []):
        if not isinstance(cap, dict):
            continue
        group_key = str(cap.get("group_key") or "").strip() or _infer_group_key(cap.get("key"))
        group_label = str(cap.get("group_label") or "").strip()
        meta = _default_group_meta(group_key)
        bucket = grouped.setdefault(
            group_key,
            {
                "key": group_key,
                "label": group_label or meta["label"],
                "icon": str(cap.get("group_icon") or meta.get("icon") or ""),
                "sequence": int(cap.get("group_sequence") or 0) or len(grouped) + 1,
                "capabilities": [],
                "capability_count": 0,
                "state_counts": {"READY": 0, "LOCKED": 0, "PREVIEW": 0},
                "capability_state_counts": {"allow": 0, "readonly": 0, "deny": 0, "pending": 0, "coming_soon": 0},
            },
        )
        if cap.get("group_label"):
            bucket["label"] = str(cap.get("group_label"))
        if cap.get("group_icon"):
            bucket["icon"] = str(cap.get("group_icon"))
        cap_group_sequence = int(cap.get("group_sequence") or 0)
        if cap_group_sequence > 0:
            current_sequence = int(bucket.get("sequence") or 0)
            bucket["sequence"] = cap_group_sequence if current_sequence <= 0 else min(current_sequence, cap_group_sequence)
        cap_copy = dict(cap)
        cap_copy["group_key"] = group_key
        cap_copy["group_label"] = bucket["label"]
        cap_copy["group_sequence"] = idx + 1
        bucket["capabilities"].append(cap_copy)
        bucket["capability_count"] = int(bucket.get("capability_count") or 0) + 1
        state = str(cap_copy.get("state") or "").strip().upper()
        capability_state = str(cap_copy.get("capability_state") or "").strip().lower()
        if state in bucket["state_counts"]:
            bucket["state_counts"][state] = int(bucket["state_counts"].get(state) or 0) + 1
        if capability_state in bucket["capability_state_counts"]:
            bucket["capability_state_counts"][capability_state] = (
                int(bucket["capability_state_counts"].get(capability_state) or 0) + 1
            )

    order_map = default_group_order_map(DEFAULT_CAPABILITY_GROUPS)
    result = list(grouped.values())
    result.sort(
        key=lambda item: (
            int(item.get("sequence") or 0) if int(item.get("sequence") or 0) > 0 else order_map.get(item.get("key"), 999),
            order_map.get(item.get("key"), 999),
            str(item.get("label") or ""),
        )
    )
    for seq, item in enumerate(result, start=1):
        item["sequence"] = seq
    return result


def load_capabilities_for_user(env, user) -> List[dict]:
    capabilities, _timings = load_capabilities_for_user_with_timings(env, user)
    return capabilities


def load_capabilities_for_user_with_timings(env, user) -> Tuple[List[dict], dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    legacy_fallback_enabled = _capability_legacy_fallback_enabled(env)
    stage_ts = time.perf_counter()
    try:
        registry_service = CapabilityRegistryService(platform_owner="smart_core")
        artifact, registry_timings_ms = registry_service.get_registry_artifact_with_timings(env, user=user)
        stage_ts = _mark("runtime_query_registry_build", stage_ts)
        if registry_timings_ms:
            for key, value in registry_timings_ms.items():
                timings_ms[f"runtime_query_registry.{key}"] = int(value)
        if isinstance(artifact, dict):
            timings_ms["runtime_query_registry.artifact_fallback_used"] = int(bool(artifact.get("fallback_used")))
            if artifact.get("source"):
                timings_ms["runtime_query_registry.artifact_source_present"] = 1
            if artifact.get("fallback_reason"):
                timings_ms["runtime_query_registry.artifact_fallback_reason_present"] = 1
        rows = artifact.get("rows") if isinstance(artifact, dict) else []
        runtime_caps = build_capability_list_projection(rows)
        stage_ts = _mark("runtime_query_list_projection", stage_ts)
        if isinstance(runtime_caps, list):
            if runtime_caps or not legacy_fallback_enabled:
                return runtime_caps, timings_ms
    except Exception:
        stage_ts = _mark("runtime_query_registry_build", stage_ts)
        if not legacy_fallback_enabled:
            return [], timings_ms

    extension_caps, _errors = collect_capability_contributions(env, user)
    stage_ts = _mark("extension_contributions_fallback", stage_ts)
    if extension_caps:
        return extension_caps, timings_ms

    try:
        extension_groups = collect_capability_group_contributions(env)
        stage_ts = _mark("extension_group_contributions", stage_ts)
        if isinstance(extension_groups, list) and extension_groups:
            global DEFAULT_CAPABILITY_GROUPS
            DEFAULT_CAPABILITY_GROUPS = [dict(item) for item in extension_groups if isinstance(item, dict)]
    except Exception:
        stage_ts = _mark("extension_group_contributions", stage_ts)

    try:
        cap_model = env["sc.capability"].sudo()
        stage_ts = _mark("capability_model_access", stage_ts)
    except Exception:
        return [], timings_ms
    try:
        caps = cap_model.search([("active", "=", True)], order="sequence, id")
        stage_ts = _mark("capability_model_search", stage_ts)
    except Exception:
        return [], timings_ms
    out: List[dict] = []
    for rec in caps:
        try:
            if rec._user_visible(user):
                out.append(rec.to_public_dict(user))
        except Exception:
            continue
    _mark("capability_model_projection", stage_ts)
    return out, timings_ms
