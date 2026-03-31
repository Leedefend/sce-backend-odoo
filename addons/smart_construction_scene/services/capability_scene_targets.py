# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from odoo.addons.smart_construction_scene import scene_registry


CAPABILITY_ENTRY_SCENE_MAP: dict[str, str] = {
    "project.initiation.enter": "project.initiation",
    "project.list.open": "projects.list",
    "project.board.open": "projects.ledger",
    "project.dashboard.enter": "project.dashboard",
    "project.dashboard.open": "project.dashboard",
    "project.plan_bootstrap.enter": "project.plan_bootstrap",
    "project.execution.enter": "project.execution",
    "project.execution.advance": "project.execution",
    "project.lifecycle.open": "portal.lifecycle",
    "project.task.list": "projects.ledger",
    "project.task.board": "projects.ledger",
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
    "contract.center.open": "projects.ledger",
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


def resolve_capability_entry_scene_key(capability_key: str) -> str:
    return str(CAPABILITY_ENTRY_SCENE_MAP.get(str(capability_key or "").strip(), "") or "").strip()


def build_capability_entry_target(capability_key: str, explicit_target: dict[str, Any] | None = None) -> dict[str, Any]:
    target = dict(explicit_target or {})
    scene_key = resolve_capability_entry_scene_key(capability_key)
    if scene_key and not str(target.get("scene_key") or "").strip():
        target["scene_key"] = scene_key
    return target


def resolve_capability_entry_target_payload(env, capability_key: str, explicit_target: dict[str, Any] | None = None) -> dict[str, Any]:
    target = build_capability_entry_target(capability_key, explicit_target=explicit_target)
    scene_key = str(target.get("scene_key") or "").strip()
    payload: dict[str, Any] = {}
    if scene_key:
        payload["scene_key"] = scene_key
        scene_map = _resolve_scene_map(env)
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
        if action_xmlid and not action_id:
            action_id = _resolve_ref_id(env, action_xmlid)
        if menu_xmlid and not menu_id:
            menu_id = _resolve_ref_id(env, menu_xmlid)
        if action_id:
            payload["action_id"] = int(action_id)
        if menu_id:
            payload["menu_id"] = int(menu_id)
    for key in ("route", "model", "view_type", "view_mode", "record_id", "action_id", "menu_id"):
        if target.get(key) not in (None, ""):
            payload[key] = target.get(key)
    return payload


def resolve_execution_projection_scene_key(source_model: str, explicit_scene_key: str = "") -> str:
    explicit = str(explicit_scene_key or "").strip()
    if explicit:
        return explicit
    return str(EXECUTION_SOURCE_SCENE_MAP.get(str(source_model or "").strip(), "projects.list") or "projects.list")
