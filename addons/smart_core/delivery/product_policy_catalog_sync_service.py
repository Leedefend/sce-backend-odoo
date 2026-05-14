# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from typing import Any

from odoo.addons.smart_core.core.scene_provider import load_scenes_from_db_or_fallback

from .product_identity import resolve_product_identity
from .product_policy_service import DEFAULT_PRODUCT_POLICY, ProductPolicyService


def _text(value: Any) -> str:
    return str(value or "").strip()


APP_TAXONOMY: dict[str, dict[str, Any]] = {
    "dashboard": {"label": "经营驾驶舱", "category": "management", "sequence": 10, "primary_scene": "dashboard.company"},
    "projects": {"label": "项目管理", "category": "construction", "sequence": 20, "primary_scene": "projects.list"},
    "contracts": {"label": "合同管理", "category": "construction", "sequence": 30, "primary_scene": "contracts.workspace"},
    "cost": {"label": "成本管理", "category": "construction", "sequence": 40, "primary_scene": "cost.cost_compare"},
    "finance": {"label": "资金财务", "category": "construction", "sequence": 50, "primary_scene": "finance.payment_requests"},
    "payments": {"label": "收付款", "category": "construction", "sequence": 60, "primary_scene": "payments.approval"},
    "my_work": {"label": "我的工作", "category": "productivity", "sequence": 70, "primary_scene": "my_work.workspace"},
    "operation": {"label": "运营管理", "category": "construction", "sequence": 80, "primary_scene": "operation.overview"},
    "portfolio": {"label": "项目组合", "category": "management", "sequence": 90, "primary_scene": "portfolio.center"},
    "risk": {"label": "风险管理", "category": "governance", "sequence": 100, "primary_scene": "risk.center"},
    "quality": {"label": "质量管理", "category": "construction", "sequence": 110, "primary_scene": "quality.center"},
    "safety": {"label": "安全管理", "category": "construction", "sequence": 120, "primary_scene": "safety.center"},
    "resource": {"label": "资源管理", "category": "construction", "sequence": 130, "primary_scene": "resource.center"},
    "task": {"label": "任务协同", "category": "productivity", "sequence": 140, "primary_scene": "task.center"},
}

APP_ALIASES = {
    "project": "projects",
    "contract": "contracts",
    "payment": "payments",
}

PLATFORM_ONLY_APP_IDS = {"workspace", "data", "config", "enterprise", "portal", "delivery", "default", "scene_smoke_default"}


def _scene_key(scene: dict[str, Any]) -> str:
    return _text(scene.get("code") or scene.get("key"))


def _scene_label(scene: dict[str, Any]) -> str:
    return _text(scene.get("title") or scene.get("label") or scene.get("name") or _scene_key(scene))


def _scene_app_id(scene_key: str) -> str:
    head = _text(scene_key).lower().split(".", 1)[0]
    return APP_ALIASES.get(head, head) or "workspace"


def _scene_route(scene: dict[str, Any], scene_key: str) -> str:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    route = _text(target.get("route"))
    return route or (f"/s/{scene_key}" if scene_key else "/")


def _taxonomy(app_id: str) -> dict[str, Any]:
    return APP_TAXONOMY.get(app_id) or {"label": app_id, "category": "construction", "sequence": 900, "primary_scene": ""}


def _sequence(app_id: str) -> int:
    try:
        return int(_taxonomy(app_id).get("sequence") or 900)
    except Exception:
        return 900


def _scene_sort_key(scene: dict[str, Any]) -> tuple[int, int, str]:
    key = _scene_key(scene)
    app_id = _scene_app_id(key)
    primary = _text(_taxonomy(app_id).get("primary_scene"))
    return (_sequence(app_id), 0 if key == primary else 100, key)


def _is_construction_publishable_scene(scene: dict[str, Any]) -> bool:
    key = _scene_key(scene)
    if not key or "__pkg" in key:
        return False
    app_id = _scene_app_id(key)
    return app_id not in PLATFORM_ONLY_APP_IDS


def _taxonomy_seed_scenes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for app_id, taxonomy in sorted(APP_TAXONOMY.items(), key=lambda item: (_sequence(item[0]), item[0])):
        scene_key = _text(taxonomy.get("primary_scene"))
        if not scene_key:
            continue
        rows.append(
            {
                "code": scene_key,
                "title": _text(taxonomy.get("label")) or app_id,
                "description": f"{_text(taxonomy.get('label')) or app_id}产品能力入口",
                "target": {"route": f"/s/{scene_key}"},
            }
        )
    return rows


