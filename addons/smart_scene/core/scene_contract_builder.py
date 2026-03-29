# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from .scene_parser_semantic_bridge import apply_scene_parser_semantic_bridge


REQUIRED_TOP_LEVEL_KEYS = (
    "contract_version",
    "scene",
    "page",
    "nav_ref",
    "zones",
    "blocks",
    "record",
    "permissions",
    "actions",
    "extensions",
    "diagnostics",
)


def _synthetic_menu_id(key: str, base: int = 700_000_000, span: int = 200_000_000) -> int:
    import zlib

    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def _normalize_nav_ref(
    nav_ref: Dict[str, Any] | None,
    *,
    scene: Dict[str, Any],
    page: Dict[str, Any],
    diagnostics: Dict[str, Any] | None,
) -> Dict[str, Any]:
    payload = dict(nav_ref or {})
    diagnostics_payload = dict(diagnostics or {})
    scene_key = str(
        payload.get("active_scene_key")
        or scene.get("scene_key")
        or scene.get("key")
        or scene.get("code")
        or ""
    ).strip()
    active_menu_id = payload.get("active_menu_id")
    if active_menu_id is None:
        active_menu_id = page.get("menu_id")
    if active_menu_id is None:
        active_menu_id = diagnostics_payload.get("active_menu_id")
    if active_menu_id is None and scene_key:
        active_menu_id = _synthetic_menu_id(f"scene:{scene_key}")
    return {
        "active_scene_key": scene_key,
        "active_menu_id": int(active_menu_id) if isinstance(active_menu_id, int) or str(active_menu_id).isdigit() else None,
        "active_menu_key": str(payload.get("active_menu_key") or (f"scene:{scene_key}" if scene_key else "")).strip(),
    }


