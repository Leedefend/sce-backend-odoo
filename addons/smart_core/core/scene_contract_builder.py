# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from odoo.addons.smart_core.core.scene_contract_parser_semantic_bridge import (
    apply_scene_contract_parser_semantic_bridge,
)


SCENE_CONTRACT_STANDARD_VERSION = "scene_contract_standard_v1"

_PRODUCT_TITLE_BY_KEY = {
    "fr1": "FR-1 项目立项",
    "fr2": "FR-2 项目推进",
    "fr3": "FR-3 成本记录",
    "fr4": "FR-4 付款记录",
    "fr5": "FR-5 结算结果",
    "my_work": "我的工作",
}

_ROUTE_ONLY_ACTIONS = {
    "projects.intake": {
        "primary_actions": [
            {
                "key": "quick_project_create",
                "label": "快速创建（推荐）",
                "target": {"type": "route", "route": "/f/project.project/new?scene_key=projects.intake&intake_mode=quick"},
            }
        ],
        "secondary_actions": [
            {
                "key": "standard_project_intake",
                "label": "标准立项",
                "target": {"type": "route", "route": "/f/project.project/new?scene_key=projects.intake"},
            }
        ],
    },
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clone_list(rows: Any) -> list[dict[str, Any]]:
    return [deepcopy(row) for row in _list(rows) if isinstance(row, dict)]


def _resolve_product_title(product_key: str) -> str:
    return _PRODUCT_TITLE_BY_KEY.get(_text(product_key), _text(product_key) or "Released Scene")


def _resolve_contract_title(*, title: str, scene_label: str, product_key: str, scene_key: str) -> str:
    return title or scene_label or _resolve_product_title(product_key) or scene_key


def _normalize_block_rows(blocks: Any, *, zone_key: str = "primary") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(_list(blocks), start=1):
        if not isinstance(item, dict):
            continue
        key = _text(item.get("key") or item.get("block_key") or f"{zone_key}.block.{index}")
        if not key:
            continue
        rows.append(
            {
                "key": key,
                "title": _text(item.get("title") or key),
                "state": _text(item.get("state") or "ready"),
                "block_type": _text(item.get("block_type") or item.get("type") or "runtime_block"),
                "source": _text(item.get("source") or "runtime_entry"),
            }
        )
    return rows


def _normalize_zones(*, block_rows: list[dict[str, Any]], layout: str) -> list[dict[str, Any]]:
    if not block_rows:
        return []
    return [
        {
            "key": "primary",
            "title": "Primary",
            "layout": layout,
            "block_keys": [_text(row.get("key")) for row in block_rows if _text(row.get("key"))],
        }
    ]


def _normalize_next_action(payload: Any) -> dict[str, Any]:
    row = _dict(payload)
    if not row:
        return {}
    params = _dict(row.get("params"))
    target = _dict(row.get("target"))
    normalized = {
        "key": _text(row.get("key")),
        "label": _text(row.get("label") or row.get("title")),
        "intent": _text(row.get("intent")),
        "params": params,
        "reason_code": _text(row.get("reason_code")),
        "target": {
            "type": _text(target.get("type") or ("intent" if _text(row.get("intent")) else "")),
            "route": _text(target.get("route")),
            "scene_key": _text(target.get("scene_key")),
        },
    }
    if not normalized["key"] and normalized["intent"]:
        normalized["key"] = normalized["intent"].replace(".", "_")
    if not normalized["label"] and normalized["intent"]:
        normalized["label"] = normalized["intent"]
    if not any(normalized.values()):
        return {}
    return normalized


def _normalize_action_rows(rows: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in _list(rows):
        if not isinstance(item, dict):
            continue
        key = _text(item.get("key"))
        label = _text(item.get("label") or item.get("title") or key)
        target = _dict(item.get("target"))
        out.append(
            {
                "key": key,
                "label": label,
                "intent": _text(item.get("intent")),
                "params": _dict(item.get("params")),
                "target": {
                    "type": _text(target.get("type")),
                    "route": _text(target.get("route")),
                    "scene_key": _text(target.get("scene_key")),
                },
            }
        )
    return out


def build_release_surface_scene_contract(
    *,
    scene_key: str,
    title: str,
    product_key: str,
    capability: str,
    route: str,
    status: str,
    state_tone: str,
    reason_code: str,
    message: str,
    layout: str,
    blocks: Any = None,
    primary_actions: Any = None,
    secondary_actions: Any = None,
    next_action: Any = None,
    trace_id: str = "",
    policy_match: bool = True,
    released: bool = True,
    diagnostics_ref: str = "",
    target_name: str = "same_tab",
) -> dict[str, Any]:
    block_rows = _normalize_block_rows(blocks, zone_key="primary")
    zones = _normalize_zones(block_rows=block_rows, layout=layout)
    return {
        "contract_version": SCENE_CONTRACT_STANDARD_VERSION,
        "identity": {
            "scene_key": _text(scene_key),
            "title": _text(title),
            "product_key": _text(product_key),
            "capability": _text(capability),
            "version": "v1",
        },
        "target": {
            "route": _text(route),
            "openable": bool(_text(route)),
            "target": _text(target_name) or "same_tab",
        },
        "state": {
            "status": _text(status) or "ready",
            "state_tone": _text(state_tone) or "stable",
            "reason_code": _text(reason_code) or "RELEASED_SURFACE_READY",
            "message": _text(message) or _text(title),
        },
        "page": {
            "layout": _text(layout) or "stack",
            "zones": zones,
            "blocks": block_rows,
        },
        "actions": {
            "primary_actions": _normalize_action_rows(primary_actions),
            "secondary_actions": _normalize_action_rows(secondary_actions),
            "next_action": _normalize_next_action(next_action),
        },
        "governance": {
            "contract_version": SCENE_CONTRACT_STANDARD_VERSION,
            "trace_id": _text(trace_id),
            "policy_match": bool(policy_match),
            "released": bool(released),
            "diagnostics_ref": _text(diagnostics_ref) or "released_scene_contract",
        },
    }


def build_release_surface_scene_contract_from_delivery_entry(entry: dict[str, Any], *, trace_id: str = "") -> dict[str, Any]:
    row = _dict(entry)
    scene_key = _text(row.get("scene_key"))
    route = _text(row.get("route"))
    product_key = _text(row.get("product_key"))
    capability = _text(row.get("capability_key"))
    label = _text(row.get("label")) or _resolve_product_title(product_key)
    route_actions = _ROUTE_ONLY_ACTIONS.get(scene_key, {})
    requires_project_context = bool(row.get("requires_project_context", False))
    message = "当前发布入口已冻结到产品面" if not requires_project_context else "当前发布入口需要项目上下文后继续"
    layout = "entry_cards" if scene_key == "projects.intake" else "entry_shell"
    return build_release_surface_scene_contract(
        scene_key=scene_key,
        title=label,
        product_key=product_key,
        capability=capability,
        route=route,
        status=_text(row.get("state") or "present"),
        state_tone="stable",
        reason_code="DELIVERY_ENGINE_RELEASED_SCENE",
        message=message,
        layout=layout,
        blocks=row.get("blocks") or [],
        primary_actions=route_actions.get("primary_actions") or [],
        secondary_actions=route_actions.get("secondary_actions") or [],
        next_action=row.get("next_action") or {},
        trace_id=trace_id,
        policy_match=True,
        released=True,
        diagnostics_ref="delivery_engine_v1.scenes",
    )


def build_release_surface_scene_contract_from_runtime_entry(
    payload: dict[str, Any],
    *,
    product_key: str,
    capability: str,
    route: str,
    diagnostics_ref: str,
    trace_id: str = "",
) -> dict[str, Any]:
    row = _dict(payload)
    title = _resolve_contract_title(
        title=_text(row.get("title")),
        scene_label=_text(row.get("scene_label")),
        product_key=product_key,
        scene_key=_text(row.get("scene_key")),
    )
    next_action = row.get("suggested_action") if isinstance(row.get("suggested_action"), dict) else {}
    contract = build_release_surface_scene_contract(
        scene_key=_text(row.get("scene_key")),
        title=title,
        product_key=product_key,
        capability=capability,
        route=route,
        status="ready",
        state_tone="stable",
        reason_code=_text(_dict(next_action).get("reason_code")) or "RELEASED_RUNTIME_ENTRY_READY",
        message=_text(row.get("state_fallback_text")) or title,
        layout="workspace_stack",
        blocks=row.get("blocks") or [],
        primary_actions=[],
        secondary_actions=[],
        next_action=next_action,
        trace_id=trace_id,
        policy_match=True,
        released=True,
        diagnostics_ref=diagnostics_ref,
    )
    return apply_scene_contract_parser_semantic_bridge(contract, row)


def build_release_surface_scene_contract_from_page_contract(
    page_contract: dict[str, Any],
    *,
    scene_key: str,
    title: str,
    product_key: str,
    capability: str,
    route: str,
    diagnostics_ref: str,
    trace_id: str = "",
) -> dict[str, Any]:
    page_row = _dict(page_contract)
    orchestration = _dict(page_row.get("page_orchestration_v1"))
    page_meta = _dict(orchestration.get("page"))
    zones = _list(orchestration.get("zones"))
    action_schema = _dict(orchestration.get("action_schema"))
    actions = _dict(action_schema.get("actions"))
    primary_actions = []
    for key in ("open_my_work",):
        action = _dict(actions.get(key))
        if not action:
            continue
        primary_actions.append(
            {
                "key": key,
                "label": _text(action.get("label")) or key,
                "intent": _text(action.get("intent")),
                "params": _dict(action.get("params")),
            }
        )
    block_rows = []
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        for block in _list(zone.get("blocks")):
            if not isinstance(block, dict):
                continue
            block_rows.append(
                {
                    "key": _text(block.get("key")),
                    "title": _text(block.get("title") or block.get("key")),
                    "state": "ready",
                    "block_type": _text(block.get("block_type") or "page_block"),
                    "source": "page_contract",
                }
            )
    normalized_title = _resolve_contract_title(
        title=_text(page_meta.get("title")) or title,
        scene_label=title,
        product_key=product_key,
        scene_key=scene_key,
    )
    contract = build_release_surface_scene_contract(
        scene_key=scene_key,
        title=normalized_title,
        product_key=product_key,
        capability=capability,
        route=route,
        status="ready",
        state_tone="stable",
        reason_code="PAGE_CONTRACT_RELEASE_READY",
        message=normalized_title,
        layout=_text(page_meta.get("layout_mode")) or "workspace",
        blocks=block_rows,
        primary_actions=primary_actions,
        secondary_actions=[],
        next_action={},
        trace_id=trace_id,
        policy_match=True,
        released=True,
        diagnostics_ref=diagnostics_ref,
    )
    surface_source = _dict(orchestration.get("meta")).get("parser_semantic_surface")
    source_payload = surface_source if isinstance(surface_source, dict) else page_row
    return apply_scene_contract_parser_semantic_bridge(contract, source_payload)


def attach_release_surface_scene_contract(
    payload: dict[str, Any],
    *,
    product_key: str,
    capability: str,
    route: str,
    diagnostics_ref: str,
    trace_id: str = "",
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    payload["scene_contract_standard_v1"] = build_release_surface_scene_contract_from_runtime_entry(
        payload,
        product_key=product_key,
        capability=capability,
        route=route,
        diagnostics_ref=diagnostics_ref,
        trace_id=trace_id,
    )
    return payload
