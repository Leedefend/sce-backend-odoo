# -*- coding: utf-8 -*-
"""
models/app_view_config.py

视图配置模型：将 Odoo 原生视图解析为“契约结构”并缓存。
支持版本控制、哈希比对、契约 API 输出。
"""
import io
import json
import logging
import threading
import types
from hashlib import md5

from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval
from .contract_mixin import ContractSchemaMixin
from odoo.addons.smart_core.app_config_engine.services.native_parse_service import NativeParseService
from odoo.addons.smart_core.app_config_engine.services.parse_fallback_service import ParseFallbackService
from odoo.addons.smart_core.app_config_engine.services.contract_governance_filter import (
    ContractGovernanceFilterService,
)
from odoo.addons.smart_core.core.view_orchestrator import ViewOrchestrator

_logger = logging.getLogger(__name__)

PRODUCT_LIST_AUDIT_FIELD_NAMES = frozenset({
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
})


class AppViewConfig(models.Model, ContractSchemaMixin):
    _name = 'app.view.config'
    _description = 'Application View Configuration'
    _rec_name = 'name'
    _order = 'model, view_type'
    SOURCE_KIND = "odoo_native_view_projection"
    SOURCE_AUTHORITIES = ("ir.ui.view", "ir.model.fields", "ir.actions.act_window")

    # ========= 基础信息 =========
    name = fields.Char('Name', required=True)
    model = fields.Char('Model', required=True, index=True)
    view_type = fields.Selection([
        ('form', 'Form'),
        ('tree', 'Tree/List'),
        ('kanban', 'Kanban'),
        ('search', 'Search'),
        ('pivot', 'Pivot'),
        ('graph', 'Graph'),
        ('calendar', 'Calendar'),
        ('gantt', 'Gantt'),
        ('activity', 'Activity'),
        ('dashboard', 'Dashboard'),
    ], string='View Type', required=True, index=True)
    action_id = fields.Many2one(
        "ir.actions.act_window",
        string="Action",
        index=True,
        ondelete="cascade",
        help="Optional action scope for action-specific native view projections.",
    )
    source_view_id = fields.Many2one(
        "ir.ui.view",
        string="Source View",
        index=True,
        ondelete="set null",
        help="Native Odoo view used to compose this projection, when action-bound.",
    )
    projection_scope = fields.Char(
        "Projection Scope",
        index=True,
        help="Stable projection identity. Generic rows use model/view_type; action-bound rows include action/view identity.",
    )

    description = fields.Text('Description')

    # ========= 版本与追踪 =========
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ========= 解析结构 =========
    arch_original = fields.Text('Original XML')       # 最终合并后的 arch XML
    arch_parsed = fields.Json('Parsed View Config')   # 标准化 JSON（契约直用）

    # ========= 权限与状态 =========
    groups_id = fields.Many2many('res.groups', string='Access Groups')
    is_active = fields.Boolean('Active', default=True)

    # ========= 扩展与 AI 元信息 =========
    fragment_ids = fields.Many2many(
        'app.view.fragment',
        string='Fragments',
        domain="[('view_type','=',view_type),('is_active','=',True)]",
    )
    enable_variants = fields.Boolean(default=True, string='Enable Variants')
    meta_info = fields.Json('Meta Info')

    _sql_constraints = [
        ('uniq_projection_scope', 'unique(projection_scope)', '每个视图投影身份仅允许一条解析配置。'),
    ]

    @api.model
    def _source_contract(self, model_name, view_type):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model_name or ""),
            "view_type": str(view_type or ""),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": True,
        }

    @staticmethod
    def _product_list_field_name(value):
        if isinstance(value, dict):
            return str(value.get("name") or value.get("field") or value.get("id") or "").strip()
        return str(value or "").strip()

    @classmethod
    def _is_product_list_audit_field(cls, value):
        return cls._product_list_field_name(value) in PRODUCT_LIST_AUDIT_FIELD_NAMES

    @classmethod
    def _without_product_list_audit_fields(cls, values):
        if not isinstance(values, list):
            return values
        return [value for value in values if not cls._is_product_list_audit_field(value)]

    @classmethod
    def _sanitize_tree_columns_for_user_surface(cls, payload):
        if not isinstance(payload, dict):
            return payload
        next_payload = dict(payload)
        for key in ("columns", "columns_schema", "read_fields"):
            if key in next_payload:
                next_payload[key] = cls._without_product_list_audit_fields(next_payload.get(key))
        return next_payload

    def _projection_identity(self, model_name, view_type):
        context = dict(self.env.context or {})
        action_id = context.get('contract_action_id')
        requested_view_id = context.get('contract_view_id') or context.get('requested_view_id')
        action = None
        source_view_id = False
        try:
            requested_view_id = int(requested_view_id or 0)
        except Exception:
            requested_view_id = 0
        if requested_view_id:
            view = self.env['ir.ui.view'].sudo().browse(requested_view_id)
            if view.exists() and view.model == model_name and view.type == view_type:
                source_view_id = view.id
        try:
            action_id = int(action_id or 0)
        except Exception:
            action_id = 0
        if action_id:
            action = self.env['ir.actions.act_window'].sudo().browse(action_id)
            if action.exists() and getattr(action, 'res_model', None) == model_name:
                if not source_view_id:
                    for view_spec in (action.views or []):
                        if view_spec and len(view_spec) >= 2 and view_spec[1] == view_type:
                            source_view_id = int(view_spec[0] or 0) or False
                            break
                return {
                    "action_id": action.id,
                    "source_view_id": source_view_id,
                    "projection_scope": "action:%s:%s:%s:view:%s" % (
                        action.id,
                        model_name,
                        view_type,
                        source_view_id or 0,
                    ),
                }
        if source_view_id:
            return {
                "action_id": False,
                "source_view_id": source_view_id,
                "projection_scope": "view:%s:%s:%s" % (
                    source_view_id,
                    model_name,
                    view_type,
                ),
            }
        return {
            "action_id": False,
            "source_view_id": False,
            "projection_scope": "generic:%s:%s" % (model_name, view_type),
        }

    # ========= 契约键白名单（类级常量） =========
    _ALLOWED_BY_VT = {
        "common": {"modifiers", "toolbar", "search", "order"},
        "tree": {"columns", "columns_schema", "row_actions", "page_size", "row_classes", "capabilities", "default_order"},
        "form": {
            "layout", "statusbar",
            "header_buttons", "button_box", "stat_buttons",
            "field_modifiers", "subviews",
            "chatter", "attachments", "widgets",
            "capabilities",
        },
        "kanban": {"kanban"},
        "pivot": {"pivot"},
        "graph": {"graph"},
        "calendar": {"calendar"},
        "gantt": {"gantt"},
        "search": {"search"},
        "activity": {"activity"},
        "dashboard": {"dashboard"},
    }

    # ====================== 小工具（类方法，避免局部作用域问题） ======================

    def _looks_like_parser_wrapper(self, data):
        """用于日志提示：判断是否是带包装层的解析器返回体"""
        return isinstance(data, dict) and any(
            k in data for k in ("id", "model", "view_type", "original_odoo_view", "parsed_structure")
        )

    def _unwrap_contract_shape(self, vt, data):
        """
        将解析器返回体“去包装”成纯契约块：
        - 解析器当前返回: {id, model, view_type, original_odoo_view, parsed_structure, ...契约键...}
        - 我们只取契约键（common + 视图专属）
        - 若返回的是 {vt: {...}} 或 {contract/base/block: {...}} 也能自动下钻
        """
        if not isinstance(data, dict):
            return {}

        allowed = set(self._ALLOWED_BY_VT["common"]) | set(self._ALLOWED_BY_VT.get(vt, set()))

        # 情况1：当前结构顶层就含有契约键
        picked = {k: data[k] for k in allowed if k in data}
        if picked:
            return picked

        # 情况2：多视图返回（如 {'tree':{...}, 'form':{...}}）
        if vt in data and isinstance(data[vt], dict):
            return self._unwrap_contract_shape(vt, data[vt])

        # 情况3：包一层 contract/base/block/data
        for key in ("contract", "base", "block", "data"):
            if key in data and isinstance(data[key], dict):
                return self._unwrap_contract_shape(vt, data[key])

        # 都不匹配 → 空
        return {}

    def _parsed_ok(self, vt, data):
        """
        解析结果成功判定（严格版）
        """
        if not isinstance(data, dict) or not data:
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok failed - data is not dict or empty")
            return False

        if vt == 'tree':
            result = isinstance(data.get('columns'), list) and len(data['columns']) > 0
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok tree check result=%s, columns=%s", result, data.get('columns'))
            return result

        if vt == 'form':
            ly = data.get('layout')
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form layout check - layout=%s, type=%s", ly, type(ly))
            if not (isinstance(ly, list) and ly):
                _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form failed - layout is not list or empty")
                return False
            has_sheet = any(isinstance(n, dict) and n.get('type') == 'sheet' for n in ly)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form sheet check - has_sheet=%s, layout=%s", has_sheet, ly)
            if not has_sheet:
                _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form failed - no sheet found")
                return False
            has_extras = any(k in data for k in ('header_buttons', 'button_box', 'statusbar', 'subviews', 'chatter'))
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form extras check - has_extras=%s, data keys=%s", has_extras, list(data.keys()))
            result = bool(has_extras)
            if not result:
                _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok form failed - no extras found")
            return result

        if vt == 'kanban':
            k = data.get('kanban')
            result = isinstance(k, dict) and (
                isinstance(k.get('columns'), list) or
                isinstance(k.get('stages_field'), str) or
                bool(k.get('template_qweb'))
            )
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok kanban check result=%s", result)
            return result

        if vt == 'pivot':
            p = data.get('pivot')
            result = isinstance(p, dict) and isinstance(p.get('measures'), list) and isinstance(p.get('dimensions'), list)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok pivot check result=%s", result)
            return result

        if vt == 'graph':
            g = data.get('graph')
            result = isinstance(g, dict) and isinstance(g.get('measures'), list) and isinstance(g.get('dimensions'), list)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok graph check result=%s", result)
            return result

        if vt == 'calendar':
            c = data.get('calendar')
            result = isinstance(c, dict) and isinstance(c.get('date_start'), str)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok calendar check result=%s", result)
            return result

        if vt == 'gantt':
            gg = data.get('gantt')
            result = isinstance(gg, dict) and isinstance(gg.get('date_start'), str)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok gantt check result=%s", result)
            return result

        if vt == 'search':
            s = data.get('search')
            result = isinstance(s, dict) and isinstance(s.get('filters'), list) and isinstance(s.get('group_by'), list) and isinstance(s.get('facets'), dict)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok search check result=%s", result)
            return result

        if vt == 'activity':
            a = data.get('activity')
            result = isinstance(a, dict)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok activity check result=%s", result)
            return result

        if vt == 'dashboard':
            d = data.get('dashboard')
            result = isinstance(d, dict)
            _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok dashboard check result=%s", result)
            return result

        # 未知视图类型一律认为未通过
        _logger.debug("VIEW_PARSE_DEBUG: _parsed_ok failed - unknown view type %s", vt)
        return False

    # ====================== 生成契约（解析 + 降级） ======================

    @api.model
    def _generate_from_fields_view_get(self, model_name, view_type='form'):
        """
        解析 Odoo 视图为“契约 2.0 视图块”。
        - 优先调用 app.view.parser.parse_odoo_view(model_name, view_type)
        - 无 parser 或解析失败时，优雅降级为最小可渲染结构（zero-config fallback）
        - 仅当结构变化（稳定哈希）时才 +1 版本
        """
        try:
            identity = self._projection_identity(model_name, view_type)
            # 1) 拿到合并后的最终视图
            view_data = self._safe_get_view_data(model_name, view_type)
            if not view_data:
                raise ValueError(_("无法解析视图：%s.%s") % (model_name, view_type))

            _logger.debug(
                "VIEW_PARSE_DEBUG: model=%s view_type=%s view_data_keys=%s",
                model_name, view_type, list(view_data.keys()) if isinstance(view_data, dict) else None,
            )
            if isinstance(view_data, dict) and view_data.get('arch'):
                _logger.debug("VIEW_PARSE_DEBUG: arch_preview=%s", (view_data['arch'] or '')[:200])

            # 2) 调用解析器（如存在）
            ctx_flags = dict(self.env.context or {})
            force_parser = bool(ctx_flags.get('contract_force_parser'))
            force_fallback = bool(ctx_flags.get('contract_force_fallback'))

            # When the projection is scoped to a concrete action/view, the
            # already-resolved view_data is the authority. The generic parser
            # can fall back to the model default tree and leak unrelated
            # columns into action-specific list contracts.
            if identity.get('source_view_id'):
                force_fallback = True

            parse_service = NativeParseService(self)
            fallback_service = ParseFallbackService(self)
            parsed_json = parse_service.parse_with_primary_parser(
                model_name,
                view_type,
                force_fallback=force_fallback,
            )
            parsed_json = fallback_service.resolve_parsed_contract(
                model_name=model_name,
                view_type=view_type,
                view_data=view_data,
                parsed_json=parsed_json,
                force_fallback=force_fallback,
            )

            # 3) 降级/合并默认排序（tree）
            if view_type == 'tree' and view_data and view_data.get('arch'):
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(view_data['arch'])
                    tag_ok = (root.tag in ('tree', 'list'))
                    if tag_ok and root.get('default_order'):
                        parsed_json['order'] = root.get('default_order')
                        _logger.debug("VIEW_PARSE_DEBUG: default_order merged → %s", parsed_json['order'])
                except Exception as e:
                    _logger.warning("default_order 读取失败: %s", e)

            # 3.2) 仅在解析器未给 columns 时，才用原始视图可见字段覆盖（保持保真）
            if view_type == 'tree' and view_data and view_data.get('arch') and not parsed_json.get('columns'):
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(view_data['arch'])
                    visible_fields = []
                    for field in root.findall('.//field[@name]'):
                        fname = field.get('name')
                        is_invisible = field.get('column_invisible')
                        if fname and is_invisible not in ('True', '1'):
                            visible_fields.append(fname)
                    if visible_fields:
                        _logger.debug("从原始视图提取可见字段用于回填: %s", visible_fields)
                        parsed_json['columns'] = visible_fields
                except Exception as e:
                    _logger.warning("从原始视图提取字段失败: %s", e)

            if view_type == 'tree':
                parsed_json = self._sanitize_tree_columns_for_user_surface(parsed_json)

            # 4) 清理不可序列化的对象
            _logger.debug("VIEW_PARSE_DEBUG: cleaning unserializable objects")
            parsed_json = self._clean_unserializable_objects(parsed_json)
            _logger.debug("VIEW_PARSE_DEBUG: cleaned parsed_json keys=%s", list((parsed_json or {}).keys()))

            # 5) 计算稳定哈希
            new_hash = self._stable_hash(parsed_json)

            # 6) 落库（只在变更时 +1 版本）
            vals = {
                'name': f"{model_name} {view_type} view",
                'model': model_name,
                'view_type': view_type,
                'action_id': identity.get('action_id') or False,
                'source_view_id': identity.get('source_view_id') or False,
                'projection_scope': identity.get('projection_scope'),
                'arch_original': view_data.get('arch') or '',
                'arch_parsed': parsed_json,
                'config_hash': new_hash,
                'last_generated': fields.Datetime.now(),
            }
            if self.env.context.get('contract_projection_readonly'):
                vals['version'] = 0
                vals['meta_info'] = {
                    'source': self._source_contract(model_name, view_type),
                    'projection_identity': identity,
                    'transient': True,
                    'runtime_readonly': True,
                }
                return self.new(vals)

            cfg = self.sudo().search([('projection_scope', '=', identity.get('projection_scope'))], limit=1)
            if not cfg and not identity.get('action_id'):
                cfg = self.sudo().search([('model', '=', model_name), ('view_type', '=', view_type)], limit=1)
                if cfg and not cfg.projection_scope:
                    vals['projection_scope'] = identity.get('projection_scope')
            if cfg:
                if cfg.config_hash != new_hash:
                    vals['version'] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info(
                        "View config updated for %s.%s scope=%s → version %s",
                        model_name,
                        view_type,
                        identity.get('projection_scope'),
                        cfg.version,
                    )
                else:
                    _logger.info(
                        "View config for %s.%s scope=%s unchanged, keep version %s",
                        model_name,
                        view_type,
                        identity.get('projection_scope'),
                        cfg.version,
                    )
            else:
                vals['version'] = 1
                cfg = self.sudo().create(vals)
                _logger.info(
                    "View config created for %s.%s scope=%s → version 1",
                    model_name,
                    view_type,
                    identity.get('projection_scope'),
                )

            return cfg

        except Exception:
            if self.env.context.get('contract_projection_readonly'):
                _logger.debug(
                    "runtime readonly view config unavailable for %s.%s",
                    model_name,
                    view_type,
                    exc_info=True,
                )
            else:
                _logger.exception("Failed to generate view config for %s.%s", model_name, view_type)
            raise

    # ====================== 标准化输出（契约直用） ======================

    def get_contract_api(self, filter_runtime=True, check_model_acl=False):
        """
        返回“视图契约”标准结构（契约 2.0 的 views.*）
        结构：依据 view_type 携带特定块；其余通用键始终存在。
        """
        self.ensure_one()
        ctx = dict(self.env.context or {})
        subject = ctx.get('contract_subject')
        action_id = ctx.get('contract_action_id')
        menu_id = ctx.get('contract_menu_id')

        vp = self.build_final_contract(
            subject=subject, action_id=action_id, menu_id=menu_id,
            ctx=ctx, check_model_acl=check_model_acl,
        )
        if self.view_type == 'tree':
            vp = self._sanitize_tree_columns_for_user_surface(vp)
        orchestration_version = self._view_orchestration_version_token(vp)

        block = {
            'model': self.model,
            'view_type': self.view_type,
            'version': self.version,
            'orchestration_version': orchestration_version,
            'effective_version': "%s:%s" % (self.version, orchestration_version),
            'meta': self.meta_info or {},
            'modifiers': vp.get('modifiers', {}),
            'toolbar': vp.get('toolbar', {'header': [], 'sidebar': [], 'footer': []}),
            'search': vp.get('search', {'filters': [], 'group_by': [], 'facets': {'enabled': True}}),
            'order': vp.get('order', None),
            'governance': vp.get('governance', {}),
            'source_trace': vp.get('source_trace', {}),
        }
        vt = self.view_type
        if vt == 'tree':
            block['columns'] = vp.get('columns', ['id'])
            block['columns_schema'] = vp.get('columns_schema', [])
            block['row_actions'] = vp.get('row_actions', [{'name': 'open_form', 'label': _('Open'), 'intent': 'form.open'}])
            block['page_size'] = vp.get('page_size', 50)
            block['row_classes'] = vp.get('row_classes', [])
        elif vt == 'form':
            block['layout'] = vp.get('layout', [{
                'type': 'sheet',
                'children': [{'type': 'group', 'children': [{'type': 'field', 'name': 'name'}]}],
            }])
            block['statusbar'] = vp.get('statusbar', {'field': 'state', 'states': []})
            block['header_buttons'] = vp.get('header_buttons', [])
            block['footer_buttons'] = vp.get('footer_buttons', [])
            block['button_box'] = vp.get('button_box', [])
            block['stat_buttons'] = vp.get('stat_buttons', [])
            block['field_modifiers'] = vp.get('field_modifiers', {})
            block['subviews'] = vp.get('subviews', {})
            block['chatter'] = vp.get('chatter', {'enabled': False})
            block['attachments'] = vp.get('attachments', {'enabled': False})
            block['capabilities'] = vp.get('capabilities', {})
        elif vt == 'kanban':
            block['kanban'] = vp.get('kanban', {'template_qweb': None, 'quick_create': True, 'stages_field': 'stage_id'})
        elif vt == 'pivot':
            block['pivot'] = vp.get('pivot', {'measures': [], 'dimensions': [], 'defaults': {}})
        elif vt == 'graph':
            block['graph'] = vp.get('graph', {'type_default': 'bar', 'measures': [], 'dimensions': []})
        elif vt == 'calendar':
            block['calendar'] = vp.get('calendar', {'date_start': 'date_start', 'date_stop': 'date_end', 'color': 'user_id'})
        elif vt == 'gantt':
            block['gantt'] = vp.get('gantt', {'date_start': 'date_start', 'date_stop': 'date_end', 'progress': 'progress'})
        elif vt == 'activity':
            block['activity'] = vp.get('activity', {'templates': None})
        elif vt == 'dashboard':
            block['dashboard'] = vp.get('dashboard', {'cards': []})
        return block

    def _view_orchestration_version_token(self, contract):
        trace = {}
        if isinstance(contract, dict):
            source_trace = contract.get('source_trace') if isinstance(contract.get('source_trace'), dict) else {}
            trace = source_trace.get('view_orchestration') if isinstance(source_trace.get('view_orchestration'), dict) else {}
        contracts = trace.get('business_config_contracts') if isinstance(trace.get('business_config_contracts'), list) else []
        tokens = []
        for row in contracts:
            if not isinstance(row, dict):
                continue
            row_id = int(row.get('id') or 0)
            version_no = int(row.get('version_no') or 0)
            if row_id or version_no:
                tokens.append("%s.%s" % (row_id, version_no))
        if trace.get('legacy_field_policy_overlay'):
            tokens.append("legacy_policy")
        return ",".join(tokens) if tokens else "native"

    # ====================== 内部：获取视图数据（版本兼容） ======================

    def _safe_get_view_data(self, model_name, view_type):
        """
        兼容不同 Odoo 版本：
        - 新：env[model].get_view(view_type=...)
        - 旧：env[model].fields_view_get(view_type=..., toolbar=True)
        返回：{"arch": str, "fields": dict, "toolbar": dict}
        """
        # View composition is user-sensitive: Odoo prunes inherited view nodes
        # by groups during get_view. Keep the runtime user here; metadata writes
        # below are still performed with sudo.
        Model = self.env[model_name]
        data = {}

        # a) 尝试跟随当前动作绑定的视图（优先精准 view_id）
        try:
            context = dict(self.env.context or {})
            identity = self._projection_identity(model_name, view_type)
            view_id = identity.get('source_view_id') or False
            if view_id:
                _logger.debug("使用指定视图ID %s 加载 %s.%s 视图", view_id, model_name, view_type)
                data = Model.with_context(load_all_views=True).get_view(view_id=view_id, view_type=view_type)
                if isinstance(data, dict) and data.get('arch'):
                    return {
                        'arch': data.get('arch'),
                        'fields': data.get('fields', {}),
                        'toolbar': data.get('toolbar', {}),
                    }
        except Exception as e:
            if self.env.context.get('contract_projection_readonly'):
                _logger.debug("加载指定视图ID失败: %s", e)
            else:
                _logger.warning("加载指定视图ID失败: %s", e)

        # b) 标准方式（按类型）
        try:
            data = Model.get_view(view_type=view_type)
            if isinstance(data, dict) and data.get('arch'):
                arch = data.get('arch', '')
                if arch:
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(arch)
                        if root.tag != view_type and not (view_type == 'tree' and root.tag == 'list'):
                            _logger.warning("视图类型不匹配: 请求 %s 但获得 %s", view_type, root.tag)
                    except Exception as e:
                        _logger.warning("XML解析失败，仍然使用视图数据: %s", e)
                return {
                    'arch': data.get('arch'),
                    'fields': data.get('fields', {}),
                    'toolbar': data.get('toolbar', {}),
                }
        except Exception as e:
            if self.env.context.get('contract_projection_readonly'):
                _logger.debug("get_view 失败: %s", e)
            else:
                _logger.warning("get_view 失败: %s", e)

        # c) 回退 fields_view_get（低版本 Odoo 有；若没有则捕获异常返回 None）
        try:
            fv = Model.fields_view_get(view_type=view_type, toolbar=True)
            return {'arch': fv.get('arch'), 'fields': fv.get('fields', {}), 'toolbar': fv.get('toolbar', {})}
        except Exception as e:
            if self.env.context.get('contract_projection_readonly'):
                _logger.debug("fields_view_get 失败: %s", e)
            else:
                _logger.warning("fields_view_get 失败: %s", e)
            return None

    # ====================== 内部：降级解析（无 parser 也可用） ======================

    def _fallback_parse(self, model_name, view_type, view_data):
        """
        生成“最小但可用”的标准结构：
        - form：深入解析 arch，恢复 header 按钮、智能按钮、notebook/page/group/field、字段修饰、chatter/附件、x2many 子视图
        - tree：保留你原有逻辑
        - kanban：提供最小可渲染块，避免误用 form 逻辑
        """
        import xml.etree.ElementTree as ET

        fields_get = (view_data or {}).get('fields') or self.env[model_name].sudo().fields_get()
        arch = (view_data or {}).get('arch', '') or ''
        base = {
            'modifiers': {},
            'toolbar': {'header': [], 'sidebar': [], 'footer': []},
            'search': {'filters': [], 'group_by': [], 'facets': {'enabled': True}},
        }

        # ======== TREE：沿用你的旧策略 ========
        if view_type == 'tree':
            view_fields = []
            columns_schema = []
            order_default = getattr(self.env[model_name], '_order', 'id desc') or 'id desc'
            if arch:
                try:
                    root = ET.fromstring(arch)
                    if root.get('default_order'):
                        order_default = root.get('default_order')
                    for field in root.findall('.//field[@name]'):
                        fname = field.get('name')
                        is_invisible = field.get('column_invisible')
                        if fname and is_invisible not in ('True', '1'):
                            view_fields.append(fname)
                            meta = (fields_get or {}).get(fname) or {}
                            label = field.get('string') or meta.get('string') or fname
                            columns_schema.append({
                                'name': fname,
                                'label': label,
                                'string': label,
                                'type': meta.get('type') or 'char',
                                'widget': field.get('widget') or '',
                                'optional': field.get('optional') or '',
                            })
                    _logger.debug("从原始视图提取到字段: %s", view_fields)
                except Exception as e:
                    _logger.warning("从原始视图解析字段失败: %s", e)

            if not view_fields:
                # 旧候选策略
                candidate_fields, relation_fields, other_fields = [], [], []
                business_priority = [
                    'name', 'display_name', 'title', 'subject', 'description',
                    'partner_id', 'user_id', 'company_id', 'sequence',
                    'tag_ids', 'stage_id', 'date_start', 'date',
                ]
                for fname, fmeta in (fields_get or {}).items():
                    if fname in ('message_ids', 'activity_ids'):
                        continue
                    if fname in business_priority:
                        candidate_fields.append(fname)
                    elif (fmeta.get('type') in ('many2one', 'many2many')) and not fname.startswith(('activity_', 'message_')):
                        relation_fields.append(fname)
                    elif not fname.startswith(('activity_', 'message_', '__')):
                        other_fields.append(fname)
                all_candidates = candidate_fields + relation_fields + other_fields
                view_fields = all_candidates[:10] if all_candidates else ['id']
                columns_schema = [
                    {
                        'name': fname,
                        'label': ((fields_get or {}).get(fname) or {}).get('string') or fname,
                        'string': ((fields_get or {}).get(fname) or {}).get('string') or fname,
                        'type': ((fields_get or {}).get(fname) or {}).get('type') or 'char',
                        'widget': '',
                        'optional': '',
                    }
                    for fname in view_fields
                ]

            base.update({
                'order': order_default,
                'columns': view_fields,
                'columns_schema': columns_schema,
                'row_actions': [{'name': 'open_form', 'label': _('Open'), 'intent': 'form.open'}],
                'page_size': 50,
                'row_classes': [],
            })
            return base

        # ======== KANBAN：最小块 + 从 arch 抽取常见属性 ========
        if view_type == 'kanban':
            kb = {'template_qweb': None, 'quick_create': True, 'stages_field': 'stage_id', 'fields': []}
            if arch:
                try:
                    root = ET.fromstring(arch)
                    # 常见分组字段：不同版本/模块写法不一，这里尽量从属性里推断
                    for attr in ('default_group_by', 'group_by', 'stages_field'):
                        val = root.get(attr)
                        if val:
                            kb['stages_field'] = val
                            break
                    # quick_create（出现 false/0/False 时关掉）
                    if root.get('quick_create'):
                        q = root.get('quick_create')
                        kb['quick_create'] = False if str(q).lower() in ('0', 'false') else True
                    # 带上 js_class 信息，便于前端增强（可选）
                    if root.get('js_class'):
                        kb['js_class'] = root.get('js_class')
                    known_fields = set((fields_get or {}).keys())
                    seen_fields = set()
                    for field_node in root.findall('.//field[@name]'):
                        fname = (field_node.get('name') or '').strip()
                        if not fname or fname in seen_fields:
                            continue
                        if known_fields and fname not in known_fields:
                            continue
                        seen_fields.add(fname)
                        kb['fields'].append(fname)
                except Exception as e:
                    _logger.warning('KANBAN fallback: 解析属性失败: %s', e)
            base.update({'kanban': kb})
            return base

        if view_type == 'search':
            search = {'filters': [], 'group_by': [], 'group_by_fields': [], 'search_fields': [], 'facets': {'enabled': True}}
            if arch:
                try:
                    root = ET.fromstring(arch)
                    search_nodes = [root] if root.tag == 'search' else list(root.findall('.//search'))
                    seen_group_by = set()
                    for search_node in search_nodes:
                        for field_node in search_node.findall('.//field'):
                            fname = (field_node.get('name') or '').strip()
                            if not fname:
                                continue
                            search['search_fields'].append({
                                'name': fname,
                                'label': field_node.get('string') or fname,
                                'operator': field_node.get('operator') or '',
                                'filter_domain_raw': field_node.get('filter_domain') or '',
                                'context_raw': field_node.get('context') or '',
                            })
                        for filter_node in search_node.findall('.//filter'):
                            name = filter_node.get('name') or filter_node.get('string') or ''
                            context_raw = filter_node.get('context') or ''
                            search['filters'].append({
                                'name': name,
                                'label': filter_node.get('string') or name,
                                'domain_raw': filter_node.get('domain') or '',
                                'context_raw': context_raw,
                            })
                            if 'group_by' in context_raw:
                                group_field = context_raw.split('group_by', 1)[1].split(':', 1)[-1].strip(" {}'\"")
                                if group_field and group_field not in seen_group_by:
                                    seen_group_by.add(group_field)
                                    search['group_by'].append(group_field)
                                    search['group_by_fields'].append({
                                        'name': name,
                                        'label': filter_node.get('string') or name,
                                        'field': group_field,
                                        'context_raw': context_raw,
                                    })
                except Exception as e:
                    _logger.warning('SEARCH fallback: 解析属性失败: %s', e)
            base['search'] = search
            return base

        if view_type == 'calendar':
            cal = {
                'date_start': 'date_start',
                'date_stop': 'date_end',
                'color': 'user_id',
                'date_slots': {'start': 'date_start', 'stop': 'date_end'},
                'color_slots': {'color': 'user_id'},
                'fields': [],
                'native_attrs': {},
            }
            if arch:
                try:
                    root = ET.fromstring(arch)
                    if root.tag != 'calendar':
                        root = root.find('.//calendar') or root
                    cal['native_attrs'] = dict(root.attrib or {})
                    for key in ('date_start', 'date_stop', 'color', 'default_scale', 'event_open_popup'):
                        if root.get(key) is not None:
                            cal[key] = root.get(key)
                    cal['date_slots'] = {'start': cal['date_start'], 'stop': cal['date_stop']}
                    cal['color_slots'] = {'color': cal['color']}
                    cal['fields'] = self._fallback_view_field_nodes(root)
                except Exception as e:
                    _logger.warning('CALENDAR fallback: 解析属性失败: %s', e)
            base['calendar'] = cal
            return base

        if view_type == 'gantt':
            gantt = {
                'date_start': 'date_start',
                'date_stop': 'date_end',
                'progress': 'progress',
                'date_slots': {'start': 'date_start', 'stop': 'date_end'},
                'resource_slots': {},
                'dependency_slots': {},
                'fields': [],
                'native_attrs': {},
            }
            if arch:
                try:
                    root = ET.fromstring(arch)
                    if root.tag != 'gantt':
                        root = root.find('.//gantt') or root
                    gantt['native_attrs'] = dict(root.attrib or {})
                    for key in ('date_start', 'date_stop', 'progress', 'default_scale'):
                        if root.get(key) is not None:
                            gantt[key] = root.get(key)
                    gantt['date_slots'] = {'start': gantt['date_start'], 'stop': gantt['date_stop']}
                    if root.get('default_group_by'):
                        gantt['resource_slots']['group_by'] = root.get('default_group_by')
                    if root.get('dependency_field'):
                        gantt['dependency_slots']['dependency_field'] = root.get('dependency_field')
                    gantt['fields'] = self._fallback_view_field_nodes(root)
                except Exception as e:
                    _logger.warning('GANTT fallback: 解析属性失败: %s', e)
            base['gantt'] = gantt
            return base

        if view_type == 'activity':
            activity = {
                'template_qweb': None,
                'activity_type_slots': {},
                'deadline_slots': {},
                'assignee_slots': {},
                'fields': [],
                'native_attrs': {},
            }
            if arch:
                try:
                    root = ET.fromstring(arch)
                    if root.tag != 'activity':
                        root = root.find('.//activity') or root
                    activity['native_attrs'] = dict(root.attrib or {})
                    if root.get('activity_type'):
                        activity['activity_type_slots']['type'] = root.get('activity_type')
                    if root.get('date_deadline'):
                        activity['deadline_slots']['deadline'] = root.get('date_deadline')
                    if root.get('user_id'):
                        activity['assignee_slots']['assignee'] = root.get('user_id')
                    activity['fields'] = self._fallback_view_field_nodes(root)
                except Exception as e:
                    _logger.warning('ACTIVITY fallback: 解析属性失败: %s', e)
            base['activity'] = activity
            return base

        # ======== FORM：新增强逻辑 ========
        # 小工具：抽取 header 按钮
        def _extract_header_buttons(root):
            btns = []
            if root is None:
                return btns
            header = root.find('.//header')
            if header is None:
                return btns
            for b in header.findall('.//button'):
                item = {
                    'name': b.get('name'),
                    'string': b.get('string') or b.get('title') or '',
                    'type': b.get('type') or 'object',
                    'class': b.get('class') or '',
                    'confirm': b.get('confirm') or '',
                    'context': b.get('context') or '',
                    'groups_xmlids': (b.get('groups') or '').split(',') if b.get('groups') else [],
                }
                # workflow-like
                if b.get('states'):
                    item['states'] = [s.strip() for s in b.get('states').split(',') if s.strip()]
                btns.append(item)
            return btns

        # 小工具：抽取 oe_button_box / stat_buttons
        def _extract_button_box(root):
            stats = []
            if root is None:
                return stats
            # 常见写法：<div class="oe_button_box"> <button class="oe_stat_button" ...>
            for div in root.findall('.//div'):
                klass = (div.get('class') or '')
                if 'oe_button_box' not in klass:
                    continue
                for b in div.findall('.//button'):
                    if 'oe_stat_button' not in (b.get('class') or ''):
                        continue
                    stats.append({
                        'string': b.get('string') or '',
                        'icon': b.get('icon') or '',
                        'type': b.get('type') or 'object',
                        'name': b.get('name'),
                        'help': b.get('help') or '',
                        'groups_xmlids': (b.get('groups') or '').split(',') if b.get('groups') else [],
                    })
            return stats

        # 小工具：把 arch 的 notebook/page/group/field 变成 layout 结构
        def _extract_layout(root):
            def field_node(f):
                fname = f.get('name')
                node = {'type': 'field', 'name': fname}
                meta = dict((fields_get or {}).get(fname) or {})
                if f.get('string'):
                    node['string'] = f.get('string')
                    node['label'] = f.get('string')
                    meta['string'] = f.get('string')
                    meta['label'] = f.get('string')
                if f.get('help'):
                    meta['help'] = f.get('help')
                if f.get('widget'):
                    node['widget'] = f.get('widget')
                    meta['widget'] = f.get('widget')
                if f.get('options'):
                    meta['options'] = f.get('options')
                for attr in ('readonly', 'required', 'invisible', 'column_invisible'):
                    if f.get(attr) is not None:
                        node[attr] = f.get(attr)
                        meta[attr] = f.get(attr)
                if meta:
                    node['fieldInfo'] = meta
                return node

            def group_node(g):
                children = []
                for n in list(g or []):
                    if getattr(n, 'tag', None) == 'field' and n.get('name'):
                        children.append(field_node(n))
                return {'type': 'group', 'children': children, 'label': g.get('string') if g is not None else None}

            def page_node(p):
                groups = [group_node(g) for g in (p.findall('.//group') if p is not None else [])]
                return {'type': 'page', 'string': p.get('string') if p is not None else '', 'children': groups}

            def sheet_node(s):
                if s is None:
                    return {'type': 'sheet', 'children': []}
                notebook = s.find('.//notebook')
                if notebook is not None:
                    pages = [page_node(pg) for pg in notebook.findall('./page')]
                    return {'type': 'sheet', 'children': [{'type': 'notebook', 'children': pages}]}
                groups = [group_node(g) for g in s.findall('.//group')]
                if groups:
                    return {'type': 'sheet', 'children': groups}
                f = s.find('.//field[@name]') if s is not None else None
                return {'type': 'sheet', 'children': [{'type': 'group', 'children': [field_node(f)]}] if f is not None else []}

            form = root if (root is not None and root.tag == 'form') else (root.find('.//form') if root is not None else None)
            if form is None:
                return [{'type': 'sheet', 'children': []}]
            sheet = None
            for d in form:
                if getattr(d, 'tag', None) == 'sheet':
                    sheet = d
                    break
            if sheet is None:
                sheet = form
            return [sheet_node(sheet)]

        # 小工具：聚合字段级 modifiers（来自 fields_view_get）
        def _collect_field_modifiers(fields_meta):
            out = {}
            for fname, meta in (fields_meta or {}).items():
                mods = meta.get('modifiers') or {}
                x = {}
                for k in ('readonly', 'required', 'invisible', 'column_invisible'):
                    if k in mods:
                        x[k] = mods[k]
                for k in ('widget', 'domain', 'context', 'groups'):
                    if k in meta:
                        x[k] = meta[k]
                if x:
                    out[fname] = x
            return out

        # 小工具：识别 chatter / attachments （避免 contains()，改为遍历判断）
        def _detect_chatter_and_attachments(root):
            info = {'chatter': {'enabled': False}, 'attachments': {'enabled': False}}
            if root is None:
                return info
            has_chatter = any(
                (el.get('widget') == 'mail_thread') or ('oe_chatter' in (el.get('class') or ''))
                for el in root.iter()
            )
            if has_chatter:
                info['chatter'] = {'enabled': True, 'features': {'message': True, 'activity': True}}
            has_attach = any(
                (el.get('widget') == 'many2many_binary') or ('oe_attachment_box' in (el.get('class') or ''))
                for el in root.iter()
            )
            if has_attach:
                info['attachments'] = {'enabled': True}
            return info

        relation_fields_cache = {}

        def _relation_fields(relation_model):
            model = str(relation_model or '').strip()
            if not model:
                return {}
            if model in relation_fields_cache:
                return relation_fields_cache[model]
            try:
                env_model = self.env[model]
                fields_map = env_model.fields_get()
            except Exception:
                fields_map = {}
            relation_fields_cache[model] = fields_map if isinstance(fields_map, dict) else {}
            return relation_fields_cache[model]

        def _infer_tree_columns(meta, relation_meta):
            # 优先 name/display_name，补充可读的轻量列
            preferred = ['name', 'display_name', 'code', 'state', 'type']
            available = [k for k, v in (relation_meta or {}).items() if isinstance(v, dict)]
            picked = []
            for col in preferred:
                if col in available and col not in picked:
                    picked.append(col)
            if not picked:
                for col in available:
                    ftype = str((relation_meta.get(col) or {}).get('type') or '').strip().lower()
                    if ftype in ('one2many', 'many2many', 'binary', 'html'):
                        continue
                    picked.append(col)
                    if len(picked) >= 4:
                        break
            if not picked:
                picked = ['display_name']

            out = []
            for col in picked[:6]:
                fmeta = relation_meta.get(col) or {}
                selection = fmeta.get('selection')
                out.append({
                    'name': col,
                    'label': fmeta.get('string') or col,
                    'ttype': str(fmeta.get('type') or 'char'),
                    'required': bool(fmeta.get('required')),
                    'readonly': bool(fmeta.get('readonly')),
                    'selection': selection if isinstance(selection, list) else [],
                })
            return out

        # 小工具：识别 x2many 并构造最小子视图（结构化列契约）
        def _infer_x2many_subviews(fields_meta):
            sub = {}
            for fname, meta in (fields_meta or {}).items():
                t = meta.get('type')
                if t in ('one2many', 'many2many'):
                    relation = str(meta.get('relation') or '').strip()
                    rel_fields = _relation_fields(relation)
                    sub[fname] = {
                        'tree': {'columns': _infer_tree_columns(meta, rel_fields)},
                        'fields': rel_fields,
                        'policies': {'inline_edit': True, 'can_create': True, 'can_unlink': True},
                    }
            return sub

        # 开始解析 FORM
        if arch:
            try:
                root = ET.fromstring(arch)
            except Exception as e:
                _logger.warning("FORM fallback: XML 解析失败，将使用极简布局: %s", e)
                root = None
        else:
            root = None

        layout = _extract_layout(root) if root is not None else [{
            'type': 'sheet',
            'children': [{'type': 'group', 'children': [{'type': 'field', 'name': 'name'}]}],
        }]
        header_buttons = _extract_header_buttons(root)
        stat_buttons = _extract_button_box(root)
        fm = _collect_field_modifiers((view_data or {}).get('fields') or {})
        ca = _detect_chatter_and_attachments(root)
        subviews = _infer_x2many_subviews((view_data or {}).get('fields') or {})

        base.update({
            'layout': layout,
            'statusbar': {'field': 'state', 'states': []},  # 可在 P1 用 header/workflow 补全
            'header_buttons': header_buttons,
            'stat_buttons': stat_buttons,
            'button_box': stat_buttons,  # 兼容命名
            'field_modifiers': fm,
            'subviews': subviews,
            'chatter': ca['chatter'],
            'attachments': ca['attachments'],
        })
        return base

    def _fallback_view_field_nodes(self, root):
        rows = []
        seen = set()
        for field_node in root.findall('.//field') if root is not None else []:
            name = (field_node.get('name') or '').strip()
            if not name or name in seen:
                continue
            seen.add(name)
            rows.append({
                'name': name,
                'label': field_node.get('string') or name,
                'widget': field_node.get('widget') or '',
                'invisible': field_node.get('invisible') or '',
                'modifiers': field_node.get('modifiers') or '',
            })
        return rows

    # ====================== 内部：稳定哈希 ======================

    def _stable_hash(self, parsed_json):
        """
        稳定哈希：仅对“影响渲染的结构”做 MD5。
        """
        raw = json.dumps(parsed_json or {}, sort_keys=True, ensure_ascii=False, default=str)
        return md5(raw.encode('utf-8')).hexdigest()

    # ====================== 内部：清理不可序列化的对象 ======================
    
    def _is_unserializable(self, obj):
        """
        检查对象是否不可序列化
        """
        # 检查是否为cython函数或方法
        if hasattr(obj, '__class__'):
            class_name = str(type(obj))
            if 'cython_function_or_method' in class_name or 'cyfunction' in class_name:
                return True
        
        # 检查是否为函数或lambda
        import types
        if isinstance(obj, (types.FunctionType, types.LambdaType, types.MethodType)):
            return True
            
        # 检查是否为其他不可序列化的类型
        import threading
        # 创建线程锁类型的实例用于类型检查
        lock_instance = threading.Lock()
        rlock_instance = threading.RLock()
        semaphore_instance = threading.Semaphore()
        event_instance = threading.Event()
        condition_instance = threading.Condition()
        
        if isinstance(obj, (type(lock_instance), type(rlock_instance), type(semaphore_instance), type(event_instance), type(condition_instance))):
            return True
            
        # 检查是否为模块对象
        if isinstance(obj, types.ModuleType):
            return True
            
        # 检查是否为文件对象
        if isinstance(obj, (io.IOBase,)):
            return True
            
        # 检查是否为其他常见的不可序列化对象
        try:
            import json
            json.dumps(obj)
            return False
        except (TypeError, ValueError):
            # 如果对象不能被JSON序列化，则认为是不可序列化的
            return True
        except Exception:
            # 其他异常也认为是不可序列化的
            return True

    def _clean_unserializable_objects(self, obj):
        """
        清理不可序列化的对象，如cyfunction Comment等
        """
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # 跳过不可序列化的键
                if isinstance(key, (int, str, float, bool)) or key is None:
                    # 如果值是不可序列化的，我们需要递归清理它而不是直接跳过
                    cleaned_value = self._clean_unserializable_objects(value)
                    # 只有当清理后的值不是None时才添加到结果中
                    if cleaned_value is not None:
                        cleaned[key] = cleaned_value
                else:
                    # 跳过不可序列化的键
                    continue
            return cleaned
        elif isinstance(obj, list):
            cleaned = []
            for item in obj:
                # 对于列表中的每个项目，我们都要递归清理
                cleaned_item = self._clean_unserializable_objects(item)
                # 只添加非None的对象
                if cleaned_item is not None:
                    cleaned.append(cleaned_item)
            return cleaned
        elif isinstance(obj, tuple):
            # 转换元组为列表并清理
            cleaned_list = []
            for item in obj:
                cleaned_item = self._clean_unserializable_objects(item)
                if cleaned_item is not None:
                    cleaned_list.append(cleaned_item)
            return cleaned_list
        elif self._is_unserializable(obj):
            # 直接返回None来替换不可序列化的对象
            return None
        else:
            return obj

    # ====================== 内部：运行态过滤（按用户组/ACL） ======================

    def _runtime_filter(self, parsed, model_name, check_model_acl=False):
        """Compatibility adapter: governance filtering moved to service layer."""
        return ContractGovernanceFilterService(self).apply_runtime_filter(
            parsed,
            model_name,
            check_model_acl=check_model_acl,
        )

    # === 聚合：基础 + 碎片 + 变体 → 最终契约（给服务层使用） ===
    def build_final_contract(self, subject=None, action_id=None, menu_id=None, ctx=None, check_model_acl=False):
        """
        生成最终视图契约：
        1) 基础 contract = self.arch_parsed（白名单结构）
        2) 叠加 fragment（按 priority 由低到高合并）
        3) 叠加 variant（applicable 后按 priority/version 合并）
        4) 运行态裁剪（groups/ACL）
        """
        self.ensure_one()
        vt = self.view_type

        # 1) 基础
        base = self.json_clone(self.arch_parsed or {})
        base = self.sanitize_governed_contract(vt, base)

        # 2) 碎片
        try:
            fragments = self.fragment_ids or []
            if fragments:
                valid = []
                for fr in fragments:
                    try:
                        _ = fr.priority
                        _ = fr.name
                        valid.append(fr)
                    except Exception as e:
                        _logger.warning("Skipping invalid fragment record: %s", e)
                        continue
                for fr in sorted(valid, key=lambda r: r.priority or 0):
                    try:
                        base = self.deep_merge(base, fr.materialize(vt))
                    except Exception as e:
                        _logger.warning("Failed to materialize fragment %s: %s", getattr(fr, 'name', 'unknown'), e)
                        continue
        except Exception as e:
            _logger.warning("Fragment processing failed, skipping: %s", e)

        # 3) 变体
        if self.enable_variants:
            Variant = self.env['app.view.variant'].sudo()
            lang = (ctx or {}).get('lang') or self.env.context.get('lang')
            company = getattr(self.env, 'company', None)
            user = self.env.user
            candidates = Variant.search([
                ('is_active', '=', True),
                ('model', '=', self.model),
                ('view_type', '=', vt),
            ])
            applicable = [
                v for v in candidates
                if v.applicable(self.model, vt, subject, action_id, menu_id, lang, company, user, ctx)
            ]
            for v in sorted(applicable, key=lambda r: (r.priority or 0, r.version or 0)):
                base = self.deep_merge(base, v.materialize_patch(vt))

        # 4) 业务视图编排：配置即编排输入。兼容的表单字段策略由编排器消费。
        base = ViewOrchestrator(self.env).compose(
            base,
            model_name=self.model,
            view_type=vt,
            action_id=action_id,
            view_id=int(self.source_view_id.id or 0) or None,
            ctx=ctx or {},
        )

        # 5) 运行态裁剪
        final = self._runtime_filter(base, self.model, check_model_acl=check_model_acl)
        return final

    # ====================== 小工具 ======================

    def _model_exists(self, name):
        try:
            self.env[name]
            return True
        except Exception:
            return False
