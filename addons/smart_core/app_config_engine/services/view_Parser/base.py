# -*- coding: utf-8 -*-
"""
services/view_parser/base.py

通用工具 & XML 保真解析 & toolbar/modifiers 等
供 contract_parser.OdooViewParser 通过 MRO 继承使用。

注意：本文件仅提供普通 Python Mixin，不继承 Odoo 模型。
"""
from odoo import models, api, _
from odoo.tools.safe_eval import safe_eval
from lxml import etree
import logging
import json

_logger = logging.getLogger(__name__)


class _BaseViewParserMixin:
    """基础工具：视图读取、XML 保真、序列化、modifiers/toolbar 归一、工具函数"""

    # ---------------- 视图数据获取 ----------------
    def _safe_get_view_data(self, model, view_type):
        """
        兼容不同 Odoo 版本：
        - 新：model.get_view(view_type=view_type)
        - 旧：model.fields_view_get(view_type=view_type, toolbar=True)
        返回：{"arch":str,"fields":dict,"toolbar":dict}
        """
        try:
            data = model.get_view(view_type=view_type)
            if isinstance(data, dict) and data.get('arch'):
                return {
                    "arch": data.get('arch'),
                    "fields": data.get('fields', {}),
                    "toolbar": data.get('toolbar', {}),
                }
        except Exception:
            pass

        try:
            fv = model.fields_view_get(view_type=view_type, toolbar=True)
            return {"arch": fv.get('arch'), "fields": fv.get('fields', {}), "toolbar": fv.get('toolbar', {})}
        except Exception as e:
            _logger.error("fields_view_get failed: %s", e)
            return {"arch": "", "fields": {}, "toolbar": {}}

    # ---------------- XML 保真解析 ----------------
    def _lossless_parse_xml(self, xml_content):
        """
        保真 XML -> dict：保存 tag/attributes/text/tail/children/raw_xml
        失败时返回包含错误信息的结构，不抛异常
        """
        try:
            if not xml_content or (isinstance(xml_content, str) and not xml_content.strip()):
                return {}
            root = etree.fromstring(xml_content.encode('utf-8')) if isinstance(xml_content, str) else xml_content
            return self._xml_to_dict(root, preserve_all=True)
        except Exception as e:
            _logger.error("XML parsing failed: %s", e)
            return {'error': str(e), 'raw_content': (xml_content or '')[:200]}

    def _xml_to_dict(self, node, preserve_all=False):
        if node is None:
            return None
        tag_name = str(node.tag) if not callable(node.tag) else 'comment'
        result = {'tag': tag_name}
        if node.attrib:
            result['attributes'] = dict(node.attrib)
        if node.text and node.text.strip():
            result['text'] = node.text.strip()
        if node.tail and node.tail.strip():
            result['tail'] = node.tail.strip()
        children = []
        for child in node:
            cdict = self._xml_to_dict(child, preserve_all=preserve_all)
            if cdict:
                children.append(cdict)
        if children:
            result['children'] = children
        if preserve_all:
            try:
                result['raw_xml'] = etree.tostring(node, encoding='unicode')
            except Exception:
                result['raw_xml'] = ''
        return result

    # ---------------- 安全求值/序列化 ----------------
    def _safe_eval_expr(self, expr):
        """
        安全求值：把字符串 expr 尝试解析为 Python 对象
        - 失败返回 None，不抛异常
        - 不注入危险变量，仅使用空上下文
        """
        if not expr or not isinstance(expr, str):
            return None
        try:
            return safe_eval(expr, {})
        except Exception:
            return None

    def _serialize_odoo_view(self, odoo_view):
        """将 get_view/fields_view_get 的结果转为可 JSON 序列化结构"""
        out = {}
        for k, v in (odoo_view or {}).items():
            try:
                json.dumps(v)
                out[k] = v
            except Exception:
                out[k] = str(v)
        return out

    # ---------------- modifiers 收集 ----------------
    def _collect_modifiers(self, arch):
        """
        收集字段级 modifiers（为服务层后续与权限/ir.rule 合并做准备）
        - 支持 attrs/invisible/readonly/required 三类
        - 返回：
          {"field_name": {"readonly":[{"raw":"...", "parsed":[...]}], "required":[...], "invisible":[...]}}
        """
        res = {}
        try:
            if not arch:
                return {}
            root = etree.fromstring(arch.encode('utf-8'))
            for fld in root.xpath('.//field[@name]'):
                name = fld.get('name')
                if not name:
                    continue
                item = res.setdefault(name, {"readonly": [], "required": [], "invisible": []})

                # attrs
                attrs_raw = fld.get('attrs')
                attrs_parsed = self._safe_eval_expr(attrs_raw) if attrs_raw else None
                if isinstance(attrs_parsed, dict):
                    for key in ('readonly', 'required', 'invisible'):
                        if key in attrs_parsed:
                            item[key].append({"raw": attrs_raw, "parsed": attrs_parsed.get(key)})

                # 顶层布尔/表达式属性
                for key in ('readonly', 'required', 'invisible'):
                    val_raw = fld.get(key)
                    if val_raw:
                        item[key].append({"raw": val_raw, "parsed": self._safe_eval_expr(val_raw)})
        except Exception:
            _logger.exception("collect modifiers failed")
        return res

    # ---------------- toolbar 归一 ----------------
    def _normalize_toolbar(self, toolbar_raw):
        """
        Odoo 会返回 toolbar: {'print': [...], 'action':[...], 'relate':[...]}
        这里归一化为：{"header":[...],"sidebar":[...],"footer":[...]}
        """
        tb = {"header": [], "sidebar": [], "footer": []}
        raw = toolbar_raw or {}

        def _coerce(items, level='header'):
            out = []
            for it in (items or []):
                entry = {
                    "key": it.get('xml_id') or (it.get('id') and f"id:{it['id']}") or (it.get('name') or ''),
                    "label": it.get('name') or it.get('string') or it.get('help') or '',
                    "kind": "open",
                    "level": level,
                    "intent": "open",
                    "payload": {
                        "action_id": it.get('id'),
                        "xml_id": it.get('xml_id'),
                        "context_raw": it.get('context'),
                        "domain_raw": it.get('domain'),
                        "groups_xmlids": [g.strip() for g in (it.get('groups') or '').split(',') if g.strip()]
                    }
                }
                out.append(entry)
            return out

        tb["header"]  = _coerce(raw.get('action'), 'header') + _coerce(raw.get('print'), 'header')
        tb["sidebar"] = _coerce(raw.get('relate'), 'sidebar')
        tb["footer"]  = []
        return tb

    # ---------------- 视图类型归一 ----------------
    def _normalize_view_types(self, view_type):
        if isinstance(view_type, str):
            return [vt.strip() for vt in view_type.split(',') if vt.strip()]
        if isinstance(view_type, (list, tuple)):
            return [str(v).strip() for v in view_type if str(v).strip()]
        raise ValueError("Invalid view_type: %r" % (view_type,))

    # ---------------- 字段元信息（form 布局用） ----------------
    def _widget_for_field(self, meta):
        ftype = (meta or {}).get('type', 'char')
        mapping = {
            'many2one': 'many2one', 'many2many': 'many2many_tags', 'one2many': 'one2many_list',
            'binary': 'image', 'html': 'html', 'text': 'textarea', 'date': 'date',
            'datetime': 'datetime', 'boolean': 'boolean', 'integer': 'integer',
            'float': 'float', 'monetary': 'monetary'
        }
        return mapping.get(ftype, ftype)

    def _field_info_for_layout(self, field_name, fields_info):
        meta = (fields_info or {}).get(field_name, {}) or {}
        return {
            'name': field_name,
            'label': meta.get('string', field_name),
            'type': meta.get('type', 'char'),
            'required': bool(meta.get('required', False)),
            'readonly': bool(meta.get('readonly', False)),
            'invisible': bool(meta.get('invisible', False)),
            'help': str(meta.get('help', '') or ''),
            'widget': self._widget_for_field(meta),
            'domain': meta.get('domain', []),
            'context': meta.get('context', {}),
            'selection': meta.get('selection', []),
            'colspan': int(meta.get('col', 1)) if str(meta.get('col', '')).isdigit() else 1,
        }
