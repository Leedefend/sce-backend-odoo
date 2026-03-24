# -*- coding: utf-8 -*-
from __future__ import annotations

import copy


DEFAULT_PRODUCT_POLICY = {
    "product_key": "construction.standard",
    "label": "Construction Standard",
    "version": "v1",
    "scene_version_bindings": {
        "projects.intake": {"version": "v1", "channel": "stable"},
        "project.management": {"version": "v1", "channel": "stable"},
        "cost": {"version": "v1", "channel": "stable"},
        "payment": {"version": "v1", "channel": "stable"},
        "settlement": {"version": "v1", "channel": "stable"},
        "my_work.workspace": {"version": "v1", "channel": "stable"},
    },
    "menu_groups": [
        {
            "group_key": "released_products",
            "group_label": "已发布产品",
            "menus": [
                {
                    "menu_key": "release.fr1.project_intake",
                    "label": "FR-1 项目立项",
                    "route": "/s/projects.intake",
                    "scene_key": "projects.intake",
                    "product_key": "fr1",
                    "capability_key": "delivery.fr1.project_intake",
                },
                {
                    "menu_key": "release.fr2.project_flow",
                    "label": "FR-2 项目推进",
                    "route": "/release/fr2",
                    "scene_key": "project.management",
                    "product_key": "fr2",
                    "capability_key": "delivery.fr2.project_flow",
                },
                {
                    "menu_key": "release.fr3.cost_tracking",
                    "label": "FR-3 成本记录",
                    "route": "/release/fr3",
                    "scene_key": "cost",
                    "product_key": "fr3",
                    "capability_key": "delivery.fr3.cost_tracking",
                },
                {
                    "menu_key": "release.fr4.payment_tracking",
                    "label": "FR-4 付款记录",
                    "route": "/release/fr4",
                    "scene_key": "payment",
                    "product_key": "fr4",
                    "capability_key": "delivery.fr4.payment_tracking",
                },
                {
                    "menu_key": "release.fr5.settlement_summary",
                    "label": "FR-5 结算结果",
                    "route": "/release/fr5",
                    "scene_key": "settlement",
                    "product_key": "fr5",
                    "capability_key": "delivery.fr5.settlement_summary",
                },
            ],
        },
        {
            "group_key": "released_utilities",
            "group_label": "工作辅助",
            "menus": [
                {
                    "menu_key": "release.my_work",
                    "label": "我的工作",
                    "route": "/my-work",
                    "scene_key": "my_work.workspace",
                    "product_key": "my_work",
                    "capability_key": "delivery.my_work.workspace",
                },
            ],
        },
    ],
    "scenes": [
        {
            "scene_key": "projects.intake",
            "label": "项目立项",
            "route": "/s/projects.intake",
            "product_key": "fr1",
            "capability_key": "delivery.fr1.project_intake",
        },
        {
            "scene_key": "project.management",
            "label": "项目推进",
            "route": "/s/project.management",
            "product_key": "fr2",
            "capability_key": "delivery.fr2.project_flow",
            "requires_project_context": True,
        },
        {
            "scene_key": "cost",
            "label": "成本记录",
            "route": "/s/cost",
            "product_key": "fr3",
            "capability_key": "delivery.fr3.cost_tracking",
            "requires_project_context": True,
        },
        {
            "scene_key": "payment",
            "label": "付款记录",
            "route": "/s/payment",
            "product_key": "fr4",
            "capability_key": "delivery.fr4.payment_tracking",
            "requires_project_context": True,
        },
        {
            "scene_key": "settlement",
            "label": "结算结果",
            "route": "/s/settlement",
            "product_key": "fr5",
            "capability_key": "delivery.fr5.settlement_summary",
            "requires_project_context": True,
        },
        {
            "scene_key": "my_work.workspace",
            "label": "我的工作",
            "route": "/my-work",
            "product_key": "my_work",
            "capability_key": "delivery.my_work.workspace",
        },
    ],
    "capabilities": [
        {
            "capability_key": "delivery.fr1.project_intake",
            "label": "FR-1 项目立项",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "projects.intake",
            "product_key": "fr1",
            "delivery_level": "exclusive",
            "entry_kind": "exclusive",
        },
        {
            "capability_key": "delivery.fr2.project_flow",
            "label": "FR-2 项目推进",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "project.management",
            "product_key": "fr2",
            "delivery_level": "exclusive",
            "entry_kind": "exclusive",
        },
        {
            "capability_key": "delivery.fr3.cost_tracking",
            "label": "FR-3 成本记录",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "cost",
            "product_key": "fr3",
            "delivery_level": "exclusive",
            "entry_kind": "exclusive",
        },
        {
            "capability_key": "delivery.fr4.payment_tracking",
            "label": "FR-4 付款记录",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "payment",
            "product_key": "fr4",
            "delivery_level": "exclusive",
            "entry_kind": "exclusive",
        },
        {
            "capability_key": "delivery.fr5.settlement_summary",
            "label": "FR-5 结算结果",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "settlement",
            "product_key": "fr5",
            "delivery_level": "exclusive",
            "entry_kind": "exclusive",
        },
        {
            "capability_key": "delivery.my_work.workspace",
            "label": "我的工作",
            "group_key": "delivery",
            "group_label": "产品交付",
            "target_scene_key": "my_work.workspace",
            "product_key": "my_work",
            "delivery_level": "shared",
            "entry_kind": "exclusive",
        },
    ],
}


