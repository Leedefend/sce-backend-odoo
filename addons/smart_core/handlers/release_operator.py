# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any

from odoo import fields
from odoo.exceptions import AccessError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import (
    EditionReleaseSnapshotPromotionService,
)
from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService
from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import ProductPolicyCatalogSyncService
from odoo.addons.smart_core.delivery.release_approval_policy_service import ReleaseApprovalPolicyService
from odoo.addons.smart_core.delivery.release_operator_surface_service import ReleaseOperatorSurfaceService
from odoo.addons.smart_core.delivery.release_runtime_user_probe_service import ReleaseRuntimeUserProbeService
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin


SOURCE_KIND = "release_operator_intent_proxy"
SOURCE_AUTHORITIES = (
    "release_operator_surface_projection",
    "release_approval_policy_projection",
    "edition_release_snapshot_projection",
    "edition_release_snapshot_state_transition",
    "product_policy_catalog_sync",
    "release_runtime_user_probe_projection",
    "sc.release.action",
    "sc.product.policy",
)
NO_BUSINESS_FACT_AUTHORITY = True


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value or 0)
    except Exception as exc:
        raise ValueError(f"{field_name.upper()}_INVALID") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name.upper()}_INVALID")
    return parsed


def _selection(value: Any, allowed: set[str], field_name: str) -> str:
    parsed = _text(value)
    if parsed not in allowed:
        raise ValueError(f"{field_name.upper()}_INVALID")
    return parsed


class _ReleaseOperatorBaseHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": cls.INTENT_TYPE == "release.operator.surface",
            "write_proxy": cls.INTENT_TYPE != "release.operator.surface",
            "delivery_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _check_permissions(self):
        if not user_is_platform_admin(self.env.user):
            raise AccessError("PERMISSION_DENIED: release operator requires platform administrator")
        return True

    def _params(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        params = payload.get("params")
        if isinstance(params, dict):
            return params
        return payload

    def _response(self, ts0: float, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_authority": self.source_authority_contract(),
            },
        }

    def _action_model(self):
        return self.env["sc.release.action"].sudo()

    def _snapshot_model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

    def _load_action(self, action_id: int):
        action = self._action_model().browse(int(action_id))
        if not action.exists() or not action.active:
            raise ValueError("RELEASE_ACTION_NOT_FOUND")
        return action

    def _load_snapshot(self, snapshot_id: int):
        snapshot = self._snapshot_model().browse(int(snapshot_id))
        if not snapshot.exists() or not snapshot.active:
            raise ValueError("RELEASE_SNAPSHOT_NOT_FOUND")
        return snapshot

    def _build_action_values(
        self,
        *,
        action_type: str,
        product_key: str,
        source_snapshot=None,
        target_snapshot=None,
        request_payload: dict[str, Any] | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        policy = ReleaseApprovalPolicyService(self.env).build_action_policy(
            action_type=action_type,
            product_key=product_key,
            user=self.env.user,
        )
        snapshot = target_snapshot or source_snapshot
        return {
            "name": f"{action_type}:{product_key}",
            "action_type": action_type,
            "state": "pending",
            "product_key": product_key,
            "base_product_key": _text(getattr(snapshot, "base_product_key", "")),
            "edition_key": _text(getattr(snapshot, "edition_key", "")),
            "requested_by_user_id": int(self.env.user.id or 0),
            "requested_at": fields.Datetime.now(),
            "source_snapshot_id": int(source_snapshot.id) if source_snapshot else False,
            "target_snapshot_id": int(target_snapshot.id) if target_snapshot else False,
            "policy_key": _text(policy.get("policy_key")),
            "approval_required": bool(policy.get("approval_required")),
            "approval_state": _text(policy.get("approval_state")) or "not_required",
            "allowed_executor_role_codes_json": list(policy.get("allowed_executor_role_codes_json") or []),
            "required_approver_role_codes_json": list(policy.get("required_approver_role_codes_json") or []),
            "policy_snapshot_json": _dict(policy.get("policy_snapshot_json")),
            "request_payload_json": dict(request_payload or {}),
            "note": _text(note),
            "execution_protocol_version": "release_operator_write_model_v1",
            "execution_trace_json": {
                "requested_intent": self.INTENT_TYPE,
                "requested_by_user_id": int(self.env.user.id or 0),
            },
        }

    def _execute_approved_action(self, action, *, note: str = "") -> dict[str, Any]:
        allowed, reason, diagnostics = ReleaseApprovalPolicyService(self.env).can_execute(action=action, user=self.env.user)
        if not allowed:
            action.write({"state": "failed", "reason_code": reason, "diagnostics_json": diagnostics})
            raise ValueError(reason)
        promotion = EditionReleaseSnapshotPromotionService(self.env)
        action_type = _text(action.action_type)
        now = fields.Datetime.now()
        result: dict[str, Any]
        if action_type == "promote_snapshot":
            snapshot_id = int(action.target_snapshot_id.id or action.source_snapshot_id.id or 0)
            if snapshot_id <= 0:
                raise ValueError("TARGET_SNAPSHOT_NOT_FOUND")
            snapshot = self._load_snapshot(snapshot_id)
            EditionReleaseSnapshotService(self.env).assert_candidate_matches_current_draft(snapshot)
            result = promotion.promote_to_released(
                snapshot_id,
                replace_active=True,
                state_reason="released_from_release_operator",
                promotion_note=_text(note) or "released from release operator",
            )
        elif action_type == "rollback_snapshot":
            snapshot_id = int(action.target_snapshot_id.id or 0)
            if snapshot_id <= 0:
                raise ValueError("ROLLBACK_TARGET_NOT_FOUND")
            result = promotion.promote_to_released(
                snapshot_id,
                replace_active=True,
                state_reason="rollback_from_release_operator",
                promotion_note=_text(note) or "rollback from release operator",
            )
        else:
            raise ValueError(f"UNSUPPORTED_RELEASE_ACTION_TYPE:{action_type}")
        action.write(
            {
                "state": "done",
                "executed_at": action.executed_at or now,
                "completed_at": now,
                "result_snapshot_id": int(result.get("id") or 0) or False,
                "result_payload_json": result,
                "reason_code": "OK",
                "diagnostics_json": {
                    **(action.diagnostics_json if isinstance(action.diagnostics_json, dict) else {}),
                    "execution": diagnostics,
                },
            }
        )
        return action.to_runtime_dict()


class ReleaseOperatorSurfaceHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.surface"
    DESCRIPTION = "平台产品发布控制台读取契约"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        action_limit = int(params.get("action_limit") or 20)
        surface = ReleaseOperatorSurfaceService(self.env).build_surface(
            product_key=product_key,
            action_limit=max(action_limit, 1),
        )
        return self._response(ts0, surface)


class ReleaseOperatorRuntimeProbeHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.runtime_probe"
    DESCRIPTION = "平台产品发布后真实用户可用性验证"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        probe = ReleaseRuntimeUserProbeService(self.env).probe(
            product_key=product_key,
            login=_text(params.get("login")),
        )
        return self._response(ts0, {"runtime_user_probe": probe})


class ReleaseOperatorPromoteHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.promote"
    DESCRIPTION = "平台产品发布候选 Promote"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "release promotion mutates platform release state"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        snapshot = self._load_snapshot(_positive_int(params.get("snapshot_id"), "snapshot_id"))
        product_key = _text(params.get("product_key")) or _text(snapshot.product_key)
        EditionReleaseSnapshotService(self.env).assert_candidate_matches_current_draft(snapshot)
        action = self._action_model().create(
            self._build_action_values(
                action_type="promote_snapshot",
                product_key=product_key,
                source_snapshot=snapshot,
                target_snapshot=snapshot,
                request_payload=params,
                note=_text(params.get("note")),
            )
        )
        if not bool(action.approval_required):
            action.write({"approval_state": "not_required", "executed_at": fields.Datetime.now()})
            result = self._execute_approved_action(action, note=_text(params.get("note")))
        else:
            result = action.to_runtime_dict()
        return self._response(ts0, {"action": result, "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key)})


class ReleaseOperatorFreezeHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.freeze"
    DESCRIPTION = "平台产品发布面冻结候选快照"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "release freeze mutates platform release snapshot state"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        version = _text(params.get("version")) or fields.Datetime.now().strftime("v%Y%m%d%H%M%S")
        snapshot = EditionReleaseSnapshotService(self.env).freeze_release_surface(
            product_key=product_key,
            version=version,
            role_code=_text(params.get("role_code")),
            note=_text(params.get("note")) or "frozen from release operator",
            replace_active=False,
        )
        return self._response(
            ts0,
            {
                "snapshot": snapshot,
                "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key),
            },
        )


class ReleaseOperatorSyncPolicyHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.sync_policy"
    DESCRIPTION = "平台产品策略从已实现能力目录同步"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "product policy sync mutates platform product policy"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        policy = ProductPolicyCatalogSyncService(self.env).sync_policy(
            product_key=product_key,
            preserve_state=_bool(params.get("preserve_state"), True),
            preserve_access_level=_bool(params.get("preserve_access_level"), True),
        )
        return self._response(
            ts0,
            {
                "policy": policy.to_runtime_dict(),
                "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key),
            },
        )


class ReleaseOperatorUpdatePolicyHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.update_policy"
    DESCRIPTION = "平台产品发布策略更新"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "product policy update mutates platform product policy"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        policy = self.env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)
        if not policy:
            policy = ProductPolicyCatalogSyncService(self.env).sync_policy(product_key=product_key)
        values: dict[str, Any] = {}
        if "state" in params:
            values["state"] = _selection(params.get("state"), {"draft", "preview", "stable", "archived"}, "state")
        if "access_level" in params:
            values["access_level"] = _selection(params.get("access_level"), {"public", "internal", "role_restricted"}, "access_level")
        if "active" in params:
            values["active"] = _bool(params.get("active"), True)
        if "allowed_role_codes" in params:
            allowed_roles = params.get("allowed_role_codes")
            values["allowed_role_codes"] = [str(item).strip() for item in allowed_roles if str(item).strip()] if isinstance(allowed_roles, list) else []
        if values:
            policy.write(values)
        return self._response(
            ts0,
            {
                "policy": policy.to_runtime_dict(),
                "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key),
            },
        )


class ReleaseOperatorSetPageEnabledHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.set_page_enabled"
    DESCRIPTION = "平台产品用户可见页面发布范围调整"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "product menu page control mutates platform product policy"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        page_key = _text(params.get("page_key") or params.get("scene_key") or params.get("menu_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        if not page_key:
            raise ValueError("PAGE_KEY_REQUIRED")
        policy = self.env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)
        if not policy:
            policy = ProductPolicyCatalogSyncService(self.env).sync_policy(product_key=product_key)
        policy = self._write_page_policy(
            policy,
            page_key=page_key,
            updates={"enabled": _bool(params.get("enabled"), True)},
        )
        return self._response(
            ts0,
            {
                "policy": policy.to_runtime_dict(),
                "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key),
            },
        )

    def _write_page_policy(self, policy, *, page_key: str, updates: dict[str, Any]):
        payload = policy.to_runtime_dict()

        def _match(row: dict[str, Any]) -> bool:
            keys = {
                _text(row.get("page_key")),
                _text(row.get("scene_key")),
                _text(row.get("target_page_key")),
                _text(row.get("target_scene_key")),
                _text(row.get("menu_key")),
                _text(row.get("capability_key")),
            }
            return page_key in keys

        menu_groups = []
        for group in payload.get("menu_groups") if isinstance(payload.get("menu_groups"), list) else []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            menus = []
            for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
                if not isinstance(menu, dict):
                    continue
                next_menu = dict(menu)
                if _match(next_menu):
                    next_menu.update(updates)
                menus.append(next_menu)
            next_group["menus"] = menus
            menu_groups.append(next_group)
        scenes = []
        for scene in payload.get("scenes") if isinstance(payload.get("scenes"), list) else []:
            if not isinstance(scene, dict):
                continue
            next_scene = dict(scene)
            if _match(next_scene):
                next_scene.update(updates)
            scenes.append(next_scene)
        capabilities = []
        for capability in payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []:
            if not isinstance(capability, dict):
                continue
            next_capability = dict(capability)
            if _match(next_capability):
                next_capability.update(updates)
            capabilities.append(next_capability)
        policy.write(
            {
                "menu_groups": menu_groups,
                "scenes": scenes,
                "capabilities": capabilities,
                "note": "page-level release scope updated from release operator",
            }
        )
        return policy


class ReleaseOperatorUpdatePagePolicyHandler(ReleaseOperatorSetPageEnabledHandler):
    INTENT_TYPE = "release.operator.update_page_policy"
    DESCRIPTION = "平台产品用户可见页面管控策略调整"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "product page policy update mutates platform product policy"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        page_key = _text(params.get("page_key") or params.get("scene_key") or params.get("menu_key"))
        if not product_key:
            raise ValueError("PRODUCT_KEY_REQUIRED")
        if not page_key:
            raise ValueError("PAGE_KEY_REQUIRED")
        policy = self.env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)
        if not policy:
            policy = ProductPolicyCatalogSyncService(self.env).sync_policy(product_key=product_key)
        updates: dict[str, Any] = {}
        if "enabled" in params:
            updates["enabled"] = _bool(params.get("enabled"), True)
        if "release_state" in params:
            updates["release_state"] = _selection(params.get("release_state"), {"released", "preview", "hidden", "retired"}, "release_state")
            if updates["release_state"] in {"hidden", "retired"}:
                updates.setdefault("enabled", False)
            else:
                updates.setdefault("enabled", True)
        if "access_level" in params:
            updates["access_level"] = _selection(params.get("access_level"), {"public", "internal", "role_restricted"}, "access_level")
        if "policy_note" in params:
            updates["policy_note"] = _text(params.get("policy_note"))
        if not updates:
            raise ValueError("PAGE_POLICY_UPDATE_REQUIRED")
        policy = self._write_page_policy(policy, page_key=page_key, updates=updates)
        return self._response(
            ts0,
            {
                "policy": policy.to_runtime_dict(),
                "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key),
            },
        )


class ReleaseOperatorApproveHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.approve"
    DESCRIPTION = "平台产品发布动作审批并执行"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "release approval mutates platform release state"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        action = self._load_action(_positive_int(params.get("action_id"), "action_id"))
        ReleaseApprovalPolicyService(self.env).approve_action(
            action=action,
            user=self.env.user,
            note=_text(params.get("note")),
        )
        result = self._execute_approved_action(action, note=_text(params.get("note")))
        return self._response(
            ts0,
            {"action": result, "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=_text(action.product_key))},
        )


class ReleaseOperatorRollbackHandler(_ReleaseOperatorBaseHandler):
    INTENT_TYPE = "release.operator.rollback"
    DESCRIPTION = "平台产品发布回滚"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "release rollback mutates platform release state"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        product_key = _text(params.get("product_key"))
        target_snapshot_id = _positive_int(params.get("target_snapshot_id"), "target_snapshot_id")
        target = self._load_snapshot(target_snapshot_id)
        product_key = product_key or _text(target.product_key)
        active = self._snapshot_model().search(
            [
                ("product_key", "=", product_key),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        action = self._action_model().create(
            self._build_action_values(
                action_type="rollback_snapshot",
                product_key=product_key,
                source_snapshot=active if active else None,
                target_snapshot=target,
                request_payload={**params, "replace_active": _bool(params.get("replace_active"), True)},
                note=_text(params.get("note")),
            )
        )
        if not bool(action.approval_required):
            action.write({"approval_state": "not_required", "executed_at": fields.Datetime.now()})
            result = self._execute_approved_action(action, note=_text(params.get("note")))
        else:
            result = action.to_runtime_dict()
        return self._response(ts0, {"action": result, "surface": ReleaseOperatorSurfaceService(self.env).build_surface(product_key=product_key)})
