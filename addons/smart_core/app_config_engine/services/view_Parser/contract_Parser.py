# -*- coding: utf-8 -*-
"""
services/view_parser/contract_parser.py

Odoo 模型入口：app.view.parser
将各解析 Mixin 汇总，输出契约 2.0 结构。
"""
from odoo import models, api
import logging

from .base import _BaseViewParserMixin
# 由于文件名包含空格和特殊字符，我们需要使用getattr来导入
import sys
import os

# 动态导入包含空格和特殊字符的模块
parsers_tree_form = __import__('odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Tree Form', fromlist=['_TreeFormParserMixin'])
_TreeFormParserMixin = getattr(parsers_tree_form, '_TreeFormParserMixin')

parsers_kanban_pivot_graph = __import__('odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Kanban Pivot Graph', fromlist=['_KanbanPivotGraphParserMixin'])
_KanbanPivotGraphParserMixin = getattr(parsers_kanban_pivot_graph, '_KanbanPivotGraphParserMixin')

parsers_calendar_gantt_activity = __import__('odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers_Calendar_Gantt Activity', fromlist=['_CalendarGanttActivitySearchParserMixin'])
_CalendarGanttActivitySearchParserMixin = getattr(parsers_calendar_gantt_activity, '_CalendarGanttActivitySearchParserMixin')

_logger = logging.getLogger(__name__)


class OdooViewParser(_BaseViewParserMixin,
                     _TreeFormParserMixin,
                     _KanbanPivotGraphParserMixin,
                     _CalendarGanttActivitySearchParserMixin,
                     models.AbstractModel):
    """对外唯一模型入口。"""
    _name = 'app.view.parser'
    _description = 'Lossless Odoo View Parser (Contract 2.0)'

    # ---------------- 公共入口 ----------------
    @api.model
    def parse_odoo_view(self, model_name, view_type):
        """
        保真解析 Odoo 原生视图，返回完整结构（单视图或多视图）
        返回：
          - 单视图：dict（标准化视图块）
          - 多视图：{ view_type: dict, ... }
        """
        view_types = self._normalize_view_types(view_type)

        if len(view_types) > 1:
            out = {}
            for vt in view_types:
                out[vt] = self._get_and_parse_view(model_name, vt)
            return out
        else:
            return self._get_and_parse_view(model_name, view_types[0])

    # ---------------- 主流程 ----------------
    def _get_and_parse_view(self, model_name, view_type):
        """
        获取最终视图（已合并继承）并解析为标准化结构
        - 首选 model.get_view(view_type=...)
        - 兼容回退 fields_view_get(view_type=..., toolbar=True)
        """
        model = self.env[model_name].sudo()
        odoo_view = self._safe_get_view_data(model, view_type)
        arch = (odoo_view or {}).get('arch') or ''
        fields_info = (odoo_view or {}).get('fields') or {}
        toolbar_raw = (odoo_view or {}).get('toolbar') or {}

        _logger.info("VIEW_PARSER_DEBUG: model=%s view_type=%s arch_length=%s fields_count=%s",
                     model_name, view_type, len(arch) if arch else 0, len(fields_info))
        if arch:
            _logger.info("VIEW_PARSER_DEBUG: arch_preview=%s", arch[:200])

        parsed_structure = self._lossless_parse_xml(arch)

        # search 合并（主视图内嵌） + 独立 search 视图
        try:
            search_view = self._safe_get_view_data(model, 'search')
        except Exception:
            search_view = None

        base = {
            "modifiers": self._collect_modifiers(arch),
            "search": self._merge_search(
                self._parse_search_from_arch(arch),
                self._parse_search_from_arch((search_view or {}).get('arch') or '')
            ),
            "toolbar": self._normalize_toolbar(toolbar_raw),
            "order": getattr(model, '_order', 'id desc') or 'id desc',
        }

        vt = view_type
        if vt == 'tree':
            tree_blk = self._parse_tree_view(arch, fields_info)
            # tree 的 default_order 覆盖全局 order
            if tree_blk.get('default_order'):
                base["order"] = tree_blk['default_order']
            base.update(tree_blk)
        elif vt == 'form':
            form_blk = self._parse_form_view(arch, fields_info, model_name)
            _logger.info("VIEW_PARSER_DEBUG: form_blk keys=%s", list(form_blk.keys()))
            _logger.info("VIEW_PARSER_DEBUG: form_blk layout=%s", form_blk.get('layout'))
            if form_blk.get('layout'):
                _logger.info("VIEW_PARSER_DEBUG: form_blk layout type=%s length=%s", type(form_blk['layout']), len(form_blk['layout']))
                if len(form_blk['layout']) > 0:
                    _logger.info("VIEW_PARSER_DEBUG: form_blk first layout item=%s", form_blk['layout'][0])
            base.update(form_blk)
        elif vt == 'kanban':
            base.update({"kanban": self._parse_kanban_view(arch, fields_info)})
        elif vt == 'pivot':
            base.update({"pivot": self._parse_pivot_view(arch, fields_info)})
        elif vt == 'graph':
            base.update({"graph": self._parse_graph_view(arch, fields_info)})
        elif vt == 'calendar':
            base.update({"calendar": self._parse_calendar_view(arch)})
        elif vt == 'gantt':
            base.update({"gantt": self._parse_gantt_view(arch)})
        elif vt == 'activity':
            base.update({"activity": self._parse_activity_view(arch)})
        elif vt == 'search':
            pass
        else:
            _logger.warning("Unknown view_type %s for %s; return minimal block.", vt, model_name)

        _logger.info("VIEW_PARSER_DEBUG: final result keys=%s", list(base.keys()))
        return {
            "id": f"{model_name}_{view_type}",
            "model": model_name,
            "view_type": view_type,
            "original_odoo_view": self._serialize_odoo_view(odoo_view),
            "parsed_structure": parsed_structure,
            **base,
        }