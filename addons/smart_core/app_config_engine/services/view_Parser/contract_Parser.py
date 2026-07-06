# -*- coding: utf-8 -*-
"""
services/view_parser/contract_parser.py

Odoo 模型入口：app.view.parser
将各解析 Mixin 汇总，输出契约 2.0 结构。
"""
from odoo import models, api
import logging

from .base import _BaseViewParserMixin
from importlib import import_module
from lxml import etree

_logger = logging.getLogger(__name__)

LEGACY_MIXIN_MODULES = {
    "_TreeFormParserMixin": "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Tree Form",
    "_KanbanPivotGraphParserMixin": "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Kanban Pivot Graph",
    "_CalendarGanttActivitySearchParserMixin": (
        "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers_Calendar_Gantt Activity"
    ),
}


def _load_legacy_mixin(class_name):
    """Load parser mixins kept under legacy filenames with spaces."""
    module = import_module(LEGACY_MIXIN_MODULES[class_name])
    return getattr(module, class_name)


_TreeFormParserMixin = _load_legacy_mixin("_TreeFormParserMixin")
_KanbanPivotGraphParserMixin = _load_legacy_mixin("_KanbanPivotGraphParserMixin")
_CalendarGanttActivitySearchParserMixin = _load_legacy_mixin("_CalendarGanttActivitySearchParserMixin")


class OdooViewParser(_BaseViewParserMixin,
                     _TreeFormParserMixin,
                     _KanbanPivotGraphParserMixin,
                     _CalendarGanttActivitySearchParserMixin,
                     models.AbstractModel):
    """对外唯一模型入口。"""
    _name = 'app.view.parser'
    _description = 'Lossless Odoo View Parser (Contract 2.0)'
    SOURCE_KIND = "odoo_view_contract_parser_projection"
    SOURCE_AUTHORITIES = ("ir.ui.view", "ir.model.fields", "odoo.get_view")
    NO_BUSINESS_FACT_AUTHORITY = True

    @api.model
    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "app.view.parser",
        }

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
        # Use the current user for view composition. Odoo's get_view applies
        # groups while resolving inherited XML, and the custom client must
        # receive the same structure as the native client for that user.
        model = self.env[model_name]
        odoo_view = self._safe_get_view_data(model, view_type)
        arch = (odoo_view or {}).get('arch') or ''
        fields_info = self._enrich_view_fields_info(model, arch, (odoo_view or {}).get('fields') or {})
        toolbar_raw = (odoo_view or {}).get('toolbar') or {}

        _logger.debug("VIEW_PARSER_DEBUG: model=%s view_type=%s arch_length=%s fields_count=%s",
                     model_name, view_type, len(arch) if arch else 0, len(fields_info))
        if arch:
            _logger.debug("VIEW_PARSER_DEBUG: arch_preview=%s", arch[:200])

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
            _logger.debug("VIEW_PARSER_DEBUG: form_blk keys=%s", list(form_blk.keys()))
            _logger.debug("VIEW_PARSER_DEBUG: form_blk layout=%s", form_blk.get('layout'))
            if form_blk.get('layout'):
                _logger.debug("VIEW_PARSER_DEBUG: form_blk layout type=%s length=%s", type(form_blk['layout']), len(form_blk['layout']))
                if len(form_blk['layout']) > 0:
                    _logger.debug("VIEW_PARSER_DEBUG: form_blk first layout item=%s", form_blk['layout'][0])
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

        _logger.debug("VIEW_PARSER_DEBUG: final result keys=%s", list(base.keys()))
        return {
            "id": f"{model_name}_{view_type}",
            "model": model_name,
            "view_type": view_type,
            "original_odoo_view": self._serialize_odoo_view(odoo_view),
            "parsed_structure": parsed_structure,
            **base,
        }

    def _enrich_view_fields_info(self, model, arch, fields_info):
        """
        Odoo get_view can omit fields that only appear inside inline x2many
        subviews. Those fields still define native form structure, so the
        parser must use fields_get as the model-level source of truth.
        """
        out = {name: dict(meta) if isinstance(meta, dict) else meta for name, meta in (fields_info or {}).items()}
        missing = []
        if arch:
            try:
                root = etree.fromstring(arch.encode('utf-8'))
                for el in root.xpath(".//field[@name]"):
                    fname = (el.get("name") or "").strip()
                    field_string = (el.get("string") or "").strip()
                    if fname and field_string and isinstance(out.get(fname), dict):
                        out[fname]["string"] = field_string
                        out[fname]["label"] = field_string
                    if fname and fname not in out and fname not in missing:
                        missing.append(fname)
            except Exception:
                _logger.exception("VIEW_PARSER_DEBUG: enrich fields_info parse failed")
        if not missing:
            return out
        try:
            model_fields = model.fields_get(missing)
        except Exception:
            _logger.exception("VIEW_PARSER_DEBUG: fields_get enrich failed for %s", missing)
            model_fields = {}
        for fname in missing:
            meta = (model_fields or {}).get(fname)
            if isinstance(meta, dict):
                out[fname] = meta
        _logger.debug(
            "VIEW_PARSER_DEBUG: enriched fields_info with arch fields=%s",
            [name for name in missing if name in out],
        )
        return out
