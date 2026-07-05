# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/assemblers/page_assembler.py
# 【职责】页面契约装配：
#   - 聚合：fields/views/search/permissions/actions/reports/workflow/validator
#   - with_data=True 时返回首屏数据（严格遵循 views.tree.columns 顺序）
#   - ★ 集成 P0 修复：从原始 <tree> 严格提取 columns，禁用“脏覆盖”，保证可渲染与顺序稳定
import json
import logging
import re
from odoo import _
from odoo.http import request
from odoo.addons.smart_core.utils.delete_policy import resolve_unlink_policy
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_ADD_CUSTOM_FIELD,
    BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_CONFIGURATION,
    BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_ORDER_SAVE,
    BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_SETTINGS,
    BUSINESS_CONFIG_AUTHORITIES,
    BUSINESS_CONFIG_INTENTS,
    BUSINESS_CONFIG_MODES,
    BUSINESS_CONFIG_OWNER_LAYER,
    FORM_FIELD_CONFIG_INTENTS,
    is_business_config_runtime_model,
)
from ...utils.misc import safe_eval
from ...utils.view_utils import extract_tree_columns_strict, normalize_cols_safely

_logger = logging.getLogger(__name__)


class PageAssembler:
    SOURCE_KIND = "app_config_page_contract_projection"
    SOURCE_AUTHORITIES = (
        "app.model.config",
        "app.view.config",
        "app.search.config",
        "app.permission.config",
        "app.action.config",
        "app.report.config",
        "app.workflow.config",
        "app.validator.config",
        "odoo.orm",
    )
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "app_config_engine.page_assembler",
        }

    _SYSTEM_RELATION_DEGRADE_MODELS = {
        "ir.ui.view",
        "ir.model",
        "ir.model.fields",
        "ir.model.access",
        "ir.rule",
        "ir.actions.actions",
        "ir.actions.act_window",
        "ir.ui.menu",
        "ir.config_parameter",
        "res.users",
        "res.groups",
    }

    def __init__(self, env, su_env=None):
        """
        env:  运行态环境（必须带当前用户，用于 ORM 自动应用记录规则、用户筛选等）
        su_env: 提权环境（默认 env.sudo()），用于收集模型/视图/权限等“元数据”，避免被权限阻塞
        """
        self.env = env
        # 旧：self.su_env = su_env or env.sudo()  # 会报错：Environment 没有 sudo()
        # 新：优先使用传入的 su_env；否则用 request.env.sudo()；再不行用任意模型 sudo 后取其 env
        if su_env is not None:
            self.su_env = su_env
        else:
            try:
                self.su_env = request.env.sudo()
            except Exception:
                self.su_env = env['ir.model'].sudo().env
    @staticmethod
    def normalize_view_types(vt):
        """字符串/数组 → 统一成 ['tree','form'] 形式"""
        if not vt:
            return ['tree', 'form']
        if isinstance(vt, str):
            return [x.strip() for x in vt.split(',') if x.strip()]
        if isinstance(vt, (list, tuple)):
            return [str(x).strip() for x in vt if str(x).strip()]
        return ['tree', 'form']

    @staticmethod
    def _normalize_action_domain(action, eval_context=None):
        if not isinstance(action, dict):
            return [], ""
        raw = action.get("domain")
        if raw in (None, False, ""):
            return [], ""
        raw_text = raw if isinstance(raw, str) else ""
        parsed = safe_eval(raw, eval_context or {}) if isinstance(raw, str) else raw
        if isinstance(parsed, tuple):
            parsed = list(parsed)
        if not isinstance(parsed, list):
            return [], raw_text
        return parsed, raw_text

    @staticmethod
    def _normalize_action_context(action, eval_context=None):
        if not isinstance(action, dict):
            return {}, ""
        raw = action.get("context")
        if raw in (None, False, ""):
            return {}, ""
        raw_text = raw if isinstance(raw, str) else ""
        parsed = safe_eval(raw, eval_context or {}) if isinstance(raw, str) else raw
        if not isinstance(parsed, dict):
            return {}, raw_text
        return parsed, raw_text

    @staticmethod
    def _normalize_business_category_codes(value):
        if value in (None, False, ""):
            return []
        raw_items = value if isinstance(value, (list, tuple, set)) else [value]
        codes = []
        seen = set()
        for item in raw_items:
            code = str(item or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            codes.append(code)
        return codes

    @classmethod
    def _extract_allowed_business_category_codes_from_domain(cls, domain):
        codes = []
        seen = set()

        def add(value):
            for code in cls._normalize_business_category_codes(value):
                if code in seen:
                    continue
                seen.add(code)
                codes.append(code)

        def visit(node):
            if not isinstance(node, (list, tuple)):
                return
            if len(node) >= 3 and str(node[0] or "").strip() == "business_category_id.code":
                operator = str(node[1] or "").strip()
                if operator in ("=", "==", "in"):
                    add(node[2])
                return
            for child in node:
                visit(child)

        visit(domain)
        return codes

    def assemble_page_contract(self, p, action=None):
        """
        页面契约主装配：
        - 确保 views.tree.columns 存在（必要时用严格提取填充）
        - 禁用“使用原始视图字段覆盖生成列”的脏逻辑，防止隐字段/one2many 混入
        - ★ 权限：使用 su_env 生成权限聚合，并返回“已按当前用户裁剪”的权限契约（effective）
        """
        model = p.get("model")
        if not model:
            # 如动作没有模型，退回诊断契约
            from .client_url_report import ClientUrlReportAssembler
            _logger.warning("Action %s has no res_model, returning diagnostic contract", action.get('id') if action else 'unknown')
            return ClientUrlReportAssembler(self.env).assemble_diagnostic_contract(p, action, issue="动作未配置模型 (res_model)")

        env = self.env
        su = self.su_env
        action = action or self._resolve_action_from_payload(p, model)
        view_types = self._include_configured_orchestrated_view_types(
            p.get("view_types"),
            model_name=model,
            action_id=action.get("id") if isinstance(action, dict) else p.get("action_id") or p.get("actionId"),
        )
        p["view_types"] = view_types
        action_eval_context = {
            "uid": env.uid,
            "user": env.user,
            "active_id": p.get("record_id") or p.get("recordId") or p.get("res_id") or p.get("resId"),
            "active_ids": [p.get("record_id") or p.get("recordId") or p.get("res_id") or p.get("resId")]
            if (p.get("record_id") or p.get("recordId") or p.get("res_id") or p.get("resId"))
            else [],
            "active_model": model,
        }
        action_domain, action_domain_raw = self._normalize_action_domain(action, action_eval_context)
        action_context, action_context_raw = self._normalize_action_context(action, action_eval_context)
        request_context = p.get("context") if isinstance(p.get("context"), dict) else {}
        effective_context = dict(action_context or {})
        env_context = self.env.context if isinstance(self.env.context, dict) else {}
        for key in ("current_project_id", "default_project_id", "allowed_company_ids", "lang", "tz"):
            if env_context.get(key) and key not in effective_context:
                effective_context[key] = env_context.get(key)
        if request_context:
            effective_context.update(request_context)
        allowed_codes = self._normalize_business_category_codes(
            effective_context.get("allowed_business_category_codes")
        )
        if not allowed_codes:
            allowed_codes = self._extract_allowed_business_category_codes_from_domain(action_domain)
        if allowed_codes:
            effective_context["allowed_business_category_codes"] = allowed_codes
        current_project_id = p.get("current_project_id") or effective_context.get("current_project_id")
        if current_project_id:
            try:
                project_id_int = int(current_project_id)
                effective_context["current_project_id"] = project_id_int
                effective_context.setdefault("default_project_id", project_id_int)
            except Exception:
                pass
        if action_domain and not p.get("domain"):
            p["domain"] = action_domain

        required_models = {
            "app.model.config": True,
            "app.view.config": True,
            "app.search.config": False,
            "app.permission.config": False,
            "app.action.config": False,
            "app.report.config": False,
            "app.workflow.config": False,
            "app.validator.config": False,
        }
        missing_models = []
        warnings = []

        def mark_missing(model_name):
            if model_name not in missing_models:
                missing_models.append(model_name)
            if required_models.get(model_name, False):
                warnings.append(f"required_missing:{model_name}")
            else:
                warnings.append(f"optional_missing:{model_name}")

        data = {
            "head": {},
            "views": {},
            "fields": {},
            "search": {},
            "permissions": {},
            "buttons": [],
            "toolbar": {"header": [], "sidebar": [], "footer": []},
            "workflow": {},
            "reports": [],
            "degraded": False,
            "missing_models": [],
            "warnings": [],
            "access_policy": {
                "mode": "allow",
                "reason_code": "",
                "message": "",
                "policy_source": "none",
                "blocked_fields": [],
                "degraded_fields": [],
            },
        }
        raw_record_id = p.get("record_id") or p.get("recordId") or p.get("res_id") or p.get("resId")
        try:
            requested_record_id = int(raw_record_id) if raw_record_id not in (None, "", False) else None
        except Exception:
            requested_record_id = None
        requested_render_profile = str(
            p.get("render_profile") or p.get("renderProfile") or p.get("profile") or ""
        ).strip().lower()
        if requested_render_profile in {"read", "view"}:
            requested_render_profile = "readonly"
        if requested_render_profile not in {"create", "edit", "readonly"}:
            requested_render_profile = ""
        if requested_record_id and requested_record_id > 0:
            data["record_id"] = requested_record_id
            data["res_id"] = requested_record_id
        if requested_render_profile:
            data["render_profile"] = requested_render_profile
        versions = {}

        # 1) 字段：从模型配置生成；再归一化到 {name: {...}} 形式
        #    - 使用 su_env 读模型元数据，避免被权限限制
        try:
            mcfg = su['app.model.config']._generate_from_ir_model(model)
            data["fields"] = self._to_fields_map(mcfg.get_model_contract().get("fields", []), env=env, model=mcfg.model)
            versions["model"] = mcfg.version
        except KeyError:
            mark_missing("app.model.config")
            _logger.warning("app.model.config missing; fallback to ORM fields for model=%s", model)
            data["fields"] = self._to_fields_map(list(env[model]._fields.keys()), env=env, model=model)
            versions["model"] = 0

        # 2) 从原始 tree 视图 XML 严格提取列（★ P0 修复核心）
        original_tree_cols = []
        original_default_order = None
        try:
            v_info = su[model].get_view(view_type='tree')
            original_tree_cols, original_default_order = extract_tree_columns_strict(v_info.get('arch'), v_info.get('fields', {}))
            if original_tree_cols:
                _logger.info("直接从源视图提取到可见字段: %s", [c['name'] for c in original_tree_cols])
        except Exception as e:
            _logger.warning("从原始视图提取字段失败: %s", e)

        # 3) 视图契约（多视图）——视图元信息用 su_env 获取，运行时修剪在各自组装器里完成
        v_versions = []
        view_context = {}
        if isinstance(action, dict) and action.get("id"):
            view_context["contract_action_id"] = action.get("id")
        requested_view_id = p.get("view_id") or p.get("viewId")
        try:
            requested_view_id = int(requested_view_id or 0)
        except Exception:
            requested_view_id = 0
        view_context["contract_projection_readonly"] = True
        for vt in view_types:
            try:
                scoped_view_context = dict(view_context)
                if requested_view_id and len(view_types) == 1:
                    scoped_view_context["contract_view_id"] = requested_view_id
                view_config_model = env['app.view.config'].with_context(**scoped_view_context) if scoped_view_context else env['app.view.config']
                vcfg = view_config_model._generate_from_fields_view_get(model, vt)
                # app.view.config is platform metadata and ordinary business
                # users do not read it directly. Keep metadata access elevated,
                # but bind the environment user to the real requester so
                # runtime group/ACL filtering still matches native Odoo.
                vcfg_runtime = vcfg.with_user(env.user).sudo().with_context(**scoped_view_context)
                v_contract = vcfg_runtime.get_contract_api(filter_runtime=True, check_model_acl=True)
                v_versions.append(str(v_contract.get("effective_version") or vcfg.version))
            except KeyError:
                mark_missing("app.view.config")
                _logger.warning("app.view.config missing; fallback view contract for model=%s vt=%s", model, vt)
                v_contract = {"type": vt}
            except Exception as e:
                data["degraded"] = True
                reason = f"view_contract_fallback:{vt}:{type(e).__name__}"
                if reason not in warnings:
                    warnings.append(reason)
                _logger.warning(
                    "view contract assemble failed; fallback minimal contract model=%s vt=%s err=%s",
                    model,
                    vt,
                    e,
                )
                v_contract = {"type": vt}

            v_contract = self._coerce_view_contract_semantics(vt, v_contract)

            if vt == 'tree':
                # 解析器没产出 columns 时，用严格列兜底
                cols = v_contract.get('columns') or []
                if not cols and original_tree_cols:
                    v_contract['columns'] = [c['name'] for c in original_tree_cols]
                    if original_default_order:
                        v_contract['default_order'] = original_default_order
                # 禁用对 columns 的二次“脏覆盖”

            data["views"][vt] = v_contract
        versions["view"] = ",".join(v_versions) if v_versions else "1"

        # 4) 搜索条件（运行时需要当前用户上下文，因此用 env）
        try:
            scfg = env['app.search.config']._generate_from_search(model)
            data["search"] = scfg.get_search_contract(filter_runtime=True, include_user_filters=True)
            versions["search"] = scfg.version
        except KeyError:
            mark_missing("app.search.config")
            _logger.warning("app.search.config missing; fallback search contract for model=%s", model)
            data["search"] = {}
            versions["search"] = 0
        self._inject_search_view_orchestration(data, env=env, model=model, view_context=view_context, versions=versions)
        self._apply_action_search_defaults(data, effective_context)
        self._inject_view_orchestration_summary(data)
        data["context"] = effective_context
        data["context_raw"] = action_context_raw

        # 4.x) 关系字段维护入口（many2one/many2many/one2many）
        # 由后端契约提供 relation_entry，前端禁止自行猜测 action/menu。
        self._inject_relation_entry_contract(data, model)

        # 5) 权限契约（★ 关键改造点）
        #    - 用 su_env 生成完整权限聚合
        #    - 返回时开启 filter_runtime=True，按“当前用户组”裁剪出 effective.rights/rules
        try:
            pcfg = su['app.permission.config']._generate_from_access_rights(model)
            data["permissions"] = pcfg.get_permission_contract(filter_runtime=True, uid=env.uid)
            versions["perm"] = pcfg.version
        except KeyError:
            mark_missing("app.permission.config")
            _logger.warning("app.permission.config missing; fallback permissions for model=%s", model)
            data["permissions"] = {}
            versions["perm"] = 0
        permissions_root = data["permissions"] if isinstance(data.get("permissions"), dict) else {}
        effective_permissions = permissions_root.get("effective") if isinstance(permissions_root.get("effective"), dict) else {}
        effective_rights = effective_permissions.get("rights") if isinstance(effective_permissions.get("rights"), dict) else {}
        effective_rights.update(
            {
                "read": env[model].check_access_rights("read", raise_exception=False),
                "write": env[model].check_access_rights("write", raise_exception=False),
                "create": env[model].check_access_rights("create", raise_exception=False),
                "unlink": env[model].check_access_rights("unlink", raise_exception=False),
            }
        )
        effective_permissions["rights"] = effective_rights
        permissions_root["effective"] = effective_permissions
        data["permissions"] = permissions_root
        if isinstance(effective_context, dict) and effective_context.get("create") is False:
            permissions_root = data["permissions"] if isinstance(data.get("permissions"), dict) else {}
            effective_permissions = permissions_root.get("effective") if isinstance(permissions_root.get("effective"), dict) else {}
            effective_rights = effective_permissions.get("rights") if isinstance(effective_permissions.get("rights"), dict) else {}
            permissions_root["create"] = False
            effective_rights["create"] = False
            effective_permissions["rights"] = effective_rights
            permissions_root["effective"] = effective_permissions
            data["permissions"] = permissions_root
        data["delete_policy"] = resolve_unlink_policy(env, model)

        # 6) 动作按钮 + 工具栏（元数据可 su_env，最终显隐由前端结合 groups/permissions 再次裁剪）
        try:
            acfg = su['app.action.config']._generate_from_ir_actions(model)
            buttons_data = acfg.with_env(env).get_action_contract()
            versions["actions"] = acfg.version if getattr(acfg, 'version', None) else 1
        except KeyError:
            mark_missing("app.action.config")
            _logger.warning("app.action.config missing; fallback empty actions for model=%s", model)
            buttons_data = []
            versions["actions"] = 0
        data["buttons"] = buttons_data
        toolbar = {
            "header": [a for a in buttons_data if a.get('level') == 'toolbar'],
            "sidebar": [a for a in buttons_data if a.get('level') == 'sidebar'],
            "footer": [a for a in buttons_data if a.get('level') == 'footer']
        }
        data["toolbar"] = toolbar if any(toolbar.values()) else {"header": [], "sidebar": [], "footer": []}

        # 7) 报表/流程/校验器（报表/流程元信息可 su_env；校验器通常也用 su_env 生成）
        try:
            rcfg = su['app.report.config']._generate_from_reports(model)
            data["reports"] = rcfg.get_report_contract(filter_runtime=True)
            versions["reports"] = rcfg.version
        except KeyError:
            mark_missing("app.report.config")
            _logger.warning("app.report.config missing; fallback empty reports for model=%s", model)
            data["reports"] = []
            versions["reports"] = 0

        try:
            wcfg = su['app.workflow.config']._generate_from_workflow(model)
            data["workflow"] = wcfg.get_workflow_contract(filter_runtime=True)
            versions["workflow"] = wcfg.version
        except KeyError:
            mark_missing("app.workflow.config")
            _logger.warning("app.workflow.config missing; fallback empty workflow for model=%s", model)
            data["workflow"] = {}
            versions["workflow"] = 0

        try:
            vcfg2 = su['app.validator.config']._generate_from_validators(model)
            data["validator"] = vcfg2.get_validator_contract()
            versions["validator"] = vcfg2.version
        except KeyError:
            mark_missing("app.validator.config")
            _logger.warning("app.validator.config missing; fallback empty validator for model=%s", model)
            data["validator"] = {}
            versions["validator"] = 0

        # 8) head（标题/ACL 概览/上下文）
        #    - ACL 概览继续用 check_access_rights（仅四权），与 permissions.effective.rights 一致
        can_create = env[model].check_access_rights('create', raise_exception=False)
        if isinstance(effective_context, dict) and effective_context.get("create") is False:
            can_create = False
        data["head"] = {
            "title": self._resolve_page_title(model, action),
            "model": model,
            "view_type": ",".join(view_types),
            "action_id": action.get('id') if isinstance(action, dict) else None,
            "domain": action_domain,
            "domain_raw": action_domain_raw,
            "context": effective_context,
            "context_raw": action_context_raw,
            "permissions": {
                "read": env[model].check_access_rights('read', raise_exception=False),
                "write": env[model].check_access_rights('write', raise_exception=False),
                "create": can_create,
                "unlink": env[model].check_access_rights('unlink', raise_exception=False),
            }
        }
        if requested_record_id and requested_record_id > 0:
            data["head"]["record_id"] = requested_record_id
            data["head"]["res_id"] = requested_record_id
        if requested_render_profile:
            data["head"]["render_profile"] = requested_render_profile
        data["domain"] = action_domain
        data["domain_raw"] = action_domain_raw
        data["context"] = effective_context
        data["context_raw"] = action_context_raw
        self._inject_create_defaults(
            data,
            model_name=model,
            render_profile=requested_render_profile,
        )
        self._inject_record_version_contract(
            data,
            model_name=model,
            record_id=requested_record_id,
            render_profile=requested_render_profile,
        )
        self._inject_form_ui_labels(data)
        self._inject_form_business_actions(
            data,
            model_name=model,
            record_id=requested_record_id,
            render_profile=requested_render_profile,
        )
        self._inject_current_form_settings_action(
            data,
            model_name=model,
            action_id=action.get("id") if isinstance(action, dict) else None,
            view_id=requested_view_id,
            render_profile=requested_render_profile,
        )
        self._inject_business_category_form_policy(
            data,
            model_name=model,
            render_profile=requested_render_profile,
        )
        self._normalize_model_specific_form_contract(data, model_name=model)
        self._apply_render_profile_action_visibility(
            data,
            render_profile=requested_render_profile,
            record_id=requested_record_id,
        )
        self._sync_visible_form_required_markers(data)

        # 8.x) 访问策略（后端唯一决策点）：allow/degrade/block
        self._apply_access_policy(data, model_name=model)
        if isinstance(data.get("head"), dict) and isinstance(data.get("access_policy"), dict):
            data["head"]["access_policy"] = dict(data.get("access_policy") or {})

        # 9) with_data：首屏数据（列表/表单）——必须用“当前用户 env”以自动应用记录规则
        if p.get("with_data"):
            data["data"] = self._fetch_initial_data(env, model, view_types, p, data)

        if missing_models:
            data["degraded"] = True
            data["missing_models"] = missing_models
        if warnings:
            data["warnings"] = warnings
        data["source_authority"] = self.source_authority_contract()
        return data, versions

    def _native_action_needs_existing_record(self, action: dict) -> bool:
        if not isinstance(action, dict):
            return False
        payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
        kind = str(action.get("kind") or "").strip().lower()
        level = str(action.get("level") or "").strip().lower()
        intent = str(action.get("intent") or "").strip().lower()
        button_type = str(action.get("buttonType") or action.get("button_type") or payload.get("type") or "").strip().lower()
        method = str(action.get("method") or action.get("name") or payload.get("method") or "").strip()
        has_open_target = bool(
            action.get("action_id")
            or action.get("actionId")
            or payload.get("action_id")
            or payload.get("ref")
            or payload.get("url")
            or action.get("url")
        )
        if kind in {"open", "url", "client"} or button_type in {"action", "url"} or intent in {"open", "url"}:
            return False
        if intent.startswith("ui."):
            return False
        if has_open_target and kind not in {"object", "server", "mutation"} and button_type not in {"object"}:
            return False
        if kind in {"object", "server", "mutation"} or button_type == "object":
            return True
        if level in {"row", "smart"}:
            return True
        if method:
            return True
        return not kind and not button_type

    def _filter_render_profile_actions(self, rows, *, profile: str, record_id=None):
        if not isinstance(rows, list):
            return []
        if profile != "create" or record_id:
            return rows
        out = []
        for row in rows:
            if isinstance(row, dict) and self._native_action_needs_existing_record(row):
                continue
            out.append(row)
        return out

    def _filter_render_profile_layout_nodes(self, nodes, *, profile: str, record_id=None):
        if not isinstance(nodes, list):
            return []
        if profile != "create" or record_id:
            return nodes
        child_keys = ("children", "pages", "tabs", "nodes", "items")
        out = []
        for node in nodes:
            if not isinstance(node, dict):
                out.append(node)
                continue
            node_type = str(node.get("type") or node.get("containerType") or "").strip().lower()
            action = node.get("action") if isinstance(node.get("action"), dict) else {}
            button_payload = dict(action)
            if node.get("buttonType"):
                button_payload["buttonType"] = node.get("buttonType")
            if node.get("name") and "name" not in button_payload:
                button_payload["name"] = node.get("name")
            if node_type == "button" and self._native_action_needs_existing_record(button_payload):
                continue
            copied = dict(node)
            for key in child_keys:
                children = copied.get(key)
                if isinstance(children, list):
                    copied[key] = self._filter_render_profile_layout_nodes(
                        children,
                        profile=profile,
                        record_id=record_id,
                    )
            out.append(copied)
        return out

    def _apply_render_profile_action_visibility(self, data: dict, *, render_profile: str = "", record_id=None) -> None:
        if not isinstance(data, dict):
            return
        profile = str(render_profile or data.get("render_profile") or "").strip().lower()
        if profile in {"read", "view"}:
            profile = "readonly"
        if profile != "create" or record_id:
            return
        data["buttons"] = self._filter_render_profile_actions(data.get("buttons"), profile=profile, record_id=record_id)
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        for key in ("header", "sidebar", "footer"):
            toolbar[key] = self._filter_render_profile_actions(toolbar.get(key), profile=profile, record_id=record_id)
        data["toolbar"] = toolbar if isinstance(toolbar, dict) else {"header": [], "sidebar": [], "footer": []}
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        for key in ("header_buttons", "button_box", "stat_buttons", "business_actions"):
            form[key] = self._filter_render_profile_actions(form.get(key), profile=profile, record_id=record_id)
        form["layout"] = self._filter_render_profile_layout_nodes(form.get("layout"), profile=profile, record_id=record_id)
        views["form"] = form
        data["views"] = views

    def _remove_layout_field(self, raw, field_name: str):
        if isinstance(raw, list):
            return [
                item
                for item in (self._remove_layout_field(item, field_name) for item in raw)
                if item is not None
            ]
        if not isinstance(raw, dict):
            return raw
        node_name = str(raw.get("name") or "").strip()
        node_type = str(raw.get("type") or raw.get("kind") or "").strip().lower()
        if node_name == field_name and (node_type == "field" or raw.get("fieldInfo") or raw.get("field_info")):
            return None
        copied = dict(raw)
        for key in ("children", "pages", "tabs", "nodes", "items", "layout"):
            if key in copied:
                copied[key] = self._remove_layout_field(copied.get(key), field_name)
        return copied

    def _remove_field_from_groups(self, rows, field_name: str):
        if not isinstance(rows, list):
            return rows
        out = []
        for row in rows:
            if not isinstance(row, dict):
                out.append(row)
                continue
            copied = dict(row)
            fields = copied.get("fields")
            if isinstance(fields, list):
                copied["fields"] = [item for item in fields if str(item or "").strip() != field_name]
            out.append(copied)
        return out

    def _normalize_model_specific_form_contract(self, data: dict, *, model_name: str = "") -> None:
        if not isinstance(data, dict):
            return
        model = str(model_name or "").strip()
        fields_map = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        payload = call_extension_hook_first(
            self.env,
            "smart_core_model_specific_form_contract_policy",
            self.env,
            {"model": model, "fields": fields_map, "data": data},
        )
        if not isinstance(payload, dict):
            return
        remove_fields = [
            str(item or "").strip()
            for item in (payload.get("remove_fields") if isinstance(payload.get("remove_fields"), list) else [])
            if str(item or "").strip()
        ]
        if not remove_fields:
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        for field_name in remove_fields:
            form["layout"] = self._remove_layout_field(form.get("layout"), field_name)
        views["form"] = form
        data["views"] = views
        for field_name in remove_fields:
            data["field_groups"] = self._remove_field_from_groups(data.get("field_groups"), field_name)
        policy = data.get("business_form_policy") if isinstance(data.get("business_form_policy"), dict) else {}
        if policy:
            policy["layout_fields"] = [
                item for item in (policy.get("layout_fields") or []) if str(item or "").strip() not in remove_fields
            ]
            policy["fields"] = [
                item
                for item in (policy.get("fields") or [])
                if not isinstance(item, dict) or str(item.get("name") or item.get("field") or "").strip() not in remove_fields
            ]
            data["business_form_policy"] = policy

    def _json_value(self, raw, default):
        if isinstance(raw, type(default)):
            return raw
        if not isinstance(raw, str) or not raw.strip():
            return default
        try:
            parsed = json.loads(raw)
        except Exception:
            return default
        return parsed if isinstance(parsed, type(default)) else default

    def _business_category_from_context(self, data: dict, model_name: str):
        if "sc.business.category" not in self.env:
            return None
        context = data.get("context") if isinstance(data.get("context"), dict) else {}
        code = str(
            context.get("default_business_category_code")
            or context.get("current_business_category_code")
            or ""
        ).strip()
        if not code:
            return None
        try:
            return self.env["sc.business.category"].sudo().search(
                [("code", "=", code), ("target_model", "=", model_name)],
                limit=1,
            )
        except Exception:
            _logger.exception("business category form policy lookup failed model=%s code=%s", model_name, code)
            return None

    def _form_policy_field_policies(self, form_policy: dict, fields_map: dict) -> dict:
        policies = {}
        for row in form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
            if not name or name not in fields_map:
                continue
            policies[name] = row
        return policies

    def _form_policy_field_labels(self, form_policy: dict, fields_map: dict) -> dict:
        labels = {}
        for name, row in self._form_policy_field_policies(form_policy, fields_map).items():
            label = str(row.get("label") or row.get("string") or "").strip()
            if label:
                labels[name] = label
        return labels

    @staticmethod
    def _normalize_render_profile(profile: str) -> str:
        normalized = str(profile or "").strip().lower()
        if normalized in {"read", "view"}:
            return "readonly"
        return normalized if normalized in {"create", "edit", "readonly"} else ""

    @classmethod
    def _form_policy_profiles_match(cls, profiles, render_profile: str) -> bool:
        if not isinstance(profiles, list) or not profiles:
            return False
        normalized_profiles = {
            cls._normalize_render_profile(str(item or "").strip())
            for item in profiles
            if str(item or "").strip()
        }
        normalized_profiles.discard("")
        profile = cls._normalize_render_profile(render_profile)
        if profile:
            return profile in normalized_profiles
        return bool(normalized_profiles & {"create", "edit"})

    @classmethod
    def _form_policy_required_names_for_profile(cls, form_policy: dict, fields_map: dict, render_profile: str) -> list[str]:
        required = []
        for name in form_policy.get("required_fields") if isinstance(form_policy.get("required_fields"), list) else []:
            field_name = str(name or "").strip()
            if field_name and field_name in fields_map and field_name not in required:
                required.append(field_name)
        for row in form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []:
            if not isinstance(row, dict):
                continue
            field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
            if (
                field_name
                and field_name in fields_map
                and field_name not in required
                and cls._form_policy_profiles_match(row.get("required_profiles"), render_profile)
            ):
                required.append(field_name)
        return required

    @classmethod
    def _apply_form_policy_required_marker(
        cls,
        descriptor: dict,
        field_policy: dict,
        render_profile: str,
        *,
        required_field_names: set[str] | None = None,
        field_name: str = "",
    ) -> None:
        if not isinstance(descriptor, dict):
            return
        required_by_list = field_name and required_field_names is not None and field_name in required_field_names
        required_by_profile = cls._form_policy_profiles_match(field_policy.get("required_profiles"), render_profile)
        if required_by_list or required_by_profile:
            descriptor["required"] = True
            descriptor["source_required"] = True

    def _form_policy_one2many_subview(self, name: str, descriptor: dict, field_policy: dict | None = None) -> dict:
        field_policy = field_policy if isinstance(field_policy, dict) else {}
        columns_raw = (
            field_policy.get("one2many_columns")
            or field_policy.get("columns")
            or field_policy.get("subview_columns")
            or []
        )
        columns = [
            str(column or "").strip()
            for column in columns_raw
            if str(column or "").strip()
        ] if isinstance(columns_raw, list) else []
        if not columns:
            return {}
        relation = str((descriptor or {}).get("relation") or "").strip()
        if not relation or relation not in self.env:
            return {}
        try:
            relation_fields = self.env[relation].sudo().fields_get(columns)
        except Exception:
            _logger.debug("business category one2many subview metadata skipped field=%s relation=%s", name, relation, exc_info=True)
            relation_fields = {}
        column_nodes = []
        for column in columns:
            meta = relation_fields.get(column) if isinstance(relation_fields.get(column), dict) else {}
            if not meta:
                continue
            column_nodes.append({
                "name": column,
                "label": str(meta.get("string") or column).strip() or column,
                "string": str(meta.get("string") or column).strip() or column,
                "ttype": str(meta.get("type") or "char").strip() or "char",
                "required": bool(meta.get("required")),
                "readonly": bool(meta.get("readonly")),
                **({"selection": meta.get("selection")} if isinstance(meta.get("selection"), list) else {}),
            })
        if not column_nodes:
            return {}
        return {
            "tree": {
                "columns": column_nodes,
            },
            "policies": {
                "can_create": True,
                "can_write": True,
                "can_delete": True,
                "ui_labels": {
                    "add_row": "添加行",
                },
            },
        }

    def _make_form_policy_field_node(
        self,
        name: str,
        fields_map: dict,
        field_labels: dict | None = None,
        field_policies: dict | None = None,
        render_profile: str = "",
        required_field_names: set[str] | None = None,
    ) -> dict:
        descriptor = dict(fields_map.get(name) if isinstance(fields_map.get(name), dict) else {})
        field_policy = (field_policies or {}).get(name) if isinstance((field_policies or {}).get(name), dict) else {}
        self._apply_form_policy_required_marker(
            descriptor,
            field_policy,
            render_profile,
            required_field_names=required_field_names,
            field_name=name,
        )
        labels = field_labels if isinstance(field_labels, dict) else {}
        label = str(labels.get(name) or (descriptor or {}).get("string") or (descriptor or {}).get("label") or name).strip()
        node = {"type": "field", "name": name}
        field_info = {"name": name}
        if label:
            node["string"] = label
            node["label"] = label
            field_info["label"] = label
        for key in ("type", "relation", "relation_field", "selection", "required", "readonly"):
            if key in descriptor:
                field_info[key] = descriptor[key]
        subview = self._form_policy_one2many_subview(name, descriptor, field_policy)
        if subview:
            field_info["subview"] = subview
        if len(field_info) > 1 or subview:
            node["fieldInfo"] = field_info
        return node

    @staticmethod
    def _has_explicit_user_form_layout(data: dict) -> bool:
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout = form.get("layout")
        user_layout_names = {
            "sc_custom_partner_flat_fields",
            "sc_custom_user_flat_fields",
        }

        def visit(node):
            if isinstance(node, dict):
                if str(node.get("name") or "").strip() in user_layout_names:
                    return True
                return any(visit(value) for value in node.values())
            if isinstance(node, list):
                return any(visit(item) for item in node)
            return False

        return visit(layout)

    def _inject_business_category_form_policy(self, data: dict, *, model_name: str, render_profile: str = "") -> None:
        if not isinstance(data, dict) or not model_name:
            return
        category = self._business_category_from_context(data, model_name)
        if not category:
            return
        form_policy = self._json_value(getattr(category, "form_policy_json", "{}") or "{}", {})
        required_fields = self._json_value(getattr(category, "required_fields_json", "[]") or "[]", [])
        if not form_policy and not required_fields:
            return
        fields_map = dict(data.get("fields") if isinstance(data.get("fields"), dict) else {})
        if not fields_map:
            return
        normalized_required = [
            str(name or "").strip()
            for name in required_fields
            if str(name or "").strip() in fields_map
        ]
        if normalized_required:
            form_policy = dict(form_policy or {})
            existing_required = form_policy.get("required_fields")
            merged = []
            for name in (existing_required if isinstance(existing_required, list) else []) + normalized_required:
                field_name = str(name or "").strip()
                if field_name and field_name in fields_map and field_name not in merged:
                    merged.append(field_name)
            form_policy["required_fields"] = merged
        sections = form_policy.get("sections") if isinstance(form_policy.get("sections"), list) else []
        layout_children = []
        field_groups = []
        seen_fields = set()
        one2many_subviews = {}
        policy_field_policies = self._form_policy_field_policies(form_policy, fields_map)
        policy_field_labels = self._form_policy_field_labels(form_policy, fields_map)
        profile = self._normalize_render_profile(render_profile)
        profile_required_names = self._form_policy_required_names_for_profile(form_policy, fields_map, profile)
        profile_required_set = set(profile_required_names)
        for name in profile_required_names:
            descriptor = dict(fields_map.get(name) if isinstance(fields_map.get(name), dict) else {})
            self._apply_form_policy_required_marker(
                descriptor,
                policy_field_policies.get(name) if isinstance(policy_field_policies.get(name), dict) else {},
                profile,
                required_field_names=profile_required_set,
                field_name=name,
            )
            if descriptor:
                fields_map[name] = descriptor
        field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
        field_policies = dict(field_policies or {})
        for name, field_policy in policy_field_policies.items():
            policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
            policy = dict(policy or {})
            for key in ("visible_profiles", "readonly_profiles", "required_profiles"):
                if isinstance(field_policy.get(key), list):
                    policy[key] = list(field_policy.get(key) or [])
            if name in profile_required_set:
                policy["source_required"] = True
            if policy:
                field_policies[name] = policy
        for name in profile_required_names:
            policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
            policy = dict(policy or {})
            policy["source_required"] = True
            field_policies[name] = policy
        if field_policies:
            data["field_policies"] = field_policies

        validation_rules = data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []
        existing_required_rules = {
            str(row.get("field") or "").strip()
            for row in validation_rules
            if isinstance(row, dict) and str(row.get("code") or "").strip().upper() == "REQUIRED"
        }
        for name in profile_required_names:
            if name in existing_required_rules:
                continue
            validation_rules.append({
                "code": "REQUIRED",
                "field": name,
                "source": "sc.business.category.form_policy_json",
                "when_profiles": ["create", "edit"],
            })
            existing_required_rules.add(name)
        if validation_rules:
            data["validation_rules"] = validation_rules
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            visible_profiles = section.get("visible_profiles")
            if isinstance(visible_profiles, list) and visible_profiles:
                allowed_profiles = {str(item).strip().lower() for item in visible_profiles if str(item).strip()}
                if profile and profile not in allowed_profiles:
                    continue
            title = str(section.get("title") or section.get("label") or section.get("name") or "").strip()
            names = []
            for raw_name in section.get("fields") if isinstance(section.get("fields"), list) else []:
                name = str(raw_name or "").strip()
                if name and name in fields_map and name not in names:
                    names.append(name)
            if not names:
                continue
            seen_fields.update(names)
            group_name = str(section.get("name") or f"business_category_section_{index + 1}").strip()
            field_nodes = [
                self._make_form_policy_field_node(
                    name,
                    fields_map,
                    policy_field_labels,
                    policy_field_policies,
                    render_profile=profile,
                    required_field_names=profile_required_set,
                )
                for name in names
            ]
            for field_node in field_nodes:
                field_name = str(field_node.get("name") or "").strip()
                field_info = field_node.get("fieldInfo") if isinstance(field_node.get("fieldInfo"), dict) else {}
                if not field_name or not field_info:
                    continue
                descriptor = dict(fields_map.get(field_name) if isinstance(fields_map.get(field_name), dict) else {})
                self._apply_form_policy_required_marker(
                    descriptor,
                    policy_field_policies.get(field_name) if isinstance(policy_field_policies.get(field_name), dict) else {},
                    profile,
                    required_field_names=profile_required_set,
                    field_name=field_name,
                )
                for key in ("type", "relation", "relation_field", "selection", "required", "readonly"):
                    if key in field_info:
                        descriptor[key] = field_info[key]
                        if key == "type":
                            descriptor.setdefault("ttype", field_info[key])
                if field_info.get("label"):
                    descriptor.setdefault("string", field_info["label"])
                    descriptor.setdefault("label", field_info["label"])
                if field_info.get("subview"):
                    one2many_subviews[field_name] = field_info["subview"]
                if descriptor:
                    fields_map[field_name] = descriptor
            layout_children.append({
                "type": "group",
                "name": group_name,
                "string": title or group_name,
                "children": field_nodes,
            })
            field_groups.append({
                "name": group_name,
                "label": title or group_name,
                "priority": int(section.get("sequence") or (index + 1) * 10),
                "collapsible": bool(section.get("collapsible", False)),
                "collapsed_by_default": bool(section.get("collapsed_by_default", False)),
                "visible_profiles": [str(item).strip() for item in visible_profiles if str(item).strip()]
                if isinstance(visible_profiles, list) else [],
                "fields": names,
            })
        if layout_children:
            views = data.get("views") if isinstance(data.get("views"), dict) else {}
            form = views.get("form") if isinstance(views.get("form"), dict) else {}
            if not self._has_explicit_user_form_layout(data):
                form["layout"] = [{
                    "type": "sheet",
                    "name": "business_category_form_sheet",
                    "children": layout_children,
                }]
            if one2many_subviews:
                subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}
                form["subviews"] = {**subviews, **one2many_subviews}
            views["form"] = form
            data["views"] = views
        data["fields"] = fields_map
        if field_groups:
            data["field_groups"] = field_groups
        policy_fields = form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []
        data["business_form_policy"] = {
            "source": "sc.business.category.form_policy_json",
            "category_id": category.id,
            "category_code": str(category.code or "").strip(),
            "category_name": str(category.name or "").strip(),
            "target_model": model_name,
            "render_profile": str(render_profile or "").strip(),
            "required_fields": profile_required_names,
            "fields": policy_fields,
            "field_labels": policy_field_labels,
            "layout_fields": list(seen_fields),
        }

    def _include_configured_orchestrated_view_types(self, view_types, *, model_name="", action_id=None):
        normalized = self.normalize_view_types(view_types)
        model = str(model_name or "").strip()
        if not model or "ui.business.config.contract" not in self.env:
            return normalized
        try:
            action_id_int = int(action_id or 0)
        except Exception:
            action_id_int = 0
        domain = [("model", "=", model), ("status", "=", "published")]
        if action_id_int > 0:
            domain.append(("action_id", "in", [False, action_id_int]))
        else:
            domain.append(("action_id", "=", False))
        try:
            rows = self.env["ui.business.config.contract"].sudo().search(domain)
        except Exception:
            _logger.exception("include configured orchestrated view types failed for model=%s action_id=%s", model, action_id_int)
            return normalized
        allowed = {"tree", "form", "kanban", "search", "pivot", "graph", "calendar", "gantt", "activity", "dashboard"}
        out = list(normalized)
        for row in rows:
            view_type = str(getattr(row, "view_type", "") or "").strip()
            if view_type == "list":
                view_type = "tree"
            if view_type in allowed and view_type not in out:
                out.append(view_type)
        return out

    def _inject_create_defaults(self, data, model_name="", render_profile=""):
        if str(render_profile or "").strip().lower() != "create":
            return
        model = str(model_name or "").strip()
        if not model or model not in self.env:
            return
        try:
            Model = self.env[model].with_context(**(data.get("context") or {}))
            fields_map = Model.fields_get()
            field_names = [name for name in fields_map.keys() if name not in {"id", "display_name"}]
            defaults = Model.default_get(field_names) if field_names else {}
        except Exception:
            _logger.exception("inject create defaults failed for model=%s", model)
            return
        if not isinstance(defaults, dict) or not defaults:
            return
        normalized = {}
        for name, value in defaults.items():
            meta = fields_map.get(name) or {}
            if meta.get("type") == "many2one" and value:
                try:
                    relation = str(meta.get("relation") or "").strip()
                    record = self.env[relation].browse(int(value)).exists() if relation and relation in self.env else None
                    normalized[name] = [int(value), record.display_name if record else "#%s" % value]
                except Exception:
                    normalized[name] = value
            else:
                normalized[name] = value
        data["record"] = {**(data.get("record") or {}), **normalized}

    def _resolve_action_from_payload(self, p, model):
        raw_action_id = p.get("action_id") or p.get("actionId")
        try:
            action_id = int(raw_action_id or 0)
        except Exception:
            action_id = 0
        if action_id <= 0:
            return None
        action = self.su_env["ir.actions.act_window"].browse(action_id)
        if not action.exists() or action.res_model != model:
            return None
        return {
            "id": action.id,
            "name": action.name or "",
            "context": action.context or "{}",
            "domain": action.domain or "[]",
        }

    def _resolve_page_title(self, model, action=None):
        if isinstance(action, dict):
            title = str(action.get("name") or "").strip()
            if title:
                return title
        model_row = self.su_env["ir.model"].search([("model", "=", model)], limit=1)
        title = str(getattr(model_row, "name", "") or "").strip()
        return title or model

    def _inject_record_version_contract(self, data, model_name="", record_id=None, render_profile=""):
        if not isinstance(data, dict):
            return
        model = str(model_name or "").strip()
        profile = str(render_profile or data.get("render_profile") or "").strip().lower()
        if profile != "edit" or not record_id or int(record_id or 0) <= 0:
            return
        policy = {
            "enabled": True,
            "strategy": "write_date_if_match",
            "token_field": "write_date",
            "request_param": "if_match",
            "write_intent": "api.data",
            "write_operation": "write",
            "conflict_reason_code": "RECORD_VERSION_CONFLICT",
            "conflict_message": "数据已被其他操作更新，请重新加载后再保存。",
            "reload_action": "reload_record",
        }
        data["record_version"] = policy
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        head["record_version"] = dict(policy)
        data["head"] = head

    def _inject_form_ui_labels(self, data):
        if not isinstance(data, dict):
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return
        labels = form.get("ui_labels") if isinstance(form.get("ui_labels"), dict) else {}
        labels.setdefault("save", _("保存"))
        labels.setdefault("saving", _("保存中..."))
        labels.setdefault("discard", _("放弃"))
        labels.setdefault("reload", _("重新加载"))
        labels.setdefault("save_success", _("保存成功，已同步最新表单内容。"))
        form["ui_labels"] = labels
        attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}
        if attachments.get("enabled") is True:
            attachment_labels = attachments.get("ui_labels") if isinstance(attachments.get("ui_labels"), dict) else {}
            attachment_labels.setdefault("delete", _("删除"))
            attachment_labels.setdefault("delete_denied", _("当前不允许删除附件"))
            attachment_labels.setdefault("delete_failed", _("附件删除失败"))
            delete_policy = resolve_unlink_policy(self.env, "ir.attachment")
            attachments["delete"] = {
                "intent": "api.data.unlink",
                "model": "ir.attachment",
                "enabled": bool(delete_policy.get("allowed")) and str(delete_policy.get("delete_mode") or "") == "unlink",
                "delete_policy": delete_policy,
            }
            attachments["ui_labels"] = attachment_labels
            form["attachments"] = attachments
        views["form"] = form
        data["views"] = views

    def _inject_form_business_actions(self, data, model_name="", record_id=None, render_profile=""):
        if not isinstance(data, dict):
            return
        model = str(model_name or "").strip()
        profile = str(render_profile or data.get("render_profile") or "").strip().lower()
        if not model or profile != "edit" or not record_id or int(record_id or 0) <= 0:
            return
        payload = call_extension_hook_first(
            self.env,
            "smart_core_form_business_actions",
            self.env,
            model,
            int(record_id or 0),
            data,
        )
        if not isinstance(payload, dict):
            return
        actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []
        if not actions:
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        header_buttons = form.get("header_buttons") if isinstance(form.get("header_buttons"), list) else []
        by_method = {
            str(row.get("method") or "").strip(): row
            for row in actions
            if isinstance(row, dict) and str(row.get("method") or "").strip()
        }
        for button in header_buttons:
            if not isinstance(button, dict):
                continue
            method = str(button.get("name") or "").strip()
            action = by_method.get(method)
            if not action:
                payload_obj = button.get("payload") if isinstance(button.get("payload"), dict) else {}
                method = str(payload_obj.get("method") or "").strip()
                action = by_method.get(method)
            if not action:
                continue
            button["key"] = str(action.get("key") or button.get("key") or button.get("name") or "").strip()
            button["business_action"] = dict(action)
            button["allowed"] = bool(action.get("allowed"))
            button["reason_code"] = str(action.get("reason_code") or "")
            button["blocked_message"] = str(action.get("blocked_message") or "")
            button["warning_message"] = str(action.get("warning_message") or "")
            button["advisory_warnings"] = action.get("advisory_warnings") if isinstance(action.get("advisory_warnings"), list) else []
            button["advisory_reason_codes"] = action.get("advisory_reason_codes") if isinstance(action.get("advisory_reason_codes"), list) else []
            button["force_block_available"] = bool(action.get("force_block_available"))
            button["suggested_action"] = str(action.get("suggested_action") or "")
            button["required_role_key"] = str(action.get("required_role_key") or "")
            button["required_role_label"] = str(action.get("required_role_label") or "")
            button["handoff_required"] = bool(action.get("handoff_required"))
            button["handoff_hint"] = str(action.get("handoff_hint") or "")
            button["mutation"] = action.get("mutation") if isinstance(action.get("mutation"), dict) else {}
            button["refresh_policy"] = action.get("refresh_policy") if isinstance(action.get("refresh_policy"), dict) else {}
            if "semantic" not in button:
                button["semantic"] = "primary_action" if bool(action.get("primary")) else "secondary_action"
        form["header_buttons"] = header_buttons
        form["business_actions"] = actions
        attachments = payload.get("attachments") if isinstance(payload.get("attachments"), dict) else {}
        if attachments:
            current_attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}
            merged_attachments = dict(current_attachments)
            merged_attachments.update(attachments)
            form["attachments"] = merged_attachments
        views["form"] = form
        data["views"] = views

    def _business_config_admin_group_xmlids(self):
        hook_groups = call_extension_hook_first(
            self.env,
            "smart_core_business_config_admin_group_xmlids",
            self.env,
        )
        if isinstance(hook_groups, (list, tuple, set)):
            groups = [str(item or "").strip() for item in hook_groups if str(item or "").strip()]
            if groups:
                return groups
        try:
            raw = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.business_config_admin_group_xmlids",
                "",
            )
        except Exception:
            raw = ""
        groups = [item.strip() for item in str(raw or "").split(",") if item.strip()]
        return groups or ["smart_core.group_smart_core_business_config_admin"]

    def _business_config_form_settings_refs(self):
        refs = call_extension_hook_first(
            self.env,
            "smart_core_business_config_form_settings_refs",
            self.env,
        )
        if isinstance(refs, dict):
            action_xmlid = str(refs.get("action_xmlid") or "").strip()
            menu_xmlid = str(refs.get("menu_xmlid") or "").strip()
            if action_xmlid and menu_xmlid:
                return action_xmlid, menu_xmlid
        try:
            Config = self.env["ir.config_parameter"].sudo()
            action_xmlid = str(Config.get_param("smart_core.business_config.form_settings_action_xmlid", "") or "").strip()
            menu_xmlid = str(Config.get_param("smart_core.business_config.form_settings_menu_xmlid", "") or "").strip()
        except Exception:
            action_xmlid = ""
            menu_xmlid = ""
        return action_xmlid, menu_xmlid

    def _is_business_config_admin(self):
        for group_xmlid in self._business_config_admin_group_xmlids():
            try:
                if self.env.user.has_group(group_xmlid):
                    return True
            except Exception:
                continue
        return False

    def _ref_or_empty(self, xmlid):
        try:
            return self.env.ref(xmlid, raise_if_not_found=False)
        except Exception:
            return self.env["ir.model"].browse()

    def _inject_current_form_settings_action(self, data, model_name="", action_id=None, view_id=None, render_profile=""):
        if not isinstance(data, dict):
            return
        model = str(model_name or "").strip()
        if not model or model not in self.env:
            return
        if is_business_config_runtime_model(model):
            return
        if str(render_profile or data.get("render_profile") or "").strip().lower() not in {"create", "edit", "readonly"}:
            return
        current_action_id = int(action_id or 0)
        if current_action_id <= 0:
            return
        if not self._is_business_config_admin():
            return
        try:
            if not self.env["ui.form.field.policy"].check_access_rights("create", raise_exception=False):
                return
        except Exception:
            return
        model_rec = self.su_env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model_rec.transient:
            return
        settings_action_xmlid, settings_menu_xmlid = self._business_config_form_settings_refs()
        if not settings_action_xmlid or not settings_menu_xmlid:
            return
        settings_action = self._ref_or_empty(settings_action_xmlid)
        settings_menu = self._ref_or_empty(settings_menu_xmlid)
        if not settings_action or not settings_action.exists() or not settings_menu or not settings_menu.exists():
            return
        current_view_id = int(view_id or 0)
        action = {
            "key": BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_SETTINGS,
            "label": "表单设置",
            "kind": "client",
            "level": "header",
            "selection": "none",
            "allowed": True,
            "semantic": "secondary_action",
            "intent": "ui.local_mode",
            "trigger": "click",
            "sourceWidgetId": "page.header",
            "target_scope": "page",
            "visible_profiles": ["create", "edit", "readonly"],
            "payload": {
                "mode": BUSINESS_CONFIG_MODES["form_field"],
                "toggle": True,
            },
            "target": {
                "mode": BUSINESS_CONFIG_MODES["form_field"],
                "toggle": True,
            },
            "target_model": BUSINESS_CONFIG_AUTHORITIES["form_field_policy"],
            "context": {
                "source": "current_form_contract",
                "source_model": model,
                "source_action_id": current_action_id,
            },
            "source_authority": {
                "kind": self.SOURCE_KIND,
                "authorities": [
                    BUSINESS_CONFIG_AUTHORITIES["contract"],
                    BUSINESS_CONFIG_AUTHORITIES["contract_version"],
                    BUSINESS_CONFIG_AUTHORITIES["form_field_policy"],
                    "ir.actions.act_window",
                    "ir.ui.menu",
                ],
                "projection_only": True,
                "no_business_fact_authority": True,
                "owner_layer": BUSINESS_CONFIG_OWNER_LAYER,
            },
        }
        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        buttons = [row for row in buttons if not (isinstance(row, dict) and row.get("key") == action["key"])]
        buttons.append(action)
        data["buttons"] = buttons
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        header = [row for row in header if not (isinstance(row, dict) and row.get("key") == action["key"])]
        header.append(action)
        toolbar["header"] = header
        toolbar.setdefault("sidebar", [])
        toolbar.setdefault("footer", [])
        data["toolbar"] = toolbar
        self._inject_current_form_settings_action_rules(
            data,
            model=model,
            model_rec=model_rec,
            action_id=current_action_id,
            view_id=current_view_id,
        )
        governance = data.get("governance") if isinstance(data.get("governance"), dict) else {}
        governance[BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_SETTINGS] = {
            "enabled": True,
            "model": model,
            "model_label": model_rec.name,
            "model_id": int(model_rec.id),
            "action_id": current_action_id,
            "view_id": current_view_id if current_view_id > 0 else False,
            "settings_action_id": int(settings_action.id),
            "settings_menu_id": int(settings_menu.id),
            "config_source": BUSINESS_CONFIG_AUTHORITIES["contract"],
            "owner_layer": BUSINESS_CONFIG_OWNER_LAYER,
        }
        data["governance"] = governance

    def _inject_current_form_settings_action_rules(self, data, *, model, model_rec, action_id, view_id):
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        if not fields:
            return
        mode = BUSINESS_CONFIG_MODES["form_field"]
        low_code_mode = BUSINESS_CONFIG_MODES["lowcode"]
        config_summary = self._current_view_orchestration_config_summary(
            model=model,
            view_type="form",
            action_id=action_id,
            view_id=view_id,
        )
        action_rows = [
            {
                "key": BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_ADD_CUSTOM_FIELD,
                "label": "添加字段",
                "kind": "intent",
                "intent": FORM_FIELD_CONFIG_INTENTS["custom_field_create"],
                "trigger": "click",
                "sourceWidgetId": "mode.%s" % mode,
                "target_scope": "mode",
                "target": {
                    "mode": mode,
                    "success_message": "字段已添加",
                    "params": {
                        "model": model,
                        "action_id": int(action_id or 0),
                        "view_id": int(view_id or 0),
                        "view_type": "form",
                    },
                    "prompt_schema": {
                        "fields": [
                            {"name": "label", "label": "字段标题", "type": "char", "required": True},
                            {
                                "name": "ttype",
                                "label": "字段类型",
                                "type": "selection",
                                "required": True,
                                "default": "char",
                                "options": [
                                    {"value": "char", "label": "单行文本"},
                                    {"value": "text", "label": "多行文本"},
                                    {"value": "integer", "label": "整数"},
                                    {"value": "float", "label": "小数"},
                                    {"value": "boolean", "label": "是/否"},
                                    {"value": "date", "label": "日期"},
                                    {"value": "datetime", "label": "日期时间"},
                                    {"value": "html", "label": "富文本"},
                                ],
                            },
                        ],
                    },
                },
            },
            {
                "key": BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_ORDER_SAVE,
                "label": "保存表单设置",
                "kind": "intent",
                "intent": BUSINESS_CONFIG_INTENTS["lowcode_apply"],
                "trigger": "submit",
                "sourceWidgetId": "mode.%s" % mode,
                "target_scope": "mode",
                "target": {
                    "mode": mode,
                    "low_code_mode": low_code_mode,
                    "success_message": "字段顺序已更新",
                    "params": {
                        "model": model,
                        "action_id": int(action_id or 0),
                        "view_id": int(view_id or 0),
                        "view_type": "form",
                    },
                },
            },
        ]
        policy_rows = self.su_env["ui.form.field.policy"]._effective_policies(
            model,
            action_id=int(action_id or 0),
            view_id=int(view_id or 0),
            user=self.env.user,
        )
        policy_by_field = {
            str(policy.field_name or "").strip(): policy
            for policy in policy_rows
            if str(policy.field_name or "").strip()
        }
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form_view = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout_field_names = set()
        layout_field_names.update(self._collect_layout_field_names(data.get("layout")))
        layout_field_names.update(self._collect_layout_field_names(form_view.get("layout")))
        layout_field_names.update(str(name or "").strip() for name in fields.keys() if str(name or "").strip())
        eligible_names = sorted(set(layout_field_names) | set(policy_by_field.keys()))
        if not eligible_names:
            return
        field_rows = self.su_env["ir.model.fields"].search([
            ("model", "=", model),
            ("name", "in", sorted(eligible_names)),
            ("ttype", "!=", "binary"),
        ])
        field_by_name = {field.name: field for field in field_rows}
        ordered_names = sorted(
            eligible_names,
            key=lambda name: (
                int((policy_by_field.get(name).sequence if policy_by_field.get(name) else 100) or 100),
                name,
            ),
        )
        for field_name in ordered_names:
            meta = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
            field = field_by_name.get(field_name)
            if not field:
                continue
            label = str((meta or {}).get("string") or (meta or {}).get("label") or field.field_description or field_name).strip()
            policy = policy_by_field.get(field_name)
            current_visible = bool(policy.visible) if policy else True
            base_params = {
                "model": model,
                "model_id": int(model_rec.id),
                "field_name": field_name,
                "label": label,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "view_type": "form",
            }
            for visible, value, label_text in ((True, "show", "显示"), (False, "hide", "隐藏")):
                action_rows.append({
                    "key": "current_form_field_%s_%s" % (field_name, value),
                    "label": "%s%s" % (label_text, label),
                    "kind": "intent",
                    "intent": FORM_FIELD_CONFIG_INTENTS["policy_set"],
                    "trigger": "change",
                    "sourceWidgetId": "field.%s" % field_name,
                    "target_scope": "widget",
                    "target": {
                        "mode": mode,
                        "success_message": "字段配置已更新",
                        "control": {
                            "type": "radio",
                            "name": "field_visibility",
                            "value": value,
                            "label": label_text,
                            "checked": bool(visible) == current_visible,
                        },
                        "params": {
                            **base_params,
                            "visible": bool(visible),
                        },
                    },
                })
        groups = data.get("action_groups") if isinstance(data.get("action_groups"), list) else []
        group_key = BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_CONFIGURATION
        groups = [row for row in groups if not (isinstance(row, dict) and row.get("key") == group_key)]
        groups.append({
            "key": group_key,
            "label": "业务配置（低代码）",
            "sourceWidgetId": "mode.%s" % mode,
            "mode_aliases": [mode, low_code_mode],
            "low_code_config": {
                "enabled": True,
                "scope": "current_form",
                "capabilities": ["field_order", "field_visibility", "custom_field_create"],
                "config_source": BUSINESS_CONFIG_AUTHORITIES["contract"],
                "config_contract": config_summary,
                "legacy_overlay": BUSINESS_CONFIG_AUTHORITIES["form_field_policy"],
            },
            "actions": action_rows,
            "source_authority": {
                "kind": self.SOURCE_KIND,
                "authorities": [
                    BUSINESS_CONFIG_AUTHORITIES["contract"],
                    BUSINESS_CONFIG_AUTHORITIES["contract_version"],
                    BUSINESS_CONFIG_AUTHORITIES["form_field_policy"],
                    BUSINESS_CONFIG_AUTHORITIES["custom_field_wizard"],
                    "ir.model.fields",
                ],
                "projection_only": True,
                "no_business_fact_authority": True,
                "owner_layer": BUSINESS_CONFIG_OWNER_LAYER,
            },
        })
        data["action_groups"] = groups

    def _current_view_orchestration_config_summary(self, *, model, view_type, action_id, view_id):
        if "ui.business.config.contract" not in self.su_env:
            return {"available": False, "reason": "model_missing"}
        try:
            contracts = self.su_env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                model,
                view_type=view_type,
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            )
        except Exception:
            _logger.exception("Failed to resolve view orchestration config summary for model=%s view_type=%s", model, view_type)
            return {"available": False, "reason": "resolve_failed"}
        items = []
        for rec in contracts[:5]:
            items.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "status": str(rec.status or ""),
                "version_no": int(rec.version_no or 1),
                "view_type": str(rec.view_type or ""),
                "action_id": int(rec.action_id.id or 0),
                "view_id": int(rec.view_id.id or 0),
                "role_key": str(rec.role_key or ""),
            })
        return {
            "available": True,
            "config_source": "ui.business.config.contract",
            "source_model": BUSINESS_CONFIG_AUTHORITIES["contract"],
            "owner_layer": "business_view_orchestration",
            "items": items,
        }

    def _collect_layout_field_names(self, raw):
        names = set()

        def visit(node):
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if not isinstance(node, dict):
                return
            node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
            field_name = str(node.get("name") or "").strip()
            if field_name and (node_type == "field" or node.get("fieldInfo") or node.get("field_info")):
                names.add(field_name)
            for child_key in ("children", "pages", "tabs", "nodes", "items", "layout"):
                visit(node.get(child_key))

        visit(raw)
        return names

    def _collect_layout_required_field_names(self, raw):
        names = set()

        def visit(node):
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if not isinstance(node, dict):
                return
            node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
            field_name = str(node.get("name") or "").strip()
            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            field_info = field_info or (node.get("field_info") if isinstance(node.get("field_info"), dict) else {})
            if field_name and (node_type == "field" or field_info):
                if node.get("required") is True or field_info.get("required") is True:
                    names.add(field_name)
            for child_key in ("children", "pages", "tabs", "nodes", "items", "layout"):
                visit(node.get(child_key))

        visit(raw)
        return names

    def _mark_layout_required_field_nodes(self, raw, required_names):
        names = {
            str(name or "").strip()
            for name in (required_names or [])
            if str(name or "").strip()
        }
        if not names:
            return

        def visit(node):
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if not isinstance(node, dict):
                return
            node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
            field_name = str(node.get("name") or "").strip()
            if field_name in names and (node_type == "field" or node.get("fieldInfo") or node.get("field_info")):
                node["required"] = True
                field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
                field_info = dict(field_info or {})
                field_info["required"] = True
                node["fieldInfo"] = field_info
            for child_key in ("children", "pages", "tabs", "nodes", "items", "layout"):
                visit(node.get(child_key))

        visit(raw)

    @staticmethod
    def _contract_validation_required_field_names(data):
        names = set()
        validation_rules = data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []
        for row in validation_rules:
            if not isinstance(row, dict):
                continue
            if str(row.get("code") or "").strip().upper() != "REQUIRED":
                continue
            field_name = str(row.get("field") or "").strip()
            if field_name:
                names.add(field_name)
        return names

    @staticmethod
    def _contract_policy_required_field_names(data):
        names = set()
        field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
        for name, policy in field_policies.items():
            if not isinstance(policy, dict):
                continue
            field_name = str(name or "").strip()
            if not field_name:
                continue
            if (
                policy.get("source_required") is True
                or policy.get("required") is True
                or bool(policy.get("required_profiles") if isinstance(policy.get("required_profiles"), list) else [])
            ):
                names.add(field_name)
        return names

    def _sync_visible_form_required_markers(self, data):
        if not isinstance(data, dict):
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return
        layout = form.get("layout")
        visible_fields = self._collect_layout_field_names(layout)
        if not visible_fields:
            return
        fields_map = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        if not fields_map:
            return
        explicit_required = self._collect_layout_required_field_names(layout)
        validation_required = self._contract_validation_required_field_names(data)
        policy_required = self._contract_policy_required_field_names(data)
        required_names = []
        for name in sorted(visible_fields):
            descriptor = fields_map.get(name) if isinstance(fields_map.get(name), dict) else {}
            if not descriptor:
                continue
            if descriptor.get("readonly") is True:
                continue
            if (
                descriptor.get("required") is True
                or name in explicit_required
                or name in validation_required
                or name in policy_required
            ):
                required_names.append(name)
        if not required_names:
            return

        for name in required_names:
            descriptor = dict(fields_map.get(name) if isinstance(fields_map.get(name), dict) else {})
            descriptor["required"] = True
            descriptor["source_required"] = True
            fields_map[name] = descriptor
        data["fields"] = fields_map

        field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
        field_policies = dict(field_policies or {})
        for name in required_names:
            policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
            policy = dict(policy or {})
            policy["source_required"] = True
            field_policies[name] = policy
        data["field_policies"] = field_policies

        validation_rules = data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []
        existing = {
            str(row.get("field") or "").strip()
            for row in validation_rules
            if isinstance(row, dict) and str(row.get("code") or "").strip().upper() == "REQUIRED"
        }
        for name in required_names:
            if name in existing:
                continue
            validation_rules.append({
                "code": "REQUIRED",
                "field": name,
                "source": "visible_form_required_marker",
                "when_profiles": ["create", "edit"],
            })
            existing.add(name)
        data["validation_rules"] = validation_rules
        self._mark_layout_required_field_nodes(layout, required_names)

    def _safe_model_can_read(self, model_name):
        name = str(model_name or "").strip()
        if not name:
            return True
        try:
            return bool(self.env[name].check_access_rights("read", raise_exception=False))
        except Exception:
            return True

    @staticmethod
    def _normalize_field_list(values):
        out = []
        for item in values or []:
            name = str(item or "").strip()
            if name and name not in out:
                out.append(name)
        return out

    def _extract_core_field_names(self, data):
        if not isinstance(data, dict):
            return []
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}

        # Priority 1: explicit field_groups.core
        groups = data.get("field_groups")
        if isinstance(groups, list):
            for item in groups:
                if not isinstance(item, dict):
                    continue
                if str(item.get("name") or "").strip().lower() != "core":
                    continue
                rows = self._normalize_field_list(item.get("fields") if isinstance(item.get("fields"), list) else [])
                if rows:
                    return rows

        # Priority 2: form profile core_fields
        form_view = (data.get("views") or {}).get("form") if isinstance(data.get("views"), dict) else {}
        form_profile = form_view.get("form_profile") if isinstance(form_view, dict) else {}
        if not isinstance(form_profile, dict):
            form_profile = data.get("form_profile") if isinstance(data.get("form_profile"), dict) else {}
        if isinstance(form_profile, dict):
            rows = self._normalize_field_list(
                form_profile.get("core_fields") if isinstance(form_profile.get("core_fields"), list) else []
            )
            if rows:
                return rows

        # Priority 3: semantic surface_role=core
        semantic_core = []
        for name, desc in fields.items():
            if not isinstance(desc, dict):
                continue
            role = str(desc.get("surface_role") or "").strip().lower()
            if role == "core":
                semantic_core.append(str(name or "").strip())
        semantic_core = self._normalize_field_list(semantic_core)
        if semantic_core:
            return semantic_core

        # Priority 4: fallback to required relation fields
        required_relation = []
        for name, desc in fields.items():
            if not isinstance(desc, dict):
                continue
            ttype = str(desc.get("type") or desc.get("ttype") or "").strip().lower()
            relation = str(desc.get("relation") or "").strip()
            if ttype in {"many2one", "many2many", "one2many"} and relation and bool(desc.get("required")):
                required_relation.append(str(name or "").strip())
        return self._normalize_field_list(required_relation)

    def _apply_access_policy(self, data, model_name=""):
        if not isinstance(data, dict):
            return
        fields = data.get("fields")
        if not isinstance(fields, dict):
            fields = {}

        blocked_fields = []
        degraded_fields = []
        policy_source = "none"

        model = str(model_name or "").strip()
        if model and not self._safe_model_can_read(model):
            blocked_fields.append(
                {
                    "field": "__model__",
                    "model": model,
                    "reason_code": "MODEL_READ_FORBIDDEN",
                }
            )
            policy_source = "model_acl"
        else:
            core_fields = set(self._extract_core_field_names(data))
            if core_fields:
                policy_source = "core_fields"
            for field_name, desc in fields.items():
                if not isinstance(desc, dict):
                    continue
                relation_entry = desc.get("relation_entry")
                if not isinstance(relation_entry, dict):
                    continue
                can_read = relation_entry.get("can_read")
                if can_read is not False:
                    continue
                relation = str(desc.get("relation") or relation_entry.get("model") or "").strip()
                row = {
                    "field": str(field_name or "").strip(),
                    "model": relation,
                    "reason_code": str(relation_entry.get("reason_code") or "RELATION_READ_FORBIDDEN"),
                }
                relation_model = str(relation or "").strip().lower()
                if (
                    str(field_name or "").strip() in core_fields
                    and relation_model not in self._SYSTEM_RELATION_DEGRADE_MODELS
                ):
                    blocked_fields.append(row)
                else:
                    degraded_fields.append(row)

        mode = "allow"
        reason_code = ""
        message = ""
        if blocked_fields:
            mode = "block"
            first = blocked_fields[0]
            reason_code = str(first.get("reason_code") or "RELATION_READ_FORBIDDEN_CORE")
            if reason_code == "RELATION_READ_FORBIDDEN":
                reason_code = "RELATION_READ_FORBIDDEN_CORE"
            label = str(first.get("field") or first.get("model") or "unknown")
            message = f"core field access blocked: {label}"
        elif degraded_fields:
            mode = "degrade"
            first = degraded_fields[0]
            reason_code = str(first.get("reason_code") or "RELATION_READ_FORBIDDEN")
            label = str(first.get("field") or first.get("model") or "unknown")
            message = f"relation access degraded: {label}"

        data["access_policy"] = {
            "mode": mode,
            "reason_code": reason_code,
            "message": message,
            "policy_source": policy_source,
            "blocked_fields": blocked_fields,
            "degraded_fields": degraded_fields,
        }

        if mode in {"block", "degrade"}:
            warnings = data.get("warnings") if isinstance(data.get("warnings"), list) else []
            marker = f"access_policy:{mode}:{reason_code or 'UNKNOWN'}"
            if marker not in warnings:
                warnings.append(marker)
            data["warnings"] = warnings

    def _coerce_view_contract_semantics(self, view_type, contract):
        """标准化高级视图关键语义键，避免前端消费时出现结构漂移。"""
        vt = str(view_type or "").strip().lower()
        cfg = dict(contract or {})
        nested = cfg.get(vt)
        nested = nested if isinstance(nested, dict) else {}

        if vt == "pivot":
            measures = cfg.get("measures", nested.get("measures", []))
            dimensions = cfg.get("dimensions", nested.get("dimensions", []))
            cfg["measures"] = measures if isinstance(measures, list) else []
            cfg["dimensions"] = dimensions if isinstance(dimensions, list) else []
            defaults = cfg.get("defaults", nested.get("defaults", {}))
            if isinstance(defaults, dict):
                cfg["defaults"] = defaults
            return cfg
        if vt == "graph":
            gtype = cfg.get("type", nested.get("type", nested.get("type_default", "bar")))
            cfg["type"] = str(gtype or "bar")
            cfg["measure"] = str(cfg.get("measure", nested.get("measure", "")) or "")
            cfg["dimension"] = str(cfg.get("dimension", nested.get("dimension", "")) or "")
            for key in ("measures", "dimensions", "chart_policy"):
                value = cfg.get(key, nested.get(key))
                if isinstance(value, (list, dict)):
                    cfg[key] = value
            return cfg
        if vt in ("calendar", "gantt"):
            date_start = cfg.get("date_start", nested.get("date_start", "date_start"))
            date_stop = cfg.get("date_stop", nested.get("date_stop", "date_end"))
            cfg["date_start"] = str(date_start or "date_start")
            cfg["date_stop"] = str(date_stop or "date_end")
            for key in ("date_slots", "resource_slots", "color_slots", "dependency_slots", "fields", "native_attrs"):
                value = cfg.get(key, nested.get(key))
                if isinstance(value, (list, dict)):
                    cfg[key] = value
            return cfg
        if vt == "activity":
            field = cfg.get("field", nested.get("field", "res_id"))
            cfg["field"] = str(field or "res_id")
            for key in ("activity_type_slots", "deadline_slots", "assignee_slots", "fields", "native_attrs"):
                value = cfg.get(key, nested.get(key))
                if isinstance(value, (list, dict)):
                    cfg[key] = value
            return cfg
        if vt == "dashboard":
            cards = cfg.get("cards", nested.get("cards", []))
            kpis = cfg.get("kpis", nested.get("kpis", []))
            cfg["cards"] = cards if isinstance(cards, list) else []
            cfg["kpis"] = kpis if isinstance(kpis, list) else []
            for key in ("metric_slots", "chart_slots", "navigation_slots"):
                value = cfg.get(key, nested.get(key))
                if isinstance(value, dict):
                    cfg[key] = value
            return cfg
        if vt == "kanban":
            for key in ("fields", "slots", "kanban_profile", "row_actions", "quick_actions", "actions"):
                value = cfg.get(key, nested.get(key))
                if isinstance(value, (list, dict)):
                    cfg[key] = value
            return cfg
        return cfg

    def _inject_view_orchestration_summary(self, data):
        views = data.get("views") if isinstance(data, dict) else {}
        if not isinstance(views, dict) or not views:
            return
        view_rows = {}
        any_applied = False
        for view_type, contract in views.items():
            if not isinstance(contract, dict):
                continue
            governance = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
            orchestration = governance.get("view_orchestration") if isinstance(governance.get("view_orchestration"), dict) else {}
            source_trace = contract.get("source_trace") if isinstance(contract.get("source_trace"), dict) else {}
            trace = source_trace.get("view_orchestration") if isinstance(source_trace.get("view_orchestration"), dict) else {}
            business_contracts = trace.get("business_config_contracts") or orchestration.get("business_config_contracts") or []
            legacy_overlay = bool(trace.get("legacy_field_policy_overlay") or orchestration.get("legacy_field_policy_overlay"))
            business_config_form_fields = trace.get("business_config_form_fields") or orchestration.get("business_config_form_fields") or []
            form_field_policy = governance.get("form_field_policy") if isinstance(governance.get("form_field_policy"), dict) else {}
            skipped_policy_fields = form_field_policy.get("skipped_by_business_config_fields") or []
            applied = bool(orchestration.get("applied") or business_contracts or legacy_overlay)
            if applied:
                any_applied = True
            view_rows[str(view_type or "")] = {
                "applied": applied,
                "owner_layer": str(trace.get("owner_layer") or orchestration.get("owner_layer") or BUSINESS_CONFIG_OWNER_LAYER),
                "business_config_contracts": business_contracts if isinstance(business_contracts, list) else [],
                "legacy_field_policy_overlay": legacy_overlay,
                "business_config_form_fields": business_config_form_fields if isinstance(business_config_form_fields, list) else [],
                "skipped_legacy_policy_fields": skipped_policy_fields if isinstance(skipped_policy_fields, list) else [],
            }
        if not view_rows:
            return
        governance = data.get("governance") if isinstance(data.get("governance"), dict) else {}
        governance["view_orchestration"] = {
            "applied": any_applied,
            "owner_layer": BUSINESS_CONFIG_OWNER_LAYER,
            "views": view_rows,
        }
        data["governance"] = governance

    def _append_view_version_token(self, versions, token):
        if not isinstance(versions, dict):
            return
        value = str(token or "").strip()
        if not value:
            return
        current = str(versions.get("view") or "").strip()
        parts = [part for part in current.split(",") if part]
        if value not in parts:
            parts.append(value)
        versions["view"] = ",".join(parts) if parts else value

    def _inject_search_view_orchestration(self, data, *, env, model, view_context, versions=None):
        if not model or "app.view.config" not in env:
            return
        context = dict(view_context or {})
        context["contract_projection_readonly"] = True
        try:
            view_config = env["app.view.config"].with_context(**context)._generate_from_fields_view_get(model, "search")
            runtime_view_config = view_config.with_user(env.user).sudo().with_context(**context)
            search_contract = runtime_view_config.get_contract_api(filter_runtime=True, check_model_acl=True)
        except Exception:
            _logger.exception("Failed to apply search view orchestration for model=%s", model)
            return
        if not isinstance(search_contract, dict):
            return
        self._append_view_version_token(versions, search_contract.get("effective_version"))
        data["views"]["search"] = self._coerce_view_contract_semantics("search", search_contract)
        orchestrated_search = search_contract.get("search") if isinstance(search_contract.get("search"), dict) else {}
        if not orchestrated_search:
            return
        base_search = data.get("search") if isinstance(data.get("search"), dict) else {}
        merged = dict(base_search)
        for key in ("filters", "group_by", "facets"):
            value = orchestrated_search.get(key)
            if value:
                merged[key] = value
        data["search"] = merged

    def _apply_action_search_defaults(self, data, action_context):
        search = data.get("search") if isinstance(data, dict) else {}
        if not isinstance(search, dict):
            return
        context = action_context if isinstance(action_context, dict) else {}
        if not context:
            return
        default_tokens = [
            str(key).strip()
            for key, value in context.items()
            if str(key).strip().startswith("search_default_") and value
        ]
        if not default_tokens:
            return

        group_rows = search.get("group_by") if isinstance(search.get("group_by"), list) else []
        matched_row = None
        for token in default_tokens:
            for row in group_rows:
                if not isinstance(row, dict):
                    continue
                field = str(row.get("field") or row.get("group_by") or row.get("key") or "").strip()
                key = str(row.get("key") or row.get("name") or field).strip()
                base_field = field.split(":", 1)[0]
                semantic_field = base_field[:-3] if base_field.endswith("_id") else base_field
                candidates = {
                    f"search_default_{key}",
                    f"search_default_group_{field}",
                    f"search_default_group_{base_field}",
                    f"search_default_group_{semantic_field}",
                    f"search_default_group_by_{field}",
                    f"search_default_group_by_{base_field}",
                    f"search_default_group_by_{semantic_field}",
                }
                if token in candidates:
                    matched_row = row
                    break
            if matched_row is not None:
                break
        if matched_row is None:
            return
        for row in group_rows:
            if not isinstance(row, dict):
                continue
            row["default"] = row is matched_row

    def _inject_relation_entry_contract(self, data, model_name=""):
        fields = data.get("fields") if isinstance(data, dict) else None
        if not isinstance(fields, dict) or not fields:
            return
        model_name = str(model_name or "").strip()
        contract_context = data.get("context") if isinstance(data.get("context"), dict) else {}
        record_defaults = data.get("record") if isinstance(data.get("record"), dict) else {}
        if record_defaults:
            contract_context = {**record_defaults, **contract_context}
        relation_models = set()
        for desc in fields.values():
            if not isinstance(desc, dict):
                continue
            ftype = str(desc.get("type") or "").strip().lower()
            relation = str(desc.get("relation") or "").strip()
            if ftype in {"many2one", "many2many", "one2many"} and relation:
                relation_models.add(relation)
        if not relation_models:
            return
        relation_entry_map = self._build_relation_entry_map(relation_models)
        for field_name, desc in fields.items():
            if not isinstance(desc, dict):
                continue
            relation = str(desc.get("relation") or "").strip()
            if relation and relation in relation_entry_map:
                desc["relation_entry"] = self._build_relation_entry_for_field(
                    field_name,
                    desc,
                    relation_entry_map[relation],
                    model_name=model_name,
                    contract_context=contract_context,
                )

    def _extract_dictionary_type_from_domain(self, domain_raw):
        if not domain_raw:
            return ""
        domain = domain_raw
        if isinstance(domain_raw, str):
            try:
                domain = safe_eval(domain_raw) if domain_raw.strip().startswith("[") else domain_raw
            except Exception:
                domain = domain_raw
        if isinstance(domain, (list, tuple)):
            for node in domain:
                if not isinstance(node, (list, tuple)) or len(node) < 3:
                    continue
                left = str(node[0] or "").strip()
                op = str(node[1] or "").strip()
                right = node[2]
                if left == "type" and op == "=" and isinstance(right, str):
                    return right.strip()
        if isinstance(domain_raw, str):
            # fallback for non-evaluable domain strings
            match = re.search(r"[('\" ]type[)'\" ]\s*,\s*['\"]=['\"]\s*,\s*['\"]([a-zA-Z0-9_]+)['\"]", domain_raw)
            if match:
                return str(match.group(1) or "").strip()
        return ""

    def _extract_field_domain_hint(self, model_name, field_name):
        model = str(model_name or "").strip()
        field = str(field_name or "").strip()
        if not model or not field:
            return None
        try:
            f = self.env[model]._fields.get(field)
        except Exception:
            return None
        if not f:
            return None
        domain = getattr(f, "domain", None)
        if isinstance(domain, (list, tuple, str)):
            return domain
        return None

    def _relation_create_disabled_by_options(self, descriptor):
        if not isinstance(descriptor, dict):
            return False
        options = descriptor.get("widget_options")
        if not isinstance(options, dict):
            options = descriptor.get("options")
        if not isinstance(options, dict):
            return False
        return any(
            options.get(key) is True
            for key in ("no_create", "no_create_edit", "no_quick_create")
        )

    def _relation_entry_override_from_options(self, descriptor):
        if not isinstance(descriptor, dict):
            return {}
        options = descriptor.get("widget_options")
        if not isinstance(options, dict):
            options = descriptor.get("options")
        if not isinstance(options, dict):
            return {}
        override = options.get("relation_entry")
        return dict(override) if isinstance(override, dict) else {}

    def _resolve_relation_entry_ref_id(self, xmlid):
        xmlid = str(xmlid or "").strip()
        if not xmlid:
            return None
        try:
            record = self.env.ref(xmlid, raise_if_not_found=False)
            return int(record.id) if record else None
        except Exception:
            return None

    def _build_relation_entry_for_field(self, field_name, descriptor, base_entry, model_name="", contract_context=None):
        entry = dict(base_entry or {})
        relation = str(descriptor.get("relation") or "").strip()
        can_read = bool(entry.get("can_read", True))
        can_create = bool(entry.get("can_create"))
        has_page = bool(entry.get("action_id"))
        default_vals = {}
        create_mode = "disabled"
        reason_code = str(entry.get("reason_code") or "").strip()
        dict_type = ""
        if relation == "sc.dictionary":
            dict_type = self._extract_dictionary_type_from_domain(descriptor.get("domain"))
            if not dict_type:
                domain_hint = self._extract_field_domain_hint(model_name, field_name)
                dict_type = self._extract_dictionary_type_from_domain(domain_hint)
            if dict_type:
                default_vals = {"type": dict_type}
        relation_domain = []
        display_field = ""
        relation_order = ""
        can_open = True
        switch_context = {}
        ui_labels_extra = {}
        is_contract_tax_field = False
        create_disabled_by_options = self._relation_create_disabled_by_options(descriptor)
        if create_disabled_by_options:
            can_create = False
            has_page = False
        options_override = self._relation_entry_override_from_options(descriptor)
        if relation == "sc.business.category" and str(field_name or "").strip() == "business_category_id":
            display_field = "name"
            relation_order = "sequence asc, id asc"
            can_create = False
            has_page = False
            can_open = False
            switch_context = {
                "enabled": True,
                "code_field": "code",
                "label_field": "name",
                "default_values_field": "default_values_json",
            }
            context = contract_context if isinstance(contract_context, dict) else {}
            raw_codes = context.get("allowed_business_category_codes")
            if not isinstance(raw_codes, list) or not raw_codes:
                raw_codes = [
                    context.get("default_business_category_code")
                    or context.get("current_business_category_code")
                ]
            codes = [
                str(code or "").strip()
                for code in raw_codes
                if str(code or "").strip()
            ]
            default_clear_fields = set()
            if codes and "sc.business.category" in self.env:
                try:
                    rows = self.env["sc.business.category"].sudo().search([("code", "in", codes)])
                    for row in rows:
                        defaults = self._json_value(getattr(row, "default_values_json", "{}") or "{}", {})
                        if isinstance(defaults, dict):
                            default_clear_fields.update(str(key or "").strip() for key in defaults.keys() if str(key or "").strip())
                except Exception:
                    default_clear_fields = set()
            if codes:
                relation_domain.append(["code", "in", codes])
            if model_name:
                relation_domain.append(["target_model", "=", model_name])
            switch_context["default_clear_fields"] = sorted(default_clear_fields)
        relation_policy = call_extension_hook_first(
            self.env,
            "smart_core_relation_entry_policy",
            self.env,
            {
                "model": model_name,
                "field_name": field_name,
                "relation": relation,
                "descriptor": descriptor if isinstance(descriptor, dict) else {},
                "context": contract_context if isinstance(contract_context, dict) else {},
            },
        )
        if isinstance(relation_policy, dict):
            if "has_page" in relation_policy:
                has_page = bool(relation_policy.get("has_page"))
            if "can_open" in relation_policy:
                can_open = bool(relation_policy.get("can_open"))
            if "can_create" in relation_policy:
                can_create = bool(relation_policy.get("can_create"))
            if relation_policy.get("quick_create"):
                is_contract_tax_field = True
            if isinstance(relation_policy.get("default_vals"), dict):
                default_vals.update(relation_policy.get("default_vals") or {})
            if isinstance(relation_policy.get("domain"), list):
                relation_domain.extend(relation_policy.get("domain") or [])
            if str(relation_policy.get("display_field") or "").strip():
                display_field = str(relation_policy.get("display_field") or "").strip()
            if str(relation_policy.get("order") or "").strip():
                relation_order = str(relation_policy.get("order") or "").strip()
            if isinstance(relation_policy.get("ui_labels"), dict):
                ui_labels_extra.update(relation_policy.get("ui_labels") or {})
        if options_override:
            action_id = options_override.get("action_id") or self._resolve_relation_entry_ref_id(options_override.get("action_xmlid"))
            menu_id = options_override.get("menu_id") or self._resolve_relation_entry_ref_id(options_override.get("menu_xmlid"))
            if action_id:
                entry["action_id"] = int(action_id)
                has_page = True
            if menu_id:
                entry["menu_id"] = int(menu_id)
            if "can_create" in options_override:
                can_create = bool(options_override.get("can_create"))
            if isinstance(options_override.get("default_vals"), dict):
                default_vals.update(options_override.get("default_vals") or {})
            if isinstance(options_override.get("default_from_fields"), dict):
                entry["default_from_fields"] = dict(options_override.get("default_from_fields") or {})
            if isinstance(options_override.get("domain"), list):
                relation_domain.extend(options_override.get("domain") or [])
            if str(options_override.get("display_field") or "").strip():
                display_field = str(options_override.get("display_field") or "").strip()
            if str(options_override.get("order") or "").strip():
                relation_order = str(options_override.get("order") or "").strip()
            if isinstance(options_override.get("ui_labels"), dict):
                ui_labels_extra.update(options_override.get("ui_labels") or {})
        inline_create = self._build_relation_inline_create_contract(
            relation,
            can_read=can_read,
            can_create=can_create,
            default_vals=default_vals,
        )

        if not can_read:
            create_mode = "disabled"
            reason_code = "RELATION_READ_FORBIDDEN"
        elif has_page:
            create_mode = "page"
            if can_create:
                reason_code = reason_code or "PAGE_ENTRY_READY"
            else:
                reason_code = reason_code or "PAGE_ENTRY_READONLY"
        elif can_create and (relation == "sc.dictionary" or is_contract_tax_field):
            if dict_type or is_contract_tax_field:
                create_mode = "quick"
                reason_code = "QUICK_CREATE_READY"
            else:
                reason_code = reason_code or "DICT_TYPE_UNRESOLVED"
        elif create_disabled_by_options:
            reason_code = reason_code or "FIELD_CREATE_DISABLED"
        else:
            reason_code = reason_code or "NO_CREATE_ENTRY"

        entry.update(
            {
                "field": str(field_name or "").strip(),
                "create_mode": create_mode,
                "default_vals": default_vals,
                "default_from_fields": entry.get("default_from_fields") if isinstance(entry.get("default_from_fields"), dict) else {},
                "domain": relation_domain,
                "display_field": display_field,
                "order": relation_order,
                "can_open": can_open,
                "switch_context": switch_context,
                "can_read": can_read,
                "can_create": can_create,
                "reason_code": reason_code,
                "inline_create": inline_create,
                "search_dialog": self._build_relation_search_dialog_contract(relation, model_name=model_name),
                "ui_labels": {
                    "search_more": _("搜索更多..."),
                    "quick_create": _("快速新建..."),
                    "create_and_edit": _("新建并维护..."),
                    "dialog_title": _("%s：搜索更多") % (descriptor.get("string") or field_name),
                    "search_placeholder": _("输入名称搜索"),
                    "search": _("搜索"),
                    "select": _("选择"),
                    "create": _("新建"),
                    "cancel": _("取消"),
                    "close": _("关闭"),
                    "empty": _("未找到匹配记录"),
                    "record_count": _("%s 条记录"),
                    "missing_name": _("请输入要新建的名称。"),
                    "search_failed": _("搜索失败，请稍后重试"),
                    "quick_create_prompt": _("当前未配置维护页面，请输入新选项名称（快速新建）"),
                    "page_unavailable_prompt": _("维护页面暂不可用，请输入新选项名称（快速新建）"),
                    "missing_create_entry": _("未找到新建入口，请联系管理员配置菜单动作"),
                    "missing_page_entry": _("未找到维护页面入口，请联系管理员配置 action/menu"),
                    "create_page_failed": _("跳转新建页面失败"),
                    "quick_create_failed": _("快速新建失败"),
                    "inline_searching": _("正在搜索..."),
                    "inline_create": _("保存时创建“%s”"),
                    "inline_create_failed": _("保存时创建失败"),
                    **ui_labels_extra,
                },
            }
        )
        return entry

    def _build_relation_search_dialog_contract(self, relation, model_name=""):
        relation = str(relation or "").strip()
        model_name = str(model_name or "").strip()
        if relation == "sc.business.category":
            return {
                "columns": [
                    {
                        "name": "name",
                        "label": _("业务类别"),
                        "type": "char",
                        "widget": "char",
                        "optional": "",
                    }
                ],
                "read_fields": ["id", "display_name", "name", "code", "default_values_json"],
                "order": "sequence asc, id asc",
                "limit": 120,
                "search": {"filters": [], "group_by": [], "facets": {"enabled": True}},
                "governance": {},
                "source_trace": {},
                "source": "business_category_relation_contract",
            }
        columns = []
        read_fields = ["id", "display_name", "name"]
        order = "id desc"
        search = {"filters": [], "group_by": [], "facets": {"enabled": True}}
        governance = {}
        source_trace = {}
        if not relation or (model_name and relation == model_name):
            return {
                "columns": columns,
                "read_fields": read_fields,
                "order": order,
                "limit": 120,
                "search": search,
                "governance": governance,
                "source_trace": source_trace,
                "source": "self_relation_minimal_view" if relation else "relation_target_native_view",
            }
        try:
            view_config_model = self.env["app.view.config"].with_context(contract_projection_readonly=True)
            view_config = view_config_model._generate_from_fields_view_get(relation, "tree")
            view_contract = view_config.get_contract_api(filter_runtime=True, check_model_acl=True)
            schema_rows = view_contract.get("columns_schema") if isinstance(view_contract, dict) else []
            for row in schema_rows if isinstance(schema_rows, list) else []:
                if not isinstance(row, dict):
                    continue
                name = str(row.get("name") or row.get("field") or "").strip()
                label = str(row.get("label") or row.get("string") or name).strip()
                if not name or name == "id":
                    continue
                columns.append({
                    "name": name,
                    "label": label or name,
                    "type": row.get("type") or "",
                    "widget": row.get("widget") or "",
                    "optional": row.get("optional") or "",
                })
                if name not in read_fields:
                    read_fields.append(name)
                if len(columns) >= 8:
                    break
            order = str(
                view_contract.get("default_order")
                or view_contract.get("order")
                or order
            ).strip() or order
            parsed_search = view_contract.get("search") if isinstance(view_contract.get("search"), dict) else {}
            if parsed_search:
                search = parsed_search
            governance = view_contract.get("governance") if isinstance(view_contract.get("governance"), dict) else {}
            source_trace = view_contract.get("source_trace") if isinstance(view_contract.get("source_trace"), dict) else {}
        except Exception:
            _logger.debug("relation search dialog native parse failed relation=%s", relation, exc_info=True)
        return {
            "columns": columns,
            "read_fields": read_fields,
            "order": order,
            "limit": 120,
            "search": search,
            "governance": governance,
            "source_trace": source_trace,
            "source": "relation_target_native_view",
        }

    def _build_relation_inline_create_contract(self, relation, *, can_read, can_create, default_vals=None):
        relation = str(relation or "").strip()
        defaults = default_vals if isinstance(default_vals, dict) else {}
        if not relation or not can_read or not can_create:
            return {
                "enabled": False,
                "create_on_no_match": False,
                "match": "single_contains_or_exact",
                "name_field": "",
                "reason_code": "RELATION_CREATE_FORBIDDEN",
            }
        try:
            Model = self.env[relation]
            fields_map = Model.fields_get()
            rec_name = str(getattr(Model, "_rec_name", "") or "name").strip() or "name"
        except Exception:
            fields_map = {}
            rec_name = "name"
        if rec_name not in fields_map and "name" in fields_map:
            rec_name = "name"
        descriptor = fields_map.get(rec_name) if isinstance(fields_map, dict) else {}
        required_fields = [
            str(name or "").strip()
            for name, meta in (fields_map or {}).items()
            if isinstance(meta, dict) and bool(meta.get("required"))
        ]
        try:
            default_get_vals = Model.default_get([
                name
                for name in required_fields
                if name not in {rec_name, "display_name"} and name not in defaults
            ])
        except Exception:
            default_get_vals = {}
        unresolved_required = [
            name
            for name in required_fields
            if name not in {rec_name, "display_name"} and name not in defaults and name not in default_get_vals
        ]
        if not rec_name or not isinstance(descriptor, dict) or unresolved_required:
            return {
                "enabled": False,
                "create_on_no_match": False,
                "match": "single_contains_or_exact",
                "name_field": rec_name,
                "reason_code": "RELATION_REQUIRED_FIELDS_UNRESOLVED",
                "required_fields": unresolved_required,
            }
        return {
            "enabled": True,
            "create_on_no_match": True,
            "match": "single_contains_or_exact",
            "name_field": rec_name,
            "value_source": "typed_keyword",
            "reason_code": "INLINE_CREATE_READY",
        }

    def _build_relation_entry_map(self, relation_models):
        relation_models = sorted(str(m).strip() for m in (relation_models or []) if str(m).strip())
        if not relation_models:
            return {}
        user_group_ids = set(self.env.user.groups_id.ids)

        def _allowed_by_groups(record):
            group_ids = set(record.groups_id.ids)
            return not group_ids or bool(group_ids & user_group_ids)

        def _safe_can_create(model_name):
            try:
                return bool(self.env[model_name].check_access_rights("create", raise_exception=False))
            except Exception:
                return False
        def _safe_can_read(model_name):
            try:
                return bool(self.env[model_name].check_access_rights("read", raise_exception=False))
            except Exception:
                return False
        def _safe_delete_policy(model_name):
            try:
                return resolve_unlink_policy(self.env, model_name)
            except Exception:
                return {
                    "model": model_name,
                    "allowed": False,
                    "delete_mode": "none",
                    "reason_code": "DELETE_POLICY_DENIED",
                    "message": _("当前模型未开放删除"),
                    "source": "delete_policy_error",
                    "requires_acl": True,
                    "requires_record_rule": True,
                    "dry_run_supported": True,
                }

        entry_map = {}
        Act = self.su_env["ir.actions.act_window"]
        actions = Act.search([("res_model", "in", relation_models)], order="id desc")
        action_by_model = {}
        for act in actions:
            if not _allowed_by_groups(act):
                continue
            model_name = str(act.res_model or "").strip()
            if not model_name or model_name in action_by_model:
                continue
            action_by_model[model_name] = act

        action_ids = [act.id for act in action_by_model.values()]
        menu_by_action = {}
        if action_ids:
            action_refs = [f"ir.actions.act_window,{aid}" for aid in action_ids]
            menus = self.su_env["ir.ui.menu"].search([("action", "in", action_refs)], order="sequence,id")
            for menu in menus:
                if not _allowed_by_groups(menu):
                    continue
                action_ref = str(menu.action or "").strip()
                if not action_ref.startswith("ir.actions.act_window,"):
                    continue
                try:
                    aid = int(action_ref.split(",")[1])
                except Exception:
                    continue
                if aid not in menu_by_action:
                    menu_by_action[aid] = menu.id

        for relation in relation_models:
            act = action_by_model.get(relation)
            if act:
                entry_map[relation] = {
                    "model": relation,
                    "action_id": int(act.id),
                    "menu_id": int(menu_by_action.get(act.id) or 0) or None,
                    "view_type": "form",
                    "view_mode": str(act.view_mode or "form"),
                    "can_read": _safe_can_read(relation),
                    "can_create": _safe_can_create(relation),
                    "delete_policy": _safe_delete_policy(relation),
                    "source": "backend_contract",
                }
                continue
            entry_map[relation] = {
                "model": relation,
                "action_id": None,
                "menu_id": None,
                "view_type": "form",
                "view_mode": "form",
                "can_read": _safe_can_read(relation),
                "can_create": _safe_can_create(relation),
                "delete_policy": _safe_delete_policy(relation),
                "source": "backend_contract",
                "reason_code": "NO_VISIBLE_ACTION",
            }
        return entry_map

    # ---------------- 首屏数据 ----------------

    def _fetch_initial_data(self, env, model, view_types, p, assembled):
        """
        拉取列表/表单首屏数据：
        - 列表：严格遵循 views.tree.columns 的顺序（如缺列，用 P0 严格列兜底）；
        - 自动继承 default_order/page_size；
        - 采用当前用户 env，确保 ORM 自动应用 ir.rule；
        """
        Model = env[model]
        fields_map = Model.fields_get()

        # 基础分页/排序/过滤
        domain = p.get("domain") or []
        limit = int(p.get("limit") or 50)
        offset = int(p.get("offset") or 0)
        order = p.get("order") or getattr(Model, "_order", "id") or "id"

        out = {}
        # 决定用于列表数据的视图类型（优先用户指定）
        preferred = p.get("view_type")
        vt_candidates = [preferred] if preferred in ("tree", "kanban") else []
        vt_candidates += [vt for vt in (view_types or []) if vt in ("tree", "kanban")]
        list_vt = vt_candidates[0] if vt_candidates else "tree"

        # 列表数据：tree/kanban 任一存在即返回 list
        if any(vt in ("tree", "kanban") for vt in (view_types or ["tree"])):
            view_cols_cfg = []
            view_order_cfg = None
            view_page_size = None

            try:
                # 从 assembled 中优先读取 view 契约里的 columns/default_order
                arch = {}
                view_cols_cfg = list(assembled["views"].get(list_vt, {}).get("columns") or []) \
                                or list(arch.get("columns") or [])
                view_order_cfg = assembled["views"].get(list_vt, {}).get("default_order") or arch.get("order")
                view_page_size = arch.get("page_size")
            except Exception:
                pass

            # ★ P0：基于严格列/契约列做安全规范化，过滤隐字段/one2many
            cols = normalize_cols_safely(view_cols_cfg, fields_map)
            order = p.get("order") or view_order_cfg or order
            limit = int(p.get("limit") or view_page_size or limit)

            # 调试日志：记录列顺序来源与最终列
            _logger.debug("COLUMN_ORDER_DEBUG: model=%s list_vt=%s", model, list_vt)
            _logger.debug("COLUMN_ORDER_DEBUG: XML解析列顺序 view_cols=%s", view_cols_cfg)
            _logger.debug("COLUMN_ORDER_DEBUG: 最终输出列顺序 cols=%s", cols)
            _logger.debug("LIST etl: vt=%s model=%s cols=%s limit=%s order=%s", list_vt, model, cols, limit, order)

            # 搜索 & 读取：只读所需列，减少 IO/序列化负担（自动应用记录规则）
            recs = Model.search(domain, order=order, limit=limit, offset=offset)
            rows = recs.read(cols)
            next_offset = (offset + len(rows)) if len(rows) == limit else None
            out["list"] = {"records": rows, "next_offset": next_offset}

        # 表单数据：表单视图且传了 record_id 才读取，避免列表请求混入记录事实。
        requested_view_type = str(p.get("view_type") or p.get("viewType") or "").strip().lower()
        wants_form_record = (
            p.get("record_id")
            and (
                requested_view_type in {"form", ""}
                or "form" in (view_types or [])
            )
        )
        if wants_form_record:
            rec = Model.browse(int(p["record_id"]))
            if rec.exists():
                form_fields = []
                form_layout = {}
                form_view = assembled.get("views", {}).get("form", {}) if isinstance(assembled.get("views"), dict) else {}
                try:
                    form_layout = form_view.get("layout") if isinstance(form_view, dict) else {}
                    form_fields = self._collect_form_fields(form_layout, fields_map=fields_map)
                    if not form_fields:
                        vcfg = self.su_env["app.view.config"].sudo().search([("model", "=", model), ("view_type", "=", "form")], limit=1)
                        form_layout = (vcfg.arch_parsed or {}).get("layout") or {}
                        form_fields = self._collect_form_fields(form_layout, fields_map=fields_map)
                    if not form_fields:
                        form_fields = list(fields_map.keys())[:20]
                except Exception:
                    # 兜底：取前 20 个字段，避免一次性 read 全量大字段
                    form_fields = list(fields_map.keys())[:20]
                form_fields = [name for name in form_fields if name in fields_map]
                out["record"] = rec.read(form_fields)[0] if form_fields else {"id": rec.id, "display_name": rec.display_name}
                out["form_layout"] = form_layout
        return out

    def _collect_form_fields(self, layout, fields_map=None):
        """
        从 form 布局树中递归收集字段名，用于决定 read() 的字段集合。
        """
        fields_map = fields_map if isinstance(fields_map, dict) else {}
        names = []

        def walk(node):
            if isinstance(node, list):
                for child in node:
                    walk(child)
                return
            if not node or not isinstance(node, dict):
                return
            if node.get('type') == 'field':
                n = node.get('name')
                if n and (not fields_map or n in fields_map) and n not in names:
                    names.append(n)
                descriptor = fields_map.get(n) if isinstance(fields_map.get(n), dict) else {}
                if descriptor.get("type") in {"one2many", "many2many"}:
                    return
            for ch in node.get('children', []) or []:
                walk(ch)

        walk(layout or {})
        return names

    def _to_fields_map(self, fields, env=None, model=None):
        """
        将多种字段描述格式统一为 {name:{name,string,type,relation,...}}：
        - 支持完整 dict、(name,label) 元组、"name" 简写；
        - 若提供 env+model，则从模型元数据补齐类型/显示名/关联模型。
        """
        res = {}
        meta = {}
        if env is not None and model:
            try:
                m = env[model]
                translated_fields = m.fields_get()
                def _resolve_selection(field_obj):
                    raw = getattr(field_obj, "selection", None)
                    if isinstance(raw, (list, tuple)):
                        return list(raw)
                    if isinstance(raw, str):
                        method = getattr(m, raw, None)
                        if callable(method):
                            try:
                                resolved = method()
                                if isinstance(resolved, (list, tuple)):
                                    return list(resolved)
                            except Exception:
                                return []
                    if callable(raw):
                        try:
                            resolved = raw(m)
                            if isinstance(resolved, (list, tuple)):
                                return list(resolved)
                        except Exception:
                            return []
                    return []

                def _resolve_domain(field_obj):
                    raw = getattr(field_obj, "domain", None)
                    if isinstance(raw, (list, tuple, str)):
                        return raw
                    return None

                meta = {}
                for k, f in m._fields.items():
                    translated = translated_fields.get(k, {}) if isinstance(translated_fields, dict) else {}
                    meta[k] = {
                        "type": translated.get("type") or getattr(f, "type", None),
                        "string": translated.get("string") or getattr(f, "string", None) or k,
                        "relation": translated.get("relation") or getattr(f, "comodel_name", None),
                        "relation_field": getattr(f, "inverse_name", None),
                        "readonly": bool(translated.get("readonly", getattr(f, "readonly", False))),
                        "required": bool(translated.get("required", getattr(f, "required", False))),
                        "help": translated.get("help") or getattr(f, "help", None) or "",
                        "domain": translated.get("domain") or _resolve_domain(f),
                        "selection": translated.get("selection") or _resolve_selection(f),
                    }
            except Exception:
                meta = {}

        def add_field(name, string=None, ftype=None, extra=None):
            if not name:
                return
            meta_info = meta.get(name, {}) or {}
            localized_selection = meta_info.get("selection") or []
            info = {
                "name": name,
                "string": meta_info.get("string") or string or name,
                "type": ftype or meta_info.get("type") or "char",
                "readonly": bool(meta_info.get("readonly", False)),
                "required": bool(meta_info.get("required", False)),
            }
            if meta_info.get("help"):
                info["help"] = meta_info["help"]
            if meta_info.get("relation"):
                info["relation"] = meta_info["relation"]
            if meta_info.get("relation_field"):
                info["relation_field"] = meta_info["relation_field"]
            domain = meta_info.get("domain")
            if domain not in (None, ""):
                info["domain"] = domain
            if localized_selection:
                info["selection"] = localized_selection
            if isinstance(extra, dict):
                for k, v in extra.items():
                    if v is None:
                        continue
                    if k == "selection" and localized_selection:
                        continue
                    info[k] = v
            res[name] = info

        for f in (fields or []):
            if isinstance(f, dict):
                name = f.get("name") or f.get("field") or f.get("id")
                if not name:
                    continue
                extra = {}
                if "readonly" in f:
                    extra["readonly"] = bool(f.get("readonly"))
                if "required" in f:
                    extra["required"] = bool(f.get("required"))
                if "domain" in f:
                    extra["domain"] = f.get("domain")
                if "context" in f:
                    extra["context"] = f.get("context") or {}
                if "selection" in f:
                    extra["selection"] = f.get("selection") or []
                elif "options" in f:
                    extra["selection"] = f.get("options") or []
                if "invisible" in f:
                    extra["invisible"] = f.get("invisible")
                add_field(
                    name,
                    f.get("label") or f.get("string"),
                    f.get("type"),
                    extra,
                )
            elif isinstance(f, (list, tuple)) and len(f) >= 1:
                name = str(f[0]).strip()
                label = str(f[1]).strip() if len(f) > 1 and f[1] is not None else None
                add_field(name, label)
            elif isinstance(f, str):
                name = f.strip()
                if name:
                    add_field(name)
        return res
