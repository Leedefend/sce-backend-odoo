# -*- coding: utf-8 -*-
from __future__ import annotations

import copy


DEFAULT_PRODUCT_POLICY = {
    "product_key": "construction.standard",
    "base_product_key": "construction",
    "edition_key": "standard",
    "state": "stable",
    "access_level": "public",
    "allowed_role_codes": [],
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
            "description": "提供项目立项入口与基础资料创建。",
            "scope": "项目创建 -> 立项资料 -> 项目入口。",
        },
        {
            "scene_key": "project.management",
            "label": "项目推进",
            "route": "/s/project.management",
            "product_key": "fr2",
            "capability_key": "delivery.fr2.project_flow",
            "requires_project_context": True,
            "description": "进入项目驾驶舱、计划与执行主线。",
            "scope": "项目驾驶舱 -> 计划准备 -> 执行推进。",
        },
        {
            "scene_key": "cost",
            "label": "成本记录",
            "route": "/s/cost",
            "product_key": "fr3",
            "capability_key": "delivery.fr3.cost_tracking",
            "requires_project_context": True,
            "description": "查看与记录项目成本事实。",
            "scope": "项目执行 -> 成本记录 -> 成本汇总。",
        },
        {
            "scene_key": "payment",
            "label": "付款记录",
            "route": "/s/payment",
            "product_key": "fr4",
            "capability_key": "delivery.fr4.payment_tracking",
            "requires_project_context": True,
            "description": "查看与记录项目付款事实。",
            "scope": "项目执行 -> 成本 -> 付款记录 -> 付款汇总。",
        },
        {
            "scene_key": "settlement",
            "label": "结算结果",
            "route": "/s/settlement",
            "product_key": "fr5",
            "capability_key": "delivery.fr5.settlement_summary",
            "requires_project_context": True,
            "description": "查看项目级成本与付款汇总后的结算结果。",
            "scope": "项目执行 -> 成本 -> 付款 -> 结算结果。",
        },
        {
            "scene_key": "my_work.workspace",
            "label": "我的工作",
            "route": "/my-work",
            "product_key": "my_work",
            "capability_key": "delivery.my_work.workspace",
            "description": "聚合当前用户的待办、风险与动作入口。",
            "scope": "工作台 -> 待办 -> 风险 -> 场景入口。",
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
    RELEASEABLE_STATES = {"preview", "stable"}

    def __init__(self, env):
        self.env = env

    def _stable_policy_domain(self, *, base_product_key: str):
        return [
            ("base_product_key", "=", str(base_product_key or "").strip() or "construction"),
            ("state", "=", "stable"),
            ("access_level", "=", "public"),
            ("active", "=", True),
        ]

    def resolve_policy_identity(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
    ) -> tuple[str, str, str]:
        explicit_product_key = str(product_key or "").strip()
        explicit_edition_key = str(edition_key or "").strip()
        explicit_base_product_key = str(base_product_key or "").strip() or "construction"
        if explicit_product_key:
            parts = explicit_product_key.split(".", 1)
            if len(parts) == 2 and parts[0] and parts[1]:
                return explicit_product_key, parts[0], parts[1]
            return explicit_product_key, explicit_base_product_key, explicit_edition_key or "standard"
        resolved_edition_key = explicit_edition_key or DEFAULT_PRODUCT_POLICY["edition_key"]
        resolved_base_product_key = explicit_base_product_key or DEFAULT_PRODUCT_POLICY["base_product_key"]
        return (
            f"{resolved_base_product_key}.{resolved_edition_key}",
            resolved_base_product_key,
            resolved_edition_key,
        )

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

    def _access_allowed(self, payload: dict, *, role_code: str) -> bool:
        access_level = str(payload.get("access_level") or "").strip() or "public"
        if access_level == "public":
            return True
        if access_level == "internal":
            return False
        if access_level == "role_restricted":
            allowed = payload.get("allowed_role_codes") if isinstance(payload.get("allowed_role_codes"), list) else []
            return str(role_code or "").strip() in {str(item or "").strip() for item in allowed if str(item or "").strip()}
        return False

    def _policy_releaseable(self, payload: dict) -> bool:
        state = str(payload.get("state") or "").strip() or "draft"
        return state in self.RELEASEABLE_STATES

    def _attach_edition_diagnostics(
        self,
        payload: dict,
        *,
        requested_product_key: str,
        requested_base_product_key: str,
        requested_edition_key: str,
        role_code: str,
        fallback_reason: str = "",
        access_allowed: bool = True,
    ) -> dict:
        row = copy.deepcopy(payload if isinstance(payload, dict) else {})
        row["edition_diagnostics"] = {
            "requested_product_key": requested_product_key,
            "requested_base_product_key": requested_base_product_key,
            "requested_edition_key": requested_edition_key,
            "resolved_product_key": str(row.get("product_key") or "").strip(),
            "resolved_base_product_key": str(row.get("base_product_key") or "").strip(),
            "resolved_edition_key": str(row.get("edition_key") or "").strip(),
            "requested_role_code": str(role_code or "").strip(),
            "policy_state": str(row.get("state") or "").strip(),
            "access_level": str(row.get("access_level") or "").strip(),
            "access_allowed": bool(access_allowed),
            "fallback_reason": str(fallback_reason or "").strip(),
            "fallback_applied": bool(fallback_reason),
        }
        return row

    def _fallback_stable_policy(self, *, base_product_key: str) -> dict:
        try:
            rec = self.env["sc.product.policy"].sudo().search(
                self._stable_policy_domain(base_product_key=base_product_key),
                order="edition_key asc, id asc",
                limit=1,
            )
        except Exception:
            rec = None
        if rec:
            return rec.to_runtime_dict()
        fallback = copy.deepcopy(DEFAULT_PRODUCT_POLICY)
        fallback["product_key"] = f"{base_product_key}.standard"
        fallback["base_product_key"] = base_product_key
        fallback["edition_key"] = "standard"
        fallback["state"] = "stable"
        fallback["access_level"] = "public"
        fallback["allowed_role_codes"] = []
        return fallback

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

    def get_policy(
        self,
        product_key: str | None = None,
        *,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        role_code: str | None = None,
        enforce_release: bool = False,
        enforce_access: bool = False,
    ) -> dict:
        key, resolved_base_product_key, resolved_edition_key = self.resolve_policy_identity(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
        )
        resolved_role_code = str(role_code or "").strip()
        try:
            rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", key), ("active", "=", True)], limit=1)
        except Exception:
            rec = None
        if rec:
            payload = rec.to_runtime_dict()
            if isinstance(payload, dict) and payload.get("product_key"):
                payload = self._sanitize_scene_version_bindings(payload)
                access_allowed = self._access_allowed(payload, role_code=resolved_role_code) if enforce_access else True
                release_allowed = self._policy_releaseable(payload) if enforce_release else True
                if access_allowed and release_allowed:
                    return self._attach_edition_diagnostics(
                        payload,
                        requested_product_key=key,
                        requested_base_product_key=resolved_base_product_key,
                        requested_edition_key=resolved_edition_key,
                        role_code=resolved_role_code,
                        access_allowed=access_allowed,
                    )
                fallback_reason = "EDITION_ACCESS_DENIED" if not access_allowed else "EDITION_STATE_NOT_RELEASEABLE"
                fallback = self._sanitize_scene_version_bindings(
                    self._fallback_stable_policy(base_product_key=resolved_base_product_key)
                )
                return self._attach_edition_diagnostics(
                    fallback,
                    requested_product_key=key,
                    requested_base_product_key=resolved_base_product_key,
                    requested_edition_key=resolved_edition_key,
                    role_code=resolved_role_code,
                    fallback_reason=fallback_reason,
                    access_allowed=access_allowed,
                )
        fallback = copy.deepcopy(DEFAULT_PRODUCT_POLICY)
        fallback["product_key"] = key
        fallback["base_product_key"] = resolved_base_product_key
        fallback["edition_key"] = resolved_edition_key
        fallback["label"] = "Construction Preview" if resolved_edition_key == "preview" else fallback.get("label")
        if enforce_release or enforce_access:
            fallback = self._sanitize_scene_version_bindings(
                self._fallback_stable_policy(base_product_key=resolved_base_product_key)
            )
        else:
            fallback = self._sanitize_scene_version_bindings(fallback)
        return self._attach_edition_diagnostics(
            fallback,
            requested_product_key=key,
            requested_base_product_key=resolved_base_product_key,
            requested_edition_key=resolved_edition_key,
            role_code=resolved_role_code,
            fallback_reason="POLICY_NOT_FOUND",
            access_allowed=True,
        )
