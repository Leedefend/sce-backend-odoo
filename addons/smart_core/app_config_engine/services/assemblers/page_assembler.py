# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/assemblers/page_assembler.py
# 【职责】页面契约装配：
#   - 聚合：fields/views/search/permissions/actions/reports/workflow/validator
#   - with_data=True 时返回首屏数据（严格遵循 views.tree.columns 顺序）
#   - ★ 集成 P0 修复：从原始 <tree> 严格提取 columns，禁用“脏覆盖”，保证可渲染与顺序稳定
import logging
import re
from odoo.http import request
from ...utils.misc import safe_eval
from ...utils.view_utils import extract_tree_columns_strict, normalize_cols_safely
from ..page_policy_service import PagePolicyService

_logger = logging.getLogger(__name__)


class PageAssembler:
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
        self.policy_service = PagePolicyService(env, self._SYSTEM_RELATION_DEGRADE_MODELS)
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
    def _form_action_identity(row):
        row = row or {}
        payload = row.get("payload") or {}
        method = payload.get("method")
        if method:
            return "method:%s" % method
        ref = payload.get("ref")
        if ref:
            return "ref:%s" % ref
        action_id = payload.get("action_id")
        if action_id not in (None, ""):
            return "action_id:%s" % action_id
        key = row.get("key")
        if key:
            return "key:%s" % key
        return None

    @staticmethod
    def _collect_form_view_action_rows(form_view):
        form_view = form_view or {}
        rows = []
        for key in ("header_buttons", "button_box", "stat_buttons"):
            bucket = form_view.get(key)
            if isinstance(bucket, list):
                rows.extend([row for row in bucket if isinstance(row, dict)])
        return rows

    def _extract_form_action_rows_from_view_config(self, view_cfg):
        parsed = getattr(view_cfg, "arch_parsed", None)
        if not isinstance(parsed, dict):
            return []
        return self._collect_form_view_action_rows(parsed)

    def _filter_form_actions_to_source_rows(self, buttons_data, source_rows):
        buttons_data = list(buttons_data or [])
        source_rows = [row for row in (source_rows or []) if isinstance(row, dict)]
        if not source_rows:
            return buttons_data

        source_by_identity = {}
        source_order = []
        for row in source_rows:
            identity = self._form_action_identity(row)
            if not identity or identity in source_by_identity:
                continue
            source_by_identity[identity] = row
            source_order.append(identity)

        if not source_by_identity:
            return buttons_data

        candidate_by_identity = {}
        for row in buttons_data:
            identity = self._form_action_identity(row)
            if not identity or identity not in source_by_identity or identity in candidate_by_identity:
                continue
            merged = dict(row)
            source = source_by_identity[identity]
            for key in ("label", "level", "selection"):
                if source.get(key) not in (None, ""):
                    merged[key] = source.get(key)
            candidate_by_identity[identity] = merged

        filtered = []
        seen = set()
        for identity in source_order:
            row = candidate_by_identity.get(identity)
            if not row:
                continue
            dedupe_key = (row.get("kind"), identity, row.get("level"))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            filtered.append(row)

        return filtered or buttons_data

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

        view_types = p["view_types"]
        env = self.env
        su = self.su_env

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
        form_action_source_rows = []
        for vt in view_types:
            try:
                vcfg = su['app.view.config']._generate_from_fields_view_get(model, vt)
                if vt == 'form':
                    form_action_source_rows = self._extract_form_action_rows_from_view_config(vcfg)
                v_contract = vcfg.get_contract_api(filter_runtime=True, check_model_acl=True)
                v_versions.append(str(vcfg.version))
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

        if self.env.context.get("contract_action_id"):
            self._restrict_form_fields_to_layout(data)

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

        # 4.x) 关系字段维护入口（many2one/many2many/one2many）
        # 由后端契约提供 relation_entry，前端禁止自行猜测 action/menu。
        self._inject_relation_entry_contract(data, model)

        # 5) 权限契约（★ 关键改造点）
        #    - 用 su_env 生成完整权限聚合
        #    - 返回时开启 filter_runtime=True，按“当前用户组”裁剪出 effective.rights/rules
        try:
            pcfg = su['app.permission.config']._generate_from_access_rights(model)
            data["permissions"] = pcfg.get_permission_contract(filter_runtime=True)
            versions["perm"] = pcfg.version
        except KeyError:
            mark_missing("app.permission.config")
            _logger.warning("app.permission.config missing; fallback permissions for model=%s", model)
            data["permissions"] = {}
            versions["perm"] = 0

        # 6) 动作按钮 + 工具栏（元数据可 su_env，最终显隐由前端结合 groups/permissions 再次裁剪）
        try:
            acfg = su['app.action.config']._generate_from_ir_actions(model)
            buttons_data = acfg.get_action_contract()
            versions["actions"] = acfg.version if getattr(acfg, 'version', None) else 1
        except KeyError:
            mark_missing("app.action.config")
            _logger.warning("app.action.config missing; fallback empty actions for model=%s", model)
            buttons_data = []
            versions["actions"] = 0
        if "form" in view_types:
            buttons_data = self._filter_form_actions_to_source_rows(buttons_data, form_action_source_rows)
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
        if action:
            data["head"] = {
                "title": action.get('name'),
                "model": model,
                "view_type": ",".join(view_types),
                "action_id": action.get('id'),
                "context": safe_eval(action.get('context')),
                "permissions": {
                    "read": env[model].check_access_rights('read', raise_exception=False),
                    "write": env[model].check_access_rights('write', raise_exception=False),
                    "create": env[model].check_access_rights('create', raise_exception=False),
                    "unlink": env[model].check_access_rights('unlink', raise_exception=False),
                }
            }

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
        return data, versions

    def _restrict_form_fields_to_layout(self, data):
        self.policy_service.restrict_form_fields_to_layout(data)

    def _safe_model_can_read(self, model_name):
        return self.policy_service.safe_model_can_read(model_name)

    @staticmethod
    def _normalize_field_list(values):
        return PagePolicyService.normalize_field_list(values)

    def _extract_core_field_names(self, data):
        return self.policy_service.extract_core_field_names(data)

    def _apply_access_policy(self, data, model_name=""):
        self.policy_service.apply_access_policy(data, model_name=model_name)

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
            return cfg
        if vt == "graph":
            gtype = cfg.get("type", nested.get("type", nested.get("type_default", "bar")))
            cfg["type"] = str(gtype or "bar")
            cfg["measure"] = str(cfg.get("measure", nested.get("measure", "")) or "")
            cfg["dimension"] = str(cfg.get("dimension", nested.get("dimension", "")) or "")
            return cfg
        if vt in ("calendar", "gantt"):
            date_start = cfg.get("date_start", nested.get("date_start", "date_start"))
            date_stop = cfg.get("date_stop", nested.get("date_stop", "date_end"))
            cfg["date_start"] = str(date_start or "date_start")
            cfg["date_stop"] = str(date_stop or "date_end")
            return cfg
        if vt == "activity":
            field = cfg.get("field", nested.get("field", "res_id"))
            cfg["field"] = str(field or "res_id")
            return cfg
        if vt == "dashboard":
            cards = cfg.get("cards", nested.get("cards", []))
            kpis = cfg.get("kpis", nested.get("kpis", []))
            cfg["cards"] = cards if isinstance(cards, list) else []
            cfg["kpis"] = kpis if isinstance(kpis, list) else []
            return cfg
        return cfg

    def _inject_relation_entry_contract(self, data, model_name=""):
        fields = data.get("fields") if isinstance(data, dict) else None
        if not isinstance(fields, dict) or not fields:
            return
        model_name = str(model_name or "").strip()
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

    def _build_relation_entry_for_field(self, field_name, descriptor, base_entry, model_name=""):
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

        if not can_read:
            create_mode = "disabled"
            reason_code = "RELATION_READ_FORBIDDEN"
        elif has_page:
            create_mode = "page"
            if can_create:
                reason_code = reason_code or "PAGE_ENTRY_READY"
            else:
                reason_code = reason_code or "PAGE_ENTRY_READONLY"
        elif can_create and relation == "sc.dictionary":
            if dict_type:
                create_mode = "quick"
                reason_code = "QUICK_CREATE_READY"
            else:
                reason_code = reason_code or "DICT_TYPE_UNRESOLVED"
        else:
            reason_code = reason_code or "NO_CREATE_ENTRY"

        entry.update(
            {
                "field": str(field_name or "").strip(),
                "create_mode": create_mode,
                "default_vals": default_vals,
                "can_read": can_read,
                "reason_code": reason_code,
            }
        )
        return entry

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
                vcfg = self.su_env["app.view.config"].sudo().search([("model", "=", model), ("view_type", "=", list_vt)], limit=1)
                arch = (vcfg.arch_parsed or {})
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
            _logger.info("COLUMN_ORDER_DEBUG: model=%s list_vt=%s", model, list_vt)
            _logger.info("COLUMN_ORDER_DEBUG: XML解析列顺序 view_cols=%s", view_cols_cfg)
            _logger.info("COLUMN_ORDER_DEBUG: 最终输出列顺序 cols=%s", cols)
            _logger.info("LIST etl: vt=%s model=%s cols=%s limit=%s order=%s", list_vt, model, cols, limit, order)

            # 搜索 & 读取：只读所需列，减少 IO/序列化负担（自动应用记录规则）
            recs = Model.search(domain, order=order, limit=limit, offset=offset)
            rows = recs.read(cols)
            next_offset = (offset + len(rows)) if len(rows) == limit else None
            out["list"] = {"records": rows, "next_offset": next_offset}

        # 表单数据：当 view_types 包含 form 且传了 record_id 才读取
        if "form" in (view_types or []) and p.get("record_id"):
            rec = Model.browse(int(p["record_id"]))
            if rec.exists():
                form_fields = []
                form_layout = {}
                try:
                    vcfg = self.su_env["app.view.config"].sudo().search([("model", "=", model), ("view_type", "=", "form")], limit=1)
                    form_layout = (vcfg.arch_parsed or {}).get("layout") or {}
                    form_fields = self._collect_form_fields(form_layout) or list(fields_map.keys())[:20]
                except Exception:
                    # 兜底：取前 20 个字段，避免一次性 read 全量大字段
                    form_fields = list(fields_map.keys())[:20]
                out["record"] = rec.read(form_fields)[0] if form_fields else {"id": rec.id, "display_name": rec.display_name}
                out["form_layout"] = form_layout
        return out

    def _collect_form_fields(self, layout):
        """
        从 form 布局树中递归收集字段名，用于决定 read() 的字段集合。
        """
        names = []

        def walk(node):
            if not node or not isinstance(node, dict):
                return
            if node.get('type') == 'field':
                n = node.get('name')
                if n and n not in names:
                    names.append(n)
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

                meta = {
                    k: {
                        "type": getattr(f, "type", None),
                        "string": getattr(f, "string", None) or k,
                        "relation": getattr(f, "comodel_name", None),
                        "readonly": bool(getattr(f, "readonly", False)),
                        "required": bool(getattr(f, "required", False)),
                        "domain": _resolve_domain(f),
                        "selection": _resolve_selection(f),
                    }
                    for k, f in m._fields.items()
                }
            except Exception:
                meta = {}

        def add_field(name, string=None, ftype=None, extra=None):
            if not name:
                return
            info = {
                "name": name,
                "string": string or (meta.get(name, {}) or {}).get("string") or name,
                "type": ftype or (meta.get(name, {}) or {}).get("type") or "char",
                "readonly": bool((meta.get(name, {}) or {}).get("readonly", False)),
                "required": bool((meta.get(name, {}) or {}).get("required", False)),
            }
            if meta.get(name, {}).get("relation"):
                info["relation"] = meta[name]["relation"]
            domain = (meta.get(name, {}) or {}).get("domain")
            if domain not in (None, ""):
                info["domain"] = domain
            selection = (meta.get(name, {}) or {}).get("selection") or []
            if selection:
                info["selection"] = selection
            if isinstance(extra, dict):
                info.update({k: v for k, v in extra.items() if v is not None})
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
