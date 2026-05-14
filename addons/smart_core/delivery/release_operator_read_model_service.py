# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

from .release_approval_policy_service import ReleaseApprovalPolicyService
from .release_audit_trail_service import ReleaseAuditTrailService
from .release_operator_contract_versions import (
    RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
    RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
)
from .product_identity import (
    LEGACY_DEFAULT_BASE_PRODUCT_KEY,
    default_operator_product_keys,
    resolve_product_identity,
    source_authority_contract as product_identity_source_authority_contract,
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class ReleaseOperatorReadModelService:
    SOURCE_KIND = "release_operator_read_model_projection"
    SOURCE_AUTHORITIES = ("release_audit_trail_projection", "release_approval_policy_projection", "delivery_product_identity_resolver")
    NO_BUSINESS_FACT_AUTHORITY = True
    DEFAULT_EDITIONS = ("standard", "preview")

    def __init__(self, env):
        self.env = env
        self.audit_service = ReleaseAuditTrailService(env)
        self.approval_policy_service = ReleaseApprovalPolicyService(env)

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="release_operator_surface",
        )

    def _default_base_product_key(self) -> tuple[str, str]:
        try:
            raw = self.env["ir.config_parameter"].sudo().get_param("smart_core.release_operator.default_base_product_key", "")
        except Exception:
            raw = ""
        configured = _text(raw)
        if configured:
            return configured, "config"
        return LEGACY_DEFAULT_BASE_PRODUCT_KEY, "legacy_default"

    def _resolve_product_key(self, product_key: str = "") -> str:
        requested = _text(product_key)
        if requested:
            return resolve_product_identity(product_key=requested).get("product_key") or requested
        default_base, _source = self._default_base_product_key()
        return default_operator_product_keys(base_product_key=default_base)[0]

    def _resolve_identity(self, product_key: str = "") -> dict[str, str]:
        resolved = self._resolve_product_key(product_key=product_key)
        identity = resolve_product_identity(product_key=resolved)
        requested = _text(product_key)
        default_base, default_source = self._default_base_product_key()
        identity["requested_product_key"] = requested
        identity["default_base_product_key"] = default_base
        identity["default_base_source"] = "request" if requested else default_source
        identity["source_authority"] = product_identity_source_authority_contract()
        return identity

    def _products(self, current_product_key: str) -> list[dict[str, Any]]:
        rows = []
        current_identity = self._resolve_identity(product_key=current_product_key)
        base_keys: list[str] = []
        configured_bases = self._configured_product_base_keys()
        for base_key in [current_identity.get("base_product_key"), *configured_bases]:
            token = _text(base_key)
            if token and token not in base_keys:
                base_keys.append(token)
        for item in [key for base_key in base_keys for key in default_operator_product_keys(base_product_key=base_key)]:
            identity = resolve_product_identity(product_key=item)
            rows.append(
                {
                    "product_key": item,
                    "base_product_key": identity["base_product_key"],
                    "edition_key": identity["edition_key"],
                    "label": self._product_label(identity),
                    "selected": item == current_product_key,
                }
            )
        return rows

    def _configured_product_base_keys(self) -> list[str]:
        try:
            raw = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.release_operator.product_base_keys",
                "construction,platform",
            )
        except Exception:
            raw = "construction,platform"
        return [_text(item) for item in str(raw or "").split(",") if _text(item)]

    def _product_label(self, identity: dict[str, str]) -> str:
        base_label = {
            "construction": "施工管理",
            "platform": "平台内核",
        }.get(_text(identity.get("base_product_key")), _text(identity.get("base_product_key")).title())
        edition_label = "标准版" if _text(identity.get("edition_key")) == "standard" else "预览版"
        return f"{base_label}{edition_label}"

    def _build_surface_copy(self, *, product_key: str) -> dict[str, Any]:
        identity = self._resolve_identity(product_key=product_key)
        edition_key = _text(identity.get("edition_key")) or "standard"
        edition_label = "标准版" if edition_key == "standard" else "预览版"
        return {
            "eyebrow": "Release Operator Surface",
            "title": "发布控制台",
            "description": f"查看 {edition_label} 当前发布状态、候选快照、待审批动作与回滚目标。",
            "error_title": "加载失败",
            "action_retry": "重试",
            "action_refresh": "刷新",
            "section_release_state": "当前发布状态",
            "section_control_scope": "受控内容",
            "section_policy_control": "产品策略管控",
            "section_candidate": "可 Promote 候选",
            "section_pending": "待审批动作",
            "section_rollback": "回滚",
            "section_history": "发布历史",
            "hint_candidate": "仅展示当前产品下 candidate / approved 状态的候选快照。",
            "hint_pending_count_prefix": "当前数量：",
            "hint_rollback": "仅当当前 active released snapshot 存在 rollback target 时可执行。",
            "hint_history": "最近 action 与 snapshot。",
            "freeze_action_label": "冻结候选快照",
            "sync_policy_action_label": "同步用户可见菜单",
            "save_policy_action_label": "保存策略",
            "policy_state_label": "发布状态",
            "policy_access_label": "访问级别",
            "metric_controlled_menus": "受控菜单",
            "metric_controlled_pages": "受控页面",
            "metric_controlled_scenes": "绑定场景",
            "metric_controlled_capabilities": "受控能力",
            "page_control_action_enable": "启用",
            "page_control_action_disable": "停用",
            "empty_candidate": "当前没有可 Promote 的候选快照。",
            "empty_pending": "当前没有待审批动作。",
            "metric_current_product": "当前产品",
            "metric_active_snapshot": "Active Released Snapshot",
            "metric_latest_action": "Latest Action",
            "metric_approval_state": "Approval State",
            "rollback_target_label": "Rollback Target",
            "rollback_action_label": "执行回滚",
            "history_actions_title": "Actions",
            "history_snapshots_title": "Snapshots",
            "approve_action_label": "审批并执行",
        }

    def _build_control_scope(self, *, product_key: str) -> dict[str, Any]:
        rec = None
        try:
            rec = self.env["sc.product.policy"].sudo().search(
                [("product_key", "=", product_key), ("active", "=", True)],
                limit=1,
            )
        except Exception:
            rec = None
        payload = rec.to_runtime_dict() if rec else {}
        menu_groups = _list(payload.get("menu_groups"))
        scenes = _list(payload.get("scenes"))
        capabilities = _list(payload.get("capabilities"))
        scene_bindings = _dict(payload.get("scene_version_bindings"))
        menu_count = 0
        enabled_menu_count = 0
        page_rows: list[dict[str, Any]] = []
        for group in menu_groups:
            if isinstance(group, dict):
                group_label = _text(group.get("group_label"))
                group_key = _text(group.get("group_key"))
                menus = [item for item in _list(group.get("menus")) if isinstance(item, dict)]
                menu_count += len(menus)
                for menu in menus:
                    enabled = bool(menu.get("enabled", True))
                    if enabled:
                        enabled_menu_count += 1
                    page_rows.append(
                        {
                            "group_key": group_key,
                            "group_label": group_label,
                            "menu_key": _text(menu.get("menu_key")),
                            "page_key": _text(menu.get("page_key")) or _text(menu.get("scene_key")),
                            "page_label": _text(menu.get("page_label")) or _text(menu.get("label")),
                            "label": _text(menu.get("label")),
                            "route": _text(menu.get("route")),
                            "scene_key": _text(menu.get("scene_key")),
                            "capability_key": _text(menu.get("capability_key")),
                            "visible_menu_path": _text(menu.get("visible_menu_path")) or f"{group_label} / {_text(menu.get('label'))}",
                            "control_granularity": _text(menu.get("control_granularity")) or "menu_page",
                            "enabled": enabled,
                        }
                    )
        enabled_scene_count = len([scene for scene in scenes if isinstance(scene, dict) and bool(scene.get("enabled", True))])
        enabled_capability_count = len([cap for cap in capabilities if isinstance(cap, dict) and bool(cap.get("enabled", True))])
        return {
            "product_key": product_key,
            "policy_id": int(payload.get("id") or 0),
            "policy_state": _text(payload.get("state")),
            "access_level": _text(payload.get("access_level")),
            "version": _text(payload.get("version")) or "v1",
            "menu_group_count": len(menu_groups),
            "menu_count": enabled_menu_count,
            "page_count": enabled_menu_count,
            "total_menu_count": menu_count,
            "total_page_count": menu_count,
            "scene_count": enabled_scene_count,
            "capability_count": enabled_capability_count,
            "scene_binding_count": len(scene_bindings),
            "menu_groups": menu_groups,
            "pages": page_rows,
            "scenes": scenes,
            "capabilities": capabilities,
        }

    def _serialize_snapshot(self, row: dict[str, Any]) -> dict[str, Any]:
        freeze_surface = _dict(row.get("freeze_surface"))
        identity = _dict(freeze_surface.get("identity"))
        return {
            "id": int(row.get("id") or 0),
            "product_key": _text(row.get("product_key")),
            "edition_key": _text(row.get("edition_key")),
            "version": _text(row.get("version")) or "v1",
            "state": _text(row.get("state")) or "candidate",
            "is_active": bool(row.get("is_active")),
            "released_at": _text(row.get("released_at")),
            "approved_at": _text(row.get("approved_at")),
            "frozen_at": _text(row.get("frozen_at")),
            "rollback_target_snapshot_id": int(row.get("rollback_target_snapshot_id") or 0),
            "label": _text(row.get("label")) or _text(identity.get("label")) or _text(row.get("product_key")),
            "channel": _text(row.get("channel")) or "stable",
            "state_reason": _text(row.get("state_reason")),
        }

    def _build_promote_actions(self, *, product_key: str, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        policy = self.approval_policy_service.resolve_policy(action_type="promote_snapshot", product_key=product_key)
        role_context = self.approval_policy_service.resolve_actor_role_context(self.env.user)
        actor_roles = list(role_context.get("actor_role_codes") or [])
        allowed = self.approval_policy_service.roles_match(actor_roles, list(_list(policy.get("allowed_executor_role_codes"))))
        actions: list[dict[str, Any]] = []
        for row in snapshots:
            state = _text(row.get("state"))
            if state not in {"candidate", "approved"}:
                continue
            snapshot_id = int(row.get("id") or 0)
            if snapshot_id <= 0:
                continue
            actions.append(
                {
                    "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
                    "key": f"promote:{snapshot_id}",
                    "label": f"Promote {row.get('version') or 'v1'}",
                    "intent": "release.operator.promote",
                    "enabled": bool(allowed),
                    "reason_code": "OK" if allowed else "RELEASE_EXECUTOR_NOT_ALLOWED",
                    "role_context": role_context,
                    "params": {
                        "product_key": product_key,
                        "snapshot_id": snapshot_id,
                        "replace_active": True,
                    },
                }
            )
        return actions

    def _build_pending_approval_queue(self, *, product_key: str) -> dict[str, Any]:
        actions = self.env["sc.release.action"].sudo().search(
            [
                ("product_key", "=", product_key),
                ("active", "=", True),
                ("approval_required", "=", True),
                ("approval_state", "=", "pending_approval"),
                ("state", "=", "pending"),
            ],
            order="requested_at desc, id desc",
            limit=20,
        )
        rows: list[dict[str, Any]] = []
        for action in actions:
            payload = action.to_runtime_dict()
            allowed, reason_code, diagnostics = self.approval_policy_service.can_approve(action=action, user=self.env.user)
            rows.append(
                {
                    **payload,
                    "can_approve": bool(allowed),
                    "approve_reason_code": reason_code,
                    "approve_diagnostics": diagnostics,
                    "approve_intent": "release.operator.approve",
                }
            )
        return {
            "count": len(rows),
            "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "actions": rows,
        }

    def _build_rollback_action(self, *, product_key: str, active_snapshot: dict[str, Any]) -> dict[str, Any]:
        policy = self.approval_policy_service.resolve_policy(action_type="rollback_snapshot", product_key=product_key)
        role_context = self.approval_policy_service.resolve_actor_role_context(self.env.user)
        actor_roles = list(role_context.get("actor_role_codes") or [])
        allowed = self.approval_policy_service.roles_match(actor_roles, list(_list(policy.get("allowed_executor_role_codes"))))
        rollback_target_snapshot_id = int(active_snapshot.get("rollback_target_snapshot_id") or 0)
        enabled = bool(allowed and rollback_target_snapshot_id > 0)
        reason_code = "OK" if enabled else ("ROLLBACK_TARGET_NOT_FOUND" if rollback_target_snapshot_id <= 0 else "RELEASE_EXECUTOR_NOT_ALLOWED")
        return {
            "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "key": f"rollback:{product_key}",
            "label": "执行回滚",
            "intent": "release.operator.rollback",
            "enabled": enabled,
            "reason_code": reason_code,
            "role_context": role_context,
            "params": {
                "product_key": product_key,
                "target_snapshot_id": rollback_target_snapshot_id,
            },
        }

    def build_read_model(self, *, product_key: str = "", action_limit: int = 20) -> dict[str, Any]:
        from .release_operator_contract_registry import build_release_operator_contract_registry

        identity = self._resolve_identity(product_key=product_key)
        audit = self.audit_service.build_audit_trail(product_key=identity["product_key"], action_limit=action_limit)
        active_snapshot = _dict(audit.get("active_released_snapshot"))
        release_actions = [row for row in _list(audit.get("release_actions")) if isinstance(row, dict)]
        release_snapshots = [row for row in _list(audit.get("release_snapshots")) if isinstance(row, dict)]
        candidate_snapshots = [
            self._serialize_snapshot(row)
            for row in release_snapshots
            if _text(_dict(row).get("state")) in {"candidate", "approved"}
        ]
        release_history_summary = {
            "actions": release_actions[:10],
            "snapshots": [self._serialize_snapshot(row) for row in release_snapshots[:10]],
        }
        pending_approval_queue = self._build_pending_approval_queue(product_key=identity["product_key"])
        current_release_state = {
            "active_snapshot": self._serialize_snapshot(active_snapshot),
            "runtime_summary": deepcopy(_dict(_dict(audit.get("runtime")).get("release_audit_trail_summary"))),
            "released_snapshot_lineage": deepcopy(_dict(_dict(audit.get("runtime")).get("released_snapshot_lineage"))),
        }
        role_context = self.approval_policy_service.resolve_actor_role_context(self.env.user)
        available_operator_actions = {
            "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "freeze": {
                "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
                "key": f"freeze:{identity['product_key']}",
                "label": "冻结候选快照",
                "intent": "release.operator.freeze",
                "enabled": True,
                "reason_code": "OK",
                "role_context": role_context,
                "params": {
                    "product_key": identity["product_key"],
                    "replace_active": False,
                },
            },
            "sync_policy": {
                "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
                "key": f"sync_policy:{identity['product_key']}",
                "label": "同步已实现能力",
                "intent": "release.operator.sync_policy",
                "enabled": True,
                "reason_code": "OK",
                "role_context": role_context,
                "params": {
                    "product_key": identity["product_key"],
                    "preserve_state": True,
                    "preserve_access_level": True,
                },
            },
            "set_page_enabled": {
                "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
                "key": f"set_page_enabled:{identity['product_key']}",
                "label": "调整页面发布范围",
                "intent": "release.operator.set_page_enabled",
                "enabled": True,
                "reason_code": "OK",
                "role_context": role_context,
                "params": {
                    "product_key": identity["product_key"],
                },
            },
            "update_policy": {
                "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
                "key": f"update_policy:{identity['product_key']}",
                "label": "保存策略",
                "intent": "release.operator.update_policy",
                "enabled": True,
                "reason_code": "OK",
                "role_context": role_context,
                "params": {
                    "product_key": identity["product_key"],
                },
            },
            "promote": self._build_promote_actions(product_key=identity["product_key"], snapshots=candidate_snapshots),
            "rollback": self._build_rollback_action(product_key=identity["product_key"], active_snapshot=active_snapshot),
        }
        surface_copy = self._build_surface_copy(product_key=identity["product_key"])
        return {
            "contract_version": RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "source_authority": self.source_authority_contract(),
            "copy": surface_copy,
            "identity": {
                "product_key": identity["product_key"],
                "base_product_key": identity["base_product_key"],
                "edition_key": identity["edition_key"],
                "source": identity.get("source") or "",
                "requested_product_key": identity.get("requested_product_key") or "",
                "default_base_product_key": identity.get("default_base_product_key") or "",
                "default_base_source": identity.get("default_base_source") or "",
                "source_authority": identity.get("source_authority") if isinstance(identity.get("source_authority"), dict) else {},
            },
            "products": self._products(identity["product_key"]),
            "actor_role_context": role_context,
            "control_scope": self._build_control_scope(product_key=identity["product_key"]),
            "current_release_state": current_release_state,
            "pending_approval_queue": pending_approval_queue,
            "candidate_snapshots": candidate_snapshots,
            "release_history_summary": release_history_summary,
            "available_operator_actions": available_operator_actions,
        }
