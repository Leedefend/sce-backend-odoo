# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .release_approval_policy_service import ReleaseApprovalPolicyService
from .release_audit_trail_service import ReleaseAuditTrailService
from .release_operator_contract_versions import (
    RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
    RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class ReleaseOperatorReadModelService:
    DEFAULT_PRODUCTS = ("construction.standard", "construction.preview")

    def __init__(self, env):
        self.env = env
        self.audit_service = ReleaseAuditTrailService(env)
        self.approval_policy_service = ReleaseApprovalPolicyService(env)

    def _resolve_product_key(self, product_key: str = "") -> str:
        requested = _text(product_key)
        if requested in self.DEFAULT_PRODUCTS:
            return requested
        return "construction.standard"

    def _resolve_identity(self, product_key: str = "") -> dict[str, str]:
        resolved = self._resolve_product_key(product_key=product_key)
        return self.approval_policy_service._release_identity(product_key=resolved)

    def _products(self, current_product_key: str) -> list[dict[str, Any]]:
        rows = []
        for item in self.DEFAULT_PRODUCTS:
            identity = self.approval_policy_service._release_identity(product_key=item)
            rows.append(
                {
                    "product_key": item,
                    "base_product_key": identity["base_product_key"],
                    "edition_key": identity["edition_key"],
                    "label": "Standard" if identity["edition_key"] == "standard" else "Preview",
                    "selected": item == current_product_key,
                }
            )
        return rows

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
            "section_candidate": "可 Promote 候选",
            "section_pending": "待审批动作",
            "section_rollback": "回滚",
            "section_history": "发布历史",
            "hint_candidate": "仅展示当前产品下 candidate / approved 状态的候选快照。",
            "hint_pending_count_prefix": "当前数量：",
            "hint_rollback": "仅当当前 active released snapshot 存在 rollback target 时可执行。",
            "hint_history": "最近 action 与 snapshot。",
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
        actor_roles = self.approval_policy_service.resolve_actor_role_codes(self.env.user)
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
        actor_roles = self.approval_policy_service.resolve_actor_role_codes(self.env.user)
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
        available_operator_actions = {
            "write_model_contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "promote": self._build_promote_actions(product_key=identity["product_key"], snapshots=candidate_snapshots),
            "rollback": self._build_rollback_action(product_key=identity["product_key"], active_snapshot=active_snapshot),
        }
        surface_copy = self._build_surface_copy(product_key=identity["product_key"])
        return {
            "contract_version": RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "copy": surface_copy,
            "identity": {
                "product_key": identity["product_key"],
                "base_product_key": identity["base_product_key"],
                "edition_key": identity["edition_key"],
            },
            "products": self._products(identity["product_key"]),
            "current_release_state": current_release_state,
            "pending_approval_queue": pending_approval_queue,
            "candidate_snapshots": candidate_snapshots,
            "release_history_summary": release_history_summary,
            "available_operator_actions": available_operator_actions,
        }
