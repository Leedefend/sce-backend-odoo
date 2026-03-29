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

_logger = logging.getLogger(__name__)


class AppViewConfig(models.Model, ContractSchemaMixin):
    _name = 'app.view.config'
    _description = 'Application View Configuration'
    _rec_name = 'name'
    _order = 'model, view_type'

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
        ('uniq_model_viewtype', 'unique(model, view_type)', '每个模型每种视图类型仅允许一条解析配置。'),
    ]

    # ========= 契约键白名单（类级常量） =========
    _ALLOWED_BY_VT = {
        "common": {"modifiers", "toolbar", "search", "order"},
        "tree": {"columns", "row_actions", "page_size", "row_classes"},
        "form": {
            "layout", "statusbar",
            "header_buttons", "button_box", "stat_buttons",
            "field_modifiers", "subviews",
            "chatter", "attachments", "widgets",
        },
        "kanban": {"kanban"},
        "pivot": {"pivot"},
        "graph": {"graph"},
        "calendar": {"calendar"},
        "gantt": {"gantt"},
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
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok failed - data is not dict or empty")
            return False

        if vt == 'tree':
            result = isinstance(data.get('columns'), list) and len(data['columns']) > 0
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok tree check result=%s, columns=%s", result, data.get('columns'))
            return result

        if vt == 'form':
            ly = data.get('layout')
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form layout check - layout=%s, type=%s", ly, type(ly))
            if not (isinstance(ly, list) and ly):
                _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form failed - layout is not list or empty")
                return False
            has_sheet = any(isinstance(n, dict) and n.get('type') == 'sheet' for n in ly)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form sheet check - has_sheet=%s, layout=%s", has_sheet, ly)
            if not has_sheet:
                _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form failed - no sheet found")
                return False
            has_extras = any(k in data for k in ('header_buttons', 'button_box', 'statusbar', 'subviews', 'chatter'))
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form extras check - has_extras=%s, data keys=%s", has_extras, list(data.keys()))
            result = bool(has_extras)
            if not result:
                _logger.info("VIEW_PARSE_DEBUG: _parsed_ok form failed - no extras found")
            return result

        if vt == 'kanban':
            k = data.get('kanban')
            result = isinstance(k, dict) and (
                isinstance(k.get('columns'), list) or
                isinstance(k.get('stages_field'), str) or
                bool(k.get('template_qweb'))
            )
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok kanban check result=%s", result)
            return result

        if vt == 'pivot':
            p = data.get('pivot')
            result = isinstance(p, dict) and isinstance(p.get('measures'), list) and isinstance(p.get('dimensions'), list)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok pivot check result=%s", result)
            return result

        if vt == 'graph':
            g = data.get('graph')
            result = isinstance(g, dict) and isinstance(g.get('measures'), list) and isinstance(g.get('dimensions'), list)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok graph check result=%s", result)
            return result

        if vt == 'calendar':
            c = data.get('calendar')
            result = isinstance(c, dict) and isinstance(c.get('date_start'), str)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok calendar check result=%s", result)
            return result

        if vt == 'gantt':
            gg = data.get('gantt')
            result = isinstance(gg, dict) and isinstance(gg.get('date_start'), str)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok gantt check result=%s", result)
            return result

        if vt == 'search':
            s = data.get('search')
            result = isinstance(s, dict) and isinstance(s.get('filters'), list) and isinstance(s.get('group_by'), list) and isinstance(s.get('facets'), dict)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok search check result=%s", result)
            return result

        if vt == 'activity':
            a = data.get('activity')
            result = isinstance(a, dict)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok activity check result=%s", result)
            return result

        if vt == 'dashboard':
            d = data.get('dashboard')
            result = isinstance(d, dict)
            _logger.info("VIEW_PARSE_DEBUG: _parsed_ok dashboard check result=%s", result)
            return result

        # 未知视图类型一律认为未通过
        _logger.info("VIEW_PARSE_DEBUG: _parsed_ok failed - unknown view type %s", vt)
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
            # 1) 拿到合并后的最终视图
            view_data = self._safe_get_view_data(model_name, view_type)
            if not view_data:
                raise ValueError(_("无法解析视图：%s.%s") % (model_name, view_type))

            _logger.info(
                "VIEW_PARSE_DEBUG: model=%s view_type=%s view_data_keys=%s",
                model_name, view_type, list(view_data.keys()) if isinstance(view_data, dict) else None,
            )
            if isinstance(view_data, dict) and view_data.get('arch'):
                _logger.info("VIEW_PARSE_DEBUG: arch_preview=%s", (view_data['arch'] or '')[:200])

            # 2) 调用解析器（如存在）
            ctx_flags = dict(self.env.context or {})
            force_parser = bool(ctx_flags.get('contract_force_parser'))
            force_fallback = bool(ctx_flags.get('contract_force_fallback'))
            action_specific_view = str(view_data.get('_contract_view_source') or '').strip() == 'action_specific'

            parse_service = NativeParseService(self)
            fallback_service = ParseFallbackService(self)
            if action_specific_view and not force_parser:
                _logger.info(
                    "VIEW_PARSE_DEBUG: action-specific view detected for %s.%s, prefer fallback parser on bound arch",
                    model_name,
                    view_type,
                )
                parsed_json = self._fallback_parse(model_name, view_type, view_data)
            else:
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
                        _logger.info("VIEW_PARSE_DEBUG: default_order merged → %s", parsed_json['order'])
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
                        _logger.info("从原始视图提取可见字段用于回填: %s", visible_fields)
                        parsed_json['columns'] = visible_fields
                except Exception as e:
                    _logger.warning("从原始视图提取字段失败: %s", e)

            # 4) 清理不可序列化的对象
            _logger.info("VIEW_PARSE_DEBUG: cleaning unserializable objects")
            parsed_json = self._clean_unserializable_objects(parsed_json)
            _logger.info("VIEW_PARSE_DEBUG: cleaned parsed_json keys=%s", list((parsed_json or {}).keys()))

            # 5) 计算稳定哈希
            new_hash = self._stable_hash(parsed_json)

            # 6) 落库（只在变更时 +1 版本）
            cfg = self.sudo().search([('model', '=', model_name), ('view_type', '=', view_type)], limit=1)
            vals = {
                'name': f"{model_name} {view_type} view",
                'model': model_name,
                'view_type': view_type,
                'arch_original': view_data.get('arch') or '',
                'arch_parsed': parsed_json,
                'config_hash': new_hash,
                'last_generated': fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals['version'] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("View config updated for %s.%s → version %s", model_name, view_type, cfg.version)
                else:
                    _logger.info("View config for %s.%s unchanged, keep version %s", model_name, view_type, cfg.version)
            else:
                vals['version'] = 1
                cfg = self.sudo().create(vals)
                _logger.info("View config created for %s.%s → version 1", model_name, view_type)

            return cfg

        except Exception:
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

        block = {
            'model': self.model,
            'view_type': self.view_type,
            'version': self.version,
            'meta': self.meta_info or {},
            'modifiers': vp.get('modifiers', {}),
            'toolbar': vp.get('toolbar', {'header': [], 'sidebar': [], 'footer': []}),
            'search': vp.get('search', {'filters': [], 'group_by': [], 'facets': {'enabled': True}}),
            'order': vp.get('order', None),
        }
        vt = self.view_type
        if vt == 'tree':
            block['columns'] = vp.get('columns', ['id'])
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
            block['button_box'] = vp.get('button_box', [])
            block['stat_buttons'] = vp.get('stat_buttons', [])
            block['field_modifiers'] = vp.get('field_modifiers', {})
            block['subviews'] = vp.get('subviews', {})
            block['chatter'] = vp.get('chatter', {'enabled': False})
            block['attachments'] = vp.get('attachments', {'enabled': False})
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

    # ====================== 内部：获取视图数据（版本兼容） ======================

    def _safe_get_view_data(self, model_name, view_type):
        """
        兼容不同 Odoo 版本：
        - 新：env[model].get_view(view_type=...)
        - 旧：env[model].fields_view_get(view_type=..., toolbar=True)
        返回：{"arch": str, "fields": dict, "toolbar": dict}
        """
        Model = self.env[model_name].sudo()
        data = {}

        # a) 尝试跟随当前动作绑定的视图（优先精准 view_id）
        try:
            context = dict(self.env.context or {})
            action_id = context.get('contract_action_id')
            view_id = False
            if action_id:
                act = self.env['ir.actions.act_window'].sudo().browse(int(action_id))
                if act.exists():
                    action_context = {}
                    try:
                        action_context = safe_eval(act.context) if isinstance(act.context, str) and act.context.strip() else {}
                    except Exception:
                        action_context = {}
                    explicit_view_xmlid = False
                    if view_type == 'form':
                        explicit_view_xmlid = action_context.get('form_view_ref')
                    elif view_type == 'tree':
                        explicit_view_xmlid = action_context.get('tree_view_ref')
                    if explicit_view_xmlid:
                        try:
                            res = self.env['ir.model.data']._xmlid_to_res_model_res_id(explicit_view_xmlid)
                            if res and res[0] == 'ir.ui.view':
                                view_id = res[1]
                        except Exception as e:
                            _logger.warning("通过 action context 解析指定视图失败: %s", e)
                    for v in (act.views or []):
                        if not (v and len(v) >= 2 and v[1] == view_type):
                            continue
                        if v[0]:
                            view_id = v[0]
                            break
                    if not view_id:
                        bound_view = self.env['ir.actions.act_window.view'].sudo().search(
                            [
                                ('act_window_id', '=', act.id),
                                ('view_mode', '=', view_type),
                                ('view_id', '!=', False),
                            ],
                            order='sequence asc, id asc',
                            limit=1,
                        )
                        if bound_view and bound_view.view_id:
                            view_id = bound_view.view_id.id
            if view_id:
                _logger.info("使用指定视图ID %s 加载 %s.%s 视图", view_id, model_name, view_type)
                data = Model.with_context(load_all_views=True).get_view(view_id=view_id, view_type=view_type)
                if isinstance(data, dict) and data.get('arch'):
                    explicit_data = {
                        'arch': data.get('arch'),
                        'fields': data.get('fields', {}),
                        'toolbar': data.get('toolbar', {}),
                        '_contract_view_id': view_id,
                        '_contract_view_source': 'action_specific',
                    }
                    try:
                        fv = Model.fields_view_get(view_id=view_id, view_type=view_type, toolbar=True)
                        fv_arch = fv.get('arch') if isinstance(fv, dict) else ''
                        explicit_arch = explicit_data.get('arch') or ''
                        if fv_arch and len(str(fv_arch)) >= len(str(explicit_arch)):
                            explicit_data = {
                                'arch': fv_arch,
                                'fields': fv.get('fields', {}),
                                'toolbar': fv.get('toolbar', {}),
                                '_contract_view_id': view_id,
                                '_contract_view_source': 'action_specific_fields_view_get',
                            }
                    except Exception as e:
                        _logger.warning("action-specific fields_view_get 失败: %s", e)
                    return explicit_data
        except Exception as e:
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
                    '_contract_view_source': 'default',
                }
        except Exception as e:
            _logger.warning("get_view 失败: %s", e)

        # c) 回退 fields_view_get（低版本 Odoo 有；若没有则捕获异常返回 None）
        try:
            fv = Model.fields_view_get(view_type=view_type, toolbar=True)
            return {
                'arch': fv.get('arch'),
                'fields': fv.get('fields', {}),
                'toolbar': fv.get('toolbar', {}),
                '_contract_view_source': 'fields_view_get',
            }
        except Exception as e:
            _logger.warning("fields_view_get 失败: %s", e)
            return None

    # ====================== 内部：降级解析（无 parser 也可用） ======================

    def _fallback_extract_header_buttons(self, root):
        btns = []
        if root is None:
            return btns
        header = root.find('.//header')
        if header is None:
            return btns
        for button in header.findall('.//button'):
            item = {
                'name': button.get('name'),
                'string': button.get('string') or button.get('title') or '',
                'type': button.get('type') or 'object',
                'class': button.get('class') or '',
                'confirm': button.get('confirm') or '',
                'context': button.get('context') or '',
                'groups_xmlids': (button.get('groups') or '').split(',') if button.get('groups') else [],
            }
            if button.get('states'):
                item['states'] = [s.strip() for s in button.get('states').split(',') if s.strip()]
            btns.append(item)
        return btns

    def _fallback_extract_button_box(self, root):
        stats = []
        if root is None:
            return stats
        for div in root.findall('.//div'):
            klass = div.get('class') or ''
            if 'oe_button_box' not in klass:
                continue
            for button in div.findall('.//button'):
                if 'oe_stat_button' not in (button.get('class') or ''):
                    continue
                stats.append({
                    'string': button.get('string') or '',
                    'icon': button.get('icon') or '',
                    'type': button.get('type') or 'object',
                    'name': button.get('name'),
                    'help': button.get('help') or '',
                    'groups_xmlids': (button.get('groups') or '').split(',') if button.get('groups') else [],
                })
        return stats

    def _fallback_extract_form_layout(self, root):
        def field_node(field):
            return {'type': 'field', 'name': field.get('name')}

        def group_node(group):
            children = []
            for node in list(group or []):
                if getattr(node, 'tag', None) == 'field' and node.get('name'):
                    children.append(field_node(node))
            return {'type': 'group', 'children': children, 'label': group.get('string') if group is not None else None}

        def page_node(page):
            groups = [group_node(group) for group in (page.findall('.//group') if page is not None else [])]
            return {'type': 'page', 'string': page.get('string') if page is not None else '', 'children': groups}

        def sheet_node(sheet):
            if sheet is None:
                return {'type': 'sheet', 'children': []}
            notebook = sheet.find('.//notebook')
            if notebook is not None:
                pages = [page_node(page) for page in notebook.findall('./page')]
                return {'type': 'sheet', 'children': [{'type': 'notebook', 'children': pages}]}
            groups = [group_node(group) for group in sheet.findall('.//group')]
            if groups:
                return {'type': 'sheet', 'children': groups}
            field = sheet.find('.//field[@name]') if sheet is not None else None
            return {'type': 'sheet', 'children': [{'type': 'group', 'children': [field_node(field)]}] if field is not None else []}

        form = root if (root is not None and root.tag == 'form') else (root.find('.//form') if root is not None else None)
        if form is None:
            return [{'type': 'sheet', 'children': []}]
        sheet = None
        for child in form:
            if getattr(child, 'tag', None) == 'sheet':
                sheet = child
                break
        if sheet is None:
            sheet = form
        return [sheet_node(sheet)]

    def _fallback_collect_field_modifiers(self, fields_meta):
        out = {}
        for fname, meta in (fields_meta or {}).items():
            mods = meta.get('modifiers') or {}
            row = {}
            for key in ('readonly', 'required', 'invisible', 'column_invisible'):
                if key in mods:
                    row[key] = mods[key]
            for key in ('widget', 'domain', 'context', 'groups'):
                if key in meta:
                    row[key] = meta[key]
            if row:
                out[fname] = row
        return out

    def _fallback_detect_chatter_and_attachments(self, root):
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

    def _fallback_relation_fields(self, relation_fields_cache, relation_model):
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

    def _fallback_infer_tree_columns(self, meta, relation_meta):
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

    def _fallback_infer_x2many_subviews(self, fields_meta, relation_fields_cache):
        sub = {}
        for fname, meta in (fields_meta or {}).items():
            ttype = meta.get('type')
            if ttype not in ('one2many', 'many2many'):
                continue
            relation = str(meta.get('relation') or '').strip()
            rel_fields = self._fallback_relation_fields(relation_fields_cache, relation)
            sub[fname] = {
                'tree': {'columns': self._fallback_infer_tree_columns(meta, rel_fields)},
                'fields': rel_fields,
                'policies': {'inline_edit': True, 'can_create': True, 'can_unlink': True},
            }
        return sub

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
            if arch:
                try:
                    root = ET.fromstring(arch)
                    for field in root.findall('.//field[@name]'):
                        fname = field.get('name')
                        is_invisible = field.get('column_invisible')
                        if fname and is_invisible not in ('True', '1'):
                            view_fields.append(fname)
                    _logger.info("从原始视图提取到字段: %s", view_fields)
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

            order_default = getattr(self.env[model_name], '_order', 'id desc') or 'id desc'
            base.update({
                'order': order_default,
                'columns': view_fields,
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

        # 开始解析 FORM
        if arch:
            try:
                root = ET.fromstring(arch)
            except Exception as e:
                _logger.warning("FORM fallback: XML 解析失败，将使用极简布局: %s", e)
                root = None
        else:
            root = None

        relation_fields_cache = {}

        layout = self._fallback_extract_form_layout(root) if root is not None else [{
            'type': 'sheet',
            'children': [{'type': 'group', 'children': [{'type': 'field', 'name': 'name'}]}],
        }]
        header_buttons = self._fallback_extract_header_buttons(root)
        stat_buttons = self._fallback_extract_button_box(root)
        fm = self._fallback_collect_field_modifiers((view_data or {}).get('fields') or {})
        ca = self._fallback_detect_chatter_and_attachments(root)
        subviews = self._fallback_infer_x2many_subviews((view_data or {}).get('fields') or {}, relation_fields_cache)

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
        """Compatibility adapter for view-level runtime filtering."""
        return ContractGovernanceFilterService(self).apply_view_runtime_filter(
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

        # 4) 运行态裁剪
        final = self._runtime_filter(base, self.model, check_model_acl=check_model_acl)
        return final

    # ====================== 小工具 ======================

    def _model_exists(self, name):
        try:
            self.env[name]
            return True
        except Exception:
            return False
