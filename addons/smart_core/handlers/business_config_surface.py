# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from typing import Any

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..utils.backend_contract_boundaries import BUSINESS_CONFIG_INTENTS, MENU_CONFIG_INTENTS, MENU_CONFIG_POLICY_MODEL
from ..utils.extension_hooks import call_extension_hook_first


BUSINESS_CONFIG_GROUP = "smart_core.group_smart_core_business_config_admin"
PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
ANALYSIS_VIEW_TYPES = ("pivot", "graph", "calendar", "dashboard")
DELIVERY_CAPABILITIES = (
    ("form_field_structure", "表单配置", "form"),
    ("list_search_configuration", "列表与搜索配置", "list_search"),
    ("menu_orchestration", "菜单配置", "menu"),
    ("approval_policy_configuration", "审批配置", "approval"),
    ("version_snapshot_rollback", "版本与快照", "version"),
    ("capability_boundary_and_coverage", "覆盖检查", "coverage"),
)


def _to_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _ref_id(value: Any) -> int:
    return _to_int(getattr(value, "id", value))


def _hash_payload(payload: Any) -> str:
    value = payload if isinstance(payload, dict) else {}
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot_contract_key(row: dict) -> str:
    return "|".join([
        str(row.get("model") or ""),
        str(row.get("view_type") or ""),
        str(row.get("action_id") or 0),
        str(row.get("view_id") or 0),
        str(row.get("role_key") or ""),
        str(row.get("name") or ""),
    ])


