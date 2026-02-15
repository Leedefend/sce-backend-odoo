# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import logging
import time
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Iterable, Dict, List, Tuple

from odoo import api, fields, SUPERUSER_ID

from ..core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag, format_versions
from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks
from odoo.addons.smart_core.utils.reason_codes import (
    REASON_OK,
    REASON_PERMISSION_DENIED,
    failure_meta_for_reason,
)
from odoo.addons.smart_core.utils.contract_governance import (
    apply_contract_governance,
    is_truthy,
    resolve_contract_mode,
)

_logger = logging.getLogger(__name__)

# Contract/API version markers for client compatibility
CONTRACT_VERSION = "v0.1"
API_VERSION = "v1"
SCENE_CHANNELS = {"stable", "beta", "dev"}
ROLE_SURFACE_MAP = {
    "owner": {
        "label": "Owner",
        "landing_scene_candidates": ["projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "label": "Project Manager",
        "landing_scene_candidates": ["projects.ledger", "projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
    },
    "finance": {
        "label": "Finance",
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "label": "Executive",
        "landing_scene_candidates": ["projects.intake", "projects.list", "projects.ledger"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_projection_root",
            "smart_construction_core.menu_sc_project_center",
        ],
    },
}

# ===================== 工具函数（权限 / 指纹 / 导航净化） =====================

def _diagnostics_enabled(env) -> bool:
    env_flag = (os.environ.get("ENV") or "").lower()
    if env_flag in {"dev", "test", "local"}:
        return True
    try:
        return env.user.has_group("base.group_system")
    except Exception:
        return False

def _user_group_xmlids(user) -> set:
    """把用户组转为 xmlid 集合（与菜单过滤口径一致）"""
    ext_map = user.groups_id.sudo().get_external_id()  # {id: 'module.xmlid' or False}
    return {xml for xml in ext_map.values() if xml}

def _to_group_xmlid(env, g) -> str | None:
    """把 group 标识（xmlid 或 int id 或 res.groups 记录）统一转 xmlid"""
    if not g:
        return None
    if isinstance(g, str):
        # 允许直接是 xmlid（module.name）
        return g if "." in g else None
    if isinstance(g, int):
        imd = env["ir.model.data"].sudo().search([("model", "=", "res.groups"), ("res_id", "=", g)], limit=1)
        return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
    if getattr(g, "_name", None) == "res.groups":
        imd = env["ir.model.data"].sudo().search([("model", "=", "res.groups"), ("res_id", "=", g.id)], limit=1)
        return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
    return None

def _normalize_required_groups(env, required: Iterable) -> List[str]:
    """把 handler.REQUIRED_GROUPS 规范成 xmlid 列表（空=对所有登录用户开放）"""
    if not required:
        return []
    out = []
    for r in required:
        xmlid = _to_group_xmlid(env, r)
        if xmlid:
            out.append(xmlid)
    return out

def _has_required_groups(user_xmlids: set, required_xmlids: Iterable[str]) -> bool:
    req = set(required_xmlids or [])
    return (not req) or req.issubset(user_xmlids)

def _fingerprint(obj: dict) -> str:
    """稳定指纹（用于导航/顶层 ETag 计算）"""
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _walk_nav_nodes(nodes):
    for node in nodes or []:
        if isinstance(node, dict):
            yield node
            children = node.get("children")
            if isinstance(children, list):
                for child in _walk_nav_nodes(children):
                    yield child


def _index_nav_by_xmlid(nodes) -> Dict[str, dict]:
    indexed = {}
    for node in _walk_nav_nodes(nodes):
        xmlid = node.get("xmlid") or (node.get("meta") or {}).get("menu_xmlid")
        if xmlid and xmlid not in indexed:
            indexed[xmlid] = node
    return indexed


def _resolve_role_code(user_xmlids: set) -> str:
    if {
        "base.group_system",
        "smart_construction_core.group_sc_super_admin",
        "smart_construction_core.group_sc_cap_config_admin",
        "smart_construction_core.group_sc_business_full",
        "smart_construction_custom.group_sc_role_executive",
    } & user_xmlids:
        return "executive"
    if {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_core.group_sc_cap_finance_read",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    } & user_xmlids:
        return "finance"
    if {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_core.group_sc_cap_project_user",
        "smart_construction_core.group_sc_cap_project_manager",
    } & user_xmlids:
        return "pm"
    return "owner"


def _pick_landing_scene(scene_candidates: List[str], scene_keys: set) -> str:
    for candidate in scene_candidates:
        if candidate in scene_keys:
            return candidate
    return "projects.list"


def _build_role_surface(user_xmlids: set, nav_tree: list, scene_keys: set) -> dict:
    role_code = _resolve_role_code(user_xmlids)
    role_meta = ROLE_SURFACE_MAP.get(role_code) or ROLE_SURFACE_MAP["owner"]
    scene_candidates = list(role_meta.get("landing_scene_candidates") or [])
    menu_candidates = list(role_meta.get("menu_xmlids") or [])
    landing_scene_key = _pick_landing_scene(scene_candidates, scene_keys)
    nav_index = _index_nav_by_xmlid(nav_tree)
    landing_menu_xmlid = ""
    landing_menu_id = None
    for xmlid in menu_candidates:
        node = nav_index.get(xmlid)
        if not node:
            continue
        landing_menu_xmlid = xmlid
        landing_menu_id = node.get("menu_id") or node.get("id")
        break
    return {
        "role_code": role_code,
        "role_label": role_meta.get("label") or role_code,
        "landing_scene_key": landing_scene_key,
        "landing_menu_xmlid": landing_menu_xmlid,
        "landing_menu_id": landing_menu_id,
        "landing_path": f"/s/{landing_scene_key}",
        "scene_candidates": scene_candidates,
        "menu_xmlids": menu_candidates,
    }


def _build_role_surface_map_payload() -> Dict[str, dict]:
    payload = {}
    for role_code, role_meta in ROLE_SURFACE_MAP.items():
        payload[role_code] = {
            "role_code": role_code,
            "role_label": role_meta.get("label") or role_code,
            "scene_candidates": list(role_meta.get("landing_scene_candidates") or []),
            "menu_xmlids": list(role_meta.get("menu_xmlids") or []),
        }
    return payload

def _is_menu_node(node: dict) -> bool:
    """仅保留真正菜单节点（有 menu_id 或有 children 的分组）"""
    return bool(node.get("menu_id") or node.get("children"))

def _clean_nav(nodes: list) -> list:
    """去除“sig:*”等非菜单节点，递归清洗"""
    cleaned = []
    for n in nodes or []:
        if not _is_menu_node(n):
            continue
        c = dict(n)
        c["children"] = _clean_nav(n.get("children") or [])
        cleaned.append(c)
    return cleaned

def _get_request_header(name: str) -> str | None:
    try:
        from odoo import http
        request = http.request
        if not request or not request.httprequest:
            return None
        return request.httprequest.headers.get(name)
    except Exception:
        return None

def _normalize_scene_channel(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip().lower()
    return raw if raw in SCENE_CHANNELS else None

def _resolve_scene_channel(env, user, params: dict | None) -> tuple[str, str, str]:
    channel = None
    selector = "default"
    source_ref = "default"
    if isinstance(params, dict):
        channel = _normalize_scene_channel(params.get("scene_channel") or params.get("channel"))
        if channel:
            selector = "param"
            source_ref = "param:scene_channel"
            return channel, selector, source_ref
    header_val = _normalize_scene_channel(_get_request_header("X-Scene-Channel"))
    if header_val:
        return header_val, "param", "header:X-Scene-Channel"

    try:
        config = env["ir.config_parameter"].sudo()
        user_val = None
        if user and user.id:
            user_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.user.{user.id}") or "")
        if user_val:
            return user_val, "user", f"user_id={user.id}"

        company_id = user.company_id.id if user and user.company_id else None
        if company_id:
            company_val = _normalize_scene_channel(config.get_param(f"sc.scene.channel.company.{company_id}") or "")
            if company_val:
                return company_val, "company", f"company_id={company_id}"

        default_val = _normalize_scene_channel(config.get_param("sc.scene.channel.default") or "")
        if default_val:
            return default_val, "config", "sc.scene.channel.default"
    except Exception:
        pass

    env_val = _normalize_scene_channel(os.environ.get("SCENE_CHANNEL"))
    if env_val:
        return env_val, "env", "SCENE_CHANNEL"

    return "stable", selector, source_ref

def _resolve_scene_contract_path(rel_path: str) -> str | None:
    roots = [
        os.environ.get("SCENE_CONTRACT_ROOT"),
        "/mnt/extra-addons",
        "/mnt/addons_external",
        "/mnt/odoo",
        "/mnt/e/sc-backend-odoo",
        "/mnt",
    ]
    for root in roots:
        if not root:
            continue
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            return candidate
    return None

def _load_scene_contract(env, scene_channel: str, use_pinned: bool) -> tuple[dict | None, str]:
    if use_pinned:
        ref = "stable/PINNED.json"
        try:
            param = env["ir.config_parameter"].sudo().get_param("sc.scene.contract.pinned")
            if param:
                return json.loads(param), ref
        except Exception:
            pass
        rel_path = "docs/contract/exports/scenes/stable/PINNED.json"
    else:
        rel_path = f"docs/contract/exports/scenes/{scene_channel}/LATEST.json"
        ref = f"{scene_channel}/LATEST.json"
    path = _resolve_scene_contract_path(rel_path)
    if not path:
        return None, ref
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), ref
    except Exception as e:
        _logger.warning("scene contract load failed: %s (%s)", path, e)
        return None, ref
# 在文件工具函数区追加：
def _to_xmlid_list(env, maybe_ids_or_xmlids):
    """
    输入可能是 [xmlid(str)] 或 [int id] 或混合，统一转 [xmlid(str)]
    """
    if not maybe_ids_or_xmlids:
        return []
    out = []
    int_ids = []
    for g in maybe_ids_or_xmlids:
        if isinstance(g, str) and "." in g:
            out.append(g)
        elif isinstance(g, int):
            int_ids.append(g)
    if int_ids:
        imds = env["ir.model.data"].sudo().search([
            ("model", "=", "res.groups"),
            ("res_id", "in", int_ids)
        ])
        # 建字典以便 O(1) 查找
        id2xml = {imd.res_id: f"{imd.module}.{imd.name}" for imd in imds if imd.module and imd.name}
        for gid in int_ids:
            if gid in id2xml:
                out.append(id2xml[gid])
    # 去重并保持稳定排序
    return sorted(set(out))

def _normalize_nav_groups(env, nodes):
    """
    递归把 nav[*].meta.groups_xmlids 统一成 xmlid(str) 列表
    """
    for n in nodes or []:
        meta = n.get("meta") or {}
        if "groups_xmlids" in meta and meta["groups_xmlids"]:
            meta["groups_xmlids"] = _to_xmlid_list(env, meta["groups_xmlids"])
            n["meta"] = meta
        if n.get("children"):
            _normalize_nav_groups(env, n["children"])

def _resolve_action_ids(env, action_xmlids: Dict[str, str]) -> Dict[int, str]:
    resolved = {}
    for xmlid, scene_key in action_xmlids.items():
        try:
            rec = env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id:
                resolved[rec.id] = scene_key
        except Exception:
            continue
    return resolved

def _normalize_view_mode(raw: str | None) -> str | None:
    if not raw:
        return None
    val = str(raw).strip().lower()
    if val in {"tree", "list", "kanban"}:
        return "list"
    if val in {"form"}:
        return "form"
    return val

def _apply_scene_keys(env, nodes):
    """
    Inject nav.node.scene_key using priority:
      menu_xmlid -> action_id -> model/view_mode
    Also ensure node.xmlid is emitted if menu_xmlid exists.
    """
    menu_map = {
        "smart_construction_demo.menu_sc_project_list_showcase": "projects.list",
        "smart_construction_core.menu_sc_project_initiation": "projects.intake",
        "smart_construction_core.menu_sc_project_project": "projects.ledger",
        "smart_construction_core.menu_sc_root": "projects.list",
        "smart_construction_core.menu_sc_project_dashboard": "projects.dashboard",
        "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
        "smart_construction_core.menu_sc_dictionary": "data.dictionary",
        "smart_construction_core.menu_payment_request": "finance.payment_requests",
        "smart_construction_portal.menu_sc_portal_lifecycle": "portal.lifecycle",
        "smart_construction_portal.menu_sc_portal_capability_matrix": "portal.capability_matrix",
        "smart_construction_portal.menu_sc_portal_dashboard": "portal.dashboard",
    }
    action_xmlid_map = {
        "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
        "smart_construction_core.action_project_initiation": "projects.intake",
        "smart_construction_core.action_sc_project_kanban_lifecycle": "projects.ledger",
        "smart_construction_core.action_sc_project_list": "projects.list",
        "smart_construction_core.action_project_dashboard": "projects.dashboard",
        "smart_construction_demo.action_project_dashboard_showcase": "projects.dashboard_showcase",
        "smart_construction_core.action_project_dictionary": "data.dictionary",
        "smart_construction_core.action_payment_request": "finance.payment_requests",
        "smart_construction_core.action_payment_request_my": "finance.payment_requests",
        "smart_construction_portal.action_sc_portal_lifecycle": "portal.lifecycle",
        "smart_construction_portal.action_sc_portal_capability_matrix": "portal.capability_matrix",
        "smart_construction_portal.action_sc_portal_dashboard": "portal.dashboard",
    }
    action_id_map = _resolve_action_ids(env, action_xmlid_map)
    model_view_map = {
        ("project.project", "list"): "projects.list",
        ("project.project", "form"): "projects.intake",
        ("payment.request", "list"): "finance.payment_requests",
        ("payment.request", "form"): "finance.payment_requests",
    }

    for n in nodes or []:
        meta = n.get("meta") or {}
        menu_xmlid = meta.get("menu_xmlid") or n.get("xmlid")
        if menu_xmlid:
            n["xmlid"] = menu_xmlid
        scene_key = None
        if menu_xmlid and menu_xmlid in menu_map:
            scene_key = menu_map[menu_xmlid]
        if not scene_key:
            action_id = meta.get("action_id")
            if isinstance(action_id, str) and action_id.isdigit():
                action_id = int(action_id)
            if action_id in action_id_map:
                scene_key = action_id_map[action_id]
        if not scene_key:
            action_xmlid = meta.get("action_xmlid")
            if action_xmlid and action_xmlid in action_xmlid_map:
                scene_key = action_xmlid_map[action_xmlid]
                meta["scene_key_inferred_from"] = "action_xmlid"
        if not scene_key:
            model = meta.get("model")
            view_mode = meta.get("view_mode") or meta.get("view_type")
            if not view_mode:
                view_modes = meta.get("view_modes")
                if isinstance(view_modes, list) and view_modes:
                    view_mode = view_modes[0]
            key = (model, _normalize_view_mode(view_mode)) if model else None
            if key in model_view_map:
                scene_key = model_view_map[key]
        if scene_key:
            n["scene_key"] = scene_key
            meta["scene_key"] = scene_key
            n["meta"] = meta
        if n.get("children"):
            _apply_scene_keys(env, n["children"])


def _append_inferred_scene_warnings(nodes, scene_keys: set, warnings: list):
    if warnings is None:
        return
    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            if meta.get("scene_key_inferred_from") == "action_xmlid":
                scene_key = node.get("scene_key") or meta.get("scene_key")
                if scene_key and scene_key not in scene_keys:
                    warnings.append({
                        "code": "SCENEKEY_INFERRED_NOT_FOUND",
                        "severity": "warn",
                        "scene_key": scene_key,
                        "message": "scene_key inferred from action_xmlid but not found in registry",
                        "field": "scene_key",
                        "reason": "inferred_scene_missing",
                        "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                        "action_xmlid": meta.get("action_xmlid"),
                    })
            if node.get("children"):
                walk(node.get("children"))
    walk(nodes)


def _resolve_action_id(env, xmlid: str | None) -> int | None:
    if not xmlid:
        return None
    try:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and rec.id:
            return int(rec.id)
    except Exception:
        return None
    return None


def _resolve_xmlid(env, xmlid: str | None) -> int | None:
    return _resolve_action_id(env, xmlid)


CRITICAL_SCENES = {
    "projects.list",
    "projects.ledger",
}


def _scene_severity(scene_key: str | None) -> str:
    if scene_key and scene_key in CRITICAL_SCENES:
        return "critical"
    return "non_critical"


def _is_critical_drift_warn(entry: dict) -> bool:
    if not isinstance(entry, dict):
        return False
    if str(entry.get("severity") or "").strip().lower() != "warn":
        return False
    scene_key = entry.get("scene_key")
    return scene_key in CRITICAL_SCENES


def _build_scene_health_payload(data: dict, trace_id: str = "", company_id: int | None = None) -> dict:
    data = data or {}
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    diag = data.get("scene_diagnostics") if isinstance(data.get("scene_diagnostics"), dict) else {}
    resolve_errors = diag.get("resolve_errors") if isinstance(diag.get("resolve_errors"), list) else []
    drift = diag.get("drift") if isinstance(diag.get("drift"), list) else []
    normalize_warnings = diag.get("normalize_warnings") if isinstance(diag.get("normalize_warnings"), list) else []

    critical_resolve_errors = [
        entry for entry in resolve_errors
        if isinstance(entry, dict) and str(entry.get("severity") or "").strip().lower() == "critical"
    ]
    critical_drift_warn = [entry for entry in drift if _is_critical_drift_warn(entry)]

    debt = []
    for entry in resolve_errors:
        if not isinstance(entry, dict):
            continue
        severity = str(entry.get("severity") or "").strip().lower()
        if severity != "critical":
            debt.append({"type": "resolve_error", **entry})
    for entry in drift:
        if not isinstance(entry, dict):
            continue
        if not _is_critical_drift_warn(entry):
            debt.append({"type": "drift", **entry})
    for entry in normalize_warnings:
        if isinstance(entry, dict):
            debt.append({"type": "normalize_warning", **entry})

    resolved_company_id = company_id
    if resolved_company_id is None:
        raw_company_id = user.get("company_id") if isinstance(user, dict) else None
        try:
            resolved_company_id = int(raw_company_id) if raw_company_id else None
        except Exception:
            resolved_company_id = None

    return {
        "company_id": resolved_company_id,
        "scene_channel": data.get("scene_channel"),
        "rollback_active": bool(diag.get("rollback_active")),
        "scene_version": data.get("scene_version"),
        "schema_version": data.get("schema_version"),
        "contract_ref": data.get("scene_contract_ref"),
        "summary": {
            "critical_resolve_errors_count": len(critical_resolve_errors),
            "critical_drift_warn_count": len(critical_drift_warn),
            "non_critical_debt_count": len(debt),
        },
        "details": {
            "resolve_errors": resolve_errors,
            "drift": drift,
            "debt": debt,
        },
        "auto_degrade": diag.get("auto_degrade") if isinstance(diag.get("auto_degrade"), dict) else {
            "triggered": False,
            "reason_codes": [],
            "action_taken": "none",
        },
        "last_updated_at": fields.Datetime.now(),
        "trace_id": trace_id or "",
    }


def _get_auto_degrade_policy(env) -> dict:
    defaults = {
        "enabled": True,
        "critical_threshold_resolve_errors": 1,
        "critical_threshold_drift_warn": 1,
        "action": "rollback_pinned",
    }
    try:
        config = env["ir.config_parameter"].sudo()
    except Exception:
        return defaults

    def _get_int(name: str, fallback: int) -> int:
        try:
            raw = config.get_param(name)
            return int(raw) if raw not in (None, "") else fallback
        except Exception:
            return fallback

    enabled_raw = config.get_param("sc.scene.auto_degrade.enabled")
    enabled = defaults["enabled"] if enabled_raw in (None, "") else is_truthy(enabled_raw)
    action = (config.get_param("sc.scene.auto_degrade.action") or defaults["action"]).strip().lower()
    if action not in {"rollback_pinned", "stable_latest"}:
        action = defaults["action"]

    return {
        "enabled": enabled,
        "critical_threshold_resolve_errors": max(1, _get_int("sc.scene.auto_degrade.critical_threshold.resolve_errors", 1)),
        "critical_threshold_drift_warn": max(1, _get_int("sc.scene.auto_degrade.critical_threshold.drift_warn", 1)),
        "action": action,
    }


def _get_auto_degrade_notify_policy(env) -> dict:
    defaults = {
        "enabled": True,
        "channels": ["internal"],
    }
    try:
        config = env["ir.config_parameter"].sudo()
    except Exception:
        return defaults

    enabled_raw = config.get_param("sc.scene.auto_degrade.notify.enabled")
    enabled = defaults["enabled"] if enabled_raw in (None, "") else is_truthy(enabled_raw)
    raw_channels = (config.get_param("sc.scene.auto_degrade.notify.channels") or "internal").strip().lower()
    allowed = {"email", "internal", "webhook"}
    channels = [item.strip() for item in raw_channels.split(",") if item.strip() in allowed]
    if not channels:
        channels = ["internal"]
    return {"enabled": enabled, "channels": channels}


def _notify_auto_degrade(env, *, user, trace_id: str, reason_codes: list, action_taken: str, from_channel: str, to_channel: str):
    policy = _get_auto_degrade_notify_policy(env)
    if not policy.get("enabled"):
        return {"sent": False, "channels": [], "trace_id": trace_id or ""}

    sent_channels = []
    message_payload = {
        "trace_id": trace_id or "",
        "reason_codes": list(reason_codes or []),
        "action_taken": action_taken,
        "from_channel": from_channel,
        "to_channel": to_channel,
        "company_id": user.company_id.id if user and user.company_id else None,
        "suggestion": "Please review scene targets and resolve critical drift/resolve errors.",
    }
    body = (
        "Auto-degrade triggered.\n"
        f"trace_id={message_payload['trace_id']}\n"
        f"action_taken={action_taken}\n"
        f"from={from_channel} to={to_channel}\n"
        f"reason_codes={','.join(message_payload['reason_codes']) or '-'}"
    )

    for channel in policy.get("channels") or []:
        if channel == "internal":
            try:
                env["sc.audit.log"].sudo().write_event(
                    event_code="SCENE_AUTO_DEGRADE_NOTIFY",
                    model="system.init",
                    res_id=0,
                    action="auto_degrade_notify_internal",
                    after={"channel": "internal", **message_payload},
                    reason="auto degrade internal notification",
                    trace_id=trace_id or "",
                    company_id=message_payload["company_id"],
                )
                sent_channels.append("internal")
            except Exception:
                pass
        elif channel == "email":
            try:
                partner = user.partner_id if user else None
                email_to = partner.email if partner and partner.email else None
                if email_to:
                    Mail = env["mail.mail"].sudo()
                    Mail.create({
                        "subject": "[Scene] Auto-degrade triggered",
                        "body_html": body.replace("\n", "<br/>"),
                        "email_to": email_to,
                    })
                    sent_channels.append("email")
            except Exception:
                pass
        elif channel == "webhook":
            try:
                env["sc.audit.log"].sudo().write_event(
                    event_code="SCENE_AUTO_DEGRADE_NOTIFY",
                    model="system.init",
                    res_id=0,
                    action="auto_degrade_notify_webhook_pending",
                    after={"channel": "webhook", **message_payload},
                    reason="auto degrade webhook notification placeholder",
                    trace_id=trace_id or "",
                    company_id=message_payload["company_id"],
                )
                sent_channels.append("webhook")
            except Exception:
                pass

    return {"sent": bool(sent_channels), "channels": sent_channels, "trace_id": trace_id or ""}


def _log_auto_degrade_once(env, *, trace_id: str, user, from_channel: str, to_channel: str, reason_codes: list, action_taken: str):
    try:
        Log = env["sc.scene.governance.log"].sudo()
        now = datetime.utcnow()
        window_start = fields.Datetime.to_string(now - timedelta(minutes=1))
        domain = [
            ("action", "=", "auto_degrade_triggered"),
            ("created_at", ">=", window_start),
        ]
        if trace_id:
            domain.append(("trace_id", "=", trace_id))
        if Log.search_count(domain):
            return
        Log.create({
            "action": "auto_degrade_triggered",
            "actor_id": user.id if user and user.id else None,
            "company_id": user.company_id.id if user and user.company_id else None,
            "from_channel": from_channel,
            "to_channel": to_channel,
            "reason": "auto degrade triggered by scene diagnostics",
            "trace_id": trace_id or "",
            "payload_json": {
                "reason_codes": list(reason_codes or []),
                "action_taken": action_taken,
            },
            "created_at": fields.Datetime.now(),
        })
        return
    except Exception:
        pass

    # fallback: if scene governance model is unavailable, keep audit evidence in core audit log
    try:
        Audit = env["sc.audit.log"].sudo()
        now = datetime.utcnow()
        window_start = fields.Datetime.to_string(now - timedelta(minutes=1))
        domain = [
            ("event_code", "=", "SCENE_AUTO_DEGRADE_TRIGGERED"),
            ("ts", ">=", window_start),
        ]
        if trace_id:
            domain.append(("trace_id", "=", trace_id))
        if Audit.search_count(domain):
            return
        Audit.write_event(
            event_code="SCENE_AUTO_DEGRADE_TRIGGERED",
            model="system.init",
            res_id=0,
            action="auto_degrade_triggered",
            after={
                "from_channel": from_channel,
                "to_channel": to_channel,
                "reason_codes": list(reason_codes or []),
                "action_taken": action_taken,
            },
            reason="auto degrade triggered by scene diagnostics",
            trace_id=trace_id or "",
            company_id=user.company_id.id if user and user.company_id else None,
        )
    except Exception:
        return


def _evaluate_auto_degrade(env, *, user, scene_channel: str, diagnostics: dict, trace_id: str) -> dict:
    policy = _get_auto_degrade_policy(env)
    result = {
        "triggered": False,
        "reason_codes": [],
        "action_taken": "none",
        "notifications": {"sent": False, "channels": []},
        "policy": policy,
        "pre_counts": {
            "critical_resolve_errors_count": 0,
            "critical_drift_warn_count": 0,
        },
    }
    if not policy.get("enabled"):
        return result

    resolve_errors = diagnostics.get("resolve_errors") if isinstance(diagnostics.get("resolve_errors"), list) else []
    drift = diagnostics.get("drift") if isinstance(diagnostics.get("drift"), list) else []
    critical_resolve_errors_count = len(
        [
            entry for entry in resolve_errors
            if isinstance(entry, dict) and str(entry.get("severity") or "").strip().lower() == "critical"
        ]
    )
    critical_drift_warn_count = len([entry for entry in drift if _is_critical_drift_warn(entry)])
    result["pre_counts"] = {
        "critical_resolve_errors_count": critical_resolve_errors_count,
        "critical_drift_warn_count": critical_drift_warn_count,
    }

    reason_codes = []
    if critical_resolve_errors_count >= int(policy.get("critical_threshold_resolve_errors") or 1):
        reason_codes.append("critical_resolve_errors")
    if critical_drift_warn_count >= int(policy.get("critical_threshold_drift_warn") or 1):
        reason_codes.append("critical_drift_warn")
    if not reason_codes:
        return result

    action = policy.get("action") or "rollback_pinned"
    to_channel = "stable"
    rollback_active = action == "rollback_pinned"
    try:
        config = env["ir.config_parameter"].sudo()
        config.set_param("sc.scene.rollback", "1" if rollback_active else "0")
        config.set_param("sc.scene.use_pinned", "1" if rollback_active else "0")
    except Exception:
        pass

    _log_auto_degrade_once(
        env,
        trace_id=trace_id,
        user=user,
        from_channel=scene_channel,
        to_channel=to_channel,
        reason_codes=reason_codes,
        action_taken=action,
    )
    notify_result = _notify_auto_degrade(
        env,
        user=user,
        trace_id=trace_id,
        reason_codes=reason_codes,
        action_taken=action,
        from_channel=scene_channel,
        to_channel=to_channel,
    )

    result["triggered"] = True
    result["reason_codes"] = reason_codes
    result["action_taken"] = action
    result["notifications"] = notify_result
    return result


def _append_resolve_error(resolve_errors, *, scene_key, kind, code, ref=None, message=None, severity=None, field=None):
    entry = {
        "scene_key": scene_key or "",
        "kind": kind,
        "code": code,
        "severity": severity or _scene_severity(scene_key),
        "message": message or "",
    }
    if ref:
        entry["ref"] = ref
    if field:
        entry["field"] = field
    resolve_errors.append(entry)


def _index_nav_scene_targets(nodes):
    targets = {}
    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            scene_key = node.get("scene_key") or meta.get("scene_key")
            if scene_key:
                targets[scene_key] = {
                    "menu_id": node.get("menu_id") or node.get("id"),
                    "action_id": meta.get("action_id"),
                    "model": meta.get("model"),
                    "view_mode": meta.get("view_mode") or meta.get("view_type"),
                }
            if node.get("children"):
                walk(node["children"])
    walk(nodes)
    return targets


def _append_act_url_deprecations(nodes, warnings):
    if warnings is None:
        return
    def walk(items):
        for node in items or []:
            meta = node.get("meta") or {}
            action_type = str(meta.get("action_type") or "").strip().lower()
            scene_key = node.get("scene_key") or meta.get("scene_key")
            if action_type == "ir.actions.act_url" and scene_key:
                warnings.append({
                    "code": "ACT_URL_LEGACY",
                    "severity": "info",
                    "scene_key": scene_key,
                    "message": "act_url menu resolved via scene_key (legacy action type)",
                    "field": "action_type",
                    "reason": "legacy_act_url",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
            if action_type == "ir.actions.act_url" and not scene_key:
                warnings.append({
                    "code": "ACT_URL_MISSING_SCENE",
                    "severity": "warn",
                    "scene_key": "",
                    "message": "act_url menu missing scene_key mapping",
                    "field": "scene_key",
                    "reason": "legacy_act_url_missing_scene",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
            if node.get("children"):
                walk(node.get("children"))
    walk(nodes)


def _normalize_scene_targets(env, scenes, nav_targets, resolve_errors):
    for scene in scenes:
        scene_key = scene.get("code") or scene.get("key")
        if not scene_key:
            continue
        target = scene.get("target") or {}
        route = target.get("route")
        route_is_missing_fallback = isinstance(route, str) and "TARGET_MISSING" in route
        action_xmlid = target.get("action_xmlid") or target.get("actionXmlid")
        menu_xmlid = target.get("menu_xmlid") or target.get("menuXmlid")
        if action_xmlid and not target.get("action_id"):
            action_id = _resolve_xmlid(env, action_xmlid)
            if action_id:
                target["action_id"] = action_id
            else:
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="XMLID_NOT_FOUND",
                    ref=action_xmlid,
                    field="action_xmlid",
                    message="action_xmlid not found",
                )
        if menu_xmlid and not target.get("menu_id"):
            menu_id = _resolve_xmlid(env, menu_xmlid)
            if menu_id:
                target["menu_id"] = menu_id
            else:
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="XMLID_NOT_FOUND",
                    ref=menu_xmlid,
                    field="menu_xmlid",
                    message="menu_xmlid not found",
                )
        if "action_xmlid" in target:
            target.pop("action_xmlid", None)
        if "actionXmlid" in target:
            target.pop("actionXmlid", None)
        if "menu_xmlid" in target:
            target.pop("menu_xmlid", None)
        if "menuXmlid" in target:
            target.pop("menuXmlid", None)
        if target.get("action_id") or target.get("model") or (target.get("route") and not route_is_missing_fallback):
            scene["target"] = target
            continue
        nav = nav_targets.get(scene_key) or {}
        resolved = {}
        if nav.get("action_id"):
            resolved["action_id"] = nav.get("action_id")
        elif nav.get("model"):
            resolved["model"] = nav.get("model")
            if nav.get("view_mode"):
                resolved["view_mode"] = nav.get("view_mode")
        if nav.get("menu_id"):
            resolved["menu_id"] = nav.get("menu_id")
        if resolved:
            scene["target"] = resolved
        else:
            semantic_fallback = f"/s/{scene_key}"
            if route_is_missing_fallback:
                # Replace legacy workbench fallback with semantic scene route.
                scene["target"] = {"route": semantic_fallback}
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="MISSING_TARGET",
                    ref=semantic_fallback,
                    field="target",
                    message="target missing; semantic fallback route applied",
                )
            else:
                scene["target"] = {"route": semantic_fallback}
                _append_resolve_error(
                    resolve_errors,
                    scene_key=scene_key,
                    kind="target",
                    code="MISSING_TARGET",
                    ref=semantic_fallback,
                    field="target",
                    message="target missing; semantic fallback route applied",
                )
    return scenes


def _normalize_scene_layouts(scenes, warnings):
    for scene in scenes:
        scene_key = scene.get("code") or scene.get("key") or ""
        layout = scene.get("layout")
        if not isinstance(layout, dict):
            warnings.append({
                "code": "LAYOUT_MISSING_OR_INVALID",
                "severity": "non_critical",
                "scene_key": scene_key,
                "message": "layout missing or invalid; no defaults applied",
                "field": "layout",
                "reason": "missing_or_invalid",
            })
            continue
    return scenes


def _to_string_list(value) -> List[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return sorted(set(out))


def _to_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return default
    return bool(value)


def _normalize_tile_status(value) -> str:
    status = str(value or "").strip().lower()
    if status in {"ga", "beta", "alpha"}:
        return status
    return ""


def _normalize_tile_state(value) -> str:
    state = str(value or "").strip().upper()
    if state in {"READY", "LOCKED", "PREVIEW"}:
        return state
    return ""


def _derive_tile_state(status: str, allowed) -> str:
    if isinstance(allowed, bool):
        return "READY" if allowed else "LOCKED"
    return "READY" if status == "ga" else "PREVIEW"


def _normalize_scene_tiles(scenes, capabilities, warnings):
    cap_map: Dict[str, dict] = {}
    for capability in capabilities or []:
        if not isinstance(capability, dict):
            continue
        cap_key = str(capability.get("key") or "").strip()
        if not cap_key:
            continue
        cap_map[cap_key] = {
            "status": _normalize_tile_status(capability.get("status")),
            "state": _normalize_tile_state(capability.get("state")),
            "reason_code": str(capability.get("reason_code") or "").strip(),
            "reason": str(capability.get("reason") or "").strip(),
        }

    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        scene_key = scene.get("code") or scene.get("key") or ""
        tiles = scene.get("tiles")
        if not isinstance(tiles, list):
            continue
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            key = str(tile.get("key") or "").strip()
            cap_meta = cap_map.get(key) if key else None
            status = _normalize_tile_status(tile.get("status"))
            state = _normalize_tile_state(tile.get("state"))
            if not status and cap_meta:
                status = cap_meta.get("status") or ""
            if not state and cap_meta:
                state = cap_meta.get("state") or ""
            if not state:
                state = _derive_tile_state(status or "ga", tile.get("allowed"))
            if not status:
                status = "ga" if state == "READY" else "alpha"
            tile["status"] = status
            tile["state"] = state
            if cap_meta:
                if not tile.get("reason_code") and cap_meta.get("reason_code"):
                    tile["reason_code"] = cap_meta.get("reason_code")
                if not tile.get("reason") and cap_meta.get("reason"):
                    tile["reason"] = cap_meta.get("reason")
            if not key:
                warnings.append({
                    "code": "TILE_KEY_MISSING",
                    "severity": "non_critical",
                    "scene_key": scene_key,
                    "message": "tile key missing; state/status defaults applied",
                    "field": "tiles.key",
                    "reason": "missing_key",
                })
    return scenes


def _normalize_scene_accesses(scenes, warnings):
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_key = scene.get("code") or scene.get("key") or ""
        raw_access = scene.get("access")
        if raw_access is None:
            access = {}
        elif isinstance(raw_access, dict):
            access = dict(raw_access)
        else:
            warnings.append({
                "code": "ACCESS_INVALID",
                "severity": "non_critical",
                "scene_key": scene_key,
                "message": "access should be object; fallback access defaults applied",
                "field": "access",
                "reason": "invalid_type",
            })
            access = {}

        tile_caps = []
        for tile in scene.get("tiles") or []:
            if not isinstance(tile, dict):
                continue
            tile_caps.extend(_to_string_list(tile.get("required_capabilities")))

        caps = sorted(set(
            _to_string_list(scene.get("required_capabilities"))
            + _to_string_list(access.get("required_capabilities"))
            + tile_caps
        ))

        visible = _to_bool(access.get("visible"), True)
        if "allowed" in access:
            allowed = _to_bool(access.get("allowed"), visible)
        else:
            # access clause exists but no explicit allow/deny => keep visible default
            allowed = visible
        has_access_clause = bool(caps)
        reason_code = str(access.get("reason_code") or "").strip().upper()
        if not reason_code:
            reason_code = REASON_OK if allowed else REASON_PERMISSION_DENIED
        suggested_action = str(access.get("suggested_action") or "").strip()
        if not suggested_action and reason_code != REASON_OK:
            suggested_action = str(failure_meta_for_reason(reason_code).get("suggested_action") or "")

        scene["access"] = {
            "visible": visible,
            "allowed": allowed,
            "reason_code": reason_code,
            "suggested_action": suggested_action,
            "required_capabilities": caps,
            "required_capabilities_count": len(caps),
            "has_access_clause": has_access_clause,
        }

    return scenes



def _build_scene_target_maps(scenes):
    menu_id_map: Dict[int, str] = {}
    action_id_map: Dict[int, str] = {}
    model_view_map: Dict[Tuple[str, str | None], str] = {}
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            continue
        target = scene.get("target")
        if not isinstance(target, dict):
            continue
        menu_id = target.get("menu_id")
        action_id = target.get("action_id")
        model = str(target.get("model") or "").strip()
        view_mode = _normalize_view_mode(target.get("view_mode") or target.get("view_type"))

        if isinstance(menu_id, int) and menu_id > 0:
            menu_id_map.setdefault(menu_id, scene_key)
        if isinstance(action_id, int) and action_id > 0:
            action_id_map.setdefault(action_id, scene_key)
        if model:
            model_view_map.setdefault((model, view_mode), scene_key)
    return menu_id_map, action_id_map, model_view_map


def _sync_nav_scene_keys(nav_tree, scenes, warnings):
    scene_keys = {
        str(scene.get("code") or scene.get("key") or "").strip()
        for scene in scenes or []
        if isinstance(scene, dict)
    }
    scene_keys = {key for key in scene_keys if key}
    if not scene_keys:
        return

    menu_id_map, action_id_map, model_view_map = _build_scene_target_maps(scenes)

    def walk(nodes):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            node_scene_key = str(node.get("scene_key") or "").strip()
            meta_scene_key = str(meta.get("scene_key") or "").strip()
            scene_key = node_scene_key or meta_scene_key
            if scene_key and scene_key not in scene_keys:
                warnings.append({
                    "code": "NAV_SCENEKEY_INVALID",
                    "severity": "warn",
                    "scene_key": scene_key,
                    "message": "nav scene_key not found in scenes payload; fallback to menu/action routing",
                    "field": "nav.scene_key",
                    "reason": "scene_not_in_registry",
                    "menu_xmlid": node.get("xmlid") or meta.get("menu_xmlid"),
                })
                node.pop("scene_key", None)
                meta.pop("scene_key", None)
                scene_key = ""

            if not scene_key:
                menu_id = node.get("menu_id") or node.get("id")
                action_id = meta.get("action_id")
                if isinstance(action_id, str) and action_id.isdigit():
                    action_id = int(action_id)
                if isinstance(menu_id, str) and menu_id.isdigit():
                    menu_id = int(menu_id)
                model = str(meta.get("model") or "").strip()
                view_mode = _normalize_view_mode(meta.get("view_mode") or meta.get("view_type"))
                if not view_mode:
                    view_modes = meta.get("view_modes")
                    if isinstance(view_modes, list) and view_modes:
                        view_mode = _normalize_view_mode(view_modes[0])

                if isinstance(menu_id, int) and menu_id in menu_id_map:
                    scene_key = menu_id_map[menu_id]
                elif isinstance(action_id, int) and action_id in action_id_map:
                    scene_key = action_id_map[action_id]
                elif model and (model, view_mode) in model_view_map:
                    scene_key = model_view_map[(model, view_mode)]
                elif model and (model, None) in model_view_map:
                    scene_key = model_view_map[(model, None)]

            if scene_key and scene_key in scene_keys:
                node["scene_key"] = scene_key
                meta["scene_key"] = scene_key
                node["meta"] = meta

            if node.get("children"):
                walk(node.get("children"))

    walk(nav_tree)


def _merge_missing_scenes_from_registry(env, scenes, warnings):
    try:
        from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs
    except Exception:
        return scenes
    current = [scene for scene in (scenes or []) if isinstance(scene, dict)]
    existing = {
        str(scene.get("code") or scene.get("key") or "").strip()
        for scene in current
        if isinstance(scene, dict)
    }
    existing = {code for code in existing if code}
    registry_scenes = load_scene_configs(env) or []
    appended = []
    for scene in registry_scenes:
        if not isinstance(scene, dict):
            continue
        code = str(scene.get("code") or scene.get("key") or "").strip()
        if not code or code in existing:
            continue
        item = dict(scene)
        target = item.get("target")
        if isinstance(target, dict):
            item["target"] = dict(target)
        current.append(item)
        existing.add(code)
        appended.append(code)
    if appended:
        warnings.append({
            "code": "SCENE_FALLBACK_MERGED",
            "severity": "info",
            "scene_key": "",
            "message": "missing scenes merged from registry fallback",
            "field": "scenes",
            "reason": "contract_gap",
            "count": len(appended),
            "scene_codes": appended[:20],
        })
    return current


def collect_available_intents(env, user) -> Tuple[List[str], Dict[str, dict]]:
    """
    从 HANDLER_REGISTRY 动态收集可用意图（按权限过滤）。
    返回：
      - intents: 只包含“主名”（INTENT_TYPE）的有序列表
      - intents_meta: 含版本与别名，供前端/调试可选使用
    """
    user_xmlids = _user_group_xmlids(user)
    intents: List[str] = []
    meta: Dict[str, dict] = {}

    # 遍历注册表（支持别名注册到同一类）
    for name, cls in HANDLER_REGISTRY.items():
        primary = getattr(cls, "INTENT_TYPE", None) or name
        version = getattr(cls, "VERSION", None)
        required = _normalize_required_groups(env, getattr(cls, "REQUIRED_GROUPS", []) or [])
        enabled = getattr(cls, "IS_ENABLED", True)
        aliases = []
        try:
            aliases = list(getattr(cls, "ALIASES") or [])
        except Exception:
            aliases = []

        # 仅按“主名”去重与授权（别名只进 meta，不重复入列）
        if not enabled:
            continue
        if not _has_required_groups(user_xmlids, required):
            continue
        if primary in intents:
            # 已收录主名，补齐 meta 即可
            if primary in meta:
                meta[primary].setdefault("aliases", [])
                meta[primary]["aliases"] = sorted(set((meta[primary]["aliases"] or []) + aliases))
            continue

        intents.append(primary)
        m = {}
        if version:
            m["version"] = version
        if aliases:
            m["aliases"] = aliases
        if required:
            m["required_groups"] = required  # 已是 xmlid
        meta[primary] = m

    intents.sort()
    return intents, meta

# ===================== Handler =====================

class SystemInitHandler(BaseIntentHandler):
    """
    意图：system.init（别名：app.init / bootstrap）
    一次性初始化：用户/环境、导航、默认首页契约（无数据）、可选预取
    """
    INTENT_TYPE = "system.init"
    DESCRIPTION = "系统初始化（用户/环境、导航、首页契约、可用意图清单），只读，支持细粒度 ETag"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    ALIASES = ["app.init", "bootstrap"]
    REQUIRED_GROUPS = []  # 登录用户可用

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        ts0 = time.time()
        params = payload.get("params") if isinstance(payload, dict) else None
        if not isinstance(params, dict):
            params = payload if isinstance(payload, dict) else {}
        contract_mode = resolve_contract_mode(params)
        trace_id = ""
        try:
            trace_id = str((self.context or {}).get("trace_id") or "")
        except Exception:
            trace_id = ""

        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        scene_channel, channel_selector, channel_source_ref = _resolve_scene_channel(env, env.user, params)
        pinned_param = params.get("scene_use_pinned") if isinstance(params, dict) else None
        rollback_param = params.get("scene_rollback") if isinstance(params, dict) else None
        try:
            rollback_active = bool(self.get_bool("scene_use_pinned", False) or self.get_bool("scene_rollback", False))
        except Exception:
            rollback_active = is_truthy(pinned_param) or is_truthy(rollback_param)
        if pinned_param is not None and str(pinned_param).strip() not in {"", "0", "false", "no", "off"}:
            rollback_active = True
        try:
            config = env["ir.config_parameter"].sudo()
            rollback_active = rollback_active or is_truthy(config.get_param("sc.scene.use_pinned")) or                 is_truthy(config.get_param("sc.scene.rollback"))
        except Exception:
            pass
        rollback_active = rollback_active or is_truthy(os.environ.get("SCENE_USE_PINNED")) or             is_truthy(os.environ.get("SCENE_ROLLBACK"))
        if rollback_active:
            scene_channel = "stable"
        
        diag_enabled = _diagnostics_enabled(self.env)
        diagnostic_info = None
        if diag_enabled:
            # 收集请求头信息（白名单）
            try:
                from odoo import http
                request = http.request
                headers = request.httprequest.headers
                x_odoo_db = headers.get("X-Odoo-DB")
                x_db = headers.get("X-DB")
                authorization = headers.get("Authorization")
            except Exception:
                x_odoo_db = None
                x_db = None
                authorization = None

            diagnostic_info = {
                "effective_db": self.env.cr.dbname if hasattr(self.env, "cr") and self.env.cr else "unknown",
                "db_source": "env_cr",
                "header_x_odoo_db": x_odoo_db,
                "header_x_db": x_db,
                "has_authorization": bool(authorization),
                "effective_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
                "root_source": "params" if params and params.get("root_xmlid") else "default",
                "uid": self.env.uid,
                "login": self.env.user.login if hasattr(self.env, "user") else "unknown",
                "params_keys": list(params.keys()) if isinstance(params, dict) else [],
                "scene_channel_param": params.get("scene_channel") if isinstance(params, dict) else None,
                "scene_use_pinned_param": params.get("scene_use_pinned") if isinstance(params, dict) else None,
                "scene_rollback_param": params.get("scene_rollback") if isinstance(params, dict) else None,
            }

            _logger.info("[B1] system.init 诊断信息: %s", diagnostic_info)
            _logger.info("[system_init][debug] params: %s", params)
            _logger.info("[system_init][debug] self.params: %s", getattr(self, "params", {}))
            _logger.info("[system_init][debug] self.env.cr.dbname: %s", self.env.cr.dbname)

        # 如果 finalize_contract 内部不读 ORM，可用 env；若会读，推荐 su_env
        cs = ContractService(su_env)

        # -------- 1) 用户/环境 --------
        scene = params.get("scene") or "web"

        user = env.user
        user_groups_xmlids = _user_group_xmlids(user)

        user_dict = {
            "id": user.id,
            "name": user.name,
            "groups_xmlids": list(user_groups_xmlids),
            "lang": user.lang,
            "tz": user.tz,
            "company_id": user.company_id.id if user.company_id else None,
        }

        # -------- 2) 导航（净化 + 指纹）--------
        p_nav = {"subject": "nav", "scene": scene}
        if params.get("root_xmlid"):
            p_nav["root_xmlid"] = params.get("root_xmlid")
        if params.get("root_menu_id"):
            p_nav["root_menu_id"] = params.get("root_menu_id")
        nav_data, nav_versions = NavDispatcher(env, su_env).build_nav(p_nav)

        nav_tree_raw = nav_data.get("nav") or []
        nav_tree = _clean_nav(nav_tree_raw)
        # ✅ 统一 groups_xmlids 口径（字符串 xmlid）
        _normalize_nav_groups(env, nav_tree)
        _apply_scene_keys(env, nav_tree)
        nav_fp = _fingerprint({"scene": scene, "nav": nav_tree})
        if nav_versions and nav_versions.get("root_filtered_fallback"):
            _logger.warning(
                "NAV_ROOT_FILTERED_FALLBACK_USED uid=%s root_xmlid=%s trace=%s",
                env.uid,
                params.get("root_xmlid"),
                self.trace_id if hasattr(self, "trace_id") else None,
            )

        default_home_action = (
            params.get("home_action_id")
            or nav_data.get("default_home_action")
            or None
        )

        # -------- 2.5) 可用意图（动态生成，严格基于注册+权限）--------
        intents, intents_meta = collect_available_intents(env, user)

        # -------- 3) 首页契约（无数据 | 仅算指纹，不直接塞入 preload）--------
        home_contract = None
        etags: Dict[str, str] = {}
        parts_version: Dict[str, str] = {}

        if default_home_action:
            try:
                p_home = {"subject": "action", "action_id": default_home_action, "with_data": False}
                home_data, home_versions = ActionDispatcher(env, su_env).dispatch(p_home)
                fixed = cs.finalize_contract({
                    "ok": True,
                    "data": home_data,
                    "meta": {"subject": "action", "version": format_versions(home_versions)}
                })
                home_contract = fixed.get("data")
                parts_version["home"] = format_versions(home_versions)
                etags["home"] = stable_etag(home_contract)
            except Exception as e:
                _logger.warning("system.init home preload failed: action=%s, err=%s", default_home_action, e)

        # -------- 4) 可选预取（仅结构指纹，不回传整包契约）--------
        preload_items = []
        want_preload = bool(params.get("with_preload", True))
        preload_actions = params.get("preload_actions") or []

        if want_preload and preload_actions:
            for act in preload_actions:
                try:
                    p_pre = {"subject": "action", "action_id": act, "with_data": False}
                    pre_data, pre_versions = ActionDispatcher(env, su_env).dispatch(p_pre)
                    fixed = cs.finalize_contract({
                        "ok": True,
                        "data": pre_data,
                        "meta": {"subject": "action", "version": format_versions(pre_versions)}
                    })
                    contract = fixed.get("data")
                    e = stable_etag(contract)
                    preload_items.append({"key": act, "etag": e})  # ✅ 仅返回 etag
                    parts_version[act] = format_versions(pre_versions)
                    etags[act] = e
                except Exception as e:
                    _logger.warning("system.init preload failed: action=%s, err=%s", act, e)
                    continue

        # -------- 5) 汇总返回（统一蛇形命名 + 导航指纹 + 动态意图）--------
        data = {
            "user": user_dict,
            "nav": nav_tree,
            "nav_meta": {                                                       # ✅ 导航指纹 + scope info
                "fingerprint": nav_fp,
                **(nav_versions or {}),
                "debug_params_keys": sorted(list(params.keys())) if isinstance(params, dict) else [],
                "debug_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
            },
            "default_route": nav_data.get("defaultRoute") or {"menu_id": None},  # ✅ snake_case
            "intents": intents,                                                  # ✅ 动态意图（主名）
            "intents_meta": intents_meta,                                        # ⬅ 可选（前端可不用）
            "feature_flags": nav_data.get("feature_flags") or {"ai_enabled": True},
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
            "schema_version": "v1",
            "scene_channel": scene_channel,
            "scene_channel_selector": channel_selector,
            "scene_channel_source_ref": channel_source_ref,
            "scene_contract_ref": None,
            "contract_mode": contract_mode,
        }
        scene_diagnostics = {
            "schema_version": data.get("schema_version"),
            "scene_version": data.get("scene_version"),
            "loaded_from": None,
            "normalize_warnings": [],
            "resolve_errors": [],
            "drift": [],
            "rollback_active": bool(rollback_active),
            "rollback_ref": None,
            "channel_selector": channel_selector,
            "channel_source_ref": channel_source_ref,
            "auto_degrade": {"triggered": False, "reason_codes": [], "action_taken": "none"},
            "timings": {},
        }
        _append_act_url_deprecations(nav_tree, scene_diagnostics["normalize_warnings"])
        if home_contract:
            data["preload"].append({"key": "home", "etag": etags.get("home")})   # ✅ 轻量化 preload
        if preload_items:
            data["preload"].extend(preload_items)

        # 扩展模块可附加场景/能力等（不影响主流程）
        run_extension_hooks(env, "smart_core_extend_system_init", data, env, user)

        # Scene orchestration source (contract export or smart_construction_scene)
        contract_payload, contract_ref = _load_scene_contract(env, scene_channel, rollback_active)
        data["scene_contract_ref"] = contract_ref
        if rollback_active:
            scene_diagnostics["rollback_ref"] = contract_ref
        if contract_payload:
            data["scenes"] = contract_payload.get("scenes") or []
            data["scene_version"] = contract_payload.get("scene_version") or data.get("scene_version")
            data["schema_version"] = contract_payload.get("schema_version") or data.get("schema_version")
            scene_diagnostics["scene_version"] = data.get("scene_version")
            scene_diagnostics["schema_version"] = data.get("schema_version")
            scene_diagnostics["loaded_from"] = "contract"
            data["scenes"] = _merge_missing_scenes_from_registry(env, data.get("scenes"), scene_diagnostics["normalize_warnings"])
        else:
            try:
                from odoo.addons.smart_construction_scene.scene_registry import (
                    load_scene_configs,
                    get_scene_version,
                    get_schema_version,
                    has_db_scenes,
                )
                t_load_start = time.time()
                drift_entries = scene_diagnostics["drift"]
                scenes_payload = load_scene_configs(env, drift=drift_entries) or []
                scene_diagnostics["loaded_from"] = "db" if has_db_scenes(env) else "fallback"
                scene_diagnostics["timings"]["load_ms"] = int((time.time() - t_load_start) * 1000)
                if scenes_payload:
                    data["scenes"] = scenes_payload
                    data["scene_version"] = get_scene_version() or data.get("scene_version")
                    data["schema_version"] = get_schema_version() or data.get("schema_version")
                    scene_diagnostics["scene_version"] = data.get("scene_version")
                    scene_diagnostics["schema_version"] = data.get("schema_version")
            except Exception as e:
                _logger.warning("system.init scene source load failed: %s", e)

        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        scene_keys = {
            (s.get("code") or s.get("key"))
            for s in scenes_payload
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        t_norm_start = time.time()
        _append_inferred_scene_warnings(nav_tree, scene_keys, scene_diagnostics["normalize_warnings"])
        _normalize_scene_layouts(scenes_payload, scene_diagnostics["normalize_warnings"])
        _normalize_scene_accesses(scenes_payload, scene_diagnostics["normalize_warnings"])
        _normalize_scene_tiles(scenes_payload, data.get("capabilities"), scene_diagnostics["normalize_warnings"])
        scene_diagnostics["timings"]["normalize_ms"] = int((time.time() - t_norm_start) * 1000)
        nav_targets = _index_nav_scene_targets(nav_tree)
        t_resolve_start = time.time()
        _normalize_scene_targets(env, scenes_payload, nav_targets, scene_diagnostics["resolve_errors"])
        _sync_nav_scene_keys(nav_tree, scenes_payload, scene_diagnostics["normalize_warnings"])
        scene_diagnostics["timings"]["resolve_ms"] = int((time.time() - t_resolve_start) * 1000)

        # dev/test 下允许注入 critical 诊断，供 system-bound auto-degrade smoke 使用
        if is_truthy(params.get("scene_inject_critical_error")) and _diagnostics_enabled(env):
            _append_resolve_error(
                scene_diagnostics["resolve_errors"],
                scene_key="projects.list",
                kind="target",
                code="TEST_CRITICAL_INJECTED",
                ref="smart_construction_scene.test.injected",
                message="injected critical resolve error for auto-degrade smoke",
                severity="critical",
            )

        auto_degrade = _evaluate_auto_degrade(
            env,
            user=user,
            scene_channel=scene_channel,
            diagnostics=scene_diagnostics,
            trace_id=trace_id,
        )
        scene_diagnostics["auto_degrade"] = auto_degrade
        if auto_degrade.get("triggered"):
            action_taken = auto_degrade.get("action_taken") or "rollback_pinned"
            scene_channel = "stable"
            rollback_active = action_taken == "rollback_pinned"
            data["scene_channel"] = scene_channel
            data["scene_contract_ref"] = "stable/PINNED.json" if rollback_active else "stable/LATEST.json"
            scene_diagnostics["rollback_active"] = bool(rollback_active)
            scene_diagnostics["rollback_ref"] = data["scene_contract_ref"] if rollback_active else None

            degraded_payload, degraded_ref = _load_scene_contract(env, scene_channel, rollback_active)
            data["scene_contract_ref"] = degraded_ref
            if rollback_active:
                scene_diagnostics["rollback_ref"] = degraded_ref
            if degraded_payload:
                data["scenes"] = degraded_payload.get("scenes") or []
                data["scene_version"] = degraded_payload.get("scene_version") or data.get("scene_version")
                data["schema_version"] = degraded_payload.get("schema_version") or data.get("schema_version")
                scene_diagnostics["scene_version"] = data.get("scene_version")
                scene_diagnostics["schema_version"] = data.get("schema_version")
                scene_diagnostics["loaded_from"] = "contract"
                scene_diagnostics["resolve_errors"] = []
                scene_diagnostics["drift"] = []
                scene_diagnostics["normalize_warnings"] = []
                data["scenes"] = _merge_missing_scenes_from_registry(env, data.get("scenes"), scene_diagnostics["normalize_warnings"])
                t_norm2 = time.time()
                _normalize_scene_layouts(data["scenes"], scene_diagnostics["normalize_warnings"])
                _normalize_scene_accesses(data["scenes"], scene_diagnostics["normalize_warnings"])
                _normalize_scene_tiles(data["scenes"], data.get("capabilities"), scene_diagnostics["normalize_warnings"])
                scene_diagnostics["timings"]["normalize_after_degrade_ms"] = int((time.time() - t_norm2) * 1000)
                t_resolve2 = time.time()
                _normalize_scene_targets(env, data["scenes"], nav_targets, scene_diagnostics["resolve_errors"])
                _sync_nav_scene_keys(nav_tree, data["scenes"], scene_diagnostics["normalize_warnings"])
                scene_diagnostics["timings"]["resolve_after_degrade_ms"] = int((time.time() - t_resolve2) * 1000)
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else scenes_payload
        data["scenes"] = scenes_payload
        data = apply_contract_governance(data, contract_mode)
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        scene_keys_latest = {
            (s.get("code") or s.get("key"))
            for s in scenes_payload
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        data["role_surface"] = _build_role_surface(user_groups_xmlids, nav_tree, scene_keys_latest)
        data["role_surface_map"] = _build_role_surface_map_payload()
        data["scene_diagnostics"] = scene_diagnostics

        # 分部 etag：加入导航
        etags["nav"] = nav_fp

        elapsed_ms = int((time.time() - ts0) * 1000)
        meta = {
            "elapsed_ms": elapsed_ms,
            "parts": {"nav": format_versions(nav_versions), **parts_version},
            "etags": etags,
            "intent": self.INTENT_TYPE,
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
            "contract_mode": contract_mode,
        }
        if contract_mode == "hud":
            data["hud"] = {
                "trace_id": trace_id,
                "latency_ms": elapsed_ms,
                "contract_version": CONTRACT_VERSION,
                "role_key": data.get("role_surface", {}).get("role_code"),
            }
        if diag_enabled and diagnostic_info is not None and contract_mode == "hud":
            data["diagnostic"] = diagnostic_info

        # 顶层 ETag：纳入用户、导航指纹、默认路由、特性开关、可用意图
        top_etag = stable_etag({
            "user": data["user"],
            "nav_fp": nav_fp,
            "default_route": data["default_route"],
            "feature_flags": data["feature_flags"],
            "intents": data["intents"],
            "scenes": data.get("scenes"),
            "scene_channel": data.get("scene_channel"),
            "scene_contract_ref": data.get("scene_contract_ref"),
            "capabilities": data.get("capabilities"),
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
        })

        return {"status": "success", "data": data, "meta": {**meta, "etag": top_etag}, "ok": True}
