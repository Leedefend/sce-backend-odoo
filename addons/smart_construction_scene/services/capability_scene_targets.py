# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from odoo.addons.smart_construction_scene import scene_registry


_SCENE_CONFIGS_CACHE: dict[str, list[dict[str, Any]]] = {}
_SCENE_MAP_CACHE: dict[str, dict[str, dict[str, Any]]] = {}
_TARGET_SCENE_LOOKUP_CACHE: dict[str, dict[tuple[str, str], str]] = {}


CAPABILITY_ENTRY_SCENE_MAP: dict[str, str] = {
    "project.initiation.enter": "projects.intake",
    "project.list.open": "projects.list",
    "project.board.open": "projects.ledger",
    "project.dashboard.enter": "project.management",
    "project.dashboard.open": "project.management",
    "project.plan_bootstrap.enter": "project.plan_bootstrap",
    "project.execution.enter": "project.execution",
    "project.execution.advance": "project.execution",
    "project.lifecycle.open": "portal.lifecycle",
    "project.task.list": "task.center",
    "project.task.board": "task.board",
    "project.document.open": "projects.ledger",
    "project.structure.manage": "cost.project_boq",
    "project.risk.list": "projects.ledger",
    "project.weekly_report.open": "projects.ledger",
    "project.lifecycle.transition": "portal.lifecycle",
    "finance.payment_request.list": "finance.payment_requests",
    "finance.payment_request.form": "finance.payment_requests",
    "finance.approval.center": "finance.center",
    "finance.ledger.payment": "finance.payment_ledger",
    "finance.ledger.treasury": "finance.treasury_ledger",
    "finance.settlement.order": "finance.settlement_orders",
    "finance.invoice.list": "finance.center",
    "finance.plan.funding": "finance.center",
    "finance.metrics.operating": "finance.operating_metrics",
    "finance.exception.monitor": "finance.operating_metrics",
    "cost.ledger.open": "cost.project_cost_ledger",
    "cost.budget.manage": "cost.project_budget",
    "cost.boq.manage": "cost.project_boq",
    "cost.progress.report": "cost.project_progress",
    "cost.profit.compare": "cost.profit_compare",
    "contract.center.open": "contract.center",
    "contract.income.track": "projects.ledger",
    "contract.expense.track": "projects.ledger",
    "contract.settlement.audit": "finance.settlement_orders",
    "analytics.dashboard.executive": "projects.dashboard",
    "analytics.lifecycle.monitor": "portal.lifecycle",
    "analytics.exception.list": "finance.operating_metrics",
    "analytics.project.focus": "projects.list",
    "governance.capability.matrix": "portal.capability_matrix",
    "governance.scene.openability": "portal.capability_matrix",
    "governance.runtime.audit": "portal.dashboard",
    "material.catalog.open": "projects.ledger",
    "material.procurement.list": "projects.ledger",
    "workspace.today.focus": "portal.dashboard",
    "workspace.project.watch": "projects.list",
}

EXECUTION_SOURCE_SCENE_MAP: dict[str, str] = {
    "construction.contract": "contracts.list",
    "payment.request": "finance.payment_requests",
    "sc.settlement.order": "settlement",
}


def _resolve_ref_id(env, xmlid: str) -> int | None:
    value = str(xmlid or "").strip()
    if not value:
        return None
    rec = env.ref(value, raise_if_not_found=False)
    if not rec:
        return None
    return int(rec.id)


def _resolve_scene_map(env) -> dict[str, dict[str, Any]]:
    scenes = scene_registry.load_scene_configs(env)
    out: dict[str, dict[str, Any]] = {}
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        key = str(scene.get("code") or scene.get("key") or "").strip()
        if not key:
            continue
        out[key] = dict(scene)
    return out


def _scene_cache_key(env) -> str:
    try:
        dbname = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
    except Exception:
        dbname = ""
    return dbname or "__default__"


def _load_scene_map_with_timings(env) -> Tuple[dict[str, dict[str, Any]], dict[str, int]]:
    cache_key = _scene_cache_key(env)
    cached_map = _SCENE_MAP_CACHE.get(cache_key)
    if isinstance(cached_map, dict):
        return cached_map, {
            "load_scene_configs_cache_hit": 0,
            "build_scene_map_cache_hit": 0,
        }

    timings_ms: dict[str, int] = {}
    scenes, scene_config_timings_ms = scene_registry.load_scene_configs_with_timings(env)
    if isinstance(scene_config_timings_ms, dict):
        for key, value in scene_config_timings_ms.items():
            timings_ms[key] = int(value)
    if isinstance(scenes, list):
        _SCENE_CONFIGS_CACHE[cache_key] = list(scenes)
    map_ts = time.perf_counter()
    scene_map = {
        str(scene.get("code") or scene.get("key") or "").strip(): dict(scene)
        for scene in (scenes or [])
        if isinstance(scene, dict) and str(scene.get("code") or scene.get("key") or "").strip()
    }
    timings_ms["build_scene_map"] = int((time.perf_counter() - map_ts) * 1000)
    _SCENE_MAP_CACHE[cache_key] = scene_map
    return scene_map, timings_ms


