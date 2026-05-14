# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from typing import Any

from odoo import api
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry
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

CONSTRUCTION_PAGE_CATALOG: tuple[dict[str, Any], ...] = (
    {"app_id": "dashboard", "page_key": "dashboard.company", "label": "经营驾驶舱", "route": "/s/dashboard.company"},
    {"app_id": "dashboard", "page_key": "dashboard.project", "label": "项目驾驶舱", "route": "/s/dashboard.project"},
    {"app_id": "projects", "page_key": "projects.list", "label": "项目台账", "route": "/s/projects.list"},
    {"app_id": "projects", "page_key": "projects.intake", "label": "项目立项", "route": "/s/projects.intake"},
    {"app_id": "projects", "page_key": "project.management", "label": "项目推进", "route": "/s/project.management"},
    {"app_id": "contracts", "page_key": "contracts.workspace", "label": "合同工作台", "route": "/s/contracts.workspace"},
    {"app_id": "contracts", "page_key": "contracts.income", "label": "收入合同", "route": "/s/contracts.income"},
    {"app_id": "contracts", "page_key": "contracts.expense", "label": "支出合同", "route": "/s/contracts.expense"},
    {"app_id": "contracts", "page_key": "contracts.supplier_pricing", "label": "供应商合同定价", "route": "/s/contracts.supplier_pricing"},
    {"app_id": "cost", "page_key": "cost.cost_compare", "label": "成本对比", "route": "/s/cost.cost_compare"},
    {"app_id": "cost", "page_key": "cost.ledger", "label": "成本台账", "route": "/s/cost.ledger"},
    {"app_id": "cost", "page_key": "cost.summary", "label": "成本统计表", "route": "/s/cost.summary"},
    {"app_id": "finance", "page_key": "finance.payment_requests", "label": "付款申请", "route": "/s/finance.payment_requests"},
    {"app_id": "finance", "page_key": "finance.receipt_income", "label": "收款登记", "route": "/s/finance.receipt_income"},
    {"app_id": "finance", "page_key": "finance.invoice", "label": "发票管理", "route": "/s/finance.invoice"},
    {"app_id": "finance", "page_key": "finance.treasury", "label": "资金台账", "route": "/s/finance.treasury"},
    {"app_id": "payments", "page_key": "payments.approval", "label": "收付款审批", "route": "/s/payments.approval"},
    {"app_id": "payments", "page_key": "payments.execution", "label": "付款执行", "route": "/s/payments.execution"},
    {"app_id": "payments", "page_key": "payments.deposit", "label": "保证金办理", "route": "/s/payments.deposit"},
    {"app_id": "my_work", "page_key": "my_work.workspace", "label": "我的工作", "route": "/my-work"},
    {"app_id": "my_work", "page_key": "my_work.approvals", "label": "我的审批", "route": "/s/my_work.approvals"},
    {"app_id": "operation", "page_key": "operation.overview", "label": "运营总览", "route": "/s/operation.overview"},
    {"app_id": "operation", "page_key": "operation.metrics", "label": "经营指标", "route": "/s/operation.metrics"},
    {"app_id": "portfolio", "page_key": "portfolio.center", "label": "项目组合", "route": "/s/portfolio.center"},
    {"app_id": "risk", "page_key": "risk.center", "label": "风险中心", "route": "/s/risk.center"},
    {"app_id": "risk", "page_key": "risk.warnings", "label": "风险预警", "route": "/s/risk.warnings"},
    {"app_id": "quality", "page_key": "quality.center", "label": "质量管理", "route": "/s/quality.center"},
    {"app_id": "quality", "page_key": "quality.inspection", "label": "质量检查", "route": "/s/quality.inspection"},
    {"app_id": "safety", "page_key": "safety.center", "label": "安全管理", "route": "/s/safety.center"},
    {"app_id": "safety", "page_key": "safety.inspection", "label": "安全检查", "route": "/s/safety.inspection"},
    {"app_id": "resource", "page_key": "resource.center", "label": "资源管理", "route": "/s/resource.center"},
    {"app_id": "resource", "page_key": "resource.material", "label": "材料档案", "route": "/s/resource.material"},
    {"app_id": "resource", "page_key": "resource.subcontract", "label": "分包资源", "route": "/s/resource.subcontract"},
    {"app_id": "task", "page_key": "task.center", "label": "任务协同", "route": "/s/task.center"},
    {"app_id": "task", "page_key": "task.todos", "label": "待办任务", "route": "/s/task.todos"},
)


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
    for page in CONSTRUCTION_PAGE_CATALOG:
        app_id = _text(page.get("app_id"))
        page_key = _text(page.get("page_key"))
        if not app_id or not page_key:
            continue
        taxonomy = _taxonomy(app_id)
        rows.append(
            {
                "code": page_key,
                "title": _text(page.get("label")) or page_key,
                "description": f"{_text(taxonomy.get('label')) or app_id}页面：{_text(page.get('label')) or page_key}",
                "target": {"route": _text(page.get("route")) or f"/s/{page_key}"},
                "page_key": page_key,
                "visible_menu_path": f"{_text(taxonomy.get('label')) or app_id} / {_text(page.get('label')) or page_key}",
            }
        )
    return rows


