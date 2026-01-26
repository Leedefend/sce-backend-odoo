# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/assemblers/page_assembler.py
# 【职责】页面契约装配：
#   - 聚合：fields/views/search/permissions/actions/reports/workflow/validator
#   - with_data=True 时返回首屏数据（严格遵循 views.tree.columns 顺序）
#   - ★ 集成 P0 修复：从原始 <tree> 严格提取 columns，禁用“脏覆盖”，保证可渲染与顺序稳定
import logging
from odoo.http import request
from ...utils.misc import safe_eval
from ...utils.view_utils import extract_tree_columns_strict, normalize_cols_safely

_logger = logging.getLogger(__name__)


class PageAssembler:
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

        data = {
            "head": {},
            "views": {},
            "fields": {},
            "search": {},
            "permissions": {},
            "buttons": [],
            "toolbar": {"header": [], "sidebar": [], "footer": []},
            "workflow": {},
            "reports": []
        }
        versions = {}

        # 1) 字段：从模型配置生成；再归一化到 {name: {...}} 形式
        #    - 使用 su_env 读模型元数据，避免被权限限制
        try:
            mcfg = su['app.model.config']._generate_from_ir_model(model)
            data["fields"] = self._to_fields_map(mcfg.get_model_contract().get("fields", []), env=env, model=mcfg.model)
            versions["model"] = mcfg.version
        except KeyError:
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
        for vt in view_types:
            try:
                vcfg = su['app.view.config']._generate_from_fields_view_get(model, vt)
                v_contract = vcfg.get_contract_api(filter_runtime=True, check_model_acl=True)
                v_versions.append(str(vcfg.version))
            except KeyError:
                _logger.warning("app.view.config missing; fallback view contract for model=%s vt=%s", model, vt)
                v_contract = {"type": vt}

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
            _logger.warning("app.search.config missing; fallback search contract for model=%s", model)
            data["search"] = {}
            versions["search"] = 0

        # 5) 权限契约（★ 关键改造点）
        #    - 用 su_env 生成完整权限聚合
        #    - 返回时开启 filter_runtime=True，按“当前用户组”裁剪出 effective.rights/rules
        try:
            pcfg = su['app.permission.config']._generate_from_access_rights(model)
            data["permissions"] = pcfg.get_permission_contract(filter_runtime=True)
            versions["perm"] = pcfg.version
        except KeyError:
            _logger.warning("app.permission.config missing; fallback permissions for model=%s", model)
            data["permissions"] = {}
            versions["perm"] = 0

        # 6) 动作按钮 + 工具栏（元数据可 su_env，最终显隐由前端结合 groups/permissions 再次裁剪）
        try:
            acfg = su['app.action.config']._generate_from_ir_actions(model)
            buttons_data = acfg.get_action_contract()
            versions["actions"] = acfg.version if getattr(acfg, 'version', None) else 1
        except KeyError:
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
            _logger.warning("app.report.config missing; fallback empty reports for model=%s", model)
            data["reports"] = []
            versions["reports"] = 0

        try:
            wcfg = su['app.workflow.config']._generate_from_workflow(model)
            data["workflow"] = wcfg.get_workflow_contract(filter_runtime=True)
            versions["workflow"] = wcfg.version
        except KeyError:
            _logger.warning("app.workflow.config missing; fallback empty workflow for model=%s", model)
            data["workflow"] = {}
            versions["workflow"] = 0

        try:
            vcfg2 = su['app.validator.config']._generate_from_validators(model)
            data["validator"] = vcfg2.get_validator_contract()
            versions["validator"] = vcfg2.version
        except KeyError:
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

        # 9) with_data：首屏数据（列表/表单）——必须用“当前用户 env”以自动应用记录规则
        if p.get("with_data"):
            data["data"] = self._fetch_initial_data(env, model, view_types, p, data)

        return data, versions

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
                meta = {
                    k: {
                        "type": getattr(f, "type", None),
                        "string": getattr(f, "string", None) or k,
                        "relation": getattr(f, "comodel_name", None),
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
            }
            if meta.get(name, {}).get("relation"):
                info["relation"] = meta[name]["relation"]
            if isinstance(extra, dict):
                info.update({k: v for k, v in extra.items() if v is not None})
            res[name] = info

        for f in (fields or []):
            if isinstance(f, dict):
                name = f.get("name") or f.get("field") or f.get("id")
                if not name:
                    continue
                add_field(
                    name,
                    f.get("label") or f.get("string"),
                    f.get("type"),
                    {
                        "readonly": bool(f.get("readonly")),
                        "required": bool(f.get("required")),
                        "domain": f.get("domain") or [],
                        "context": f.get("context") or {},
                        "selection": f.get("selection") or f.get("options") or [],
                        "invisible": f.get("invisible"),
                    },
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
