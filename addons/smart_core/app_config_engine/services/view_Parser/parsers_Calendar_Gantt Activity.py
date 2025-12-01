# -*- coding: utf-8 -*-
"""
services/view_parser/parsers_calendar_gantt_activity.py

calendar / gantt / activity / search 解析与合并
"""
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class _CalendarGanttActivitySearchParserMixin:
    # ---------------- calendar 解析 ----------------
    def _parse_calendar_view(self, arch):
        out = {
            "date_start": "date_start",
            "date_stop": "date_end",
            "color": "user_id",
            "event_open_popup": None,
            "default_scale": None,
        }
        try:
            if arch:
                root = etree.fromstring(arch.encode('utf-8'))
                if root.tag != 'calendar':
                    cals = root.xpath('.//calendar')
                    root = cals[0] if cals else root

                for k in ('date_start', 'date_stop', 'color'):
                    if root.get(k):
                        out[k] = root.get(k)

                eop = root.get('event_open_popup')
                if isinstance(eop, str):
                    out["event_open_popup"] = eop.strip().lower() in ('1', 'true', 'yes', 'y', 'on')

                if root.get('default_scale'):
                    out["default_scale"] = root.get('default_scale')

                for extra in ('quick_add', 'mode', 'create'):
                    if root.get(extra) is not None:
                        out[extra] = root.get(extra)
        except Exception:
            _logger.exception("parse calendar view failed")
        return out

    # ---------------- gantt 解析 ----------------
    def _parse_gantt_view(self, arch):
        out = {
            "date_start": "date_start",
            "date_stop": "date_end",
            "progress": "progress",
            "default_scale": None,
            "event_open_popup": None,
            "decorations": []
        }
        try:
            if arch:
                root = etree.fromstring(arch.encode('utf-8'))
                if root.tag != 'gantt':
                    g = root.xpath('.//gantt')
                    root = g[0] if g else root

                for k in ('date_start', 'date_stop', 'progress'):
                    if root.get(k):
                        out[k] = root.get(k)

                if root.get('default_scale'):
                    out["default_scale"] = root.get('default_scale')

                eop = root.get('event_open_popup')
                if isinstance(eop, str):
                    out["event_open_popup"] = eop.strip().lower() in ('1', 'true', 'yes', 'y', 'on')

                for k, v in (root.attrib or {}).items():
                    if k.startswith('decoration-') and v:
                        out["decorations"].append({
                            "class": k.replace('decoration-', ''),
                            "expr_raw": v,
                            "expr": self._safe_eval_expr(v)
                        })

                if root.get('consolidate'):
                    out['consolidate'] = root.get('consolidate')
        except Exception:
            _logger.exception("parse gantt view failed")
        return out

    # ---------------- activity 解析（最小可用） ----------------
    def _parse_activity_view(self, arch):
        out = {"template_qweb": None}
        try:
            if arch:
                root = etree.fromstring(arch.encode('utf-8'))
                if root.tag != 'activity':
                    ac = root.xpath('.//activity')
                    root = ac[0] if ac else root
                tmpl = root.xpath('.//templates')
                out["template_qweb"] = tmpl and etree.tostring(tmpl[0], encoding='unicode') or None
        except Exception:
            _logger.exception("parse activity view failed")
        return out

    # ---------------- search 解析与合并 ----------------
    def _parse_search_from_arch(self, arch):
        out = {"filters": [], "group_by": [], "facets": {"enabled": True}}
        try:
            if not arch:
                return out
            root = etree.fromstring(arch.encode('utf-8'))
            search_nodes = root.xpath('.//search') if root.tag != 'search' else [root]
            if not search_nodes:
                return out

            gb_set = []  # 使用列表以“遇到即记录 + 去重”的方式保持稳定顺序
            seen_gb = set()
            filters = []
            for s in search_nodes:
                for f in s.xpath('.//filter'):
                    name = f.get('name') or ''
                    label = f.get('string') or name
                    domain_raw = f.get('domain')
                    context_raw = f.get('context')
                    domain_val = self._safe_eval_expr(domain_raw)
                    context_val = self._safe_eval_expr(context_raw)

                    filters.append({
                        "name": name or label,
                        "label": label,
                        "domain": domain_val if isinstance(domain_val, (list, tuple)) else [],
                        "domain_raw": domain_raw,
                        "context_raw": context_raw
                    })

                    gb = None
                    if isinstance(context_val, dict):
                        gb = context_val.get('group_by')
                    if gb:
                        if isinstance(gb, str):
                            if gb not in seen_gb:
                                gb_set.append(gb); seen_gb.add(gb)
                        elif isinstance(gb, (list, tuple)):
                            for g in gb:
                                if isinstance(g, str) and g not in seen_gb:
                                    gb_set.append(g); seen_gb.add(g)

            out["filters"] = filters
            out["group_by"] = gb_set
            return out
        except Exception:
            _logger.exception("parse search view failed")
            return out

    def _merge_search(self, primary, secondary):
        """
        合并两个 search 结构：
        - filters：按 (name,label,domain_raw,context_raw) 去重保序
        - group_by：遇到即并入，去重保序
        - facets.enabled：任一为 True 则 True
        """
        primary = primary or {"filters": [], "group_by": [], "facets": {"enabled": True}}
        secondary = secondary or {"filters": [], "group_by": [], "facets": {"enabled": True}}

        def _key(f):
            return (
                (f.get('name') or ''),
                (f.get('label') or ''),
                (f.get('domain_raw') or ''),
                (f.get('context_raw') or ''),
            )

        seen = set()
        merged_filters = []
        for f in (primary.get('filters', []) + secondary.get('filters', [])):
            k = _key(f)
            if k in seen:
                continue
            seen.add(k)
            merged_filters.append(f)

        gb_seen = set()
        merged_gb = []
        for g in (primary.get('group_by', []) + secondary.get('group_by', [])):
            if g not in gb_seen:
                gb_seen.add(g)
                merged_gb.append(g)

        facets_enabled = bool((primary.get('facets') or {}).get('enabled') or (secondary.get('facets') or {}).get('enabled'))

        return {"filters": merged_filters, "group_by": merged_gb, "facets": {"enabled": facets_enabled}}
