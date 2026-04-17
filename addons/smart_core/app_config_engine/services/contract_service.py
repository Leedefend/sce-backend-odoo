# -*- coding: utf-8 -*-
"""
smart_core/app_config_engine/services/contract_service.py
【职责】统一接口服务入口：
  1) 读取 JSON Body、If-None-Match（ETag）；
  2) 解析/规范化 payload；
  3) 根据 subject 分发到对应 Dispatcher；
  4) 计算 ETag、命中 304、拼装 meta；
  5) 返回响应三件套：status/headers/body

相对原版的关键改动：
- 修正 3.x 统一化后处理的缩进，确保 finalize_contract 一定执行。
- 合并视图内按钮（form.header_buttons/stat_buttons/button_box）到顶层 buttons，并去重。
- statusbar 在字段为 state 且 states 为空时，从 fields.state.selection 兜底构造。
- 去除 _norm_str 重复定义，仅保留一个静态方法版本。
"""
import re
from copy import deepcopy
import ast
from odoo.tools.safe_eval import safe_eval
import json, time, logging
from odoo.http import request
from odoo import api, SUPERUSER_ID
from typing import Tuple
from odoo.addons.smart_core.app_config_engine.utils.http import read_json_body
from odoo.addons.smart_core.app_config_engine.utils.payload import parse_payload
from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag, format_versions
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher import MenuDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.exceptions import (
    BAD_REQUEST,
    VALIDATION_ERROR,
    INTERNAL_ERROR,
    DEFAULT_API_VERSION,
    DEFAULT_CONTRACT_VERSION,
    build_error_envelope,
)
from odoo.addons.smart_core.utils.contract_governance import (
    apply_contract_governance,
    resolve_contract_mode,
)

_logger = logging.getLogger(__name__)


