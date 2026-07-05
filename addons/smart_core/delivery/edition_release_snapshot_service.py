# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from odoo import SUPERUSER_ID, api, fields
from odoo.modules.registry import Registry
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
try:
    from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
except Exception:  # pragma: no cover - standalone boundary tests install minimal modules.
    call_extension_hook_first = None

from .delivery_engine import DeliveryEngine
from .edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from .product_policy_service import ProductPolicyService


FREEZE_SURFACE_CONTRACT_VERSION = "edition_freeze_surface_v1"
SOURCE_KIND = "edition_release_snapshot_projection"
SOURCE_AUTHORITIES = (
    "sc.edition.release.snapshot",
    "delivery_engine_projection",
    "delivery_product_policy_projection",
)
NO_BUSINESS_FACT_AUTHORITY = True
LEGACY_DEFAULT_ROLE_SOURCE_KIND = "legacy_release_snapshot_default_role_projection"
PLATFORM_DEFAULT_RELEASE_ROLE_CODE = "owner"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


class EditionReleaseSnapshotService:
    def __init__(self, env):
        self.env = env
        self.policy_service = ProductPolicyService(env)
        self.delivery_engine = DeliveryEngine(env)
        self.promotion_service = EditionReleaseSnapshotPromotionService(env)

    def _model(self):
        registry = getattr(self.env, "registry", None)
        models = getattr(registry, "models", {}) if registry is not None else {}
        if "sc.edition.release.snapshot" not in models:
            return None
        return self.env["sc.edition.release.snapshot"].sudo()

    def _model_registered(self, model_name: str) -> bool:
        token = _text(model_name)
        if not token:
            return False
        registry = getattr(self.env, "registry", None)
        models = getattr(registry, "models", {}) if registry is not None else {}
        return token in models

    def now(self):
        return fields.Datetime.now()

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=SOURCE_KIND,
            authorities=SOURCE_AUTHORITIES,
            rebuildable=None,
            no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="edition_release_snapshot",
            legacy_default_role_source=LEGACY_DEFAULT_ROLE_SOURCE_KIND,
        )

    @classmethod
    def legacy_default_role_source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=LEGACY_DEFAULT_ROLE_SOURCE_KIND,
            authorities=("platform_default_role_code", "extension_hook:smart_core_default_release_snapshot_role_code"),
            rebuildable=None,
            no_business_fact_authority=True,
            legacy_compatibility=True,
        )

    def _default_release_role_code(self) -> str:
        if callable(call_extension_hook_first):
            payload = call_extension_hook_first(self.env, "smart_core_default_release_snapshot_role_code", self.env)
            value = _text(payload)
            if value:
                return value
        return PLATFORM_DEFAULT_RELEASE_ROLE_CODE

    def _freeze_role_code(self, policy: dict[str, Any], explicit_role_code: str = "") -> str:
        if _text(explicit_role_code):
            return _text(explicit_role_code)
        allowed = policy.get("allowed_role_codes") if isinstance(policy.get("allowed_role_codes"), list) else []
        for item in allowed:
            value = _text(item)
            if value:
                return value
        return self._default_release_role_code()

    def _default_requested_role_code(
        self,
        *,
        requested_product_key: str,
        explicit_role_code: str = "",
    ) -> str:
        if _text(explicit_role_code):
            return _text(explicit_role_code)
        rec = None
        if self._model_registered("sc.product.policy"):
            rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", _text(requested_product_key)), ("active", "=", True)], limit=1)
        if rec and isinstance(rec.allowed_role_codes, list):
            for item in rec.allowed_role_codes:
                value = _text(item)
                if value:
                    return value
        return self._default_release_role_code()

    def _default_requested_role_context(
        self,
        *,
        requested_product_key: str,
        explicit_role_code: str = "",
    ) -> dict[str, Any]:
        role_code = self._default_requested_role_code(
            requested_product_key=requested_product_key,
            explicit_role_code=explicit_role_code,
        )
        return {
            "role_code": role_code,
            "source": "explicit" if _text(explicit_role_code) else "product_policy_or_legacy_default",
            "legacy_default_role_source_authority": (
                self.legacy_default_role_source_authority_contract() if not _text(explicit_role_code) else {}
            ),
        }

    def build_freeze_surface(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        role_code: str = "",
    ) -> dict[str, Any]:
        requested_product_key, requested_base_product_key, requested_edition_key = self.policy_service.resolve_policy_identity(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
        )
        requested_role_context = self._default_requested_role_context(
            requested_product_key=requested_product_key,
            explicit_role_code=role_code,
        )
        requested_role_code = _text(requested_role_context.get("role_code"))
        policy = self.policy_service.get_policy(
            product_key=requested_product_key,
            edition_key=requested_edition_key,
            base_product_key=requested_base_product_key,
            role_code=requested_role_code,
            enforce_release=True,
            enforce_access=True,
        )
        freeze_role_code = self._freeze_role_code(policy, explicit_role_code=requested_role_code)
        delivery = self.delivery_engine.build(
            data={"role_surface": {"role_code": freeze_role_code}, "scenes": [], "capabilities": []},
            product_key=requested_product_key,
            edition_key=requested_edition_key,
            base_product_key=requested_base_product_key,
        )
        resolved_policy = _dict(policy)
        resolved_delivery = _dict(delivery)
        effective_product_key = _text(resolved_delivery.get("product_key")) or _text(resolved_policy.get("product_key"))
        effective_base_product_key = _text(resolved_delivery.get("base_product_key")) or _text(resolved_policy.get("base_product_key"))
        effective_edition_key = _text(resolved_delivery.get("edition_key")) or _text(resolved_policy.get("edition_key"))
        policy_rec = None
        if self._model_registered("sc.product.policy"):
            policy_rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", effective_product_key), ("active", "=", True)], limit=1)
        declared_scene_bindings = (
            deepcopy(policy_rec.scene_version_bindings)
            if policy_rec and isinstance(policy_rec.scene_version_bindings, dict)
            else deepcopy(_dict(resolved_policy.get("scene_version_bindings")))
        )
        identity = {
            "product_key": effective_product_key,
            "base_product_key": effective_base_product_key,
            "edition_key": effective_edition_key,
            "label": _text(resolved_policy.get("label")),
            "version": _text(resolved_policy.get("version")) or "v1",
            "channel": "preview" if effective_edition_key == "preview" else "stable",
        }
        runtime_meta = {
            "source_authority": self.source_authority_contract(),
            "requested": {
                "product_key": requested_product_key,
                "base_product_key": requested_base_product_key,
                "edition_key": requested_edition_key,
                "role_code": freeze_role_code,
            },
            "effective": {
                "product_key": effective_product_key,
                "base_product_key": effective_base_product_key,
                "edition_key": effective_edition_key,
                "role_code": freeze_role_code,
            },
            "edition_diagnostics": _dict(resolved_policy.get("edition_diagnostics")),
            "delivery_engine_meta": _dict(resolved_delivery.get("meta")),
            "requested_role_context": requested_role_context,
        }
        snapshot = {
            "contract_version": FREEZE_SURFACE_CONTRACT_VERSION,
            "source_authority": self.source_authority_contract(),
            "identity": identity,
            "policy": {
                "product_key": effective_product_key,
                "base_product_key": effective_base_product_key,
                "edition_key": effective_edition_key,
                "state": _text(resolved_policy.get("state")),
                "access_level": _text(resolved_policy.get("access_level")),
                "allowed_role_codes": deepcopy(_list(resolved_policy.get("allowed_role_codes"))),
                "label": _text(resolved_policy.get("label")),
                "version": _text(resolved_policy.get("version")) or "v1",
            },
            "nav": deepcopy(_list(resolved_delivery.get("nav"))),
            "capabilities": deepcopy(_list(resolved_delivery.get("capabilities"))),
            "scenes": deepcopy(_list(resolved_delivery.get("scenes"))),
            "scene_version_bindings": declared_scene_bindings,
            "resolved_scene_version_bindings": deepcopy(_dict(resolved_policy.get("scene_version_bindings"))),
            "scene_binding_diagnostics": deepcopy(_dict(resolved_policy.get("scene_binding_diagnostics"))),
            "runtime_meta": runtime_meta,
        }
        return snapshot

    def _draft_pages_from_policy(self, policy: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for group in _list(policy.get("menu_groups")):
            if not isinstance(group, dict):
                continue
            for menu in _list(group.get("menus")):
                if not isinstance(menu, dict):
                    continue
                page_key = _text(menu.get("page_key") or menu.get("scene_key") or menu.get("menu_key"))
                if not page_key:
                    continue
                enabled = bool(menu.get("enabled", True))
                release_state = _text(menu.get("release_state")) or ("released" if enabled else "hidden")
                rows.append(
                    {
                        "page_key": page_key,
                        "menu_key": _text(menu.get("menu_key")),
                        "label": _text(menu.get("page_label") or menu.get("label") or page_key),
                        "visible_menu_path": _text(menu.get("visible_menu_path")),
                        "route": _text(menu.get("route")),
                        "release_state": release_state,
                        "enabled": enabled,
                        "access_level": _text(menu.get("access_level")) or _text(policy.get("access_level")) or "public",
                        "menu_id": int(menu.get("menu_id") or 0),
                        "action_id": int(menu.get("action_id") or 0),
                        "menu_xmlid": _text(menu.get("menu_xmlid")),
                        "res_model": _text(menu.get("res_model")),
                    }
                )
        return rows

    def _draft_fingerprint(self, *, policy: dict[str, Any], pages: list[dict[str, Any]]) -> str:
        normalized_pages = [
            {
                "page_key": _text(row.get("page_key")),
                "release_state": _text(row.get("release_state")),
                "enabled": bool(row.get("enabled")),
                "access_level": _text(row.get("access_level")),
                "route": _text(row.get("route")),
                "menu_id": int(row.get("menu_id") or 0),
                "action_id": int(row.get("action_id") or 0),
                "menu_xmlid": _text(row.get("menu_xmlid")),
                "res_model": _text(row.get("res_model")),
            }
            for row in sorted(pages, key=lambda item: _text(item.get("page_key")))
        ]
        payload = {
            "product_key": _text(policy.get("product_key")),
            "state": _text(policy.get("state")),
            "access_level": _text(policy.get("access_level")),
            "allowed_role_codes": sorted(_text(item) for item in _list(policy.get("allowed_role_codes")) if _text(item)),
            "pages": normalized_pages,
        }
        return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()

    def _preflight_checks_from_pages(self, *, pages: list[dict[str, Any]], active_snapshot_id: int) -> list[dict[str, Any]]:
        effective_pages = [row for row in pages if bool(row.get("enabled")) and _text(row.get("release_state")) in {"released", "preview"}]
        preview_pages = [row for row in effective_pages if _text(row.get("release_state")) == "preview"]
        hidden_pages = [row for row in pages if not bool(row.get("enabled")) or _text(row.get("release_state")) in {"hidden", "retired"}]
        checks = [
            {
                "key": "has_product_pages",
                "label": "产品页面范围",
                "status": "pass" if effective_pages else "fail",
                "message": f"有效发布页面 {len(effective_pages)}/{len(pages)}",
                "blocking": not bool(effective_pages),
            },
            {
                "key": "preview_pages",
                "label": "预览页面",
                "status": "warn" if preview_pages else "pass",
                "message": f"预览页面 {len(preview_pages)} 个",
                "blocking": False,
            },
            {
                "key": "hidden_pages",
                "label": "下线页面",
                "status": "warn" if hidden_pages else "pass",
                "message": f"未发布/已下线页面 {len(hidden_pages)} 个",
                "blocking": False,
            },
            {
                "key": "active_release",
                "label": "当前发布版",
                "status": "pass" if active_snapshot_id > 0 else "warn",
                "message": f"active snapshot: {active_snapshot_id or 'none'}",
                "blocking": False,
            },
        ]
        checks.append(self._target_integrity_check(effective_pages))
        checks.append(self._source_target_check(effective_pages))
        return checks

    def _page_ref(self, page: dict[str, Any]) -> dict[str, Any]:
        return {
            "page_key": _text(page.get("page_key")),
            "label": _text(page.get("label")) or _text(page.get("page_key")),
            "visible_menu_path": _text(page.get("visible_menu_path")),
            "route": _text(page.get("route")),
            "menu_id": _to_int(page.get("menu_id")),
            "action_id": _to_int(page.get("action_id")),
            "menu_xmlid": _text(page.get("menu_xmlid")),
            "res_model": _text(page.get("res_model")),
        }

    def _issue(self, code: str, page: dict[str, Any], message: str) -> dict[str, Any]:
        return {
            "code": code,
            "blocking": True,
            "message": message,
            **self._page_ref(page),
        }

    def _target_integrity_check(self, pages: list[dict[str, Any]]) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_key = _text(page.get("page_key"))
            route = _text(page.get("route"))
            scene_key = _text(page.get("scene_key"))
            menu_xmlid = _text(page.get("menu_xmlid"))
            menu_id = _to_int(page.get("menu_id"))
            action_id = _to_int(page.get("action_id"))
            res_model = _text(page.get("res_model"))
            if not page_key:
                issues.append(self._issue("PAGE_KEY_MISSING", page, "发布页缺少 page_key"))
            if not (route or scene_key or menu_id or action_id):
                issues.append(self._issue("TARGET_MISSING", page, "发布页缺少可打开目标"))
                continue
            if route.startswith("/a/"):
                if scene_key:
                    issues.append(self._issue("ACTION_MENU_HAS_SCENE_KEY", page, "Odoo action 菜单不能带 scene_key"))
                if not action_id:
                    issues.append(self._issue("ACTION_ID_MISSING", page, "Odoo action 菜单缺少 action_id"))
                if not res_model:
                    issues.append(self._issue("RES_MODEL_MISSING", page, "Odoo action 菜单缺少 res_model"))
                if not menu_xmlid:
                    issues.append(self._issue("MENU_XMLID_MISSING", page, "Odoo action 菜单缺少 menu_xmlid"))
            elif route.startswith("/s/"):
                if not scene_key:
                    issues.append(self._issue("SCENE_KEY_MISSING", page, "scene 路由缺少 scene_key"))
                elif route.strip("/") != f"s/{scene_key}".strip("/"):
                    issues.append(self._issue("SCENE_ROUTE_MISMATCH", page, "scene_key 与 /s 路由不一致"))
            elif route and not (menu_id or action_id or scene_key):
                issues.append(self._issue("UNKNOWN_ROUTE_TARGET", page, "发布页路由缺少可校验目标引用"))
        status = "fail" if issues else "pass"
        return {
            "key": "page_target_integrity",
            "label": "页面目标完整性",
            "status": status,
            "message": f"目标结构问题 {len(issues)} 个",
            "blocking": bool(issues),
            "issue_count": len(issues),
            "issues": issues[:20],
        }

    def _source_db_name(self) -> str:
        try:
            configured = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.release_operator.catalog_source_db",
                "",
            )
        except Exception:
            configured = ""
        return _text(configured) or "sc_demo"

    def _source_target_check(self, pages: list[dict[str, Any]]) -> dict[str, Any]:
        action_pages = [
            page
            for page in pages
            if isinstance(page, dict) and (_text(page.get("route")).startswith("/a/") or _to_int(page.get("action_id")) or _to_int(page.get("menu_id")))
        ]
        if not action_pages:
            return {
                "key": "source_action_targets",
                "label": "源库动作目标",
                "status": "pass",
                "message": "无需校验 Odoo action 目标",
                "blocking": False,
                "issue_count": 0,
                "issues": [],
            }
        source_db = self._source_db_name()
        current_db = _text(getattr(getattr(self.env, "cr", None), "dbname", ""))
        try:
            if source_db == current_db:
                issues = self._source_target_issues(self.env, action_pages)
            else:
                registry = Registry(source_db)
                with registry.cursor() as cr:
                    source_env = api.Environment(cr, SUPERUSER_ID, {})
                    issues = self._source_target_issues(source_env, action_pages)
        except Exception as exc:
            return {
                "key": "source_action_targets",
                "label": "源库动作目标",
                "status": "warn",
                "message": f"源库 {source_db} 不可用，已跳过真实目标校验: {_text(exc)}",
                "blocking": False,
                "source_db": source_db,
                "issue_count": 0,
                "issues": [],
            }
        return {
            "key": "source_action_targets",
            "label": "源库动作目标",
            "status": "fail" if issues else "pass",
            "message": f"源库动作目标问题 {len(issues)} 个",
            "blocking": bool(issues),
            "source_db": source_db,
            "issue_count": len(issues),
            "issues": issues[:20],
        }

    def _source_target_issues(self, source_env, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for page in pages:
            menu_id = _to_int(page.get("menu_id"))
            action_id = _to_int(page.get("action_id"))
            res_model = _text(page.get("res_model"))
            if menu_id:
                menu = source_env["ir.ui.menu"].sudo().browse(menu_id)
                if not menu.exists():
                    issues.append(self._issue("SOURCE_MENU_NOT_FOUND", page, "源库菜单不存在"))
                    continue
                menu_action_id = 0
                try:
                    menu_action_id = _to_int(menu.action.id)
                except Exception:
                    menu_action_id = 0
                if action_id and menu_action_id and action_id != menu_action_id:
                    issues.append(self._issue("SOURCE_MENU_ACTION_MISMATCH", page, "源库菜单 action 与发布页不一致"))
            if action_id:
                action = source_env["ir.actions.actions"].sudo().browse(action_id)
                if not action.exists():
                    issues.append(self._issue("SOURCE_ACTION_NOT_FOUND", page, "源库 action 不存在"))
                    continue
            if res_model and res_model not in getattr(source_env.registry, "models", {}):
                issues.append(self._issue("SOURCE_MODEL_NOT_FOUND", page, "源库模型不存在"))
        return issues

    def _draft_delta(self, *, current_active, draft_pages: list[dict[str, Any]]) -> dict[str, Any]:
        active_meta = current_active.meta_json if current_active and isinstance(current_active.meta_json, dict) else {}
        active_draft = _dict(active_meta.get("release_draft"))
        active_pages = _list(active_draft.get("pages"))
        active_by_key = {_text(row.get("page_key")): row for row in active_pages if isinstance(row, dict) and _text(row.get("page_key"))}
        draft_by_key = {_text(row.get("page_key")): row for row in draft_pages if _text(row.get("page_key"))}
        added = [key for key in draft_by_key if key not in active_by_key]
        removed = [key for key in active_by_key if key not in draft_by_key]
        changed: list[str] = []
        for key, row in draft_by_key.items():
            old = active_by_key.get(key)
            if not old:
                continue
            for field in ("enabled", "release_state", "access_level", "route"):
                if row.get(field) != old.get(field):
                    changed.append(key)
                    break
        return {
            "base_snapshot_id": int(current_active.id) if current_active else 0,
            "added_page_count": len(added),
            "removed_page_count": len(removed),
            "changed_page_count": len(changed),
            "sample_added_pages": added[:5],
            "sample_removed_pages": removed[:5],
            "sample_changed_pages": changed[:5],
        }

    def build_policy_draft_contract(self, *, product_key: str) -> dict[str, Any]:
        policy_rec = None
        if self._model_registered("sc.product.policy"):
            policy_rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", _text(product_key)), ("active", "=", True)], limit=1)
        policy = policy_rec.to_runtime_dict() if policy_rec else {}
        pages = self._draft_pages_from_policy(policy)
        effective_pages = [row for row in pages if bool(row.get("enabled")) and _text(row.get("release_state")) in {"released", "preview"}]
        active = None
        model = self._model()
        if model is not None:
            active = model.search(
                [
                    ("product_key", "=", _text(product_key)),
                    ("state", "=", "released"),
                    ("is_active", "=", True),
                    ("active", "=", True),
                ],
                order="released_at desc, activated_at desc, id desc",
                limit=1,
            )
        preflight = self._preflight_checks_from_pages(pages=pages, active_snapshot_id=int(active.id) if active else 0)
        return {
            "policy_id": int(policy_rec.id) if policy_rec else 0,
            "policy_write_date": policy_rec.write_date.isoformat() if policy_rec and policy_rec.write_date else "",
            "fingerprint": self._draft_fingerprint(policy=policy, pages=pages),
            "page_count": len(effective_pages),
            "total_page_count": len(pages),
            "preview_page_count": len([row for row in effective_pages if _text(row.get("release_state")) == "preview"]),
            "hidden_page_count": len([row for row in pages if not bool(row.get("enabled")) or _text(row.get("release_state")) in {"hidden", "retired"}]),
            "pages": pages,
            "preflight_checks": preflight,
            "blocking_issue_count": len([item for item in preflight if bool(item.get("blocking"))]),
            "diff_from_active": self._draft_delta(current_active=active, draft_pages=pages),
        }

    def assert_candidate_matches_current_draft(self, snapshot) -> None:
        meta = snapshot.meta_json if snapshot and isinstance(snapshot.meta_json, dict) else {}
        frozen_draft = _dict(meta.get("release_draft"))
        frozen_fingerprint = _text(frozen_draft.get("fingerprint"))
        current = self.build_policy_draft_contract(product_key=_text(snapshot.product_key))
        current_fingerprint = _text(current.get("fingerprint"))
        if not frozen_fingerprint or frozen_fingerprint != current_fingerprint:
            raise ValueError("CANDIDATE_DRAFT_OUTDATED")
        if int(frozen_draft.get("blocking_issue_count") or 0) > 0:
            raise ValueError("CANDIDATE_PREFLIGHT_BLOCKED")

    def _lineage_meta(self, rec) -> dict[str, Any]:
        runtime = rec.snapshot_json if isinstance(rec.snapshot_json, dict) else {}
        runtime_meta = _dict(runtime.get("runtime_meta"))
        return {
            "snapshot_id": int(rec.id),
            "product_key": _text(rec.product_key),
            "base_product_key": _text(rec.base_product_key),
            "edition_key": _text(rec.edition_key),
            "version": _text(rec.version) or "v1",
            "channel": _text(rec.channel) or "stable",
            "state": _text(rec.state) or "candidate",
            "is_active": bool(rec.is_active),
            "released_at": rec.released_at.isoformat() if rec.released_at else "",
            "approved_at": rec.approved_at.isoformat() if rec.approved_at else "",
            "frozen_at": rec.frozen_at.isoformat() if rec.frozen_at else "",
            "state_reason": _text(rec.state_reason),
            "promotion_note": _text(rec.promotion_note),
            "promoted_from_snapshot_id": int(rec.promoted_from_snapshot_id.id) if rec.promoted_from_snapshot_id else 0,
            "rollback_target_snapshot_id": int(rec.rollback_target_snapshot_id.id) if rec.rollback_target_snapshot_id else 0,
            "replaced_by_snapshot_id": int(rec.replaced_by_snapshot_id.id) if rec.replaced_by_snapshot_id else 0,
            "effective_runtime": _dict(runtime_meta.get("effective")),
        }

    def freeze_release_surface(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        version: str = "v1",
        role_code: str = "",
        note: str = "",
        replace_active: bool = True,
    ) -> dict[str, Any]:
        payload = self.build_freeze_surface(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
            role_code=role_code,
        )
        identity = _dict(payload.get("identity"))
        resolved_product_key = _text(identity.get("product_key"))
        resolved_base_product_key = _text(identity.get("base_product_key"))
        resolved_edition_key = _text(identity.get("edition_key")) or "standard"
        resolved_version = _text(version) or _text(identity.get("version")) or "v1"
        channel = _text(identity.get("channel")) or ("preview" if resolved_edition_key == "preview" else "stable")
        label = _text(identity.get("label")) or resolved_product_key
        now = self.now()
        model = self._model()
        if model is None:
            raise ValueError("SNAPSHOT_MODEL_NOT_AVAILABLE")
        current_active = model.search(
            [("product_key", "=", resolved_product_key), ("is_active", "=", True), ("active", "=", True)],
            order="activated_at desc, id desc",
            limit=1,
        )
        target = model.search(
            [("product_key", "=", resolved_product_key), ("version", "=", resolved_version), ("active", "=", True)],
            limit=1,
        )
        rollback_target_id = int(current_active.id) if current_active and (not target or int(current_active.id) != int(target.id)) else False
        policy_rec = None
        if self._model_registered("sc.product.policy"):
            policy_rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", resolved_product_key), ("active", "=", True)], limit=1)
        draft_contract = self.build_policy_draft_contract(product_key=resolved_product_key)
        if int(draft_contract.get("blocking_issue_count") or 0) > 0:
            raise ValueError("RELEASE_PREFLIGHT_BLOCKED")
        payload["release_draft"] = {
            "fingerprint": _text(draft_contract.get("fingerprint")),
            "page_count": int(draft_contract.get("page_count") or 0),
            "total_page_count": int(draft_contract.get("total_page_count") or 0),
            "preview_page_count": int(draft_contract.get("preview_page_count") or 0),
            "hidden_page_count": int(draft_contract.get("hidden_page_count") or 0),
        }
        values = {
            "state": "candidate",
            "product_key": resolved_product_key,
            "base_product_key": resolved_base_product_key,
            "edition_key": resolved_edition_key,
            "label": label,
            "version": resolved_version,
            "channel": channel,
            "frozen_at": now,
            "approved_at": False,
            "released_at": False,
            "activated_at": False,
            "superseded_at": False,
            "source_policy_id": int(policy_rec.id) if policy_rec else False,
            "promoted_from_snapshot_id": False,
            "rollback_target_snapshot_id": rollback_target_id or False,
            "replaced_by_snapshot_id": False,
            "snapshot_json": payload,
            "meta_json": {
                "freeze_context": {
                    "requested_product_key": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("product_key")),
                    "requested_edition_key": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("edition_key")),
                    "effective_product_key": _text(_dict(_dict(payload.get("runtime_meta")).get("effective")).get("product_key")),
                    "effective_edition_key": _text(_dict(_dict(payload.get("runtime_meta")).get("effective")).get("edition_key")),
                    "role_code": _text(_dict(_dict(payload.get("runtime_meta")).get("requested")).get("role_code")),
                },
                "release_draft": draft_contract,
                "release_diff": _dict(draft_contract.get("diff_from_active")),
                "preflight_checks": _list(draft_contract.get("preflight_checks")),
                "rollback_basis_available": bool(rollback_target_id),
            },
            "state_reason": "frozen_release_surface_candidate",
            "promotion_note": "",
            "note": _text(note) or "frozen from edition delivery surface",
            "is_active": False,
        }
        if target:
            target.write(values)
            rec = target
        else:
            rec = model.create(values)
        self.promotion_service.promote_to_approved(
            int(rec.id),
            state_reason="freeze_surface_approved",
            promotion_note="approved by freeze service",
        )
        if replace_active:
            return self.promotion_service.promote_to_released(
                int(rec.id),
                replace_active=True,
                state_reason="freeze_surface_released",
                promotion_note="released by freeze service",
            )
        return rec.to_runtime_dict()

    def list_snapshots(self, *, product_key: str | None = None) -> list[dict[str, Any]]:
        model = self._model()
        if model is None:
            return []
        domain = [("active", "=", True)]
        if _text(product_key):
            domain.append(("product_key", "=", _text(product_key)))
        return [row.to_runtime_dict() for row in model.search(domain, order="product_key asc, version desc, id desc")]

    def resolve_active_snapshot(self, *, product_key: str) -> dict[str, Any]:
        model = self._model()
        if model is None:
            return {}
        rec = model.search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="activated_at desc, id desc",
            limit=1,
        )
        return rec.to_runtime_dict() if rec else {}

    def resolve_active_snapshot_lineage(self, *, product_key: str) -> dict[str, Any]:
        model = self._model()
        if model is None:
            return {}
        rec = model.search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        return self._lineage_meta(rec) if rec else {}

    def rollback_to_snapshot(self, *, product_key: str, target_snapshot_id: int | None = None, note: str = "") -> dict[str, Any]:
        model = self._model()
        if model is None:
            raise ValueError("SNAPSHOT_MODEL_NOT_AVAILABLE")
        current = model.search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        if not current:
            raise ValueError("ACTIVE_RELEASE_SNAPSHOT_NOT_FOUND")
        target = model.browse(int(target_snapshot_id)) if target_snapshot_id else current.rollback_target_snapshot_id
        if not target or not target.exists():
            raise ValueError("ROLLBACK_TARGET_NOT_FOUND")
        if _text(target.product_key) != _text(product_key):
            raise ValueError("ROLLBACK_TARGET_PRODUCT_MISMATCH")
        if _text(target.state) not in {"approved", "released", "superseded"}:
            raise ValueError("ROLLBACK_TARGET_NOT_RELEASEABLE")
        now = self.now()
        current.write(
            {
                "state": "superseded",
                "is_active": False,
                "superseded_at": now,
                "state_reason": "rolled_back_to_previous_released_snapshot",
                "promotion_note": _text(note) or "rolled back to previous release snapshot",
            }
        )
        target.write(
            {
                "state": "released",
                "is_active": True,
                "released_at": target.released_at or now,
                "activated_at": now,
                "superseded_at": False,
                "state_reason": "rollback_reactivated_released_snapshot",
                "promotion_note": _text(note) or "rollback reactivated previous release snapshot",
                "replaced_by_snapshot_id": False,
            }
        )
        return target.to_runtime_dict()