class _BusinessConfigSurfaceBase(BaseIntentHandler):
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        MENU_CONFIG_POLICY_MODEL,
        "ui.form.field.policy",
        "sc.user.view.preference",
    )
    NO_BUSINESS_FACT_AUTHORITY = True

    def _ensure_access(self):
        user = self.env.user
        if getattr(self.env, "context", {}).get("business_config_system_remediation"):
            return
        if int(getattr(user, "id", 0) or 0) == 1:
            return
        if user.has_group(BUSINESS_CONFIG_GROUP) or user.has_group(PLATFORM_ADMIN_GROUP):
            return
        raise AccessError("只有业务配置管理员或平台管理员可以查看业务配置工作台。")

    def _contract_count(
        self,
        *,
        model: str = "",
        view_type: str = "",
        action_id: int = 0,
        view_id: int = 0,
        role_key: str = "",
    ) -> int:
        if "ui.business.config.contract" not in self.env:
            return 0
        domain = [
            ("active", "=", True),
            ("company_id", "in", [False, self.env.company.id]),
        ]
        if model:
            domain.append(("model", "=", model))
        if view_type:
            domain.append(("view_type", "in", [False, view_type]))
        if action_id:
            domain.append(("action_id", "in", [False, action_id]))
        if view_id:
            domain.append(("view_id", "in", [False, view_id]))
        if role_key:
            domain.append(("role_key", "in", [False, role_key]))
        Contract = self.env["ui.business.config.contract"].sudo()
        try:
            return int(Contract.search_count(domain))
        except Exception:
            return len(Contract.search(domain, limit=100))

    def _published_contract_count(
        self,
        *,
        model: str = "",
        view_type: str = "",
        action_id: int = 0,
        view_id: int = 0,
        role_key: str = "",
    ) -> int:
        if "ui.business.config.contract" not in self.env:
            return 0
        domain = [
            ("active", "=", True),
            ("status", "=", "published"),
            ("company_id", "in", [False, self.env.company.id]),
        ]
        if model:
            domain.append(("model", "=", model))
        if view_type:
            domain.append(("view_type", "in", [False, view_type]))
        if action_id:
            domain.append(("action_id", "in", [False, action_id]))
        if view_id:
            domain.append(("view_id", "in", [False, view_id]))
        if role_key:
            domain.append(("role_key", "in", [False, role_key]))
        Contract = self.env["ui.business.config.contract"].sudo()
        try:
            return int(Contract.search_count(domain))
        except Exception:
            return len(Contract.search(domain, limit=100))

    def _runtime_contract_count(
        self,
        *,
        model: str = "",
        view_type: str = "",
        action_id: int = 0,
        view_id: int = 0,
        role_key: str = "",
    ) -> int:
        if not model or "ui.business.config.contract" not in self.env:
            return 0
        Contract = self.env["ui.business.config.contract"].sudo()
        if hasattr(Contract, "_effective_view_orchestration_contracts"):
            try:
                return len(Contract._effective_view_orchestration_contracts(
                    model,
                    view_type=view_type,
                    action_id=action_id or None,
                    view_id=view_id or None,
                    role_key=role_key or None,
                ))
            except Exception:
                pass
        domain = [
            ("active", "=", True),
            ("status", "=", "published"),
            ("model", "=", model),
            ("company_id", "=", self.env.company.id),
        ]
        if view_type:
            domain.append(("view_type", "in", [False, view_type]))
        if action_id:
            domain.append(("action_id", "in", [False, action_id]))
        if view_id:
            domain.append(("view_id", "in", [False, view_id]))
        if role_key:
            domain.append(("role_key", "in", [False, role_key]))
        try:
            return int(Contract.search_count(domain))
        except Exception:
            return len(Contract.search(domain, limit=100))

    def _action_view_types(self, action_id: int) -> set[str]:
        if not action_id or "ir.actions.act_window" not in self.env:
            return set()
        try:
            action = self.env["ir.actions.act_window"].sudo().browse(action_id).exists()
        except Exception:
            action = None
        view_mode = _to_text(getattr(action, "view_mode", "")) if action else ""
        return {item.strip() for item in view_mode.split(",") if item.strip()}

    def _xmlid_record_id(self, xmlid: str) -> int:
        xmlid = _to_text(xmlid)
        if not xmlid or "." not in xmlid or not hasattr(self.env, "ref"):
            return 0
        try:
            record = self.env.ref(xmlid, raise_if_not_found=False)
        except Exception:
            record = None
        return _ref_id(record)

    def _approval_policy_section(self, model: str) -> dict:
        refs = call_extension_hook_first(self.env, "smart_core_business_config_approval_policy_refs", self.env) or {}
        refs = refs if isinstance(refs, dict) else {}
        if not refs:
            addon = "smart_" + "construction_core"
            refs = {
                "action_xmlid": f"{addon}.action_sc_approval_policy",
                "menu_xmlid": f"{addon}.menu_sc_approval_policy",
            }
        action_id = self._xmlid_record_id(_to_text(refs.get("action_xmlid")))
        menu_id = self._xmlid_record_id(_to_text(refs.get("menu_xmlid")))
        count = 0
        if "sc.approval.policy" in self.env:
            domain = [("active", "=", True)]
            if model:
                domain.append(("target_model", "=", model))
            try:
                count = int(self.env["sc.approval.policy"].sudo().search_count(domain))
            except Exception:
                count = 0
        route_query = {}
        if menu_id:
            route_query["menu_id"] = str(menu_id)
        if model:
            route_query["target_model"] = model
            route_query["domain_raw"] = "[('target_model', '=', '%s')]" % model.replace("'", "\\'")
        return {
            "key": "approval",
            "label": "审批规则",
            "contract_count": count,
            "intent": "sc.approval.policy",
            "boundary": "industry_policy_runtime",
            "route": {
                "path": "/a/%s" % action_id if action_id else "",
                "query": route_query,
            },
        }

    def _snapshot_summary(self) -> dict:
        if "ui.business.config.contract" not in self.env:
            return {}
        rows = self.env["ui.business.config.contract"].sudo().search(
            [], order="model, view_type, action_id, view_id, role_key, name, id"
        )
        status_counts = {}
        view_type_counts = {}
        role_scope_count = 0
        action_scope_count = 0
        for rec in rows:
            status = _to_text(getattr(rec, "status", "")) or "unknown"
            view_type = _to_text(getattr(rec, "view_type", "")) or "all"
            status_counts[status] = status_counts.get(status, 0) + 1
            view_type_counts[view_type] = view_type_counts.get(view_type, 0) + 1
            if _to_text(getattr(rec, "role_key", "")):
                role_scope_count += 1
            if _to_int(getattr(getattr(rec, "action_id", None), "id", getattr(rec, "action_id", 0))):
                action_scope_count += 1
        return {
            "database": _to_text(getattr(getattr(self.env, "cr", None), "dbname", "")),
            "contract_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "view_type_counts": dict(sorted(view_type_counts.items())),
            "role_scope_count": role_scope_count,
            "action_scope_count": action_scope_count,
        }

    def _snapshot_contract_row(self, rec) -> dict:
        payload = getattr(rec, "contract_json", {}) or {}
        return {
            "id": _to_int(getattr(rec, "id", 0)),
            "name": _to_text(getattr(rec, "name", "")),
            "model": _to_text(getattr(rec, "model", "")),
            "view_type": _to_text(getattr(rec, "view_type", "")),
            "action_id": _ref_id(getattr(rec, "action_id", 0)),
            "view_id": _ref_id(getattr(rec, "view_id", 0)),
            "role_key": _to_text(getattr(rec, "role_key", "")),
            "status": _to_text(getattr(rec, "status", "")),
            "version_no": _to_int(getattr(rec, "version_no", 0)),
            "payload_hash": _hash_payload(payload),
        }

    def _snapshot_contract_rows(self) -> list[dict]:
        if "ui.business.config.contract" not in self.env:
            return []
        rows = self.env["ui.business.config.contract"].sudo().search(
            [], order="model, view_type, action_id, view_id, role_key, name, id"
        )
        return sorted([self._snapshot_contract_row(rec) for rec in rows], key=_snapshot_contract_key)

    def _snapshot_report(self) -> dict:
        rows = self._snapshot_contract_rows()
        summary = self._snapshot_summary()
        return {
            **summary,
            "contracts": rows,
        }

    def _load_snapshot_payload(self, value: Any) -> dict:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = {}
        if not isinstance(value, dict):
            return {}
        contracts = value.get("contracts")
        if not isinstance(contracts, list):
            return {}
        return value

    def _compare_snapshot(self, previous_snapshot: dict) -> dict:
        current = self._snapshot_report()
        previous_rows = {
            _snapshot_contract_key(row): row
            for row in previous_snapshot.get("contracts", [])
            if isinstance(row, dict)
        }
        current_rows = {
            _snapshot_contract_key(row): row
            for row in current.get("contracts", [])
            if isinstance(row, dict)
        }
        added_keys = sorted(set(current_rows) - set(previous_rows))
        removed_keys = sorted(set(previous_rows) - set(current_rows))
        common_keys = sorted(set(current_rows) & set(previous_rows))
        changed = []
        for key in common_keys:
            previous = previous_rows[key]
            current_row = current_rows[key]
            if (
                previous.get("payload_hash") == current_row.get("payload_hash")
                and previous.get("status") == current_row.get("status")
            ):
                continue
            changed.append({
                "key": key,
                "name": current_row.get("name") or previous.get("name") or "",
                "model": current_row.get("model") or previous.get("model") or "",
                "view_type": current_row.get("view_type") or previous.get("view_type") or "",
                "previous_status": previous.get("status") or "",
                "current_status": current_row.get("status") or "",
                "previous_version_no": _to_int(previous.get("version_no")),
                "current_version_no": _to_int(current_row.get("version_no")),
            })
        return {
            "current_database": current.get("database") or "",
            "baseline_database": _to_text(previous_snapshot.get("database")),
            "current_contract_count": len(current_rows),
            "baseline_contract_count": len(previous_rows),
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "changed_count": len(changed),
            "added": [current_rows[key] for key in added_keys[:30]],
            "removed": [previous_rows[key] for key in removed_keys[:30]],
            "changed": changed[:50],
        }

    def _delivery_readiness(self, sections: list[dict], snapshot_summary: dict) -> dict:
        section_by_key = {str(section.get("key") or ""): section for section in sections}
        items = []
        blocker_count = 0
        ready_count = 0
        for capability_id, label, section_key in DELIVERY_CAPABILITIES:
            section = section_by_key.get(section_key) or {}
            if section_key == "version":
                contract_count = _to_int(snapshot_summary.get("contract_count"))
                boundary = "business_contract_version"
                status = "ready" if contract_count else "pending"
                action = "snapshot_compare"
            elif section_key == "coverage":
                contract_count = _to_int(snapshot_summary.get("action_scope_count"))
                boundary = "coverage_guard"
                status = "ready"
                action = "coverage_scan"
            else:
                contract_count = _to_int(section.get("contract_count"))
                boundary = _to_text(section.get("boundary"))
                status = "ready" if contract_count else "pending"
                action = "configure"
            if status == "ready":
                ready_count += 1
            else:
                blocker_count += 1
            items.append({
                "id": capability_id,
                "label": label,
                "section_key": section_key,
                "status": status,
                "contract_count": contract_count,
                "boundary": boundary,
                "action": action,
            })
        overall_status = "ready" if blocker_count == 0 else "attention"
        return {
            "schema_version": "low_code_delivery_readiness.v1",
            "overall_status": overall_status,
            "ready_count": ready_count,
            "total_count": len(items),
            "blocker_count": blocker_count,
            "items": items,
        }


