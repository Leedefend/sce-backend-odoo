# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/load_contract.py
import hashlib
import json
import re

from odoo import SUPERUSER_ID, api

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_positive_int
from ..core.unified_page_contract_lite_preview import with_lite_preview_if_requested
from ..utils.extension_hooks import call_extension_hook_first
from ..utils.reason_codes import REASON_OK, REASON_PERMISSION_DENIED

VALID_VIEWS   = {'form','tree','kanban','search','pivot','graph','calendar','gantt','activity','dashboard'}
VALID_INCLUDE = {'model','view','action','permission'}
REASON_DISABLED = "DISABLED"
REASON_STATE_BLOCKED = "STATE_BLOCKED"

def _json(obj):
    return json.dumps(obj, ensure_ascii=False, default=str, separators=(",",":"))

def _convert_model_code(code: str, env=None) -> str:
    mapping = {
        'partner':'res.partner','product':'product.product',
        'user':'res.users','company':'res.company',
        'order':'sale.order','invoice':'account.move','employee':'hr.employee',
    }
    if env is not None:
        ext = call_extension_hook_first(env, "smart_core_model_code_mapping", env)
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
    SOURCE_KIND = "odoo_native_contract_projection"
    SOURCE_AUTHORITIES = (
        "ir.ui.view",
        "ir.actions.act_window",
        "ir.ui.menu",
        "ir.model.fields",
        "ir.model.access",
        "ir.rule",
    )

    # 旧别名
    @classmethod
    def aliases(cls):
        return ["load_view"]

    def _source_authority_contract(self, model_name: str, view_type):
        view_types = view_type if isinstance(view_type, list) else [view_type]
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model_name or ""),
            "view_types": [str(item or "").strip() for item in view_types if str(item or "").strip()],
            "projection_only": True,
            "rebuildable": True,
        }

    def _optional_text_param(self, params: dict, key: str):
        if key not in params:
            return "", None
        raw = params.get(key)
        if raw is None or raw == "":
            return "", None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{key} 无效")
        return str(raw).strip(), None

    # ✅ 与框架对齐：覆写 handle，而不是 run
    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        # 兼容两种形态：payload={"params":{...}} 或 payload 直接就是 params
        p = payload.get("params") if isinstance(payload, dict) and "params" in payload else payload
        p = p or {}
        if not isinstance(p, dict):
            return self._err(400, "params 无效")

        # ---------- 1) 解析模型 ----------
        raw_model, model_error = self._optional_text_param(p, "model")
        if model_error:
            return model_error
        if not raw_model:
            raw_model, model_code_error = self._optional_text_param(p, "model_code")
            if model_code_error:
                return model_code_error
        menu_id, menu_id_error = parse_positive_int(p.get("menu_id"), allow_empty=True)
        if menu_id_error:
            return self._err(400, "menu_id 无效")
        action_id, action_id_error = parse_positive_int(p.get("action_id"), allow_empty=True)
        if action_id_error:
            return self._err(400, "action_id 无效")

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
        if model_name not in self.env:
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
        client_version, client_version_error = self._optional_text_param(p, "version")
        if client_version_error:
            return client_version_error
        if_none_match, if_none_match_error = self._optional_text_param(p, "if_none_match")
        if if_none_match_error:
            return if_none_match_error
        if_none_match = if_none_match.strip('"')

        # ---------- 5) 上下文透传（lang/tz/company） ----------
        ctx_user = dict(self.env.context or {})
        request_context = p.get("context") if isinstance(p.get("context"), dict) else {}
        if request_context:
            ctx_user.update(request_context)
        current_project_id = (
            p.get("current_project_id")
            if "current_project_id" in p
            else request_context.get("current_project_id")
        )
        project_id_int, project_id_error = parse_positive_int(current_project_id, allow_empty=True)
        if project_id_error:
            return self._err(400, "current_project_id 无效")
        if project_id_int:
            ctx_user["current_project_id"] = project_id_int
            ctx_user.setdefault("default_project_id", project_id_int)
        user_lang = (getattr(self.env.user, "lang", None) or "").strip()
        if p.get("lang"):
            ctx_user["lang"] = p["lang"]
        elif user_lang:
            ctx_user["lang"] = user_lang
        if p.get("tz"):   ctx_user["tz"]   = p["tz"]
        company_id, company_id_error = parse_positive_int(p.get("company_id"), allow_empty=True)
        if company_id_error:
            return self._err(400, "company_id 无效")
        if company_id:
            ctx_user["allowed_company_ids"] = [company_id]
            ctx_user["company_id"] = company_id
        operation_strategy = str(p.get("operation_strategy") or p.get("operationStrategy") or "").strip()
        if operation_strategy:
            ctx_user["operation_strategy"] = operation_strategy

        # ---------- 6) 生成契约（按当前用户权限，不 sudo） ----------
        if "app.contract.service" in self.env:
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
        else:
            result = self._generate_with_ui_contract(
                model_name=model_name,
                view_type=view_type_final,
                menu_id=menu_id,
                action_id=action_id,
                ctx_user=ctx_user,
            )

        status = result.get("status","success")
        data   = result.get("data",{}) or {}
        meta   = result.get("meta",{}) or {}

        # ---------- 6.x) 统一语义契约补充（非破坏式） ----------
        # 保留现有 head/views/fields/search/... 结构，新增 native_view + semantic_page。
        self._ensure_form_auxiliary_slots(data, model_name)
        self._ensure_native_view_field_descriptors(data, model_name)
        self._inject_semantic_contract(data)
        hook_payload = call_extension_hook_first(
            self.env,
            "smart_core_finalize_projected_contract_data",
            self.env,
            data,
            {
                "view_type": view_type_final,
                "subject": "load_contract",
                "meta": meta or {},
            },
        )
        if isinstance(hook_payload, dict):
            data = hook_payload

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
        source_authority = self._source_authority_contract(model_name, view_type_final)
        if if_none_match and if_none_match == etag and not force_refresh:
            return {"status": "not_modified", "code": 304, "data": None, "meta": {"etag": etag, "source_authority": source_authority}}

        meta_out = dict(meta)
        meta_out["etag"] = etag
        meta_out["source_authority"] = source_authority
        response = {"status": status, "code": 200, "data": data, "meta": meta_out}
        return with_lite_preview_if_requested(response, p, "load_contract", payload_type="lite_contract")

    def _generate_with_ui_contract(self, *, model_name, view_type, menu_id, action_id, ctx_user):
        """Compatibility bridge for legacy load_contract/load_view callers."""
        from .ui_contract import UiContractHandler

        params = {
            "op": "model",
            "model": model_name,
            "view_type": view_type,
            "source_mode": "backend_internal",
        }
        if menu_id:
            params["menu_id"] = menu_id
        if action_id:
            params["action_id"] = action_id

        runtime_env = api.Environment(self.env.cr, self.env.user.id, ctx_user)
        contract = UiContractHandler(runtime_env).handle(params)
        if isinstance(contract, dict) and contract.get("ok") is False:
            return {
                "status": "error",
                "code": contract.get("code") or 500,
                "data": contract.get("data") or {},
                "meta": contract.get("meta") or {},
                "message": ((contract.get("error") or {}).get("message") or "ui.contract failed"),
            }

        data = getattr(contract, "data", None)
        meta = getattr(contract, "meta", None)
        if isinstance(contract, dict):
            data = contract.get("data")
            meta = contract.get("meta")
        return {
            "status": "success",
            "code": 200,
            "data": data or {},
            "meta": meta or {},
        }

    def _ensure_native_view_field_descriptors(self, data: dict, model_name: str):
        """Keep native layout nodes renderable when the upstream contract omits descriptors."""
        if not isinstance(data, dict) or not model_name or model_name not in self.env:
            return
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        referenced: set[str] = set()

        def visit(value):
            if isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str) and name in self.env[model_name]._fields:
                    referenced.add(name)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        for key in ("views", "layout", "native_view", "parser_contract"):
            visit(data.get(key))

        missing = sorted(name for name in referenced if name not in fields)
        if missing:
            try:
                fields.update(self.env[model_name].fields_get(missing))
            except Exception:
                _logger.exception("Failed to enrich native view field descriptors for %s", model_name)
        data["fields"] = fields

    def _ensure_form_auxiliary_slots(self, data: dict, model_name: str):
        """Expose stable form auxiliary slots so clients do not infer them."""
        if not isinstance(data, dict):
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return

        def _as_dict(value):
            return value if isinstance(value, dict) else {}

        def _layout_ribbon(node):
            if isinstance(node, list):
                for item in node:
                    found = _layout_ribbon(item)
                    if found:
                        return found
                return None
            if not isinstance(node, dict):
                return None
            widget = str(node.get("widget") or node.get("widgetName") or node.get("name") or "").strip()
            node_type = str(node.get("type") or node.get("kind") or "").strip()
            if node_type == "widget" and widget == "web_ribbon":
                return {
                    "enabled": True,
                    "widget": "web_ribbon",
                    "title": node.get("title") or node.get("text") or node.get("label") or "Ribbon",
                    "class": node.get("class") or node.get("className") or "",
                    "bg_color": node.get("bg_color") or node.get("bgColor") or "",
                }
            for key in ("children", "tabs", "pages", "nodes", "items"):
                found = _layout_ribbon(node.get(key))
                if found:
                    return found
            return None

        if "ribbon" not in form:
            form["ribbon"] = _layout_ribbon(form.get("layout")) or {"enabled": False}
        elif not isinstance(form.get("ribbon"), dict):
            form["ribbon"] = {"enabled": bool(form.get("ribbon"))}

        chatter = _as_dict(form.get("chatter"))
        chatter_enabled = bool(chatter.get("enabled"))
        if not chatter_enabled:
            model_fields = {}
            try:
                model_fields = getattr(self.env[model_name], "_fields", {}) or {}
            except Exception:
                model_fields = {}
            chatter_fields = [
                field_name
                for field_name in ("message_follower_ids", "activity_ids", "message_ids", "website_message_ids")
                if field_name in model_fields
            ]
            if chatter_fields:
                chatter = {
                    **chatter,
                    "enabled": True,
                    "label": chatter.get("label") or "沟通记录",
                    "fields": chatter.get("fields") if isinstance(chatter.get("fields"), list) else chatter_fields,
                    "features": chatter.get("features") if isinstance(chatter.get("features"), dict) else {
                        "message": "message_ids" in model_fields,
                        "note": "message_ids" in model_fields,
                        "activity": "activity_ids" in model_fields,
                    },
                    "actions": chatter.get("actions") if isinstance(chatter.get("actions"), list) else [
                        {
                            "key": "chatter_send_message",
                            "label": "记录沟通",
                            "kind": "chatter",
                            "level": "chatter",
                            "selection": "none",
                            "intent": "message",
                            "payload": {"mode": "message"},
                        },
                        {
                            "key": "chatter_log_note",
                            "label": "记录备注",
                            "kind": "chatter",
                            "level": "chatter",
                            "selection": "none",
                            "intent": "note",
                            "payload": {"mode": "note"},
                        },
                        {
                            "key": "chatter_schedule_activity",
                            "label": "活动",
                            "kind": "chatter",
                            "level": "chatter",
                            "selection": "none",
                            "intent": "activity",
                            "payload": {
                                "mode": "activity",
                                "execute_intent": "chatter.activity.schedule",
                                "activity_type_xmlid": "mail.mail_activity_data_todo",
                                "fields": [
                                    {"name": "summary", "label": "摘要", "type": "char", "required": True},
                                    {"name": "date_deadline", "label": "截止日期", "type": "date", "required": False},
                                    {"name": "note", "label": "备注", "type": "text", "required": False},
                                ],
                            },
                        },
                    ],
                }
                form["chatter"] = chatter

        attachments = _as_dict(form.get("attachments"))
        if bool(_as_dict(form.get("chatter")).get("enabled")) and not attachments.get("enabled"):
            form["attachments"] = {
                **attachments,
                "enabled": True,
                "label": attachments.get("label") or "附件",
                "upload": attachments.get("upload") if isinstance(attachments.get("upload"), dict) else {
                    "intent": "file.upload",
                    "max_bytes": 5 * 1024 * 1024,
                    "accepted_types": [],
                },
                "download": attachments.get("download") if isinstance(attachments.get("download"), dict) else {
                    "intent": "file.download",
                },
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
                    "reason_code": REASON_OK,
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
            reason_code = str(raw.get("reason_code") or (REASON_OK if enabled else REASON_DISABLED))
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
                "card_fields": card_fields,
                "metric_fields": metric_fields,
            }

        def _permission_verdict(value):
            allowed = bool(value)
            return {
                "allowed": allowed,
                "reason_code": REASON_OK if allowed else REASON_PERMISSION_DENIED,
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
            "reason_code": REASON_OK if permission_verdicts["read"]["allowed"] else REASON_PERMISSION_DENIED,
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
            reason_code = REASON_OK
            reason = ""
            if not allowed:
                if not current_enabled:
                    reason_code = str(action.get("reason_code") or REASON_DISABLED)
                    reason = str(action.get("reason") or "")
                elif not permission_allowed:
                    reason_code = REASON_PERMISSION_DENIED
                    reason = "permission denied"
                elif state_blocked:
                    reason_code = REASON_STATE_BLOCKED
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
                            {"key": "open", "label": "打开", "enabled": True, "reason_code": REASON_OK},
                            {"key": "create", "label": "新增", "enabled": can_create, "reason_code": REASON_OK if can_create else REASON_PERMISSION_DENIED},
                            {"key": "unlink", "label": "移除", "enabled": can_unlink, "reason_code": REASON_OK if can_unlink else REASON_PERMISSION_DENIED},
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
                {"key": "open", "label": "打开", "enabled": True, "reason_code": REASON_OK},
                {
                    "key": "edit",
                    "label": "编辑",
                    "enabled": bool(permissions.get("write", False)),
                    "reason_code": REASON_OK if permissions.get("write") else REASON_PERMISSION_DENIED,
                },
            ]
            _add_zone("detail_zone", {"type": "relation_table_block", "data": {"columns": tree_columns, "row_actions": _with_action_gate_list(tree_row_actions)}})

        kanban_semantics = None
        if isinstance(views.get("kanban"), dict):
            kanban_view = views.get("kanban") or {}
            kanban_semantics = _extract_kanban_semantics(kanban_view)
            kanban_card_actions = [
                {"key": "open", "label": "查看详情", "enabled": True, "reason_code": REASON_OK},
                {
                    "key": "edit",
                    "label": "编辑",
                    "enabled": bool(permissions.get("write", False)),
                    "reason_code": REASON_OK if permissions.get("write") else REASON_PERMISSION_DENIED,
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
                "reason_code": REASON_STATE_BLOCKED if is_closed_state else REASON_OK,
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
            "governance": data.get("governance") if isinstance(data.get("governance"), dict) else {},
            "source_trace": data.get("source_trace") if isinstance(data.get("source_trace"), dict) else {},
            "action_gating": action_gating,
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