def _normalize_zones_and_blocks(zones: Dict[str, Any]) -> tuple[list[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    zone_rows = []
    blocks: Dict[str, Dict[str, Any]] = {}
    if not isinstance(zones, dict):
        return zone_rows, blocks

    for zone_key, zone in zones.items():
        if not isinstance(zone, dict):
            continue
        normalized_zone_key = str(zone.get("zone_key") or zone_key or "").strip()
        if not normalized_zone_key:
            continue
        block_keys = []
        block_rows = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for index, block in enumerate(block_rows):
            if not isinstance(block, dict):
                continue
            block_key = str(block.get("block_key") or block.get("key") or f"{normalized_zone_key}.block.{index}").strip()
            if not block_key:
                continue
            block_keys.append(block_key)
            if block_key not in blocks:
                blocks[block_key] = dict(block)

        zone_rows.append(
            {
                "key": normalized_zone_key,
                "title": str(zone.get("title") or normalized_zone_key),
                "zone_type": str(zone.get("zone_type") or "secondary"),
                "display_mode": str(zone.get("display_mode") or "stack"),
                "block_keys": block_keys,
                "priority": int(zone.get("priority") or 0),
            }
        )

    return zone_rows, blocks


def _normalize_actions(actions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(actions or {})
    action_groups = {
        "primary_actions": list(payload.get("primary_actions") or []),
        "secondary_actions": list(payload.get("secondary_actions") or []),
        "contextual_actions": list(payload.get("contextual_actions") or []),
        "danger_actions": list(payload.get("danger_actions") or []),
        "recommended_actions": list(payload.get("recommended_actions") or []),
    }
    return action_groups


def _normalize_permissions(permissions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(permissions or {})
    return {
        "can_read": bool(payload.get("can_read", True)),
        "can_edit": bool(payload.get("can_edit", True)),
        "can_create": bool(payload.get("can_create", False)),
        "can_delete": bool(payload.get("can_delete", False)),
        "disabled_actions": dict(payload.get("disabled_actions") or {}),
        "record_state_summary": dict(payload.get("record_state_summary") or {}),
    }


def _normalize_extensions(extensions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(extensions or {})
    return {
        "injected_blocks": list(payload.get("injected_blocks") or []),
        "injected_actions": list(payload.get("injected_actions") or []),
        "providers": list(payload.get("providers") or []),
    }


def _normalize_diagnostics(diagnostics: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(diagnostics or {})
    payload.setdefault("trace_id", str(payload.get("trace_id") or ""))
    payload.setdefault("source_versions", {})
    payload.setdefault("build_pipeline", ["scene_resolver", "structure_mapper", "layout_orchestrator", "scene_contract_builder"])
    payload.setdefault("warnings", [])
    payload.setdefault("semantic_runtime_state", {})
    payload.setdefault("semantic_runtime_assertions", {})
    payload.setdefault("consumer_semantics", {})
    return payload


def _build_semantic_runtime_assertions(*, page: Dict[str, Any], permissions: Dict[str, Any], diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    runtime_state = dict(diagnostics.get("semantic_runtime_state") or {})
    summary = dict(permissions.get("record_state_summary") or {})
    page_status = str(page.get("page_status") or "").strip()
    runtime_page_status = str(runtime_state.get("page_status") or "").strip()
    summary_page_status = str(summary.get("page_status") or "").strip()

    return {
        "runtime_state_present": bool(runtime_state),
        "page_status_aligned": (not runtime_page_status) or runtime_page_status == page_status,
        "record_state_summary_aligned": (not summary_page_status) or summary_page_status == page_status,
        "current_state_projected": (not runtime_state.get("current_state")) or runtime_state.get("current_state") == summary.get("current_state"),
    }


def _build_consumer_semantics(*, page: Dict[str, Any], permissions: Dict[str, Any], diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    runtime_state = dict(diagnostics.get("semantic_runtime_state") or {})
    assertions = dict(diagnostics.get("semantic_runtime_assertions") or {})
    bridge_assertions = dict(diagnostics.get("consumer_runtime_assertions") or {})
    summary = dict(permissions.get("record_state_summary") or {})
    return {
        "runtime": {
            "page_status": str(page.get("page_status") or ""),
            "runtime_page_status": str(runtime_state.get("page_status") or ""),
            "current_state": str(runtime_state.get("current_state") or summary.get("current_state") or ""),
            "missing_required_count": int(runtime_state.get("missing_required_count") or summary.get("missing_required_count") or 0),
            "active_transition_count": int(runtime_state.get("active_transition_count") or summary.get("active_transition_count") or 0),
            "alignment": {
                "runtime_state_present": bool(assertions.get("runtime_state_present")),
                "page_status_aligned": bool(assertions.get("page_status_aligned")),
                "record_state_summary_aligned": bool(assertions.get("record_state_summary_aligned")),
                "current_state_projected": bool(assertions.get("current_state_projected")),
            },
            "bridge_alignment": {
                "consumer_runtime_present": bool(bridge_assertions.get("consumer_runtime_present")),
                "semantic_runtime_state_present": bool(bridge_assertions.get("semantic_runtime_state_present")),
                "page_status_aligned": bool(bridge_assertions.get("page_status_aligned")),
                "current_state_aligned": bool(bridge_assertions.get("current_state_aligned")),
            },
        }
    }


def _build_consumer_runtime_alias(*, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    consumer_semantics = dict(diagnostics.get("consumer_semantics") or {})
    runtime = dict(consumer_semantics.get("runtime") or {})
    return runtime


def validate_scene_contract_shape(contract: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not isinstance(contract, dict):
        return {"ok": False, "issues": [{"code": "contract_not_dict"}]}
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in contract:
            issues.append({"code": "missing_key", "key": key})
    diagnostics = contract.get("diagnostics")
    if "diagnostics" in contract and not isinstance(diagnostics, dict):
        issues.append({"code": "diagnostics_not_dict"})
    elif isinstance(diagnostics, dict) and "semantic_runtime_state" in diagnostics and not isinstance(
        diagnostics.get("semantic_runtime_state"), dict
    ):
        issues.append({"code": "invalid_diagnostics_semantic_runtime_state"})
    elif isinstance(diagnostics, dict) and "consumer_runtime" in diagnostics and not isinstance(
        diagnostics.get("consumer_runtime"), dict
    ):
        issues.append({"code": "invalid_diagnostics_consumer_runtime"})
    return {"ok": len(issues) == 0, "issues": issues}


def build_scene_contract(
    *,
    scene: Dict[str, Any],
    page: Dict[str, Any],
    zones: Dict[str, Any],
    record: Dict[str, Any] | None = None,
    nav_ref: Dict[str, Any] | None = None,
    permissions: Dict[str, Any] | None = None,
    actions: Dict[str, Any] | None = None,
    extensions: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
    semantic_surface: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    zone_rows, block_rows = _normalize_zones_and_blocks(dict(zones or {}))
    normalized_scene = dict(scene or {})
    normalized_page = dict(page or {})

    if "scene_key" not in normalized_scene:
        normalized_scene["scene_key"] = str(normalized_scene.get("key") or "").strip()
    if "record_id" not in normalized_page:
        normalized_page["record_id"] = None

    contract = {
        "contract_version": "v1",
        "scene": normalized_scene,
        "page": normalized_page,
        "nav_ref": _normalize_nav_ref(nav_ref, scene=normalized_scene, page=normalized_page, diagnostics=diagnostics),
        "zones": dict(zones or {}),
        "zones_v1": zone_rows,
        "blocks": block_rows,
        "record": dict(record or {}),
        "permissions": _normalize_permissions(permissions),
        "actions": _normalize_actions(actions),
        "extensions": _normalize_extensions(extensions),
        "diagnostics": _normalize_diagnostics(diagnostics),
    }
    contract["diagnostics"]["semantic_runtime_assertions"] = _build_semantic_runtime_assertions(
        page=contract["page"],
        permissions=contract["permissions"],
        diagnostics=contract["diagnostics"],
    )
    contract["diagnostics"]["consumer_semantics"] = _build_consumer_semantics(
        page=contract["page"],
        permissions=contract["permissions"],
        diagnostics=contract["diagnostics"],
    )
    contract["diagnostics"]["consumer_runtime"] = _build_consumer_runtime_alias(diagnostics=contract["diagnostics"])
    contract["scene_contract_v1"] = {
        "contract_version": "v1",
        "scene": dict(contract["scene"]),
        "page": dict(contract["page"]),
        "nav_ref": dict(contract["nav_ref"]),
        "zones": list(contract["zones_v1"]),
        "blocks": dict(contract["blocks"]),
        "actions": dict(contract["actions"]),
        "permissions": dict(contract["permissions"]),
        "record": dict(contract["record"]),
        "extensions": dict(contract["extensions"]),
        "diagnostics": dict(contract["diagnostics"]),
    }
    contract = apply_scene_parser_semantic_bridge(contract, semantic_surface)
    contract["diagnostics"]["consumer_semantics"] = _build_consumer_semantics(
        page=contract["page"],
        permissions=contract["permissions"],
        diagnostics=contract["diagnostics"],
    )
    contract["diagnostics"]["consumer_runtime"] = _build_consumer_runtime_alias(diagnostics=contract["diagnostics"])
    if isinstance(contract.get("scene_contract_v1"), dict):
        contract["scene_contract_v1"]["diagnostics"] = dict(contract["diagnostics"])
    verdict = validate_scene_contract_shape(contract)
    contract["diagnostics"]["scene_contract_shape"] = verdict
    return contract