class ProductPolicyService:
    def __init__(self, env):
        self.env = env

    def _snapshot_binding_is_releaseable(self, *, scene_key: str, product_key: str, binding: dict | None) -> bool:
        row = binding if isinstance(binding, dict) else {}
        version = str(row.get("version") or "").strip() or "v1"
        channel = str(row.get("channel") or "").strip() or "stable"
        rec = self.env["sc.scene.snapshot"].sudo().search(
            [
                ("scene_key", "=", scene_key),
                ("product_key", "=", product_key),
                ("version", "=", version),
                ("channel", "=", channel),
                ("state", "=", "stable"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            limit=1,
        )
        return bool(rec)

    def _sanitize_scene_version_bindings(self, payload: dict) -> dict:
        bindings = payload.get("scene_version_bindings") if isinstance(payload.get("scene_version_bindings"), dict) else {}
        sanitized = {}
        diagnostics = {}
        for scene_key, binding in bindings.items():
            key = str(scene_key or "").strip()
            if not key:
                continue
            row = binding if isinstance(binding, dict) else {}
            product_key = ""
            for scene_row in payload.get("scenes") or []:
                if isinstance(scene_row, dict) and str(scene_row.get("scene_key") or "").strip() == key:
                    product_key = str(scene_row.get("product_key") or "").strip()
                    break
            if not product_key:
                diagnostics[key] = {
                    "binding_allowed": False,
                    "reason": "SCENE_POLICY_MISSING",
                }
                continue
            if self._snapshot_binding_is_releaseable(scene_key=key, product_key=product_key, binding=row):
                sanitized[key] = {
                    "version": str(row.get("version") or "").strip() or "v1",
                    "channel": str(row.get("channel") or "").strip() or "stable",
                }
                diagnostics[key] = {
                    "binding_allowed": True,
                    "reason": "ACTIVE_STABLE_BOUND",
                }
            else:
                diagnostics[key] = {
                    "binding_allowed": False,
                    "reason": "SNAPSHOT_NOT_ACTIVE_STABLE",
                }
        payload["scene_version_bindings"] = sanitized
        payload["scene_binding_diagnostics"] = diagnostics
        return payload

    def get_policy(self, product_key: str | None = None) -> dict:
        key = str(product_key or DEFAULT_PRODUCT_POLICY["product_key"]).strip() or DEFAULT_PRODUCT_POLICY["product_key"]
        try:
            rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", key), ("active", "=", True)], limit=1)
        except Exception:
            rec = None
        if rec:
            payload = rec.to_runtime_dict()
            if isinstance(payload, dict) and payload.get("product_key"):
                return self._sanitize_scene_version_bindings(payload)
        fallback = copy.deepcopy(DEFAULT_PRODUCT_POLICY)
        fallback["product_key"] = key
        return self._sanitize_scene_version_bindings(fallback)