class BusinessConfigSurfaceGetHandler(_BusinessConfigSurfaceBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["surface_get"]
    DESCRIPTION = "读取当前页面可配置能力摘要"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_surface_projection"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        model = _to_text(params.get("model"))
        action_id = _to_int(params.get("action_id") or params.get("actionId"))
        view_id = _to_int(params.get("view_id") or params.get("viewId"))
        role_key = _to_text(params.get("role_key") or params.get("roleKey"))
        action_view_types = self._action_view_types(action_id)
        analysis_contract_count = sum(
            self._contract_count(
                model=model,
                view_type=view_type,
                action_id=action_id,
                view_id=view_id,
                role_key=role_key,
            )
            for view_type in ANALYSIS_VIEW_TYPES
        ) if model else 0
        sections = [
            {
                "key": "form",
                "label": "表单配置",
                "contract_count": self._contract_count(
                    model=model,
                    view_type="form",
                    action_id=action_id,
                    view_id=view_id,
                    role_key=role_key,
                ) if model else 0,
                "intent": BUSINESS_CONFIG_INTENTS["form_audit"],
                "boundary": "business_contract",
            },
            {
                "key": "list_search",
                "label": "列表/搜索配置",
                "contract_count": (
                    self._contract_count(
                        model=model,
                        view_type="tree",
                        action_id=action_id,
                        view_id=view_id,
                        role_key=role_key,
                    )
                    + self._contract_count(
                        model=model,
                        view_type="search",
                        action_id=action_id,
                        view_id=view_id,
                        role_key=role_key,
                    )
                    if model else 0
                ),
                "intent": BUSINESS_CONFIG_INTENTS["list_search_audit"],
                "boundary": "business_contract_not_user_preference",
            },
        ]
        if analysis_contract_count or action_view_types.intersection(ANALYSIS_VIEW_TYPES):
            sections.append({
                "key": "analysis",
                "label": "分析视图配置",
                "contract_count": analysis_contract_count,
                "intent": BUSINESS_CONFIG_INTENTS["contract_versions"],
                "boundary": "business_contract",
            })
        sections.append({
            "key": "menu",
            "label": "菜单配置",
            "contract_count": self._contract_count(model="ir.ui.menu", role_key=role_key),
            "intent": MENU_CONFIG_INTENTS["audit"],
            "boundary": "business_contract_with_policy_runtime",
        })
        sections.append(self._approval_policy_section(model))
        snapshot_summary = self._snapshot_summary()
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": action_id,
                "view_id": view_id,
                "role_key": role_key,
                "sections": sections,
                "snapshot_summary": snapshot_summary,
                "delivery_readiness": self._delivery_readiness(sections, snapshot_summary),
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class BusinessConfigSnapshotSummaryHandler(_BusinessConfigSurfaceBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["snapshot_summary"]
    DESCRIPTION = "读取业务配置快照摘要"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_snapshot_summary"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": ["ui.business.config.contract"],
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        return {
            "ok": True,
            "data": self._snapshot_summary(),
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class BusinessConfigSnapshotExportHandler(_BusinessConfigSurfaceBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["snapshot_export"]
    DESCRIPTION = "导出业务配置快照"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_snapshot_export"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": ["ui.business.config.contract"],
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        return {
            "ok": True,
            "data": self._snapshot_report(),
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class BusinessConfigSnapshotCompareHandler(_BusinessConfigSurfaceBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["snapshot_compare"]
    DESCRIPTION = "对比业务配置快照"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_snapshot_compare"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": ["ui.business.config.contract"],
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        snapshot = self._load_snapshot_payload(params.get("snapshot") or params.get("snapshot_json") or params.get("snapshotJson"))
        if not snapshot:
            return self._err(400, "snapshot 必须是 make verify.business_config.snapshot 导出的 JSON 对象", "USER_ERROR")
        return {
            "ok": True,
            "data": self._compare_snapshot(snapshot),
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class BusinessConfigCoverageScanHandler(_BusinessConfigSurfaceBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["coverage_scan"]
    DESCRIPTION = "扫描 action 维度的业务配置覆盖情况"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_coverage_scan"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _root_menu_id(self, root_menu_xmlid: str) -> int:
        xmlid = _to_text(root_menu_xmlid)
        if not xmlid or "." not in xmlid:
            return 0
        try:
            record = self.env.ref(xmlid, raise_if_not_found=False)
        except Exception:
            record = None
        if record is not None and _to_text(getattr(record, "_name", "")) == "ir.ui.menu":
            return _to_int(getattr(record, "id", 0))
        return 0

    def _is_under_root(self, menu, root_menu_id: int) -> bool:
        if not root_menu_id:
            return True
        current = menu
        seen: set[int] = set()
        while current:
            current_id = _to_int(getattr(current, "id", 0))
            if not current_id or current_id in seen:
                return False
            if current_id == root_menu_id:
                return True
            seen.add(current_id)
            current = getattr(current, "parent_id", None)
        return False

    def _menu_action_ids(self, *, root_menu_xmlid: str = "", include_all_root_menu_actions: bool = False) -> set[int]:
        if "ir.ui.menu" not in self.env:
            return set()
        Menu = self.env["ir.ui.menu"]
        root_menu_id = self._root_menu_id(root_menu_xmlid)
        if include_all_root_menu_actions:
            SearchMenu = Menu.sudo()
            try:
                menus = SearchMenu.search([], limit=10000)
            except TypeError:
                menus = SearchMenu.search([])
        elif hasattr(Menu, "_visible_menu_ids"):
            try:
                visible_ids = list(Menu._visible_menu_ids(debug=False))
            except TypeError:
                visible_ids = list(Menu._visible_menu_ids())
            menus = Menu.browse(visible_ids).exists()
        else:
            try:
                menus = Menu.search([("action", "like", "ir.actions.act_window,")], limit=10000)
            except TypeError:
                menus = Menu.search([("action", "like", "ir.actions.act_window,")])
        action_ids: set[int] = set()
        for menu in menus:
            if not self._is_under_root(menu, root_menu_id):
                continue
            action = getattr(menu, "action", None)
            if _to_text(getattr(action, "_name", "")) == "ir.actions.act_window":
                action_id = _to_int(getattr(action, "id", 0))
                if action_id:
                    action_ids.add(action_id)
                continue
            raw = _to_text(action)
            if not raw.startswith("ir.actions.act_window,"):
                continue
            action_id = _to_int(raw.split(",", 1)[1])
            if action_id:
                action_ids.add(action_id)
        return action_ids

    def _delivery_navigation_action_ids(self, *, product_key: str = "", edition_key: str = "", base_product_key: str = "") -> set[int]:
        from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine

        try:
            payload = DeliveryEngine(self.env).build(
                data={},
                product_key=_to_text(product_key) or None,
                edition_key=_to_text(edition_key) or None,
                base_product_key=_to_text(base_product_key) or None,
                native_nav=[],
            )
        except Exception:
            return set()
        nav = payload.get("nav") if isinstance(payload, dict) and isinstance(payload.get("nav"), list) else []
        action_ids: set[int] = set()

        def collect(node):
            if not isinstance(node, dict):
                return
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            entry_target = meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {}
            refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
            action_id = _to_int(meta.get("action_id")) or _to_int(refs.get("action_id")) or _to_int(node.get("action_id"))
            if action_id:
                action_ids.add(action_id)
            for child in node.get("children") if isinstance(node.get("children"), list) else []:
                collect(child)

        for node in nav:
            collect(node)
        return action_ids

    def _action_rows(
        self,
        *,
        limit: int,
        model: str = "",
        include_unreachable_actions: bool = False,
        include_all_root_menu_actions: bool = False,
        root_menu_xmlid: str = "",
        use_product_navigation_actions: bool = False,
        product_key: str = "",
        edition_key: str = "",
        base_product_key: str = "",
    ):
        if "ir.actions.act_window" not in self.env:
            return []
        Action = self.env["ir.actions.act_window"].sudo()
        domain = [("res_model", "!=", False)]
        if not include_unreachable_actions:
            if use_product_navigation_actions and not include_all_root_menu_actions:
                menu_action_ids = sorted(self._delivery_navigation_action_ids(
                    product_key=product_key,
                    edition_key=edition_key,
                    base_product_key=base_product_key,
                ))
                if not menu_action_ids:
                    menu_action_ids = sorted(self._menu_action_ids(
                        root_menu_xmlid=root_menu_xmlid,
                        include_all_root_menu_actions=include_all_root_menu_actions,
                    ))
            else:
                menu_action_ids = sorted(self._menu_action_ids(
                    root_menu_xmlid=root_menu_xmlid,
                    include_all_root_menu_actions=include_all_root_menu_actions,
                ))
            if not menu_action_ids:
                return []
            domain.append(("id", "in", menu_action_ids))
        if model:
            domain.append(("res_model", "=", model))
        try:
            return Action.search(domain, limit=limit, order="name, id")
        except TypeError:
            return Action.search(domain, limit=limit)

    def _action_modes(self, action) -> set[str]:
        raw = _to_text(getattr(action, "view_mode", ""))
        modes = {item.strip() for item in raw.replace("list", "tree").split(",") if item.strip()}
        if not modes:
            modes = {"tree", "form"}
        return modes

    def _target_view_types(self, action) -> list[str]:
        modes = self._action_modes(action)
        targets = []
        if "form" in modes:
            targets.append("form")
        if "tree" in modes:
            targets.append("tree")
        if modes.intersection({"tree", "form", "kanban"}):
            targets.append("search")
        for view_type in ANALYSIS_VIEW_TYPES:
            if view_type in modes:
                targets.append(view_type)
        return targets

    def _menu_ids_for_action(self, action_id: int) -> list[int]:
        if not action_id or "ir.ui.menu" not in self.env:
            return []
        Menu = self.env["ir.ui.menu"].sudo()
        domain = [("action", "=", "ir.actions.act_window,%s" % int(action_id))]
        try:
            menus = Menu.search(domain, limit=100)
        except Exception:
            menus = []
        menu_ids = []
        for menu in menus:
            action = getattr(menu, "action", None)
            action_ref = _to_text(action)
            action_model = _to_text(getattr(action, "_name", ""))
            action_record_id = _to_int(getattr(action, "id", 0))
            if action_model == "ir.actions.act_window" and action_record_id != action_id:
                continue
            if action_model != "ir.actions.act_window" and action_ref and action_ref != "ir.actions.act_window,%s" % int(action_id):
                continue
            menu_id = _to_int(getattr(menu, "id", 0))
            if menu_id and menu_id not in menu_ids:
                menu_ids.append(menu_id)
        return menu_ids

    def _menu_count_for_action(self, action_id: int) -> int:
        menu_ids = self._menu_ids_for_action(action_id)
        if menu_ids:
            return len(menu_ids)
        if not action_id or "ir.ui.menu" not in self.env:
            return 0
        Menu = self.env["ir.ui.menu"].sudo()
        domain = [("action", "=", "ir.actions.act_window,%s" % int(action_id))]
        try:
            return int(Menu.search_count(domain))
        except Exception:
            return len(Menu.search(domain, limit=100))

    def _runtime_route_for_action(self, action_id: int, menu_ids: list[int]) -> dict:
        if not action_id:
            return {}
        query = {"action_id": str(int(action_id))}
        if menu_ids:
            query["menu_id"] = str(int(menu_ids[0]))
        return {
            "path": "/a/%s" % int(action_id),
            "query": query,
        }

    def _user_preference_count(self, *, model: str, action_id: int) -> int:
        if "sc.user.view.preference" not in self.env:
            return 0
        Preference = self.env["sc.user.view.preference"].sudo()
        domain = [
            ("preference_key", "=", "list_columns"),
            ("view_type", "in", ["list", "tree"]),
        ]
        if model:
            domain.append(("model_name", "=", model))
        if action_id:
            domain.append(("action_id", "=", action_id))
        try:
            return int(Preference.search_count(domain))
        except Exception:
            return len(Preference.search(domain, limit=100))

    def _action_item(self, action, role_key: str, view_id: int = 0) -> dict:
        model = _to_text(getattr(action, "res_model", ""))
        action_id = int(getattr(action, "id", 0) or 0)
        targets = self._target_view_types(action)
        coverage = {}
        published_coverage = {}
        runtime_coverage = {}
        runtime_evidence = {}
        runtime_gap_reasons = {}
        missing = []
        runtime_missing = []
        for view_type in targets:
            count = self._contract_count(model=model, view_type=view_type, action_id=action_id, view_id=view_id, role_key=role_key)
            published_count = self._published_contract_count(model=model, view_type=view_type, action_id=action_id, view_id=view_id, role_key=role_key)
            runtime_count = self._runtime_contract_count(model=model, view_type=view_type, action_id=action_id, view_id=view_id, role_key=role_key)
            coverage[view_type] = count
            published_coverage[view_type] = published_count
            runtime_coverage[view_type] = runtime_count
            runtime_evidence[view_type] = {
                "source": "ui.business.config.contract._effective_view_orchestration_contracts",
                "configured_count": count,
                "published_count": published_count,
                "runtime_count": runtime_count,
            }
            if count <= 0:
                missing.append(view_type)
            if runtime_count <= 0:
                runtime_missing.append(view_type)
                if count <= 0:
                    runtime_gap_reasons[view_type] = "missing_contract"
                elif published_count <= 0:
                    runtime_gap_reasons[view_type] = "not_published"
                else:
                    runtime_gap_reasons[view_type] = "not_runtime_applicable"
        menu_ids = self._menu_ids_for_action(action_id)
        menu_count = len(menu_ids) if menu_ids else self._menu_count_for_action(action_id)
        user_preference_count = self._user_preference_count(model=model, action_id=action_id)
        remediation_actions = self._remediation_actions(
            runtime_gap_reasons=runtime_gap_reasons,
            has_menu=menu_count > 0,
            user_preference_count=user_preference_count,
        )
        severity = self._severity(
            runtime_gap_reasons=runtime_gap_reasons,
            has_menu=menu_count > 0,
            user_preference_count=user_preference_count,
        )
        sort_priority = self._sort_priority(severity=severity, remediation_actions=remediation_actions)
        return {
            "action_id": action_id,
            "name": _to_text(getattr(action, "name", "")),
            "model": model,
            "view_id": view_id,
            "view_mode": _to_text(getattr(action, "view_mode", "")),
            "severity": severity,
            "sort_priority": sort_priority,
            "target_view_types": targets,
            "menu_count": menu_count,
            "menu_ids": menu_ids,
            "has_menu": menu_count > 0,
            "runtime_route": self._runtime_route_for_action(action_id, menu_ids),
            "user_preference_count": user_preference_count,
            "user_preference_boundary": "ui_only",
            "coverage": coverage,
            "published_coverage": published_coverage,
            "runtime_coverage": runtime_coverage,
            "runtime_evidence": runtime_evidence,
            "runtime_gap_reasons": runtime_gap_reasons,
            "remediation_actions": remediation_actions,
            "missing_view_types": missing,
            "runtime_missing_view_types": runtime_missing,
            "is_complete": not missing,
            "is_runtime_complete": not runtime_missing,
        }

    def _severity(self, *, runtime_gap_reasons: dict, has_menu: bool, user_preference_count: int) -> str:
        del user_preference_count
        reasons = set(runtime_gap_reasons.values())
        if "missing_contract" in reasons or not has_menu:
            return "error"
        if "not_published" in reasons or "not_runtime_applicable" in reasons:
            return "warning"
        return "ok"

    def _sort_priority(self, *, severity: str, remediation_actions: list[dict]) -> int:
        severity_rank = {
            "error": 10,
            "warning": 20,
            "notice": 30,
            "ok": 90,
        }.get(severity, 80)
        action_priority = min([int((action or {}).get("priority") or 99) for action in remediation_actions] or [99])
        return severity_rank * 100 + action_priority

    def _remediation_actions(self, *, runtime_gap_reasons: dict, has_menu: bool, user_preference_count: int) -> list[dict]:
        actions = []
        reasons = set(runtime_gap_reasons.values())
        if "missing_contract" in reasons:
            actions.append({
                "code": "configure_contract",
                "label": "补配置",
                "target": "business_contract_editor",
                "priority": 10,
            })
        if "not_published" in reasons:
            actions.append({
                "code": "publish_contract",
                "label": "看版本",
                "target": "business_contract_versions",
                "priority": 20,
            })
        if "not_runtime_applicable" in reasons:
            actions.append({
                "code": "fix_scope",
                "label": "查作用域",
                "target": "business_config_scope",
                "priority": 30,
            })
        if not has_menu:
            actions.append({
                "code": "configure_menu",
                "label": "配菜单",
                "target": "menu_config",
                "priority": 40,
            })
        if user_preference_count > 0:
            actions.append({
                "code": "review_user_preference_boundary",
                "label": "查偏好",
                "target": "list_search_audit",
                "priority": 50,
            })
        return actions

    def _remediation_action_counts(self, rows: list[dict]) -> dict:
        counts = {}
        for row in rows:
            for action in row.get("remediation_actions") or []:
                code = _to_text((action or {}).get("code"))
                if code:
                    counts[code] = counts.get(code, 0) + 1
        return counts

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        role_key = _to_text(params.get("role_key") or params.get("roleKey"))
        view_id = _to_int(params.get("view_id") or params.get("viewId"))
        model = _to_text(params.get("model"))
        include_unreachable_actions = bool(params.get("include_unreachable_actions") or params.get("includeUnreachableActions"))
        include_all_root_menu_actions = bool(params.get("include_all_root_menu_actions") or params.get("includeAllRootMenuActions"))
        use_product_navigation_actions = bool(params.get("use_product_navigation_actions") or params.get("useProductNavigationActions"))
        product_key = _to_text(params.get("product_key") or params.get("productKey"))
        edition_key = _to_text(params.get("edition_key") or params.get("editionKey"))
        base_product_key = _to_text(params.get("base_product_key") or params.get("baseProductKey"))
        skip_unavailable_models = bool(params.get("skip_unavailable_models") or params.get("skipUnavailableModels"))
        root_menu_xmlid = _to_text(params.get("root_menu_xmlid") or params.get("rootMenuXmlid"))
        raw_limit = _to_int(params.get("limit")) or 1000
        limit = max(1, min(raw_limit, 2000))
        actions = [
            action for action in self._action_rows(
                limit=limit,
                model=model,
                include_unreachable_actions=include_unreachable_actions,
                include_all_root_menu_actions=include_all_root_menu_actions,
                root_menu_xmlid=root_menu_xmlid,
                use_product_navigation_actions=use_product_navigation_actions,
                product_key=product_key,
                edition_key=edition_key,
                base_product_key=base_product_key,
            )
            if _to_text(getattr(action, "res_model", ""))
            and (
                not skip_unavailable_models
                or _to_text(getattr(action, "res_model", "")) in self.env
            )
        ]
        rows = sorted(
            [self._action_item(action, role_key, view_id=view_id) for action in actions],
            key=lambda row: (int(row.get("sort_priority") or 9999), _to_text(row.get("model")), _to_text(row.get("name"))),
        )
        missing_rows = [row for row in rows if not row["is_complete"]]
        runtime_missing_rows = [row for row in rows if not row["is_runtime_complete"]]
        severity_counts = self._severity_counts(rows)
        summary = {
            "action_count": len(rows),
            "complete_count": len(rows) - len(missing_rows),
            "missing_count": len(missing_rows),
            "runtime_complete_count": len(rows) - len(runtime_missing_rows),
            "runtime_missing_count": len(runtime_missing_rows),
            "missing_form_count": len([row for row in rows if "form" in row["missing_view_types"]]),
            "missing_list_count": len([row for row in rows if "tree" in row["missing_view_types"]]),
            "missing_search_count": len([row for row in rows if "search" in row["missing_view_types"]]),
            "missing_analysis_count": len([
                row for row in rows
                if set(row["missing_view_types"]).intersection(ANALYSIS_VIEW_TYPES)
            ]),
            "runtime_missing_form_count": len([row for row in rows if "form" in row["runtime_missing_view_types"]]),
            "runtime_missing_list_count": len([row for row in rows if "tree" in row["runtime_missing_view_types"]]),
            "runtime_missing_search_count": len([row for row in rows if "search" in row["runtime_missing_view_types"]]),
            "runtime_missing_analysis_count": len([
                row for row in rows
                if set(row["runtime_missing_view_types"]).intersection(ANALYSIS_VIEW_TYPES)
            ]),
            "not_published_gap_count": sum(
                len([reason for reason in row["runtime_gap_reasons"].values() if reason == "not_published"])
                for row in rows
            ),
            "not_runtime_applicable_gap_count": sum(
                len([reason for reason in row["runtime_gap_reasons"].values() if reason == "not_runtime_applicable"])
                for row in rows
            ),
            "no_menu_count": len([row for row in rows if not row["has_menu"]]),
            "user_preference_count": sum(row["user_preference_count"] for row in rows),
            "remediation_action_counts": self._remediation_action_counts(rows),
            "severity_counts": severity_counts,
            "overall_status": self._overall_status(severity_counts),
        }
        return {
            "ok": True,
            "data": {
                "model": model,
                "view_id": view_id,
                "role_key": role_key,
                "limit": limit,
                "include_unreachable_actions": include_unreachable_actions,
                "include_all_root_menu_actions": include_all_root_menu_actions,
                "use_product_navigation_actions": use_product_navigation_actions,
                "product_key": product_key,
                "edition_key": edition_key,
                "base_product_key": base_product_key,
                "skip_unavailable_models": skip_unavailable_models,
                "root_menu_xmlid": root_menu_xmlid,
                "runtime_evidence_source": "ui.business.config.contract._effective_view_orchestration_contracts",
                "summary": summary,
                "items": rows,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }

    def _severity_counts(self, rows: list[dict]) -> dict:
        counts = {"error": 0, "warning": 0, "notice": 0, "ok": 0}
        for row in rows:
            severity = _to_text(row.get("severity")) or "ok"
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _overall_status(self, severity_counts: dict) -> str:
        if int((severity_counts or {}).get("error") or 0) > 0:
            return "blocked"
        if int((severity_counts or {}).get("warning") or 0) > 0:
            return "warning"
        if int((severity_counts or {}).get("notice") or 0) > 0:
            return "notice"
        return "pass"


class BusinessConfigCoverageBootstrapListSearchHandler(BusinessConfigCoverageScanHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["coverage_bootstrap_list_search"]
    DESCRIPTION = "批量从运行态后端视图固化缺失的列表/搜索业务配置"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_coverage_list_search_bootstrap"
    NON_IDEMPOTENT_ALLOWED = "coverage remediation publishes official list/search business contracts"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": [
                "ui.business.config.contract",
                "ui.business.config.contract.version",
                "app.view.config",
                "app.search.config",
                "ir.actions.act_window",
                "ir.ui.menu",
            ],
            "projection_only": False,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
            "personal_preference_boundary": "not_a_source",
        }

    @staticmethod
    def _bootstrap_view_types(row: dict, allowed_view_types: set[str]) -> list[str]:
        runtime_gap_reasons = row.get("runtime_gap_reasons") if isinstance(row.get("runtime_gap_reasons"), dict) else {}
        return [
            view_type for view_type in (row.get("runtime_missing_view_types") or [])
            if view_type in allowed_view_types
            and _to_text(runtime_gap_reasons.get(view_type)) == "missing_contract"
        ]

    def _bootstrap_row(self, row: dict, *, role_key: str, view_id: int = 0) -> dict:
        from .form_field_configuration import BusinessConfigListSearchBootstrapHandler

        view_types = self._bootstrap_view_types(row, {"tree", "search"})
        if not view_types:
            return {"ok": True, "skipped": True, "saved_count": 0}
        result = BusinessConfigListSearchBootstrapHandler(
            env=self.env,
            payload={
                "params": {
                    "model": _to_text(row.get("model")),
                    "action_id": _to_int(row.get("action_id")),
                    **({"view_id": view_id} if view_id else {}),
                    "role_key": role_key,
                    "view_types": view_types,
                    "publish": True,
                }
            },
        ).handle()
        data = result.get("data") if isinstance(result, dict) else {}
        return {
            "ok": bool(isinstance(result, dict) and result.get("ok")),
            "action_id": _to_int(row.get("action_id")),
            "name": _to_text(row.get("name")),
            "model": _to_text(row.get("model")),
            "view_types": view_types,
            "saved_count": int((data or {}).get("saved_count") or 0),
            "error": (result.get("error") if isinstance(result, dict) else None),
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        role_key = _to_text(params.get("role_key") or params.get("roleKey"))
        view_id = _to_int(params.get("view_id") or params.get("viewId"))
        raw_batch_limit = _to_int(params.get("batch_limit") or params.get("batchLimit")) or 100
        batch_limit = max(1, min(raw_batch_limit, 300))
        scan = super().handle()
        rows = (scan.get("data") or {}).get("items") if isinstance(scan, dict) else []
        candidates = [
            row for row in (rows or [])
            if self._bootstrap_view_types(row, {"tree", "search"})
        ][:batch_limit]
        results = []
        saved_count = 0
        failed_count = 0
        skipped_count = 0
        for row in candidates:
            item = self._bootstrap_row(row, role_key=role_key, view_id=view_id)
            results.append(item)
            if item.get("skipped"):
                skipped_count += 1
            elif item.get("ok"):
                saved_count += int(item.get("saved_count") or 0)
            else:
                failed_count += 1
        return {
            "ok": failed_count == 0,
            "data": {
                "model": _to_text((scan.get("data") or {}).get("model")) if isinstance(scan, dict) else "",
                "view_id": view_id,
                "role_key": role_key,
                "limit": _to_int((scan.get("data") or {}).get("limit")) if isinstance(scan, dict) else 0,
                "batch_limit": batch_limit,
                "candidate_count": len(candidates),
                "saved_count": saved_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "results": results,
                "personal_preference_boundary": "not_a_source",
                "source_scan_summary": (scan.get("data") or {}).get("summary") if isinstance(scan, dict) else {},
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class BusinessConfigCoverageBootstrapMissingHandler(BusinessConfigCoverageBootstrapListSearchHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["coverage_bootstrap_missing"]
    DESCRIPTION = "批量从运行态后端视图固化缺失的表单、列表、搜索、分析业务配置"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_business_config_coverage_missing_bootstrap"
    NON_IDEMPOTENT_ALLOWED = "coverage remediation publishes official form/list/search/analysis business contracts"

    @classmethod
    def source_authority_contract(cls) -> dict:
        contract = super().source_authority_contract()
        contract["kind"] = cls.SOURCE_KIND
        contract["runtime_carrier"] = cls.INTENT_TYPE
        return contract

    def _bootstrap_row(self, row: dict, *, role_key: str, view_id: int = 0) -> dict:
        from .form_field_configuration import (
            BusinessConfigAnalysisBootstrapHandler,
            BusinessConfigFormBootstrapHandler,
            BusinessConfigListSearchBootstrapHandler,
        )

        missing = self._bootstrap_view_types(row, {"form", "tree", "search", "pivot", "graph"})
        if not missing:
            return {"ok": True, "skipped": True, "saved_count": 0}
        result_items = []
        saved_count = 0
        failed = False
        action_id = _to_int(row.get("action_id"))
        model = _to_text(row.get("model"))
        if "form" in missing:
            form_result = BusinessConfigFormBootstrapHandler(
                env=self.env,
                payload={
                    "params": {
                        "model": model,
                        "action_id": action_id,
                        **({"view_id": view_id} if view_id else {}),
                        "role_key": role_key,
                        "publish": True,
                    }
                },
            ).handle()
            data = form_result.get("data") if isinstance(form_result, dict) else {}
            ok = bool(isinstance(form_result, dict) and form_result.get("ok"))
            result_items.append({
                "view_type": "form",
                "ok": ok,
                "saved_count": 1 if ok else 0,
                "field_count": int((data or {}).get("field_count") or 0),
                "error": (form_result.get("error") if isinstance(form_result, dict) else None),
            })
            if ok:
                saved_count += 1
            else:
                failed = True
        list_search_types = [view_type for view_type in missing if view_type in {"tree", "search"}]
        if list_search_types:
            list_result = BusinessConfigListSearchBootstrapHandler(
                env=self.env,
                payload={
                    "params": {
                        "model": model,
                        "action_id": action_id,
                        **({"view_id": view_id} if view_id else {}),
                        "role_key": role_key,
                        "view_types": list_search_types,
                        "publish": True,
                    }
                },
            ).handle()
            data = list_result.get("data") if isinstance(list_result, dict) else {}
            ok = bool(isinstance(list_result, dict) and list_result.get("ok"))
            item_saved = int((data or {}).get("saved_count") or 0) if ok else 0
            result_items.append({
                "view_type": ",".join(list_search_types),
                "ok": ok,
                "saved_count": item_saved,
                "error": (list_result.get("error") if isinstance(list_result, dict) else None),
            })
            if ok:
                saved_count += item_saved
            else:
                failed = True
        analysis_types = [view_type for view_type in missing if view_type in {"pivot", "graph"}]
        if analysis_types:
            analysis_result = BusinessConfigAnalysisBootstrapHandler(
                env=self.env,
                payload={
                    "params": {
                        "model": model,
                        "action_id": action_id,
                        **({"view_id": view_id} if view_id else {}),
                        "role_key": role_key,
                        "view_types": analysis_types,
                        "publish": True,
                    }
                },
            ).handle()
            data = analysis_result.get("data") if isinstance(analysis_result, dict) else {}
            ok = bool(isinstance(analysis_result, dict) and analysis_result.get("ok"))
            item_saved = int((data or {}).get("saved_count") or 0) if ok else 0
            result_items.append({
                "view_type": ",".join(analysis_types),
                "ok": ok,
                "saved_count": item_saved,
                "error": (analysis_result.get("error") if isinstance(analysis_result, dict) else None),
            })
            if ok:
                saved_count += item_saved
            else:
                failed = True
        return {
            "ok": not failed,
            "action_id": action_id,
            "name": _to_text(row.get("name")),
            "model": model,
            "view_types": missing,
            "saved_count": saved_count,
            "items": result_items,
            "error": next((item.get("error") for item in result_items if not item.get("ok")), None),
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        role_key = _to_text(params.get("role_key") or params.get("roleKey"))
        view_id = _to_int(params.get("view_id") or params.get("viewId"))
        raw_batch_limit = _to_int(params.get("batch_limit") or params.get("batchLimit")) or 100
        batch_limit = max(1, min(raw_batch_limit, 300))
        scan = BusinessConfigCoverageScanHandler.handle(self)
        rows = (scan.get("data") or {}).get("items") if isinstance(scan, dict) else []
        candidates = [
            row for row in (rows or [])
            if self._bootstrap_view_types(row, {"form", "tree", "search", "pivot", "graph"})
        ][:batch_limit]
        results = []
        saved_count = 0
        failed_count = 0
        skipped_count = 0
        for row in candidates:
            item = self._bootstrap_row(row, role_key=role_key, view_id=view_id)
            results.append(item)
            if item.get("skipped"):
                skipped_count += 1
            elif item.get("ok"):
                saved_count += int(item.get("saved_count") or 0)
            else:
                failed_count += 1
                saved_count += int(item.get("saved_count") or 0)
        return {
            "ok": failed_count == 0,
            "data": {
                "model": _to_text((scan.get("data") or {}).get("model")) if isinstance(scan, dict) else "",
                "view_id": view_id,
                "role_key": role_key,
                "limit": _to_int((scan.get("data") or {}).get("limit")) if isinstance(scan, dict) else 0,
                "batch_limit": batch_limit,
                "candidate_count": len(candidates),
                "saved_count": saved_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "results": results,
                "personal_preference_boundary": "not_a_source",
                "source_scan_summary": (scan.get("data") or {}).get("summary") if isinstance(scan, dict) else {},
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }
