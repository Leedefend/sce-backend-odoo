# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/load_contract.py
from ..core.base_handler import BaseIntentHandler
from ..core.load_contract_entry_context import (
    infer_view_types_from_entry_context,
    normalize_requested_include_parts,
    normalize_request_flags,
    normalize_requested_view_types,
    resolve_model_from_entry_context,
)
from ..core.native_view_contract_projection import inject_primary_view_projection
from ..app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from ..core.platform_policy_defaults import get_model_code_mapping
from odoo import api, SUPERUSER_ID
import json, hashlib

VALID_VIEWS   = {'form','tree','kanban','search','pivot','graph','calendar','gantt','activity','dashboard'}
VALID_INCLUDE = {'model','view','action','permission'}

def _json(obj):
    return json.dumps(obj, ensure_ascii=False, default=str, separators=(",",":"))

def _convert_model_code(code: str, env=None) -> str:
    mapping = {
        'partner':'res.partner','product':'product.product',
        'user':'res.users','company':'res.company',
        'order':'sale.order','invoice':'account.move','employee':'hr.employee',
    }
    if env is not None:
        ext = get_model_code_mapping(env)
        if isinstance(ext, dict):
            for key, value in ext.items():
                k = str(key or "").strip()
                v = str(value or "").strip()
                if k and v:
                    mapping[k] = v
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
        code = _convert_model_code(raw_model, self.env)
        if "." not in code and "_" in code:
            code = code.replace("_", ".")
        model_name = code

        # 模型存在性
        if not self._model_exists(model_name):
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

        try:
            view_types = normalize_requested_view_types(
                view_type_raw,
                inferred_view_types=self._infer_view_types(menu_id=menu_id, action_id=action_id),
                valid_views=VALID_VIEWS,
                default_view_type="tree",
            )
        except ValueError as exc:
            invalid_view = str(exc).split(":", 1)[-1].strip() or "unknown"
            return self._err(400, f"不支持的 view_type: {invalid_view}")

        # 最终形式：多个用列表，单个用字符串
        view_type_final = view_types if len(view_types) > 1 else (view_types[0] if view_types else "form")


        # ---------- 3) include ----------
        include_parts = normalize_requested_include_parts(
            p.get("include", "all"),
            valid_include=VALID_INCLUDE,
        )
        if not include_parts:
            return self._err(400, "include 无效，应为 all 或 model,view,action,permission 组合")

        # ---------- 4) 其它参数 ----------
        request_flags = normalize_request_flags(p)
        force_refresh = request_flags["force_refresh"]
        client_version = request_flags["client_version"]
        if_none_match = request_flags["if_none_match"]

        # ---------- 5) 上下文透传（lang/tz/company） ----------
        ctx_user = dict(self.env.context or {})
        if p.get("lang"): ctx_user["lang"] = p["lang"]
        if p.get("tz"):   ctx_user["tz"]   = p["tz"]
        if p.get("company_id"):
            try: ctx_user["allowed_company_ids"] = [int(p["company_id"])]
            except Exception: pass

        # ---------- 6) 生成契约（按当前用户权限，不 sudo） ----------
        result = self._generate_contract(
            model_name=model_name,
            view_type=view_type_final,
            include_parts=include_parts,
            force_refresh=force_refresh,
            client_version=client_version,
            menu_id=menu_id,
            action_id=action_id,
            ctx_user=ctx_user,
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

    def _model_exists(self, model_name: str) -> bool:
        name = str(model_name or "").strip()
        if not name:
            return False
        registry = getattr(self.env, "registry", None)
        try:
            if registry is not None and getattr(registry, "get", None):
                if registry.get(name):
                    return True
        except Exception:
            pass
        try:
            self.env[name]
            return True
        except Exception:
            return False

    def _generate_contract(
        self,
        *,
        model_name: str,
        view_type,
        include_parts,
        force_refresh: bool,
        client_version: str,
        menu_id,
        action_id,
        ctx_user: dict,
    ) -> dict:
        try:
            svc = self.env["app.contract.service"].with_context(ctx_user)
        except KeyError:
            svc = None

        if svc is not None and hasattr(svc, "generate_contract"):
            return svc.generate_contract(
                model_name=model_name,
                view_type=view_type,
                include_parts=include_parts,
                force_refresh=force_refresh,
                client_version=client_version,
                menu_id=menu_id,
                action_id=action_id,
            ) or {}

        runtime_env = api.Environment(self.env.cr, self.env.uid, dict(ctx_user or {}))
        runtime_su_env = api.Environment(runtime_env.cr, SUPERUSER_ID, dict(runtime_env.context or {}))
        dispatcher = ActionDispatcher(runtime_env, runtime_su_env)
        data, versions = dispatcher.dispatch(
            {
                "subject": "model",
                "model": model_name,
                "view_type": view_type,
                "menu_id": menu_id,
                "action_id": action_id,
                "include": ",".join(sorted(include_parts)) if isinstance(include_parts, set) else include_parts,
                "force_refresh": force_refresh,
                "version": client_version,
            }
        )
        return {
            "status": "success",
            "data": data or {},
            "meta": versions or {},
        }

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
                return {
                    "filters": [],
                    "group_by": [],
                    "search_fields": [],
                    "search_panel": {"enabled": False, "sections": []},
                    "favorites": {"enabled": False, "items": []},
                }

            filters = _normalize_search_items(raw_search.get("filters"), "filter")
            group_by = _normalize_search_items(raw_search.get("group_by"), "group_by")
            search_fields = _normalize_search_items(raw_search.get("fields"), "search_field")
            search_panel_raw = raw_search.get("search_panel") if isinstance(raw_search.get("search_panel"), dict) else {}
            search_panel = {
                "enabled": bool(search_panel_raw.get("enabled", False)),
                "sections": search_panel_raw.get("sections") if isinstance(search_panel_raw.get("sections"), list) else [],
            }

            favorites_raw = raw_search.get("favorites") if isinstance(raw_search.get("favorites"), dict) else {}
            favorite_items = _normalize_search_items(favorites_raw.get("items"), "favorite")
            favorites = {
                "enabled": bool(favorites_raw.get("enabled", False)),
                "items": favorite_items,
            }

            return {
                "filters": filters,
                "group_by": group_by,
                "search_fields": search_fields,
                "search_panel": search_panel,
                "favorites": favorites,
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
                "group_by_field": str(kanban_view.get("default_group_by") or stage_field or ""),
                "card_fields": card_fields,
                "metric_fields": metric_fields,
                "quick_action_count": len(kanban_view.get("quick_actions") if isinstance(kanban_view.get("quick_actions"), list) else []),
                "support_tier": "lightweight",
            }

        def _extract_form_semantics(form_view):
            if not isinstance(form_view, dict):
                return None
            layout = form_view.get("layout") if isinstance(form_view.get("layout"), list) else []
            field_modifiers = form_view.get("field_modifiers") if isinstance(form_view.get("field_modifiers"), dict) else {}
            subviews = form_view.get("subviews") if isinstance(form_view.get("subviews"), dict) else {}

            relation_items = []
            for field_name, sv in subviews.items():
                if not isinstance(sv, dict):
                    continue
                field_meta = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
                policies = sv.get("policies") if isinstance(sv.get("policies"), dict) else {}
                inline_edit = bool(policies.get("inline_edit"))
                relation_items.append({
                    "field": field_name,
                    "relation_model": str(field_meta.get("relation") or ""),
                    "field_type": str(field_meta.get("type") or ""),
                    "preferred_view_type": "tree" if isinstance(sv.get("tree"), dict) else ("form" if isinstance(sv.get("form"), dict) else ""),
                    "editable": {
                        "inline_edit": inline_edit,
                        "can_create": bool(policies.get("can_create", True)),
                        "can_unlink": bool(policies.get("can_unlink", True)),
                    },
                    "takeover_hint": "native" if inline_edit else "frontend",
                })

            behavior_map = {}
            for field_name, modifier in field_modifiers.items():
                if not isinstance(modifier, dict):
                    continue
                behavior_map[field_name] = {
                    "readonly": bool(modifier.get("readonly")),
                    "required": bool(modifier.get("required")),
                    "invisible": bool(modifier.get("invisible")),
                    "widget": str(modifier.get("widget") or ""),
                    "has_domain": "domain" in modifier and modifier.get("domain") not in (None, [], ""),
                    "has_context": "context" in modifier and modifier.get("context") not in (None, {}, ""),
                }
            for relation in relation_items:
                field_name = str(relation.get("field") or "")
                if field_name and field_name not in behavior_map:
                    behavior_map[field_name] = {
                        "readonly": False,
                        "required": False,
                        "invisible": False,
                        "widget": "",
                        "has_domain": False,
                        "has_context": False,
                    }

            return {
                "layout_section_count": len(layout),
                "has_statusbar": isinstance(form_view.get("statusbar"), dict) and bool(form_view.get("statusbar")),
                "has_notebook": any(isinstance(node, dict) and node.get("type") == "notebook" for node in layout),
                "has_chatter": isinstance(form_view.get("chatter"), dict) and bool(form_view.get("chatter")),
                "has_attachments": isinstance(form_view.get("attachments"), dict) and bool(form_view.get("attachments")),
                "relation_fields": relation_items,
                "field_behavior_map": behavior_map,
            }

        def _extract_list_semantics(tree_view, *, toolbar_actions):
            if not isinstance(tree_view, dict):
                return None
            capabilities = tree_view.get("capabilities") if isinstance(tree_view.get("capabilities"), dict) else {}
            columns_schema = tree_view.get("columns_schema") if isinstance(tree_view.get("columns_schema"), list) else []
            row_actions = tree_view.get("row_actions") if isinstance(tree_view.get("row_actions"), list) else []
            normalized_columns = []
            for col in columns_schema:
                if not isinstance(col, dict):
                    continue
                normalized_columns.append({
                    "name": str(col.get("name") or ""),
                    "widget": str(col.get("widget") or ""),
                    "optional": str(col.get("optional") or ""),
                    "readonly": bool(col.get("readonly")),
                    "invisible": bool(col.get("invisible") or col.get("column_invisible")),
                    "has_sum": bool(col.get("sum")),
                })

            return {
                "columns": normalized_columns,
                "default_order": str(tree_view.get("default_order") or ""),
                "page_size": int(tree_view.get("page_size") or 50),
                "editable": {
                    "inline_edit": bool(capabilities.get("inline_edit")),
                    "can_create": bool(capabilities.get("can_create", True)),
                    "can_delete": bool(capabilities.get("can_delete", True)),
                },
                "row_action_keys": [str(item.get("name") or item.get("key") or "") for item in row_actions if isinstance(item, dict)],
                "toolbar_action_count": len(toolbar_actions),
                "supports_export_current_result": True,
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

        closed_states = {"done", "closed", "cancel", "cancelled", "archived"}
        state_field = ""
        state_value = ""
        state_source = "unknown"

        raw_record_state = data.get("record_state") if isinstance(data.get("record_state"), dict) else {}
        if raw_record_state:
            state_field = str(raw_record_state.get("field") or "")
            state_value = str(raw_record_state.get("value") or "")
            state_source = "record_state"
        elif head.get("state"):
            state_field = "state"
            state_value = str(head.get("state") or "")
            state_source = "head"

        def _action_requires_write(action_key: str) -> bool:
            lowered = str(action_key or "").lower()
            write_tokens = ("edit", "write", "save", "create", "unlink", "delete", "archive")
            return any(token in lowered for token in write_tokens)

        def _with_action_gate(action: dict):
            if not isinstance(action, dict):
                return action
            key = str(action.get("key") or "")
            requires_write = _action_requires_write(key)
            permission_allowed = bool(permission_verdicts["write"]["allowed"]) if requires_write else bool(permission_verdicts["execute"]["allowed"])
            is_closed_state = str(state_value).lower() in closed_states if state_value else False
            state_blocked = is_closed_state and requires_write
            current_enabled = bool(action.get("enabled", True))
            allowed = bool(current_enabled and permission_allowed and not state_blocked)
            reason_code = "OK"
            reason = ""
            if not allowed:
                if not current_enabled:
                    reason_code = str(action.get("reason_code") or "DISABLED")
                    reason = str(action.get("reason") or "")
                elif not permission_allowed:
                    reason_code = "PERMISSION_DENIED"
                    reason = "permission denied"
                elif state_blocked:
                    reason_code = "STATE_BLOCKED"
                    reason = "record state blocks action"

            return {
                **action,
                "enabled": allowed,
                "reason_code": reason_code,
                "reason": reason,
                "gate": {
                    "allowed": allowed,
                    "requires_write": requires_write,
                    "state_blocked": state_blocked,
                    "reason_code": reason_code,
                },
            }

        def _with_action_gate_list(items):
            return [_with_action_gate(item) for item in items if isinstance(item, dict)]

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
                statusbar = form_view.get("statusbar") if isinstance(form_view.get("statusbar"), dict) else {}
                _add_zone("summary_zone", {"type": "status_block", "data": statusbar})
                if statusbar and not state_value:
                    state_field = str(statusbar.get("field") or statusbar.get("name") or state_field)
                    state_value = str(statusbar.get("value") or statusbar.get("current") or state_value)
                    state_source = "statusbar"
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
                        "row_actions": _with_action_gate_list([
                            {"key": "open", "label": "打开", "enabled": True, "reason_code": "OK"},
                            {"key": "create", "label": "新增", "enabled": can_create, "reason_code": "OK" if can_create else "PERMISSION_DENIED"},
                            {"key": "unlink", "label": "移除", "enabled": can_unlink, "reason_code": "OK" if can_unlink else "PERMISSION_DENIED"},
                        ]),
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
            _add_zone("detail_zone", {"type": "relation_table_block", "data": {"columns": tree_columns, "row_actions": _with_action_gate_list(tree_row_actions)}})

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
                    "data": dict(kanban_view, card_actions=_with_action_gate_list(kanban_card_actions), kanban_semantics=kanban_semantics or {}),
                },
            )

        search_semantics = _extract_search_semantics(search)
        if search:
            _add_zone("action_zone", {"type": "action_bar_block", "data": {"search": search, "search_semantics": search_semantics}})

        model_name = str(head.get("model") or data.get("model") or "")
        view_type = str(head.get("view_type") or "")
        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        normalized_buttons = _with_action_gate_list(_normalize_action_list(buttons, default_prefix="button"))
        toolbar_actions = []
        if isinstance(toolbar, dict):
            toolbar_actions.extend(toolbar.get("header") if isinstance(toolbar.get("header"), list) else [])
            toolbar_actions.extend(toolbar.get("sidebar") if isinstance(toolbar.get("sidebar"), list) else [])
            toolbar_actions.extend(toolbar.get("footer") if isinstance(toolbar.get("footer"), list) else [])
        normalized_toolbar_actions = _with_action_gate_list(_normalize_action_list(toolbar_actions, default_prefix="toolbar"))
        normalized_header_actions = _with_action_gate_list(normalized_header_actions)
        form_semantics = _extract_form_semantics(views.get("form"))
        list_semantics = _extract_list_semantics(views.get("tree"), toolbar_actions=normalized_toolbar_actions)

        is_closed_state = str(state_value).lower() in closed_states if state_value else False
        action_gating = {
            "record_state": {
                "field": state_field,
                "value": state_value,
                "source": state_source,
            },
            "policy": {
                "closed_states": sorted(closed_states),
            },
            "verdict": {
                "is_closed_state": is_closed_state,
                "reason_code": "STATE_BLOCKED" if is_closed_state else "OK",
            },
        }

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

        capability_profile = self._build_view_capability_profile(
            model_name=model_name,
            primary_view_type=view_type,
            views=views,
            fields=fields,
            permissions=permissions,
            search_semantics=search_semantics,
            kanban_semantics=kanban_semantics,
            head=head,
            data=data,
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
            "action_gating": action_gating,
            "form_semantics": form_semantics,
            "list_semantics": list_semantics,
            "search_semantics": search_semantics,
            "kanban_semantics": kanban_semantics,
            "capability_profile": capability_profile,
            "actions": {
                "buttons": buttons,
                "toolbar": toolbar_actions,
                "header_actions": normalized_header_actions,
                "record_actions": normalized_buttons,
                "toolbar_actions": normalized_toolbar_actions,
            },
            "zones": zones,
        }
        native_view = data.get("native_view")
        if isinstance(native_view, dict):
            native_view["render_policy"] = capability_profile.get("render_policy")

        inject_primary_view_projection(data, requested_view_type=(head.get("view_type") if isinstance(head, dict) else None))

    def _build_view_capability_profile(
        self,
        *,
        model_name: str,
        primary_view_type: str,
        views: dict,
        fields: dict,
        permissions: dict,
        search_semantics: dict,
        kanban_semantics: dict | None,
        head: dict,
        data: dict,
    ) -> dict:
        profiles = {}
        if isinstance(views.get("form"), dict):
            profiles["form"] = self._classify_form_view_profile(views.get("form") or {}, fields=fields)
        if isinstance(views.get("tree"), dict):
            profiles["tree"] = self._classify_tree_view_profile(
                views.get("tree") or {},
                search_semantics=search_semantics,
            )
        if isinstance(views.get("kanban"), dict):
            profiles["kanban"] = self._classify_kanban_view_profile(
                views.get("kanban") or {},
                kanban_semantics=kanban_semantics,
            )

        resolved_primary = str(primary_view_type or "").strip()
        if not resolved_primary or resolved_primary not in profiles:
            for candidate in ("form", "tree", "kanban"):
                if candidate in profiles:
                    resolved_primary = candidate
                    break

        primary_profile = profiles.get(resolved_primary) or {
            "view_type": resolved_primary or "unknown",
            "takeover_class": "native_retained",
            "support_tier": "native_only",
            "recommended_runtime": "native",
            "supported_features": [],
            "conditional_features": [],
            "unsupported_features": [],
            "fallback_triggers": ["missing_view_profile"],
            "reason_codes": ["VIEW_PROFILE_MISSING"],
            "notes": ["missing profile for requested primary view"],
        }

        fallback_action = self._build_open_native_action(
            model_name=model_name,
            primary_view_type=resolved_primary or primary_view_type or "",
            permissions=permissions,
            head=head,
            data=data,
        )

        return {
            "version": "v1",
            "policy": "frontend_takeover_scope_v1",
            "primary_view_type": resolved_primary or primary_view_type or "",
            "view_profiles": profiles,
            "render_policy": {
                "takeover_class": primary_profile.get("takeover_class"),
                "support_tier": primary_profile.get("support_tier"),
                "recommended_runtime": primary_profile.get("recommended_runtime"),
                "reason_codes": primary_profile.get("reason_codes") if isinstance(primary_profile.get("reason_codes"), list) else [],
                "fallback_action": fallback_action,
            },
            "fallback_strategy": {
                "action_key": "open_native",
                "fallback_triggers": primary_profile.get("fallback_triggers") if isinstance(primary_profile.get("fallback_triggers"), list) else [],
                "notes": primary_profile.get("notes") if isinstance(primary_profile.get("notes"), list) else [],
            },
        }

    def _classify_form_view_profile(self, form_view: dict, *, fields: dict) -> dict:
        supported_features = [
            "field_groups",
            "notebook_tabs",
            "header_actions",
            "stat_buttons",
            "statusbar_basic",
            "attachments_chatter",
            "simple_x2many_display",
            "save_edit_cycle",
            "field_modifiers_basic",
            "field_behavior_map",
        ]
        conditional_features = []
        unsupported_features = [
            "full_domain_context_options_parity",
            "lossless_complex_arch_rebuild",
            "complex_modifier_linkage",
        ]
        fallback_triggers = []
        reason_codes = ["FORM_STANDARD_CHAIN"]
        notes = ["standard form chain is supported, but not full native parity"]

        subviews = form_view.get("subviews") if isinstance(form_view.get("subviews"), dict) else {}
        has_inline_edit = False
        for field_name, subview in subviews.items():
            if not isinstance(subview, dict):
                continue
            policies = subview.get("policies") if isinstance(subview.get("policies"), dict) else {}
            if bool(policies.get("inline_edit")):
                has_inline_edit = True
                conditional_features.append(f"{field_name}:inline_edit")

        if has_inline_edit:
            unsupported_features.append("complex_one2many_inline_edit")
            fallback_triggers.append("one2many_inline_edit")
            reason_codes.append("FORM_INLINE_SUBVIEW_NATIVE_FALLBACK")
            notes.append("inline editable x2many subviews should fallback to native in v1")

        return {
            "view_type": "form",
            "takeover_class": "conditional_takeover" if has_inline_edit else "frontend_takeover",
            "support_tier": "standard",
            "recommended_runtime": "native" if has_inline_edit else "frontend",
            "supported_features": supported_features,
            "conditional_features": conditional_features,
            "unsupported_features": unsupported_features,
            "fallback_triggers": fallback_triggers,
            "reason_codes": reason_codes,
            "notes": notes,
        }

    def _classify_tree_view_profile(self, tree_view: dict, *, search_semantics: dict) -> dict:
        supported_features = [
            "column_order",
            "default_sort",
            "basic_search",
            "basic_filters",
            "grouping",
            "pagination",
            "row_open",
            "multi_select",
            "basic_batch_actions",
            "basic_toolbar_actions",
            "status_badges_basic",
            "export_current_result",
        ]
        conditional_features = []
        unsupported_features = []
        fallback_triggers = []
        reason_codes = ["TREE_STANDARD_CHAIN"]
        notes = ["standard list chain is supported, but advanced search ecosystem is incomplete"]

        capabilities = tree_view.get("capabilities") if isinstance(tree_view.get("capabilities"), dict) else {}
        if bool(capabilities.get("inline_edit")):
            unsupported_features.append("tree_inline_edit")
            fallback_triggers.append("tree_inline_edit")
            reason_codes.append("TREE_INLINE_EDIT_NATIVE_FALLBACK")
            notes.append("editable tree/list should fallback to native in v1")

        if isinstance(search_semantics, dict):
            search_panel = search_semantics.get("search_panel") if isinstance(search_semantics.get("search_panel"), dict) else {}
            favorites = search_semantics.get("favorites") if isinstance(search_semantics.get("favorites"), dict) else {}
            if bool(search_panel.get("enabled")):
                unsupported_features.append("searchpanel_full_ecosystem")
                fallback_triggers.append("searchpanel_enabled")
                reason_codes.append("TREE_SEARCHPANEL_NATIVE_FALLBACK")
            if bool(favorites.get("enabled")):
                unsupported_features.append("favorites_full_ecosystem")
                fallback_triggers.append("favorites_enabled")
                reason_codes.append("TREE_FAVORITES_NATIVE_FALLBACK")

        return {
            "view_type": "tree",
            "takeover_class": "conditional_takeover" if fallback_triggers else "frontend_takeover",
            "support_tier": "standard",
            "recommended_runtime": "native" if fallback_triggers else "frontend",
            "supported_features": supported_features,
            "conditional_features": conditional_features,
            "unsupported_features": unsupported_features,
            "fallback_triggers": fallback_triggers,
            "reason_codes": reason_codes,
            "notes": notes,
        }

    def _classify_kanban_view_profile(self, kanban_view: dict, *, kanban_semantics: dict | None) -> dict:
        supported_features = [
            "card_title",
            "card_summary_fields",
            "simple_grouping",
            "quick_actions_basic",
            "status_semantics_basic",
            "lightweight_card_grid",
            "group_by_field",
        ]
        unsupported_features = [
            "drag_drop",
            "swimlane_fidelity",
            "badge_tag_progress_hints",
            "deep_template_consumption",
        ]
        reason_codes = ["KANBAN_LIGHTWEIGHT_CHAIN"]
        notes = ["kanban is supported only as a lightweight card surface in v1"]
        fallback_triggers = []

        if not isinstance(kanban_semantics, dict) or not str(kanban_semantics.get("title_field") or "").strip():
            fallback_triggers.append("kanban_semantics_missing")
            reason_codes.append("KANBAN_SEMANTICS_MISSING")
            notes.append("missing kanban semantics should fallback to native")

        if not isinstance(kanban_view.get("fields"), list) or not (kanban_view.get("fields") or []):
            fallback_triggers.append("kanban_fields_missing")
            reason_codes.append("KANBAN_FIELDS_MISSING")

        return {
            "view_type": "kanban",
            "takeover_class": "conditional_takeover",
            "support_tier": "lightweight",
            "recommended_runtime": "native" if fallback_triggers else "frontend",
            "supported_features": supported_features,
            "conditional_features": [],
            "unsupported_features": unsupported_features,
            "fallback_triggers": fallback_triggers,
            "reason_codes": reason_codes,
            "notes": notes,
        }

    def _build_open_native_action(self, *, model_name: str, primary_view_type: str, permissions: dict, head: dict, data: dict) -> dict:
        allowed = bool((permissions or {}).get("read", False))
        action_payload = {
            "model": model_name,
            "view_type": primary_view_type,
        }
        for key in ("menu_id", "action_id", "res_id"):
            value = data.get(key)
            if value in (None, "", False):
                value = head.get(key) if isinstance(head, dict) else None
            if value not in (None, "", False):
                action_payload[key] = value

        return {
            "key": "open_native",
            "label": "打开原生页面",
            "type": "intent",
            "intent": "open_native",
            "enabled": allowed,
            "reason_code": "OK" if allowed else "PERMISSION_DENIED",
            "reason": "" if allowed else "permission denied",
            "payload": action_payload,
        }

    # ---------- 辅助：从 menu_id / action_id 推导 res_model ----------
    def _resolve_model_from_context(self, menu_id=None, action_id=None) -> str | None:
        return resolve_model_from_entry_context(
            self.env,
            su_env=self.su_env,
            menu_id=menu_id,
            action_id=action_id,
        )

    # 统一错误
    def _err(self, code, msg):
        return {"status":"error","code":code,"message":msg,"data":None}
    
    # 放在类里（LoadContractHandler）作为私有方法
    def _infer_view_types(self, menu_id=None, action_id=None):
        """从菜单/动作推断默认 view_types（返回列表），失败返回 []"""
        return infer_view_types_from_entry_context(
            self.env,
            su_env=self.su_env,
            menu_id=menu_id,
            action_id=action_id,
            valid_views=VALID_VIEWS,
        )