class ProductPolicyCatalogSyncService:
    SOURCE_KIND = "product_policy_catalog_sync"
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    def build_construction_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        scenes_payload = load_scenes_from_db_or_fallback(self.env, drift=None, logger=None) or {}
        raw_scenes = scenes_payload.get("scenes") if isinstance(scenes_payload.get("scenes"), list) else []
        source_by_key: dict[str, dict[str, Any]] = {}
        for scene in _taxonomy_seed_scenes():
            source_by_key[_scene_key(scene)] = scene
        for scene in raw_scenes:
            if isinstance(scene, dict) and _is_construction_publishable_scene(scene):
                source_by_key[_scene_key(scene)] = scene
        source_scenes = list(source_by_key.values())

        groups_by_app: dict[str, list[dict[str, Any]]] = defaultdict(list)
        scene_rows: list[dict[str, Any]] = []
        capability_rows: list[dict[str, Any]] = []
        scene_bindings: dict[str, dict[str, str]] = {}
        for scene in sorted(source_scenes, key=_scene_sort_key):
            scene_key = _scene_key(scene)
            app_id = _scene_app_id(scene_key)
            app_taxonomy = _taxonomy(app_id)
            app_label = _text(app_taxonomy.get("label")) or app_id
            label = _scene_label(scene)
            route = _scene_route(scene, scene_key)
            capability_key = f"construction.{scene_key}"
            menu = {
                "menu_key": f"release.{scene_key}",
                "label": label,
                "route": route,
                "scene_key": scene_key,
                "product_key": app_id,
                "capability_key": capability_key,
            }
            groups_by_app[app_id].append(menu)
            scene_rows.append(
                {
                    "scene_key": scene_key,
                    "label": label,
                    "route": route,
                    "product_key": app_id,
                    "capability_key": capability_key,
                    "description": _text(scene.get("description")) or f"{app_label}场景：{label}",
                    "scope": app_label,
                }
            )
            capability_rows.append(
                {
                    "capability_key": capability_key,
                    "label": label,
                    "group_key": app_id,
                    "group_label": app_label,
                    "target_scene_key": scene_key,
                    "product_key": app_id,
                    "delivery_level": "shared" if app_id in {"dashboard", "my_work", "task"} else "exclusive",
                    "entry_kind": "scene",
                }
            )
            scene_bindings[scene_key] = {"version": "v1", "channel": "stable"}

        menu_groups = [
            {
                "group_key": f"construction.{app_id}",
                "group_label": _text(_taxonomy(app_id).get("label")) or app_id,
                "category": _text(_taxonomy(app_id).get("category")) or "construction",
                "menus": menus,
            }
            for app_id, menus in sorted(groups_by_app.items(), key=lambda item: (_sequence(item[0]), item[0]))
        ]
        label = "施工管理预览版" if identity["edition_key"] == "preview" else "施工管理标准版"
        return {
            "product_key": identity["product_key"],
            "base_product_key": identity["base_product_key"],
            "edition_key": identity["edition_key"],
            "state": "preview" if identity["edition_key"] == "preview" else "stable",
            "access_level": "public",
            "allowed_role_codes": [],
            "label": label,
            "version": "v1",
            "scene_version_bindings": scene_bindings,
            "menu_groups": menu_groups,
            "scenes": scene_rows,
            "capabilities": capability_rows,
            "policy_source_authority": {
                "kind": self.SOURCE_KIND,
                "authorities": ["scene_runtime_provider_projection", "delivery_product_identity_resolver"],
                "loaded_from": _text(scenes_payload.get("loaded_from")) or "unknown",
                "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            },
        }

    def build_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        if identity["base_product_key"] == "construction":
            return self.build_construction_policy_payload(product_key=identity["product_key"])
        return ProductPolicyService(self.env).get_policy(product_key=identity["product_key"])

    def sync_policy(self, *, product_key: str, preserve_state: bool = True, preserve_access_level: bool = True):
        identity = resolve_product_identity(product_key=product_key)
        payload = self.build_policy_payload(product_key=identity["product_key"])
        model = self.env["sc.product.policy"].sudo()
        rec = model.search([("product_key", "=", identity["product_key"])], limit=1)
        current = rec.to_runtime_dict() if rec else {}
        values = {
            "active": True,
            "product_key": identity["product_key"],
            "base_product_key": _text(payload.get("base_product_key")) or identity["base_product_key"],
            "edition_key": _text(payload.get("edition_key")) or identity["edition_key"],
            "state": _text(current.get("state")) if preserve_state and current else (_text(payload.get("state")) or "stable"),
            "access_level": _text(current.get("access_level")) if preserve_access_level and current else (_text(payload.get("access_level")) or "public"),
            "allowed_role_codes": payload.get("allowed_role_codes") if isinstance(payload.get("allowed_role_codes"), list) else [],
            "label": _text(payload.get("label")) or _text(DEFAULT_PRODUCT_POLICY.get("label")) or identity["product_key"],
            "version": _text(payload.get("version")) or "v1",
            "scene_version_bindings": payload.get("scene_version_bindings") if isinstance(payload.get("scene_version_bindings"), dict) else {},
            "menu_groups": payload.get("menu_groups") if isinstance(payload.get("menu_groups"), list) else [],
            "scenes": payload.get("scenes") if isinstance(payload.get("scenes"), list) else [],
            "capabilities": payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else [],
            "note": "synced from productized scene catalog",
        }
        if rec:
            rec.write(values)
        else:
            rec = model.create(values)
        return rec
