# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/load_contract.py
from ..core.base_handler import BaseIntentHandler
from odoo import api, SUPERUSER_ID
import json, re, hashlib

VALID_VIEWS   = {'form','tree','kanban','search','pivot','graph','calendar','gantt','activity','dashboard'}
VALID_INCLUDE = {'model','view','action','permission'}

def _json(obj):
    return json.dumps(obj, ensure_ascii=False, default=str, separators=(",",":"))

def _convert_model_code(code: str) -> str:
    mapping = {
        'partner':'res.partner','product':'product.product','project':'project.project',
        'task':'project.task','user':'res.users','company':'res.company',
        'order':'sale.order','invoice':'account.move','employee':'hr.employee',
    }
    return mapping.get(code, code)

class LoadContractHandler(BaseIntentHandler):
    """
    intent: load_contract   （推荐，完整契约）
    alias : load_view       （兼容旧前端）
    params:
      - model | model_code   ⭐ 至少其一；缺省时可通过 menu_id / action_id 推导
      - menu_id?, action_id?
      - view_type?           "form" | "tree,form" | ["tree","form"] ...
      - include?             "all" | "model,view,action,permission"
      - force_refresh?       bool
      - version?, if_none_match?, lang?, tz?, company_id?
    """
    INTENT_TYPE  = "load_contract"
    DESCRIPTION  = "拉取聚合契约（view/model/permission/action），用于前端自动页"
    REQUIRED_GROUPS = []  # 登录用户可用

    # 旧别名
    @classmethod
    def aliases(cls):
        return ["load_view"]

    # ✅ 与框架对齐：覆写 handle，而不是 run
    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        # 兼容两种形态：payload={"params":{...}} 或 payload 直接就是 params
        p = payload.get("params") if isinstance(payload, dict) and "params" in payload else payload
        p = p or {}

        # ---------- 1) 解析模型 ----------
        raw_model = (p.get("model") or p.get("model_code") or "").strip()
        menu_id   = p.get("menu_id")
        action_id = p.get("action_id")

        if not raw_model:
            # 尝试从 menu_id / action_id 推导
            raw_model = self._resolve_model_from_context(menu_id=menu_id, action_id=action_id) or ""

        if not raw_model:
            return self._err(400, "缺少参数 model 或 model_code，且无法从 menu_id / action_id 推导")

        # 别名映射与常规化
        code = _convert_model_code(raw_model)
        if "." not in code and "_" in code:
            code = code.replace("_", ".")
        model_name = code

        # 模型存在性
        if not self.env.get(model_name):
            # 在 return 404 前追加：
            try:
                mod = self.env["ir.module.module"].sudo().search([("name","=","project")], limit=1)
                mod_state = mod.state if mod else "not found"
            except Exception:
                mod_state = "unknown"

            return self._err(
                404,
                f"未知模型: {model_name or (raw_model or '').strip()} "
                f"(db={self.env.cr.dbname}, module(project)={mod_state})"
            )

        # ---------- 3) 视图类型 ----------
        view_type_raw = p.get("view_type", None)


        # ---------- 2) 视图类型 ----------
        view_type_raw = p.get("view_type", None)  # 改：不立刻默认 "form"
        view_types: list[str] = []

        if isinstance(view_type_raw, (list, tuple)):
            parts = [str(v).strip().lower() for v in view_type_raw]
        elif isinstance(view_type_raw, str) and view_type_raw.strip():
            parts = re.split(r'[,\s]+', view_type_raw.strip())
        else:
            # 前端没传：尝试从菜单/动作推断
            parts = self._infer_view_types(menu_id=menu_id, action_id=action_id)
            if not parts:
                parts = ["tree"]  # 仍然兜底 tree

        # 过滤到白名单并保序去重
        seen = set()
        for v in parts:
            if not v:
                continue
            if v not in VALID_VIEWS:
                return self._err(400, f"不支持的 view_type: {v}")
            if v not in seen:
                seen.add(v)
                view_types.append(v)

        # 最终形式：多个用列表，单个用字符串
        view_type_final = view_types if len(view_types) > 1 else (view_types[0] if view_types else "form")


        # ---------- 3) include ----------
        include_raw = str(p.get("include", "all")).strip().lower()
        if include_raw == "all":
            include_parts = set(VALID_INCLUDE)
        else:
            include_parts = set(x.strip() for x in include_raw.split(",")) & VALID_INCLUDE
        if not include_parts:
            return self._err(400, "include 无效，应为 all 或 model,view,action,permission 组合")

        # ---------- 4) 其它参数 ----------
        force_refresh   = str(p.get("force_refresh","")).lower() in ("1","true","yes")
        client_version  = (p.get("version") or "").strip()
        if_none_match   = (p.get("if_none_match") or "").strip().strip('"')

        # ---------- 5) 上下文透传（lang/tz/company） ----------
        ctx_user = dict(self.env.context or {})
        if p.get("lang"): ctx_user["lang"] = p["lang"]
        if p.get("tz"):   ctx_user["tz"]   = p["tz"]
        if p.get("company_id"):
            try: ctx_user["allowed_company_ids"] = [int(p["company_id"])]
            except Exception: pass

        # ---------- 6) 生成契约（按当前用户权限，不 sudo） ----------
        svc = self.env["app.contract.service"].with_context(ctx_user)
        result = svc.generate_contract(
            model_name=model_name,
            view_type=view_type_final,
            include_parts=include_parts,
            force_refresh=force_refresh,
            client_version=client_version,
            # 可选：把 menu_id/action_id 也传入，便于服务侧做面包屑/默认动作
            menu_id=menu_id,
            action_id=action_id,
        ) or {}

        status = result.get("status","success")
        data   = result.get("data",{}) or {}
        meta   = result.get("meta",{}) or {}

        # ---------- 6.x) 统一语义契约补充（非破坏式） ----------
        # 保留现有 head/views/fields/search/... 结构，新增 native_view + semantic_page。
        self._inject_semantic_contract(data)

        # ---------- 7) 计算聚合 ETag ----------
        etag_source = _json({
            "view_hash":    meta.get("view_hash"),
            "model_hash":   meta.get("model_hash"),
            "perm_key":     meta.get("perm_key"),
            "action_hash":  meta.get("action_hash"),
            "schema_version": meta.get("schema_version"),
            "uid": self.env.user.id,
            "co":  self.env.company.id,
            "lang": ctx_user.get("lang"),
        })
        etag = hashlib.sha1(etag_source.encode("utf-8")).hexdigest()

        # ---------- 8) If-None-Match → 304 语义 ----------
        if if_none_match and if_none_match == etag and not force_refresh:
            return {"status": "not_modified", "code": 304, "data": None, "meta": {"etag": etag}}

        meta_out = dict(meta); meta_out["etag"] = etag
        return {"status": status, "code": 200, "data": data, "meta": meta_out}

    def _inject_semantic_contract(self, data: dict):
        if not isinstance(data, dict):
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        search = data.get("search") if isinstance(data.get("search"), dict) else {}
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        permissions = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}

        if "native_view" not in data:
            data["native_view"] = {
                "views": views,
                "search": search,
                "toolbar": toolbar,
            }

        if "semantic_page" in data and isinstance(data.get("semantic_page"), dict):
            return

        zones = []

        def _add_zone(zone_key, block):
            for zone in zones:
                if zone.get("key") == zone_key:
                    blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
                    blocks.append(block)
                    zone["blocks"] = blocks
                    return
            zones.append({"key": zone_key, "blocks": [block]})

        def _normalize_action(raw, fallback_key="", fallback_label=""):
            if isinstance(raw, str):
                key = raw.strip() or fallback_key or "action"
                return {
                    "key": key,
                    "label": fallback_label or key,
                    "type": "action",
                    "enabled": True,
                    "reason_code": "OK",
                }
            if not isinstance(raw, dict):
                return None

            key = str(
                raw.get("key")
                or raw.get("name")
                or raw.get("xml_id")
                or raw.get("xmlid")
                or raw.get("id")
                or fallback_key
                or "action"
            )
            label = str(raw.get("label") or raw.get("string") or fallback_label or key)
            action_type = str(raw.get("action_type") or raw.get("type") or "action")
            enabled = bool(raw.get("enabled", True))
            reason_code = str(raw.get("reason_code") or ("OK" if enabled else "DISABLED"))
            reason = str(raw.get("reason") or "")
            return {
                "key": key,
                "label": label,
                "type": action_type,
                "enabled": enabled,
                "reason_code": reason_code,
                "reason": reason,
            }

        def _normalize_action_list(items, default_prefix="action"):
            normalized = []
            if not isinstance(items, list):
                return normalized
            for index, item in enumerate(items):
                action = _normalize_action(item, fallback_key=f"{default_prefix}_{index + 1}")
                if action:
                    normalized.append(action)
            return normalized

        def _normalize_search_items(items, default_prefix):
            normalized = []
            if not isinstance(items, list):
                return normalized
            for index, item in enumerate(items):
                if isinstance(item, str):
                    key = item.strip() or f"{default_prefix}_{index + 1}"
                    normalized.append({"key": key, "label": key})
                    continue
                if not isinstance(item, dict):
                    continue
                key = str(item.get("key") or item.get("name") or f"{default_prefix}_{index + 1}")
                label = str(item.get("label") or item.get("string") or key)
                normalized.append({
                    "key": key,
                    "label": label,
                    "domain": item.get("domain") if isinstance(item.get("domain"), list) else None,
                })
            return normalized

        def _extract_search_semantics(raw_search):
            if not isinstance(raw_search, dict):
                return {"filters": [], "group_by": [], "search_fields": [], "search_panel": {"enabled": False}}

            filters = _normalize_search_items(raw_search.get("filters"), "filter")
            group_by = _normalize_search_items(raw_search.get("group_by"), "group_by")
            search_fields = _normalize_search_items(raw_search.get("fields"), "search_field")
            search_panel_raw = raw_search.get("search_panel") if isinstance(raw_search.get("search_panel"), dict) else {}
            search_panel = {
                "enabled": bool(search_panel_raw.get("enabled", False)),
                "sections": search_panel_raw.get("sections") if isinstance(search_panel_raw.get("sections"), list) else [],
            }

            return {
                "filters": filters,
                "group_by": group_by,
                "search_fields": search_fields,
                "search_panel": search_panel,
                "quick_filters": filters[:4],
            }

        def _extract_kanban_semantics(kanban_view):
            if not isinstance(kanban_view, dict):
                return None
            card_fields = kanban_view.get("fields") if isinstance(kanban_view.get("fields"), list) else []
            profile = kanban_view.get("kanban_profile") if isinstance(kanban_view.get("kanban_profile"), dict) else {}
            title_field = str(profile.get("title_field") or (card_fields[0] if card_fields else "name"))
            stage_field = str(kanban_view.get("stages_field") or profile.get("stage_field") or ("stage_id" if "stage_id" in card_fields else ""))
            subtitle_field = str(profile.get("subtitle_field") or ("manager_id" if "manager_id" in card_fields else ""))

            metric_fields = []
            for field_name in card_fields:
                field_meta = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
                field_type = str(field_meta.get("type") or "")
                if field_type in {"float", "integer", "monetary"}:
                    metric_fields.append(field_name)

            return {
                "title_field": title_field,
                "subtitle_field": subtitle_field,
                "stage_field": stage_field,
                "card_fields": card_fields,
                "metric_fields": metric_fields,
            }

        def _permission_verdict(value):
            allowed = bool(value)
            return {
                "allowed": allowed,
                "reason_code": "OK" if allowed else "PERMISSION_DENIED",
                "reason": "" if allowed else "permission denied",
            }

        permission_verdicts = {
            "read": _permission_verdict(permissions.get("read", False)),
            "create": _permission_verdict(permissions.get("create", False)),
            "write": _permission_verdict(permissions.get("write", False)),
            "unlink": _permission_verdict(permissions.get("unlink", False)),
        }
        permission_verdicts["execute"] = {
            "allowed": bool(permission_verdicts["read"]["allowed"]),
            "reason_code": "OK" if permission_verdicts["read"]["allowed"] else "PERMISSION_DENIED",
            "reason": "" if permission_verdicts["read"]["allowed"] else "permission denied",
        }

        # header_zone
        header_blocks = []
        header_buttons = []
        if isinstance(views.get("form"), dict):
            form_view = views.get("form") or {}
            header_buttons = (form_view.get("header_buttons") or []) + (form_view.get("button_box") or []) + (form_view.get("stat_buttons") or [])
        if header_buttons:
            header_blocks.append({"type": "action_bar_block", "data": {"buttons": header_buttons}})
        if head:
            header_blocks.append({"type": "title_block", "data": head})
        if header_blocks:
            zones.append({"key": "header_zone", "blocks": header_blocks})
        normalized_header_actions = _normalize_action_list(header_buttons, default_prefix="header")

        # detail/relation/collaboration by view
        if isinstance(views.get("form"), dict):
            form_view = views.get("form") or {}
            if form_view.get("statusbar"):
                _add_zone("summary_zone", {"type": "status_block", "data": form_view.get("statusbar")})
            stat_buttons = []
            if isinstance(form_view.get("button_box"), list):
                stat_buttons.extend(form_view.get("button_box") or [])
            if isinstance(form_view.get("stat_buttons"), list):
                stat_buttons.extend(form_view.get("stat_buttons") or [])
            if stat_buttons:
                _add_zone("summary_zone", {"type": "stat_button_block", "data": {"buttons": stat_buttons}})
            if form_view.get("layout"):
                _add_zone("detail_zone", {"type": "field_group_block", "data": {"layout": form_view.get("layout")}})
                # notebook/page 结构作为显式 block 暴露，便于前端稳定识别 tabs 区。
                _add_zone("detail_zone", {"type": "notebook_block", "data": {"layout": form_view.get("layout")}})
            if isinstance(form_view.get("field_modifiers"), dict) and form_view.get("field_modifiers"):
                _add_zone("detail_zone", {"type": "field_group_block", "data": {"field_modifiers": form_view.get("field_modifiers")}})
            if form_view.get("subviews"):
                subviews = form_view.get("subviews") if isinstance(form_view.get("subviews"), dict) else {}
                relation_items = []
                for field_name, sv in subviews.items():
                    if not isinstance(sv, dict):
                        continue
                    field_meta = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
                    field_mod = form_view.get("field_modifiers", {}).get(field_name, {}) if isinstance(form_view.get("field_modifiers"), dict) else {}
                    policies = sv.get("policies") if isinstance(sv.get("policies"), dict) else {}
                    has_tree = isinstance(sv.get("tree"), dict)
                    has_form = isinstance(sv.get("form"), dict)
                    preferred_view = "tree" if has_tree else ("form" if has_form else "tree")
                    inline_edit = bool(policies.get("inline_edit")) if "inline_edit" in policies else (has_tree and not bool(field_mod.get("readonly")))
                    can_create = bool(policies.get("can_create")) if "can_create" in policies else (not bool(field_mod.get("readonly")))
                    can_unlink = bool(policies.get("can_unlink")) if "can_unlink" in policies else (not bool(field_mod.get("readonly")))
                    relation_items.append({
                        "field": field_name,
                        "relation_model": field_meta.get("relation") or "",
                        "field_type": field_meta.get("type") or "",
                        "preferred_view_type": preferred_view,
                        "views": {
                            "tree": sv.get("tree") if has_tree else None,
                            "form": sv.get("form") if has_form else None,
                        },
                        "editable": {
                            "inline_edit": inline_edit,
                            "can_create": can_create,
                            "can_unlink": can_unlink,
                        },
                        "row_actions": [
                            {"key": "open", "label": "打开", "enabled": True, "reason_code": "OK"},
                            {"key": "create", "label": "新增", "enabled": can_create, "reason_code": "OK" if can_create else "PERMISSION_DENIED"},
                            {"key": "unlink", "label": "移除", "enabled": can_unlink, "reason_code": "OK" if can_unlink else "PERMISSION_DENIED"},
                        ],
                    })
                _add_zone("relation_zone", {
                    "type": "relation_table_block",
                    "data": {
                        "subviews": subviews,
                        "items": relation_items,
                    },
                })
            if form_view.get("chatter") or form_view.get("attachments"):
                _add_zone("collaboration_zone", {"type": "chatter_block", "data": form_view.get("chatter") or {}})
                _add_zone("attachment_zone", {"type": "attachment_block", "data": form_view.get("attachments") or {}})

        if isinstance(views.get("tree"), dict):
            tree_view = views.get("tree") or {}
            tree_columns = tree_view.get("columns") or []
            tree_row_actions = [
                {"key": "open", "label": "打开", "enabled": True, "reason_code": "OK"},
                {
                    "key": "edit",
                    "label": "编辑",
                    "enabled": bool(permissions.get("write", False)),
                    "reason_code": "OK" if permissions.get("write") else "PERMISSION_DENIED",
                },
            ]
            _add_zone("detail_zone", {"type": "relation_table_block", "data": {"columns": tree_columns, "row_actions": tree_row_actions}})

        kanban_semantics = None
        if isinstance(views.get("kanban"), dict):
            kanban_view = views.get("kanban") or {}
            kanban_semantics = _extract_kanban_semantics(kanban_view)
            kanban_card_actions = [
                {"key": "open", "label": "查看详情", "enabled": True, "reason_code": "OK"},
                {
                    "key": "edit",
                    "label": "编辑",
                    "enabled": bool(permissions.get("write", False)),
                    "reason_code": "OK" if permissions.get("write") else "PERMISSION_DENIED",
                },
            ]
            _add_zone(
                "detail_zone",
                {
                    "type": "relation_card_block",
                    "data": dict(kanban_view, card_actions=kanban_card_actions, kanban_semantics=kanban_semantics or {}),
                },
            )

        search_semantics = _extract_search_semantics(search)
        if search:
            _add_zone("action_zone", {"type": "action_bar_block", "data": {"search": search, "search_semantics": search_semantics}})

        model_name = str(head.get("model") or data.get("model") or "")
        view_type = str(head.get("view_type") or "")
        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        normalized_buttons = _normalize_action_list(buttons, default_prefix="button")
        toolbar_actions = []
        if isinstance(toolbar, dict):
            toolbar_actions.extend(toolbar.get("header") if isinstance(toolbar.get("header"), list) else [])
            toolbar_actions.extend(toolbar.get("sidebar") if isinstance(toolbar.get("sidebar"), list) else [])
            toolbar_actions.extend(toolbar.get("footer") if isinstance(toolbar.get("footer"), list) else [])
        normalized_toolbar_actions = _normalize_action_list(toolbar_actions, default_prefix="toolbar")

        if normalized_buttons or normalized_toolbar_actions or normalized_header_actions:
            _add_zone(
                "action_zone",
                {
                    "type": "action_bar_block",
                    "data": {
                        "header_actions": normalized_header_actions,
                        "record_actions": normalized_buttons,
                        "toolbar_actions": normalized_toolbar_actions,
                    },
                },
            )

        data["semantic_page"] = {
            "version": "v1",
            "source": "load_contract",
            "model": model_name,
            "view_type": view_type,
            "layout": "auto",
            "header": head,
            "fields": fields,
            "permissions": permissions,
            "permission_verdicts": permission_verdicts,
            "search_semantics": search_semantics,
            "kanban_semantics": kanban_semantics,
            "actions": {
                "buttons": buttons,
                "toolbar": toolbar_actions,
                "header_actions": normalized_header_actions,
                "record_actions": normalized_buttons,
                "toolbar_actions": normalized_toolbar_actions,
            },
            "zones": zones,
        }

    # ---------- 辅助：从 menu_id / action_id 推导 res_model ----------
    def _resolve_model_from_context(self, menu_id=None, action_id=None) -> str | None:
        su_env = self.su_env or api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))
        try:
            if menu_id:
                m = su_env["ir.ui.menu"].browse(int(menu_id))
                act = m.action if m.exists() else None
                if act:
                    # 统一从 action 取 res_model
                    res_model = getattr(act, "res_model", None)
                    if not res_model and act._name == "ir.actions.act_window":
                        res_model = act.res_model
                    if res_model:
                        return str(res_model)
            if action_id and not menu_id:
                act = su_env["ir.actions.actions"].browse(int(action_id))
                if act and act.exists():
                    res_model = getattr(act, "res_model", None)
                    if not res_model and act._name == "ir.actions.act_window":
                        res_model = act.res_model
                    if res_model:
                        return str(res_model)
        except Exception:
            # 静默失败，交由上层报“缺少 model”
            return None
        return None

    # 统一错误
    def _err(self, code, msg):
        return {"status":"error","code":code,"message":msg,"data":None}
    
    # 放在类里（LoadContractHandler）作为私有方法
    def _infer_view_types(self, menu_id=None, action_id=None):
        """从菜单/动作推断默认 view_types（返回列表），失败返回 []"""
        su_env = self.su_env or api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))
        try:
            act = None
            if menu_id:
                m = su_env["ir.ui.menu"].browse(int(menu_id))
                act = m.action if m.exists() else None
            if (not act) and action_id:
                act = su_env["ir.actions.actions"].browse(int(action_id))
            if not act or not act.exists():
                return []
            # 仅 act_window 有 view_mode 概念
            if act._name == "ir.actions.act_window":
                raw = (getattr(act, "view_mode", None) or "").strip()
                if not raw:
                    return []
                parts = [v.strip().lower() for v in raw.split(",") if v.strip()]
                # 交叉到白名单 & 去重保序
                seen, out = set(), []
                for v in parts:
                    if v in VALID_VIEWS and v not in seen:
                        seen.add(v); out.append(v)
                return out
            return []
        except Exception:
            return []