def _action_id(action: Any) -> int:
    try:
        return int(action.id or 0) if action else 0
    except Exception:
        return 0


def _action_model(action: Any) -> str:
    try:
        return _text(getattr(action, "res_model", ""))
    except Exception:
        return ""


def _menu_xmlid(menu: Any) -> str:
    try:
        return _text(menu.get_external_id().get(menu.id, ""))
    except Exception:
        return ""


def _menu_path(menu: Any) -> list[str]:
    path: list[str] = []
    current = menu
    while current:
        name = _text(getattr(current, "name", ""))
        if name:
            path.append(name)
        current = getattr(current, "parent_id", None)
    return list(reversed(path))


def _slug(value: str) -> str:
    return _text(value).replace(".", "_").replace("-", "_").replace(" ", "_").lower() or "menu"


class ProductPolicyCatalogSyncService:
    SOURCE_KIND = "product_policy_catalog_sync"
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    def _construction_source_db(self) -> str:
        try:
            configured = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.release_operator.construction_source_db",
                "",
            )
        except Exception:
            configured = ""
        return _text(configured) or "sc_demo"

    def _extract_user_menu_pages(self, source_env) -> list[dict[str, Any]]:
        menus = source_env["ir.ui.menu"].sudo().search([("action", "!=", False)], order="sequence,id")
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for menu in menus:
            xmlid = _menu_xmlid(menu)
            if not xmlid.startswith("smart_construction_core."):
                continue
            action = menu.action
            action_id = _action_id(action)
            if action_id <= 0:
                continue
            path = _menu_path(menu)
            if not path:
                continue
            page_key = xmlid
            if page_key in seen:
                continue
            seen.add(page_key)
            root_label = path[0] if path else "施工管理"
            group_label = path[1] if len(path) > 1 else root_label
            page_label = path[-1]
            menu_id = int(menu.id or 0)
            rows.append(
                {
                    "app_id": _slug(group_label),
                    "group_key": f"construction.{_slug(group_label)}",
                    "group_label": group_label,
                    "root_label": root_label,
                    "menu_id": menu_id,
                    "menu_xmlid": xmlid,
                    "menu_key": xmlid,
                    "page_key": page_key,
                    "page_label": page_label,
                    "label": page_label,
                    "route": f"/a/{action_id}?menu_id={menu_id}",
                    "scene_key": "",
                    "action_id": action_id,
                    "action_model": _text(getattr(action, "_name", "")),
                    "res_model": _action_model(action),
                    "visible_menu_path": " / ".join(path),
                    "control_granularity": "user_visible_menu_page",
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "control_object": "用户可见菜单页面",
                    "source_kind": "ir.ui.menu",
                }
            )
        return rows

    def _load_source_user_menu_pages(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source_db = self._construction_source_db()
        current_db = _text(getattr(getattr(self.env, "cr", None), "dbname", ""))
        if source_db == current_db:
            return self._extract_user_menu_pages(self.env), {"source_db": current_db, "source": "current_db_ir_ui_menu"}
        try:
            registry = Registry(source_db)
            with registry.cursor() as cr:
                source_env = api.Environment(cr, SUPERUSER_ID, {})
                return self._extract_user_menu_pages(source_env), {
                    "source_db": source_db,
                    "source": "external_db_ir_ui_menu",
                }
        except Exception as exc:
            return [], {
                "source_db": source_db,
                "source": "external_db_ir_ui_menu_failed",
                "error": str(exc),
            }

    def build_construction_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        menu_pages, menu_source = self._load_source_user_menu_pages()
        if menu_pages:
            return self._build_construction_policy_payload_from_menu_pages(
                identity=identity,
                menu_pages=menu_pages,
                menu_source=menu_source,
            )
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
                "page_key": scene_key,
                "page_label": label,
                "route": route,
                "scene_key": scene_key,
                "product_key": app_id,
                "capability_key": capability_key,
                "visible_menu_path": _text(scene.get("visible_menu_path")) or f"{app_label} / {label}",
                "control_granularity": "menu_page",
                "enabled": True,
            }
            groups_by_app[app_id].append(menu)
            scene_rows.append(
                {
                    "scene_key": scene_key,
                    "page_key": scene_key,
                    "label": label,
                    "route": route,
                    "product_key": app_id,
                    "capability_key": capability_key,
                    "visible_menu_path": menu["visible_menu_path"],
                    "control_granularity": "menu_page",
                    "enabled": True,
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
                    "target_page_key": scene_key,
                    "product_key": app_id,
                    "delivery_level": "shared" if app_id in {"dashboard", "my_work", "task"} else "exclusive",
                    "entry_kind": "menu_page",
                    "visible_menu_path": menu["visible_menu_path"],
                    "enabled": True,
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

    def _build_construction_policy_payload_from_menu_pages(
        self,
        *,
        identity: dict[str, str],
        menu_pages: list[dict[str, Any]],
        menu_source: dict[str, Any],
    ) -> dict[str, Any]:
        groups_by_key: dict[str, dict[str, Any]] = {}
        scene_rows: list[dict[str, Any]] = []
        capability_rows: list[dict[str, Any]] = []
        scene_bindings: dict[str, dict[str, str]] = {}
        for index, page in enumerate(menu_pages, start=1):
            group_key = _text(page.get("group_key")) or "construction.menu"
            group = groups_by_key.setdefault(
                group_key,
                {
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "施工管理",
                    "category": "user_visible_menu",
                    "menus": [],
                },
            )
            page_key = _text(page.get("page_key"))
            label = _text(page.get("page_label") or page.get("label")) or page_key
            capability_key = f"construction.menu.{_slug(page_key)}"
            menu = {
                "menu_key": _text(page.get("menu_key")) or page_key,
                "label": label,
                "page_key": page_key,
                "page_label": label,
                "route": _text(page.get("route")),
                "scene_key": _text(page.get("scene_key")),
                "product_key": _text(page.get("app_id")),
                "capability_key": capability_key,
                "visible_menu_path": _text(page.get("visible_menu_path")) or label,
                "control_granularity": "user_visible_menu_page",
                "enabled": bool(page.get("enabled", True)),
                "release_state": _text(page.get("release_state")) or "released",
                "access_level": _text(page.get("access_level")) or "public",
                "control_object": "用户可见菜单页面",
                "source_kind": "ir.ui.menu",
                "menu_id": int(page.get("menu_id") or 0),
                "menu_xmlid": _text(page.get("menu_xmlid")),
                "action_id": int(page.get("action_id") or 0),
                "action_model": _text(page.get("action_model")),
                "res_model": _text(page.get("res_model")),
                "sequence": index,
            }
            group["menus"].append(menu)
            capability_rows.append(
                {
                    "capability_key": capability_key,
                    "label": label,
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "施工管理",
                    "target_scene_key": _text(page.get("scene_key")),
                    "target_page_key": page_key,
                    "product_key": _text(page.get("app_id")),
                    "delivery_level": "exclusive",
                    "entry_kind": "user_visible_menu_page",
                    "visible_menu_path": menu["visible_menu_path"],
                    "enabled": bool(page.get("enabled", True)),
                    "release_state": _text(page.get("release_state")) or "released",
                    "access_level": _text(page.get("access_level")) or "public",
                    "control_object": "用户可见菜单页面",
                    "source_kind": "ir.ui.menu",
                    "menu_xmlid": _text(page.get("menu_xmlid")),
                    "action_id": int(page.get("action_id") or 0),
                    "res_model": _text(page.get("res_model")),
                }
            )
        menu_groups = [groups_by_key[key] for key in groups_by_key]
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
                "authorities": ["ir.ui.menu", "ir.actions", "ir.model.data", "delivery_product_identity_resolver"],
                "source_db": _text(menu_source.get("source_db")),
                "source": _text(menu_source.get("source")),
                "menu_page_count": len(menu_pages),
                "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            },
            "control_definition": [
                {"key": "included", "label": "是否纳入产品", "meaning": "决定该用户菜单页面是否进入当前产品发布包。"},
                {"key": "release_state", "label": "发布阶段", "meaning": "released 面向正式用户；preview 仅预览；hidden/retired 不进入有效发布范围。"},
                {"key": "access_level", "label": "可见范围", "meaning": "public 全部授权用户；internal 内部；role_restricted 后续按角色策略限制。"},
                {"key": "source_identity", "label": "来源证据", "meaning": "记录真实 ir.ui.menu、action、res_model 与源数据库，保证平台管控对象与用户入口一致。"},
            ],
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
        self._merge_existing_page_controls(payload, current)
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

    def _merge_existing_page_controls(self, payload: dict[str, Any], current: dict[str, Any]) -> None:
        current_controls: dict[str, dict[str, Any]] = {}
        for group in current.get("menu_groups") if isinstance(current.get("menu_groups"), list) else []:
            if not isinstance(group, dict):
                continue
            for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
                if not isinstance(menu, dict):
                    continue
                page_key = _text(menu.get("page_key") or menu.get("scene_key") or menu.get("menu_key"))
                if page_key:
                    current_controls[page_key] = menu
        if not current_controls:
            return

        def _apply(row: dict[str, Any]) -> dict[str, Any]:
            page_key = _text(row.get("page_key") or row.get("scene_key") or row.get("target_page_key") or row.get("target_scene_key") or row.get("menu_key"))
            current_row = current_controls.get(page_key) or {}
            if not current_row:
                return row
            next_row = dict(row)
            for key in ("enabled", "release_state", "access_level", "policy_note"):
                if key in current_row:
                    next_row[key] = current_row.get(key)
            return next_row

        menu_groups = []
        for group in payload.get("menu_groups") if isinstance(payload.get("menu_groups"), list) else []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            menus = group.get("menus") if isinstance(group.get("menus"), list) else []
            next_group["menus"] = [_apply(menu) for menu in menus if isinstance(menu, dict)]
            menu_groups.append(next_group)
        payload["menu_groups"] = menu_groups
        scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
        capabilities = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []
        payload["scenes"] = [_apply(scene) for scene in scenes if isinstance(scene, dict)]
        payload["capabilities"] = [_apply(capability) for capability in capabilities if isinstance(capability, dict)]