class ContractService:
    def __init__(self, request_env):
        # 当前用户环境（保留权限语义）
        self.env = request_env
        # 超级权限环境（用于读取配置/菜单元数据，避免 ACL 限制导致元数据拿不到）
        self.su_env = api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))

    def handle_request(self) -> Tuple[bool, int, list, bytes]:
        """
        主处理流程：返回 (ok, status, headers, body)
        - ok: 逻辑成功标志，这里仅用于内部诊断（控制器不使用）
        - status: HTTP 状态码（含 304 命中）
        - headers: 响应头（含 ETag）
        - body: 二进制 JSON
        """
        ts0 = time.time()
        trace_id = get_trace_id(request.httprequest.headers)

        def _err(status: int, code: str, message: str, details: dict | None = None):
            body = build_error_envelope(
                code=code,
                message=message,
                trace_id=trace_id,
                details=details,
                api_version=DEFAULT_API_VERSION,
                contract_version=DEFAULT_CONTRACT_VERSION,
            )
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("X-Trace-Id", trace_id),
            ]
            return False, status, headers, json.dumps(body, ensure_ascii=False).encode("utf-8")

        # 1) 读取 body 与请求头
        payload = read_json_body()
        client_etag = (request.httprequest.headers.get('If-None-Match') or "").strip()
        if client_etag.startswith('"') and client_etag.endswith('"'):
            client_etag = client_etag[1:-1]
        _logger.warning("CONTRACT_REQUEST payload=%s headers=%s", payload, dict(request.httprequest.headers))

        # 2) 解析/规范化 payload（强约束字段、兜底默认值）
        p = parse_payload(payload)
        contract_mode = resolve_contract_mode(payload if isinstance(payload, dict) else p)
        _logger.warning("CONTRACT_PARSED_PAYLOAD %s", p)

        # 3) 根据 subject 分发
        subject = p.get('subject')
        data, versions = {}, {}

        if subject == 'nav':
            data, versions = NavDispatcher(self.env, self.su_env).build_nav(p)
        elif subject == 'menu':
            data, versions = MenuDispatcher(self.env, self.su_env).open_menu(p)
        elif subject in ('action', 'model', 'operation'):
            data, versions = ActionDispatcher(self.env, self.su_env).dispatch(p)
        else:
            return _err(400, BAD_REQUEST, "不支持的 subject", {"subject": subject})

        # 3.x) 统一化后处理（关键嵌点）
        # -----------------------------------------
        # finalize_contract 期望传入“完整返回体”，所以这里包一个最小壳：
        #   { "ok": True, "data": <分发产出的 data>, "meta": { "subject": ... } }
        # 统一化会在 data 下修正 views/buttons/search/workflow/permissions 等。
        # 若开启了自检（_self_check_strict），发现问题会抛 AssertionError。
        try:
            data = self.finalize_and_govern_data(
                data,
                subject=subject,
                meta={"version": format_versions(versions)},
                contract_mode=contract_mode,
                inject_contract_mode=False,
            )
        except AssertionError as ae:
            # 统一化自检失败：返回 422，方便开发期快速定位脏数据/不一致
            _logger.exception("contract finalize self-check failed")
            return _err(422, VALIDATION_ERROR, "contract_self_check_failed", {"detail": str(ae)})
        # -----------------------------------------

        # 4) 计算 ETag，支持 304
        etag = stable_etag({"data": data, "contract_mode": contract_mode})
        # 约定：with_data=True 时不缓存（避免列表数据频繁变化造成误判）
        skip_cache = bool(p.get("with_data"))
        if not skip_cache and client_etag and client_etag == etag:
            # 命中 304：只回 ETag，body 为空
            return True, 304, [("ETag", etag), ("X-Trace-Id", trace_id)], b''

        # 5) 拼装 meta，包含版本/耗时等
        elapsed = int((time.time() - ts0) * 1000)
        meta = {
            "subject": subject,
            "version": format_versions(versions),  # "model:12|view:34|..."
            "etag": etag,
            "ts": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "elapsed_ms": elapsed,
            "trace_id": trace_id,
            "api_version": DEFAULT_API_VERSION,
            "contract_version": DEFAULT_CONTRACT_VERSION,
            "contract_mode": contract_mode,
        }

        # 6) 返回成功响应
        body = json.dumps({"ok": True, "data": data, "meta": meta}, ensure_ascii=False, default=str).encode('utf-8')
        return True, 200, [
            ('Content-Type','application/json; charset=utf-8'),
            ('ETag', etag),
            ("X-Trace-Id", trace_id),
        ], body

    # =========================
    # 对外唯一需要调用的入口
    # =========================
    def finalize_contract(self, contract):
        """
        统一化后处理入口：
        - 输入：contract（dict），为你原先已经组装好的完整返回体
        - 输出：返回同结构的“修正版”contract
        """
        data = deepcopy(contract)  # 深拷贝，避免原地副作用

        # 0) 先把视图内按钮汇总到顶层，便于统一清洗/权限处理
        self._merge_view_buttons_to_top(data)

        # 0.5) 统一 form layout.fieldInfo 真值源（fields 为 canonical）
        self._sync_form_layout_field_info(data)

        # 0.55) 统一 form 结构语义壳（surface 类型 + semantic_page 映射 + 空分组标签）
        self._normalize_form_structure_semantics(data)

        # 0.6) 统一 form 动作承载区域（button_box 主源，stat_buttons 去重）
        self._dedupe_form_action_surfaces(data)

        # 0.7) 补齐 form x2many 子视图最小承载（tree.columns + policies）
        self._ensure_form_x2many_subviews(data)

        # 1) 对齐表单状态栏字段（form.statusbar.field）
        self._fix_form_statusbar_field(data)

        # 1.x)（可选兜底）为 statusbar.states 提供 selection 值（仅 state 字段）
        self._fill_statusbar_states_from_selection(data)

        # 2) 清理非法/占位的 object 按钮
        self._cleanup_object_buttons(data)

        # 3) 统一搜索过滤器 key 命名（全部转 snake_case）
        self._normalize_search_filter_keys(data)

        # 4) 尝试把 domain_raw 解析为结构化 domain（能解析的才解析）
        self._unify_domains_from_raw(data)

        # 5) 约束“永真”权限子句，仅对项目经理组生效（或删除）
        self._sanitize_permissions(data)

        # 6) 处理不被契约支持的 groups_xmlids 取非（"!" 前缀）
        self._strip_negative_groups_syntax(data)

        # 7) （可选）开发态自检——发现问题直接抛错，避免脏数据流出
        self._self_check_strict(data)

        return data

    @staticmethod
    def _iter_layout_nodes(node):
        if isinstance(node, dict):
            yield node
            for key in ("children", "tabs", "pages", "nodes", "items"):
                children = node.get(key)
                if isinstance(children, list):
                    for child in children:
                        yield from ContractService._iter_layout_nodes(child)
            return
        if isinstance(node, list):
            for item in node:
                yield from ContractService._iter_layout_nodes(item)

    @staticmethod
    def _canonical_field_type(meta):
        info = meta if isinstance(meta, dict) else {}
        return str(info.get("type") or info.get("ttype") or "").strip().lower()

    @staticmethod
    def _canonical_widget_by_type(field_type):
        mapping = {
            "many2one": "many2one",
            "one2many": "one2many_list",
            "many2many": "many2many_tags",
            "boolean": "boolean",
            "date": "date",
            "datetime": "datetime",
            "text": "textarea",
            "html": "html",
            "binary": "image",
        }
        ftype = str(field_type or "").strip().lower()
        return mapping.get(ftype, ftype)

    def _sync_form_layout_field_info(self, contract):
        payload = contract if isinstance(contract, dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        fields_meta = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        if not fields_meta:
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout = form.get("layout")
        if not isinstance(layout, (list, dict)):
            return

        for node in self._iter_layout_nodes(layout):
            if str(node.get("type") or "").strip().lower() != "field":
                continue
            field_name = str(node.get("name") or "").strip()
            if not field_name:
                continue
            canonical = fields_meta.get(field_name)
            if not isinstance(canonical, dict):
                continue

            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            canonical_type = self._canonical_field_type(canonical)
            layout_modifiers = field_info.get("modifiers") if isinstance(field_info.get("modifiers"), dict) else {}

            next_field_info = {
                "name": field_name,
            }

            canonical_label = str(canonical.get("string") or field_name)
            current_label = str(field_info.get("label") or "").strip()
            if (not current_label) or current_label == field_name:
                next_field_info["label"] = canonical_label
            else:
                next_field_info["label"] = current_label

            current_widget = str(field_info.get("widget") or "").strip().lower()
            canonical_widget = str(canonical.get("widget") or self._canonical_widget_by_type(canonical_type) or "")
            needs_widget_fix = not current_widget
            if canonical_type in {"many2one", "one2many", "many2many"} and current_widget in {"", "char", "text", "input"}:
                needs_widget_fix = True
            if canonical_type == "html" and current_widget in {"", "char", "text", "input", "textarea"}:
                needs_widget_fix = True
            if canonical_type == "boolean" and current_widget in {"", "char", "text", "input", "textarea"}:
                needs_widget_fix = True
            if canonical_type == "selection" and current_widget in {"", "char", "text", "input", "textarea"}:
                needs_widget_fix = True
            if needs_widget_fix and canonical_widget:
                next_field_info["widget"] = canonical_widget
            elif current_widget:
                next_field_info["widget"] = current_widget

            colspan = field_info.get("colspan")
            if isinstance(colspan, int) and colspan > 0:
                next_field_info["colspan"] = colspan

            if layout_modifiers:
                next_field_info["modifiers"] = layout_modifiers

            node["fieldInfo"] = next_field_info

    def _normalize_form_structure_semantics(self, contract):
        payload = contract if isinstance(contract, dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return

        for key in ("header_buttons", "button_box", "stat_buttons"):
            value = form.get(key)
            if isinstance(value, list):
                continue
            if isinstance(value, dict):
                form[key] = [item for item in value.values() if isinstance(item, dict)]
            else:
                form[key] = []

        layout = form.get("layout")
        group_index = 1
        for node in self._iter_layout_nodes(layout):
            node_type = str(node.get("type") or "").strip().lower()
            if node_type == "group":
                label = str(node.get("label") or "").strip()
                synthetic = label.startswith("信息分组")
                inferred = self._infer_group_semantic_label(node)
                normalized_existing = self._normalize_group_label(label, self._collect_group_field_names(node)) if label else ""
                if normalized_existing and normalized_existing != label:
                    node["label"] = normalized_existing
                elif inferred and ((not label) or synthetic):
                    node["label"] = inferred
                elif not label:
                    node["label"] = f"信息分组{group_index}"
                    group_index += 1
                continue

            if node_type == "page":
                title = str(
                    node.get("string")
                    or (node.get("attributes") or {}).get("string")
                    or node.get("title")
                    or node.get("label")
                    or node.get("name")
                    or ""
                ).strip()
                if title:
                    title = self._normalize_group_label(title, self._collect_group_field_names(node))
                    node["title"] = title
                    node["label"] = title
                continue

            if node_type == "notebook":
                tabs = node.get("tabs") if isinstance(node.get("tabs"), list) else []
                pages = node.get("pages") if isinstance(node.get("pages"), list) else []
                children = node.get("children") if isinstance(node.get("children"), list) else []
                page_children = [
                    row for row in children
                    if isinstance(row, dict) and str(row.get("type") or "").strip().lower() == "page"
                ]
                derived_tabs = tabs or pages or page_children
                normalized_tabs = [row for row in derived_tabs if isinstance(row, dict)]
                for tab_index, tab in enumerate(normalized_tabs, start=1):
                    tab_title = str(
                        tab.get("string")
                        or (tab.get("attributes") or {}).get("string")
                        or tab.get("title")
                        or tab.get("label")
                        or tab.get("name")
                        or ""
                    ).strip()
                    if not tab_title:
                        tab_children = tab.get("children") if isinstance(tab.get("children"), list) else []
                        for child in tab_children:
                            if not isinstance(child, dict):
                                continue
                            child_type = str(child.get("type") or "").strip().lower()
                            if child_type == "page":
                                tab_title = str(
                                    child.get("string")
                                    or (child.get("attributes") or {}).get("string")
                                    or child.get("title")
                                    or child.get("label")
                                    or child.get("name")
                                    or ""
                                ).strip()
                                if tab_title:
                                    break
                        if not tab_title:
                            for child in tab_children:
                                if not isinstance(child, dict):
                                    continue
                                child_label = str(
                                    child.get("label")
                                    or child.get("title")
                                    or child.get("name")
                                    or (child.get("attributes") or {}).get("string")
                                    or ""
                                ).strip()
                                if child_label and not child_label.startswith("信息分组"):
                                    tab_title = child_label
                                    break
                        if not tab_title:
                            tab_title = f"页签{tab_index}"
                    if tab_title:
                        tab_title = self._normalize_group_label(tab_title, self._collect_group_field_names(tab))
                        tab["title"] = tab_title
                        tab["label"] = tab_title
                node["tabs"] = normalized_tabs
                node["pages"] = list(normalized_tabs)
                notebook_label = str(
                    node.get("label")
                    or node.get("title")
                    or node.get("name")
                    or (node.get("attributes") or {}).get("string")
                    or ""
                ).strip()
                if (not notebook_label) and normalized_tabs:
                    first_tab = normalized_tabs[0] if isinstance(normalized_tabs[0], dict) else {}
                    notebook_label = str(
                        first_tab.get("title")
                        or first_tab.get("label")
                        or first_tab.get("name")
                        or ""
                    ).strip()
                if notebook_label:
                    node["label"] = notebook_label
                if page_children:
                    node["children"] = [
                        row for row in children
                        if not (isinstance(row, dict) and str(row.get("type") or "").strip().lower() == "page")
                    ]
                continue

            if node_type == "button":
                button_label = str(node.get("label") or "").strip()
                if not button_label:
                    button_label = str(
                        node.get("name")
                        or (node.get("attributes") or {}).get("string")
                        or (node.get("attributes") or {}).get("title")
                        or "动作"
                    ).strip()
                    node["label"] = button_label

        views["form"] = form
        data["views"] = views

        semantic_page = data.get("semantic_page") if isinstance(data.get("semantic_page"), dict) else {}
        form_semantics = semantic_page.get("form_semantics") if isinstance(semantic_page.get("form_semantics"), dict) else {}
        if isinstance(layout, (list, dict)):
            form_semantics["layout"] = layout
            form_semantics["layout_source"] = "views.form.layout"
            if isinstance(layout, list):
                form_semantics["layout_section_count"] = len(layout)
            elif isinstance(layout, dict):
                form_semantics["layout_section_count"] = 1
        semantic_page["form_semantics"] = form_semantics
        data["semantic_page"] = semantic_page

        payload["data"] = data

    @staticmethod
    def _infer_group_semantic_label(node):
        item = node if isinstance(node, dict) else {}
        field_names = ContractService._collect_group_field_names(item)
        attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        for key in ("string", "title", "name"):
            value = str(item.get(key) or attrs.get(key) or "").strip()
            if value and not value.startswith("信息分组"):
                return ContractService._normalize_group_label(value, field_names)

        children = item.get("children") if isinstance(item.get("children"), list) else []
        for child in children:
            if not isinstance(child, dict):
                continue
            child_type = str(child.get("type") or "").strip().lower()
            if child_type != "separator":
                continue
            child_attrs = child.get("attributes") if isinstance(child.get("attributes"), dict) else {}
            sep_title = str(
                child.get("label")
                or child.get("title")
                or child.get("name")
                or child_attrs.get("string")
                or ""
            ).strip()
            if sep_title:
                return ContractService._normalize_group_label(sep_title, field_names)

        for child in children:
            if not isinstance(child, dict):
                continue
            child_type = str(child.get("type") or "").strip().lower()
            if child_type == "field":
                info = child.get("fieldInfo") if isinstance(child.get("fieldInfo"), dict) else {}
                field_label = str(info.get("label") or "").strip()
                if field_label:
                    return ContractService._normalize_group_label(field_label, field_names)
            if child_type == "group":
                sub_label = str(child.get("label") or "").strip()
                if sub_label and not sub_label.startswith("信息分组"):
                    return ContractService._normalize_group_label(sub_label, field_names)
        return ""

    @staticmethod
    def _collect_group_field_names(node):
        out = []

        def walk(item):
            if not isinstance(item, dict):
                return
            node_type = str(item.get("type") or "").strip().lower()
            if node_type == "field":
                name = str(item.get("name") or "").strip()
                if name and name not in out:
                    out.append(name)
            for key in ("children", "tabs", "pages", "nodes", "items"):
                rows = item.get(key)
                if isinstance(rows, list):
                    for row in rows:
                        walk(row)

        walk(node)
        return out

    @staticmethod
    def _normalize_group_label(label, field_names):
        raw = str(label or "").strip()
        if not raw:
            return raw

        fields = {str(name or "").strip() for name in (field_names or []) if str(name or "").strip()}
        weak_literals = {
            "任务名称", "名称", "name", "Name", "Name of the Tasks",
            "已启用", "Active", "active",
        }
        if raw in weak_literals:
            if {"name", "partner_id", "company_id"} & fields:
                return "主体信息"
            if {"active", "user_id", "date_start", "date"} & fields:
                return "管理信息"
            if {"project_id", "project_manager_id"} & fields:
                return "项目归属"
            return "基本信息"

        normalized_map = {
            "Visibility": "可见性",
            "Accept Emails From": "接收邮件来自",
            "Tasks": "任务",
            "Time Management": "时间管理",
            "Analytics": "分析",
            "Description": "描述",
            "Settings": "设置",
        }
        return normalized_map.get(raw, raw)

    @staticmethod
    def _action_identity(action):
        row = action if isinstance(action, dict) else {}
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        for key in ("name", "xml_id", "key", "id"):
            value = row.get(key)
            if value not in (None, ""):
                return f"{key}:{value}"
        for key in ("method", "action_id", "xml_id", "ref"):
            value = payload.get(key)
            if value not in (None, ""):
                return f"payload.{key}:{value}"
        label = str(row.get("label") or row.get("string") or "").strip()
        return f"label:{label}" if label else "unknown"

    def _dedupe_action_list(self, rows):
        items = rows if isinstance(rows, list) else []
        out = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            key = self._action_identity(item)
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _dedupe_form_action_surfaces(self, contract):
        payload = contract if isinstance(contract, dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return

        button_box = self._dedupe_action_list(form.get("button_box"))
        stat_buttons = self._dedupe_action_list(form.get("stat_buttons"))

        primary_keys = {self._action_identity(item) for item in button_box}
        if primary_keys:
            stat_buttons = [
                item for item in stat_buttons
                if self._action_identity(item) not in primary_keys
            ]

        form["button_box"] = button_box
        form["stat_buttons"] = stat_buttons
        views["form"] = form
        data["views"] = views
        payload["data"] = data

    def _infer_relation_tree_columns(self, relation_model):
        model = str(relation_model or "").strip()
        if not model:
            return ["display_name"]
        try:
            relation_fields = self.env[model].sudo().fields_get()
        except Exception:
            relation_fields = {}
        if not isinstance(relation_fields, dict) or not relation_fields:
            return ["display_name"]

        preferred = ["name", "display_name", "stage_id", "state", "user_id"]
        selected = [field for field in preferred if field in relation_fields]
        if not selected:
            selected = [field for field in relation_fields.keys() if not str(field).startswith("_")][:3]
        if "display_name" not in selected and "display_name" in relation_fields:
            selected.insert(0, "display_name")
        return selected[:6] or ["display_name"]

    def _ensure_form_x2many_subviews(self, contract):
        payload = contract if isinstance(contract, dict) else {}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        fields_meta = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        if not fields_meta:
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return
        subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}

        for field_name, meta in fields_meta.items():
            if not isinstance(meta, dict):
                continue
            field_type = str(meta.get("type") or meta.get("ttype") or "").strip().lower()
            if field_type not in {"one2many", "many2many"}:
                continue
            relation = str(meta.get("relation") or meta.get("comodel_name") or "").strip()
            current = subviews.get(field_name) if isinstance(subviews.get(field_name), dict) else {}
            tree_cfg = current.get("tree") if isinstance(current.get("tree"), dict) else {}
            columns = tree_cfg.get("columns") if isinstance(tree_cfg.get("columns"), list) else []
            if not columns:
                tree_cfg["columns"] = self._infer_relation_tree_columns(relation)
            policies = current.get("policies") if isinstance(current.get("policies"), dict) else {}
            policies.setdefault("inline_edit", True)
            policies.setdefault("can_create", True)
            policies.setdefault("can_unlink", True)
            current["tree"] = tree_cfg
            current.setdefault("fields", {})
            current["policies"] = policies
            subviews[field_name] = current

        form["subviews"] = subviews
        views["form"] = form
        data["views"] = views
        payload["data"] = data

    def finalize_data(self, data, *, subject=None, meta=None):
        meta_out = dict(meta or {})
        if subject and "subject" not in meta_out:
            meta_out["subject"] = subject
        fixed = self.finalize_contract({"ok": True, "data": data, "meta": meta_out})
        return fixed.get("data", data) or {}

    def govern_data(
        self,
        data,
        *,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        return apply_contract_governance(
            data or {},
            contract_mode,
            contract_surface=contract_surface,
            source_mode=source_mode,
            inject_contract_mode=inject_contract_mode,
        )

    def apply_delivery_surface_governance(
        self,
        data,
        *,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        """Canonical name for the final delivery-surface governance step."""
        return self.govern_data(
            data,
            contract_mode=contract_mode,
            contract_surface=contract_surface,
            source_mode=source_mode,
            inject_contract_mode=inject_contract_mode,
        )

    @staticmethod
    def inject_render_hints(data, payload):
        if not isinstance(data, dict):
            return data

        def _collect_layers(source):
            layers = []
            if isinstance(source, dict):
                layers.append(source)
                for key in ("payload", "params", "data", "args"):
                    value = source.get(key)
                    if isinstance(value, dict):
                        layers.append(value)
            return layers

        def _get_param(source, *keys):
            for layer in _collect_layers(source):
                for key in keys:
                    if key not in layer:
                        continue
                    value = layer.get(key)
                    if isinstance(value, str) and not value.strip():
                        continue
                    if value is not None:
                        return value
            return None

        form_view = (
            str((data.get("head") or {}).get("view_type") or data.get("view_type") or "").strip().lower() == "form"
            or isinstance(((data.get("views") or {}).get("form")), dict)
        )
        if not form_view:
            return data
        render_profile = str(
            _get_param(payload, "render_profile", "renderProfile", "profile", "mode") or ""
        ).strip().lower()
        if render_profile in {"read", "view"}:
            render_profile = "readonly"
        if render_profile not in {"create", "edit", "readonly"}:
            render_profile = ""
        raw_record = _get_param(payload, "record_id", "recordId", "res_id", "resId")
        record_id = None
        try:
            if raw_record is not None and str(raw_record).strip():
                record_id = int(raw_record)
        except Exception:
            record_id = None
        if record_id and record_id > 0:
            data["res_id"] = record_id
            head = data.get("head")
            if isinstance(head, dict) and not head.get("res_id"):
                head["res_id"] = record_id
                data["head"] = head

        if not render_profile:
            render_profile = "edit" if (record_id and record_id > 0) else "create"

        data["render_profile"] = render_profile

        permissions = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
        effective = permissions.get("effective") if isinstance(permissions.get("effective"), dict) else {}
        rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}

        if render_profile == "readonly":
            rights["write"] = False
            rights["unlink"] = False
            rights["create"] = False
            fields_meta = data.get("fields") if isinstance(data.get("fields"), dict) else {}
            for meta in fields_meta.values():
                if isinstance(meta, dict):
                    meta["readonly"] = True
            data["fields"] = fields_meta
        elif render_profile == "create":
            rights["create"] = True
            rights["write"] = False
            rights["unlink"] = False
            data.pop("res_id", None)
            head = data.get("head")
            if isinstance(head, dict):
                head.pop("res_id", None)
                data["head"] = head

        effective["rights"] = rights
        effective["render_profile"] = render_profile
        permissions["effective"] = effective
        data["permissions"] = permissions
        return data

    def finalize_and_govern_data(
        self,
        data,
        *,
        subject=None,
        meta=None,
        payload=None,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        """Canonical post-dispatch pipeline: finalize -> render hints -> delivery governance."""
        finalized = self.finalize_data(data, subject=subject, meta=meta)
        hinted = self.inject_render_hints(finalized, payload or {})
        return self.apply_delivery_surface_governance(
            hinted,
            contract_mode=contract_mode,
            contract_surface=contract_surface,
            source_mode=source_mode,
            inject_contract_mode=inject_contract_mode,
        )

    def shape_handler_delivery_data(
        self,
        data,
        *,
        payload=None,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        """Canonical handler-side post-dispatch shaping helper.

        UiContractHandler receives already-dispatched data and only needs the
        final handler-side sequence:
        1. finalize canonical contract structure
        2. inject render hints
        3. apply delivery-surface governance
        """
        return self.finalize_and_govern_data(
            data or {},
            payload=payload or {},
            contract_mode=contract_mode,
            contract_surface=contract_surface,
            source_mode=source_mode,
            inject_contract_mode=inject_contract_mode,
        )

    # =========================
    # 具体修复实现
    # =========================
    def _merge_view_buttons_to_top(self, data):
        try:
            root = data.get("data") or {}
            views = root.get("views") or {}
            form = views.get("form") or {}
            header_buttons = form.get("header_buttons") or []
            # 兼容两种命名
            stat_buttons = form.get("stat_buttons") or form.get("button_box") or []
            top_buttons = root.get("buttons") or []

            def _key(b):
                if not isinstance(b, dict): 
                    return None
                p = (b.get("payload") or {})
                # 语义主键：不含 label，确保真正相同的动作被折叠
                ident = p.get("method") or p.get("ref") or p.get("url") or ""
                return (b.get("kind"), b.get("level"), ident)


            merged = {}
            for b in (top_buttons + header_buttons + stat_buttons):
                if not isinstance(b, dict):
                    continue
                merged[_key(b)] = b
            root["buttons"] = list(merged.values())
            data["data"] = root
        except Exception:
            pass

    def _fix_form_statusbar_field(self, data):
        """
        目的：消除 form.statusbar.field 与实际可用字段不一致的问题
        策略：
          - 如果 form.statusbar.field 不在 fields 集合里，则优先用 workflow.state_field
          - 如果 workflow.state_field 也不存在，则尝试回落到 'stage_id' 或删除 statusbar
        """
        try:
            views = data['data']['views']
            fields = data['data']['fields']
            workflow = data['data'].get('workflow', {})
            form = views.get('form', {})
            statusbar = form.get('statusbar', {})

            sb_field = statusbar.get('field')
            if not sb_field or sb_field not in fields:
                # 优先用 workflow.state_field
                wf_field = workflow.get('state_field')
                if wf_field and wf_field in fields:
                    statusbar['field'] = wf_field
                elif 'stage_id' in fields:
                    statusbar['field'] = 'stage_id'
                else:
                    # 实在没有可用的状态字段，移除 statusbar 避免前端报错
                    form.pop('statusbar', None)

            # 回写
            views['form'] = form
            data['data']['views'] = views
        except Exception:
            # 容错：任何异常不影响主流程
            pass

    def _fill_statusbar_states_from_selection(self, data):
        """当 statusbar.states 为空时，优先从 statusbar.field 对应字段 selection 构造可消费状态。"""
        try:
            fields = (data.get("data") or {}).get("fields") or {}
            form = (data.get("data") or {}).get("views", {}).get("form", {}) or {}
            sb = form.get("statusbar") or {}
            sb_field = str(sb.get("field") or sb.get("name") or "").strip()
            if not sb_field:
                return

            field_meta = fields.get(sb_field) if isinstance(fields.get(sb_field), dict) else {}
            field_type = str(field_meta.get("type") or field_meta.get("ttype") or "").strip().lower()
            existing_states = sb.get("states") if isinstance(sb.get("states"), list) else []

            states = []
            if field_type == "selection":
                selection = field_meta.get("selection") if isinstance(field_meta.get("selection"), list) else []
                for idx, pair in enumerate(selection, start=1):
                    if not (isinstance(pair, (list, tuple)) and len(pair) >= 2):
                        continue
                    value = pair[0]
                    label = str(pair[1] or pair[0] or "").strip()
                    if value in (None, ""):
                        continue
                    states.append({
                        "value": value,
                        "label": label,
                        "sequence": idx,
                    })
            elif existing_states:
                for idx, row in enumerate(existing_states, start=1):
                    if not isinstance(row, dict):
                        continue
                    value = row.get("value")
                    label = str(row.get("label") or value or "").strip()
                    if value in (None, ""):
                        continue
                    item = dict(row)
                    item["label"] = label
                    item.setdefault("sequence", idx)
                    states.append(item)

            if states:
                sb["states"] = states
                sb["states_source"] = "selection" if field_type == "selection" else "statusbar_declared"
            else:
                sb["states"] = []
                sb["states_source"] = "dynamic_relation"
                sb["states_reason"] = "statusbar field is not static selection"

            sb.setdefault("label", str(field_meta.get("string") or sb_field))
            form["statusbar"] = sb
            data["data"]["views"]["form"] = form
        except Exception:
            pass

    def _cleanup_object_buttons(self, data):
        """
        目的：移除/修正空方法或空标签的对象按钮（kind == 'object'）
        规则：
          - method 为空的一律移除
          - label 为空：若 method 存在，则用 method 作为兜底 label
        """
        try:
            buttons = data['data'].get('buttons', [])
            cleaned = []
            for btn in buttons:
                if not isinstance(btn, dict):
                    continue
                kind = btn.get('kind')
                payload = btn.get('payload') or {}
                method = (payload.get('method') or '').strip() if isinstance(payload.get('method'), str) else payload.get('method')
                label = (btn.get('label') or '').strip()

                if kind == 'object':
                    # 对象按钮必须有方法名
                    if not method:
                        continue  # 丢弃此按钮
                    # 标签兜底：如果 label 为空，用 method 名顶上，避免前端显示空白
                    if not label:
                        btn['label'] = str(method)
                cleaned.append(btn)

            data['data']['buttons'] = cleaned
        except Exception:
            pass

    def _normalize_search_filter_keys(self, data):
        """
        目的：统一搜索过滤器 key 为 snake_case，避免大小写/空格导致路由或缓存不一致
        例：'Manager' -> 'manager'， 'My Projects' -> 'my_projects'
        """
        try:
            filters_ = data['data']['search'].get('filters', [])
            for f in filters_:
                key = f.get('key')
                if not key:
                    continue
                snake = self._to_snake_case(key)
                f['key'] = snake
        except Exception:
            pass

    @staticmethod
    def _to_snake_case(s):
        """
        把任意字符串转为 snake_case：
        - 先把空白/连接符替换为下划线
        - 再把驼峰切分为下划线
        """
        s = re.sub(r'[\s\-]+', '_', str(s).strip())
        s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)         # AbcX -> Abc_X
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)         # abcX -> abc_X
        s = re.sub(r'_+', '_', s).lower()
        return s

    def _unify_domains_from_raw(self, data):
        """
        目的：把能安全解析的 domain_raw（字符串）转换为结构化的 domain（列表）
        安全策略：
          - 仅在 domain 为空且 domain_raw 看起来像一个 Python 列表字面量时尝试解析
          - 如果包含明显不可在此处安全解析的符号（如 context_today(), user.等），则跳过
        """
        try:
            filters_ = data['data']['search'].get('filters', [])
            for f in filters_:
                dom = f.get('domain')
                dom_raw = f.get('domain_raw')

                if (not dom) and isinstance(dom_raw, str) and dom_raw.strip().startswith('['):
                    raw = dom_raw.strip()

                    # 粗略过滤：遇到明显依赖上下文/用户函数的，先别解析，避免报错
                    if any(x in raw for x in ('context_today', 'user.', 'uid', 'company_id', 'res_model')):
                        continue

                    try:
                        parsed = safe_eval(raw, {})  # 不提供上下文，限制解析能力，保证安全
                        if isinstance(parsed, list):
                            f['domain'] = parsed
                    except Exception:
                        pass
        except Exception:
            pass

    def _sanitize_permissions(self, data):
        """
        目的：约束权限规则中“永真域”[(1,'=',1)]，避免误放权
        策略：
        - 若检测到该子句，则仅对项目经理组生效（groups_xmlids += project.group_project_manager）
        - 同时取消 global 放开（global=False）
        - 不依赖 group id 映射，避免跨库/环境差异
        - 兼容 data 或 {"data": data} 两种包装
        """
        try:
            # 兼容顶层/包裹两种结构
            root = data.get('data') if isinstance(data, dict) and 'data' in data else data
            if not isinstance(root, dict):
                return

            perms = (root.get('permissions') or {})
            rules = (perms.get('rules') or {})

            changed = False

            for op in ('read', 'write', 'create', 'unlink'):
                block = rules.get(op) or {}
                clauses = block.get('clauses') or []
                for c in clauses:
                    dom = c.get('domain', [])
                    raw = (c.get('domain_raw') or '').strip()
                    if self._domain_is_tautology(dom, raw):
                        # 绑定到项目经理组
                        xmlids = set(c.get('groups_xmlids') or [])
                        xmlids.add('project.group_project_manager')
                        c['groups_xmlids'] = sorted(xmlids)

                        # 取消全局放开
                        if c.get('global') is True:
                            c['global'] = False

                        changed = True

            if changed:
                _logger.info("SANITIZE_PERMS: 永真域已限制到项目经理组并取消 global。")

        except Exception:
            _logger.exception("SANITIZE_PERMS: 处理权限时发生异常（已忽略以不中断流程）")

    def _safe_literal_eval(self, s: str):
        """对 domain_raw 做安全解析；解析失败返回 None"""
        try:
            return ast.literal_eval(s)
        except Exception:
            return None

    def _domain_is_tautology(self, dom, raw):
        """
        识别“恒真域”，用于在权限/规则展示时省略无意义的域：
        - [] 或 [(1, '=', 1)]
        同时兼容 raw 是字符串的情况。
        """
        # 1) 结构化优先
        try:
            if isinstance(dom, (list, tuple)):
                if dom == []:
                    return True
                if len(dom) == 1 and isinstance(dom[0], (list, tuple)) and len(dom[0]) == 3:
                    l, op, r = dom[0]
                    if (op in ("=", "==")) and (l in (1, True)) and (r in (1, True)):
                        return True
        except Exception:
            pass

        # 2) 若给了 raw，尝试解析后复用本函数判断
        if raw:
            try:
                v = self._safe_literal_eval(raw)
                if isinstance(v, (list, tuple)):
                    return self._domain_is_tautology(v, None)
            except Exception:
                pass

        # 3) 字符串兜底
        s = self._norm_str(raw or "")
        if s in ("[]", "[(1,'=',1)]", "[(1,'==',1)]"):
            return True
        return False

    def _strip_negative_groups_syntax(self, data):
        """
        目的：去除 groups_xmlids 中非标准取非语法（'!group.xmlid'）
        说明：
        - 契约很多时候不支持 '!' 前缀；这里直接剥离这些项
        - 更严谨做法：在服务端**生成阶段**就按用户组判定是否下发此按钮
        """
        try:
            buttons = data['data'].get('buttons', [])
            for btn in buttons:
                groups = btn.get('groups_xmlids', []) or []
                if not groups:
                    continue
                normalized = [g for g in groups if not (isinstance(g, str) and g.startswith('!'))]
                btn['groups_xmlids'] = normalized
        except Exception:
            pass
        try:
            views = (data.get('data') or {}).get('views') or {}
            form = (views.get('form') or {})
            for bucket in ('header_buttons', 'stat_buttons', 'button_box'):
                for btn in form.get(bucket, []) or []:
                    groups = btn.get('groups_xmlids', []) or []
                    btn['groups_xmlids'] = [g for g in groups if not (isinstance(g, str) and g.startswith('!'))]
        except Exception:
            pass

    @staticmethod
    def _norm_str(s):
        """
        宽松字符串归一化：去空白、统一引号、小写化。
        用于对 domain_raw 做容错比较。
        """
        if s is None:
            return ""
        return re.sub(r"\s+", "", str(s)).replace('"', "'").lower()

    # =========================
    # 自检（开发/测试环境启用）
    # =========================
    def _self_check_strict(self, data):
        """
        目的：在开发/测试环境提前暴露契约不一致问题（生产可关）
        断言项：
          - form.statusbar.field 必须存在于 fields（如果 statusbar 存在）
          - 所有 kind=object 的按钮必须有非空 method
          - tree.columns 中的字段必须存在于 fields
        """
        try:
            fields = data['data'].get('fields', {})
            # 1) statusbar 字段存在性
            form = data['data']['views'].get('form', {})
            statusbar = form.get('statusbar')
            if statusbar:
                sb_field = statusbar.get('field')
                assert sb_field in fields, "statusbar.field 不在 fields 集合中：%s" % sb_field

            # 2) object 按钮必须有 method
            for btn in data['data'].get('buttons', []):
                if btn.get('kind') == 'object':
                    method = (btn.get('payload') or {}).get('method')
                    assert method, "发现 kind=object 但无 method 的按钮：%s" % btn

            # 3) tree.columns 必须在 fields 里
            cols = data['data']['views'].get('tree', {}).get('columns', []) or []
            for col in cols:
                assert col in fields, "tree.columns 包含未知字段：%s" % col

        except AssertionError:
            # 这里直接抛出有利于测试阶段快速发现；线上可改为 logger.warning
            raise
        except Exception:
            # 容错：自检异常不影响主流程
            pass