def _build_target_scene_lookup(env) -> dict[tuple[str, str], str]:
    cache_key = _scene_cache_key(env)
    cached = _TARGET_SCENE_LOOKUP_CACHE.get(cache_key)
    if isinstance(cached, dict):
        return cached

    scene_map, _timings = _load_scene_map_with_timings(env)
    lookup: dict[tuple[str, str], str] = {}
    for scene_key, scene in (scene_map or {}).items():
        if not isinstance(scene, dict):
            continue
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        action_xmlid = str(target.get("action_xmlid") or "").strip()
        menu_xmlid = str(target.get("menu_xmlid") or "").strip()
        model = str(target.get("model") or "").strip()
        view_mode = str(target.get("view_mode") or target.get("view_type") or "").strip().lower()
        if action_xmlid:
            lookup.setdefault(("action_xmlid", action_xmlid), scene_key)
        if menu_xmlid:
            lookup.setdefault(("menu_xmlid", menu_xmlid), scene_key)
        if model and view_mode:
            lookup.setdefault(("model_view", f"{model}:{view_mode}"), scene_key)
    _TARGET_SCENE_LOOKUP_CACHE[cache_key] = lookup
    return lookup


def _derive_scene_key_from_explicit_target(env, explicit_target: dict[str, Any] | None = None) -> str:
    if not env or not isinstance(explicit_target, dict):
        return ""
    lookup = _build_target_scene_lookup(env)
    action_xmlid = str(explicit_target.get("action_xmlid") or "").strip()
    if action_xmlid:
        scene_key = str(lookup.get(("action_xmlid", action_xmlid), "") or "").strip()
        if scene_key:
            return scene_key
    menu_xmlid = str(explicit_target.get("menu_xmlid") or "").strip()
    if menu_xmlid:
        scene_key = str(lookup.get(("menu_xmlid", menu_xmlid), "") or "").strip()
        if scene_key:
            return scene_key
    model = str(explicit_target.get("model") or "").strip()
    view_mode = str(explicit_target.get("view_mode") or explicit_target.get("view_type") or "").strip().lower()
    if model and view_mode:
        return str(lookup.get(("model_view", f"{model}:{view_mode}"), "") or "").strip()
    return ""


def resolve_capability_entry_scene_key(
    capability_key: str,
    *,
    env=None,
    explicit_target: dict[str, Any] | None = None,
) -> str:
    resolved = str(CAPABILITY_ENTRY_SCENE_MAP.get(str(capability_key or "").strip(), "") or "").strip()
    if resolved:
        return resolved
    return _derive_scene_key_from_explicit_target(env, explicit_target=explicit_target)


def build_capability_entry_target(
    capability_key: str,
    explicit_target: dict[str, Any] | None = None,
    *,
    env=None,
) -> dict[str, Any]:
    target = dict(explicit_target or {})
    scene_key = resolve_capability_entry_scene_key(
        capability_key,
        env=env,
        explicit_target=explicit_target,
    )
    if scene_key and not str(target.get("scene_key") or "").strip():
        target["scene_key"] = scene_key
    return target


def resolve_capability_entry_target_payload(env, capability_key: str, explicit_target: dict[str, Any] | None = None) -> dict[str, Any]:
    payload, _timings = resolve_capability_entry_target_payload_with_timings(
        env,
        capability_key,
        explicit_target=explicit_target,
    )
    return payload


def resolve_capability_entry_target_payload_with_timings(
    env,
    capability_key: str,
    explicit_target: dict[str, Any] | None = None,
) -> Tuple[dict[str, Any], dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    target = build_capability_entry_target(capability_key, explicit_target=explicit_target, env=env)
    stage_ts = _mark("build_capability_entry_target", stage_ts)
    scene_key = str(target.get("scene_key") or "").strip()
    payload: dict[str, Any] = {}
    if scene_key:
        payload["scene_key"] = scene_key
        scene_ts = time.perf_counter()
        scene_map, scene_map_timings_ms = _load_scene_map_with_timings(env)
        scene_ts = _mark("resolve_scene_map", scene_ts)
        if isinstance(scene_map_timings_ms, dict):
            for key, value in scene_map_timings_ms.items():
                timings_ms[f"scene_registry.{key}"] = int(value)
        scene = scene_map.get(scene_key) or {}
        scene_target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        payload["route"] = str(scene_target.get("route") or f"/workbench?scene={scene_key}")
        for key in ("model", "view_type", "view_mode", "record_id"):
            if scene_target.get(key) not in (None, ""):
                payload[key] = scene_target.get(key)
        action_xmlid = str(scene_target.get("action_xmlid") or "").strip()
        menu_xmlid = str(scene_target.get("menu_xmlid") or "").strip()
        action_id = scene_target.get("action_id")
        menu_id = scene_target.get("menu_id")
        xmlid_ts = time.perf_counter()
        if action_xmlid and not action_id:
            action_id = _resolve_ref_id(env, action_xmlid)
        if menu_xmlid and not menu_id:
            menu_id = _resolve_ref_id(env, menu_xmlid)
        _mark("resolve_xmlids", xmlid_ts)
        if action_id:
            payload["action_id"] = int(action_id)
        if menu_id:
            payload["menu_id"] = int(menu_id)
        stage_ts = _mark("scene_target_payload", stage_ts)
    for key in ("route", "model", "view_type", "view_mode", "record_id", "action_id", "menu_id"):
        if target.get(key) not in (None, ""):
            payload[key] = target.get(key)
    _mark("overlay_explicit_target", stage_ts)
    return payload, timings_ms


def resolve_execution_projection_scene_key(source_model: str, explicit_scene_key: str = "") -> str:
    explicit = str(explicit_scene_key or "").strip()
    if explicit:
        return explicit
    return str(EXECUTION_SOURCE_SCENE_MAP.get(str(source_model or "").strip(), "projects.list") or "projects.list")
