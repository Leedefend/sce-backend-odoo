# -*- coding: utf-8 -*-
from __future__ import annotations


def _text(value) -> str:
    return str(value or "").strip()


def _as_dict(value) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def build_direct_runtime_handoff(
    *,
    family: str,
    user_entry: str,
    final_scene: str,
    primary_action: dict,
    required_provider: str,
    fallback_policy: dict,
    rollout_wave: str = "wave_1",
) -> dict:
    return {
        "owner_layer": "scene_orchestration",
        "rollout_wave": rollout_wave,
        "family": family,
        "runtime_entry_type": "governed_user_flow",
        "runtime_consumer": "family_runtime_consumer",
        "runtime_mode": "direct",
        "user_entry": user_entry,
        "final_scene": final_scene,
        "primary_action": dict(primary_action),
        "required_provider": required_provider,
        "fallback_policy": dict(fallback_policy),
        "acceptance": {
            "runtime_ready": True,
            "workflow_ready": True,
            "advisory_only": True,
        },
    }


def build_wave1_rollout_handoff(runtime_handoff_surface: dict | None) -> dict:
    runtime_handoff = _as_dict(runtime_handoff_surface)
    if not runtime_handoff:
        return {}

    consume_mode = _text(runtime_handoff.get("consume_mode")) or "direct"
    advisory_only = consume_mode == "advisory"
    rollout_mode = "advisory_only" if advisory_only else "direct_runtime_handoff"

    return {
        "owner_layer": "scene_orchestration",
        "rollout_wave": "wave_1",
        "family": _text(runtime_handoff.get("family")),
        "rollout_mode": rollout_mode,
        "consume_mode": consume_mode,
        "runtime_entry_type": _text(runtime_handoff.get("runtime_entry_type")) or "governed_user_flow",
        "runtime_consumer": _text(runtime_handoff.get("runtime_consumer")) or "family_runtime_consumer",
        "runtime_mode": _text(runtime_handoff.get("runtime_mode")) or "direct",
        "user_entry": _text(runtime_handoff.get("user_entry")),
        "final_scene": _text(runtime_handoff.get("final_scene")),
        "primary_action": _as_dict(runtime_handoff.get("primary_action")),
        "required_provider": _text(runtime_handoff.get("required_provider")),
        "fallback_policy": _as_dict(runtime_handoff.get("fallback_policy")),
        "acceptance": {
            "runtime_ready": bool(runtime_handoff.get("runtime_ready")),
            "workflow_ready": bool(runtime_handoff.get("workflow_ready")),
            "advisory_only": advisory_only,
        },
    }
