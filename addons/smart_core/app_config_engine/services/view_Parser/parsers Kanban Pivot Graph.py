# -*- coding: utf-8 -*-
"""
services/view_parser/parsers_kanban_pivot_graph.py

kanban / pivot / graph 解析
"""
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class _KanbanPivotGraphParserMixin:
    # ---------------- kanban 解析 ----------------
    def _parse_kanban_view(self, arch, fields_info):
        out = {
            "template_qweb": None,
            "quick_create": True,
            "stages_field": "stage_id",
            "default_group_by": None,
            "class_list": [],
            "decorations": [],
        }
        try:
            if not arch:
                return out
            root = etree.fromstring(arch.encode('utf-8'))
            if root.tag != 'kanban':
                kn = root.xpath('.//kanban')
                if kn:
                    root = kn[0]

            out["default_group_by"] = root.get('default_group_by') or None
            if out["default_group_by"]:
                out["stages_field"] = out["default_group_by"]

            qc = root.get('quick_create')
            if isinstance(qc, str):
                qc_l = qc.strip().lower()
                out["quick_create"] = qc_l not in ('0', 'false', 'no', 'off')

            cls = root.get('class') or ''
            if cls.strip():
                out["class_list"] = [c for c in cls.strip().split() if c]
            for k, v in (root.attrib or {}).items():
                if k.startswith('decoration-') and v:
                    out["decorations"].append({
                        "class": k.replace('decoration-', ''),
                        "expr_raw": v,
                        "expr": self._safe_eval_expr(v)
                    })

            tmpl = root.xpath('.//templates')
            out["template_qweb"] = tmpl and etree.tostring(tmpl[0], encoding='unicode') or None

            quick = []
            for btn in root.xpath('.//button'):
                entry = self._button_to_action(btn, level='header')
                if entry:
                    quick.append(entry)
            if quick:
                out["quick_actions"] = quick

        except Exception:
            _logger.exception("parse kanban view failed")
        return out

    # ---------------- pivot 解析 ----------------
    def _parse_pivot_view(self, arch, fields_info):
        measures, dimensions = [], []
        try:
            if arch:
                root = etree.fromstring(arch.encode('utf-8'))
                for fld in root.xpath('.//field[@name]'):
                    name = fld.get('name')
                    ftype = fld.get('type')
                    label = fld.get('string') or name
                    if ftype == 'measure':
                        measures.append({
                            "name": name,
                            "label": label,
                            "aggregate": fld.get('aggregate') or None
                        })
                    else:
                        dim_type = ftype if ftype in ('row', 'col') else None
                        dimensions.append({
                            "name": name,
                            "label": label,
                            "axis": dim_type,
                            "interval": fld.get('interval') or None
                        })
                for ms in root.xpath('.//measure[@name]'):
                    measures.append({
                        "name": ms.get('name'),
                        "label": ms.get('string') or ms.get('name'),
                        "aggregate": ms.get('aggregate') or None
                    })
        except Exception:
            _logger.exception("parse pivot view failed")
        return {"measures": measures, "dimensions": dimensions, "defaults": {}}

    # ---------------- graph 解析 ----------------
    def _parse_graph_view(self, arch, fields_info):
        measures, dimensions = [], []
        type_default = "bar"
        try:
            if arch:
                root = etree.fromstring(arch.encode('utf-8'))
                type_default = root.get('type') or type_default
                for fld in root.xpath('.//field[@name]'):
                    name = fld.get('name')
                    ftype = fld.get('type')
                    label = fld.get('string') or name
                    if (ftype == 'measure'):
                        measures.append({
                            "name": name,
                            "label": label,
                            "aggregate": fld.get('aggregate') or None,
                            "format": fld.get('format') or None
                        })
                    elif ftype in (None, 'row', 'x'):
                        dimensions.append({
                            "name": name,
                            "label": label,
                            "interval": fld.get('interval') or None
                        })
                for ms in root.xpath('.//measure[@name]'):
                    name = ms.get('name')
                    label = ms.get('string') or name
                    measures.append({
                        "name": name,
                        "label": label,
                        "aggregate": ms.get('aggregate') or None,
                        "format": ms.get('format') or None
                    })
        except Exception:
            _logger.exception("parse graph view failed")
        return {"type_default": type_default, "measures": measures, "dimensions": dimensions}
