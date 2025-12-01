# -*- coding: utf-8 -*-
"""
services/view_parser/parsers_tree_form.py

Tree / Form 解析、表单布局转换、按钮归一化（增强版，直接可用）
- tree：default_order / editable / create / delete / limit / 列级修饰 / 行装饰 / 行按钮 / columns_schema / search
- form：layout(notebook/page/group/field) / header_buttons / button_box(stat_buttons) / chatter / attachments /
        field_modifiers(arch + fields_info 合并) / x2many subviews（inline + 引用） / statusbar 智能识别 / search

依赖：
- _BaseViewParserMixin 中的：_safe_get_view_data, _lossless_parse_xml, _normalize_toolbar, _merge_search, _parse_search_from_arch,
  _serialize_odoo_view, _normalize_view_types 等通用能力
"""
from odoo import _
from lxml import etree
import logging
import ast
import json

_logger = logging.getLogger(__name__)


class _TreeFormParserMixin:
    # ---------------- tree 解析 ----------------
    def _parse_tree_view(self, arch, fields_info):
        columns, row_actions, row_classes = [], [], []
        page_size = 50
        modifiers = {}
        capabilities = {"inline_edit": False, "can_create": True, "can_delete": True}
        default_order = None

        try:
            root = etree.fromstring(arch.encode('utf-8')) if arch else None
            if root is not None and root.tag in ('tree', 'list'):
                # default_order / editable / create / delete / limit
                default_order = root.get('default_order')
                editable = (root.get('editable') or '').strip().lower()  # bottom/top/''/true
                capabilities["inline_edit"] = editable in ('bottom', 'top', '1', 'true')
                capabilities["can_create"] = (root.get('create', '1') not in ('0', 'false', 'False'))
                capabilities["can_delete"] = (root.get('delete', '1') not in ('0', 'false', 'False'))

                limit_attr = root.get('limit')
                if limit_attr:
                    try:
                        page_size = int(limit_attr)
                    except Exception:
                        page_size = 50

                # 1) 列与列级属性
                for el in root.xpath('./field[@name]'):
                    fname = el.get('name')
                    if not fname:
                        continue
                    if fname not in columns:
                        columns.append(fname)
                    mods = modifiers.setdefault(fname, {})
                    # optional: hide/show/column
                    opt = el.get('optional')
                    if opt:
                        mods['optional'] = opt
                    # 列上 attrs/invisible/readonly/required
                    for key in ('readonly', 'required', 'invisible', 'column_invisible'):
                        val = el.get(key)
                        if val:
                            mods[key] = self._safe_eval_expr(val) or val
                    # 列上的 widget / sum（页脚汇总）
                    if el.get('widget'):
                        mods['widget'] = el.get('widget')
                    if el.get('sum'):
                        mods['sum'] = el.get('sum')

                _logger.info("TREE_PARSER_DEBUG: parsed_columns=%s", columns)

                # 2) 行级按钮（tree 内所有 <button>）
                for btn in root.xpath('.//button'):
                    entry = self._button_to_action(btn, level='row')
                    if entry:
                        row_actions.append(entry)

                # 3) 行样式：decoration-xxx
                for k, v in root.attrib.items():
                    if k.startswith('decoration-') and v:
                        row_classes.append({
                            "expr_raw": v,
                            "expr": self._safe_eval_expr(v),
                            "class": k.replace('decoration-', '')
                        })

        except Exception:
            _logger.exception("parse tree view failed")

        if not row_actions:
            row_actions = [{
                "name": "open_form",
                "label": _("Open"),
                "kind": "open",
                "level": "row",
                "selection": "single",
                "intent": "open",
                "payload": {"ref": None, "view_mode": "form"},
            }]
        if not columns:
            # 没有列时，取 fields_info 前几列兜底
            columns = [k for k in (fields_info or {}).keys() if not k.startswith('__')][:6] or ['id']

        # 列模式（兼容 + 细节）
        columns_schema = [{
            "name": c,
            "widget": (modifiers.get(c, {}).get('widget') or (fields_info.get(c, {}) or {}).get('type', 'char')),
            **({k: v for k, v in (modifiers.get(c) or {}).items() if k != 'widget'})
        } for c in columns]

        _logger.info("TREE_PARSER_DEBUG: final_columns=%s fields_info_keys=%s", columns, list((fields_info or {}).keys())[:10])

        return {
            "columns": columns,
            "columns_schema": columns_schema,
            "row_actions": row_actions,
            "page_size": page_size,
            "row_classes": row_classes,
            "modifiers": modifiers,
            "capabilities": capabilities,
            "default_order": default_order,
            # 让服务层不需要再兜底 search
            "search": {"filters": [], "group_by": [], "facets": {"enabled": True}},
        }

    # ---------------- form 解析（增强） ----------------
    def _parse_form_view(self, arch, fields_info, model_name):
        """
        返回契约块：
        {
          layout, statusbar, header_buttons, button_box, stat_buttons, field_modifiers,
          subviews, chatter, attachments, search
        }
        """
        root = None
        if arch:
            try:
                root = etree.fromstring(arch.encode('utf-8'))
            except Exception:
                _logger.exception("FORM_PARSER_DEBUG: XML parse failed, fallback to minimal layout")

        # 1) DOM 优先解析真实布局（避免 lossless 未还原导致空表单）
        layout_dom = self._extract_form_layout_dom(root, fields_info) if root is not None else []
        _logger.info("FORM_PARSER_DEBUG: layout_dom=%s", layout_dom)

        # 2) lossless 结果作为兜底/补充
        layout_ll = self._convert_parsed_structure_to_layout(self._lossless_parse_xml(arch), fields_info)
        layout = self._merge_layout(layout_dom, layout_ll)
        _logger.info("FORM_PARSER_DEBUG: merged layout=%s", layout)

        # 3) statusbar 智能识别 + 状态集
        statusbar = self._build_statusbar(root, fields_info, model_name)
        _logger.info("FORM_PARSER_DEBUG: statusbar=%s", statusbar)

        # 4) header 按钮
        header_buttons = self._extract_header_buttons(root) if root is not None else []
        _logger.info("FORM_PARSER_DEBUG: header_buttons=%s", header_buttons)

        # 5) Smart Buttons（oe_button_box/oe_stat_button）
        stat_buttons = self._extract_button_box(root) if root is not None else []
        # 兼容：有些版本直接把 oe_stat_button 放 sheet/header 下
        if root is not None and not stat_buttons:
            for b in root.xpath(".//button[contains(concat(' ', normalize-space(@class), ' '), ' oe_stat_button ')]"):
                norm = self._button_to_action(b, level='smart')
                if norm:
                    stat_buttons.append(norm)
        button_box = list(stat_buttons)
        _logger.info("FORM_PARSER_DEBUG: button_box=%s", button_box)

        # 6) 字段修饰（字段级 + arch 覆盖）
        field_modifiers = self._collect_field_modifiers(fields_info, root)
        _logger.info("FORM_PARSER_DEBUG: field_modifiers keys=%s", list(field_modifiers.keys()))

        # 7) 子视图（inline + 引用式）
        subviews = self._collect_x2many_subviews_from_dom(root, fields_info)
        if not subviews:
            subviews = self._infer_x2many_subviews(fields_info)
        _logger.info("FORM_PARSER_DEBUG: subviews keys=%s", list(subviews.keys()))

        # 8) 协作能力（优先模型字段判定，其次 DOM 探测）
        chatter, attachments = self._detect_chatter_and_attachments_model_first(model_name, fields_info, root)
        _logger.info("FORM_PARSER_DEBUG: chatter=%s, attachments=%s", chatter, attachments)

        # 9) 最小 search（表单内置搜索占位）
        search = {"filters": [], "group_by": [], "facets": {"enabled": True}}

        result = {
            "layout": layout if isinstance(layout, list) else [layout],
            "statusbar": statusbar,
            "header_buttons": header_buttons,
            "button_box": button_box,
            "stat_buttons": stat_buttons,
            "field_modifiers": field_modifiers,
            "subviews": subviews,
            "chatter": chatter,
            "attachments": attachments,
            "search": search,
        }
        _logger.info("FORM_PARSER_DEBUG: final result keys=%s", list(result.keys()))
        return result

    # ---------------- 按钮归一 ----------------
    def _button_to_action(self, btn_node, level='header'):
        try:
            btype    = (btn_node.get('type') or 'object').strip().lower()
            name_raw = (btn_node.get('name') or '').strip()
            label    = (btn_node.get('string') or btn_node.get('title') or name_raw or 'Button').strip()
            classes  = [c.strip() for c in (btn_node.get('class') or '').split() if c.strip()]
            states   = [s.strip() for s in (btn_node.get('states') or '').split(',') if s and s.strip()]
            confirm  = btn_node.get('confirm') or btn_node.get('help') or ''
            icon     = btn_node.get('icon') or next((c for c in classes if c.startswith('fa-') or c.startswith('oi-')), '')
            options_raw = btn_node.get('options')
            domain_raw  = btn_node.get('domain')
            context_raw = btn_node.get('context')
            priority    = btn_node.get('priority')

            # 层级判定
            lvl = level
            p = btn_node.getparent()
            while p is not None:
                tag = getattr(p, 'tag', '')
                if tag == 'tree':
                    lvl = 'row'; break
                if tag in ('form', 'kanban'):
                    lvl = 'header'; break
                p = p.getparent()
            if 'oe_stat_button' in classes or 'oe_stat_info' in classes:
                lvl = 'smart'

            # 选择模式
            selection = 'multi' if lvl == 'row' else 'single'
            ctx_val = self._safe_eval_expr(context_raw)
            if isinstance(ctx_val, dict):
                sel = ctx_val.get('selection')
                if isinstance(sel, str) and sel in ('single', 'multi', 'none'):
                    selection = sel

            # groups 与可见性
            groups_attr   = btn_node.get('groups') or ''
            groups_xmlids = [g.strip() for g in groups_attr.split(',') if g.strip()]
            attrs_raw     = btn_node.get('attrs')
            attrs_parsed  = self._safe_eval_expr(attrs_raw) if attrs_raw else None

            visible_attrs = {
                "readonly": self._safe_eval_expr(btn_node.get('readonly')) if btn_node.get('readonly') else None,
                "required": self._safe_eval_expr(btn_node.get('required')) if btn_node.get('required') else None,
                "invisible": self._safe_eval_expr(btn_node.get('invisible')) if btn_node.get('invisible') else None,
            }
            if isinstance(attrs_parsed, dict):
                for k in ('readonly', 'required', 'invisible'):
                    if k in attrs_parsed:
                        visible_attrs[k] = attrs_parsed.get(k)

            try:
                priority_val = int(priority) if (priority is not None and str(priority).strip().lstrip('-').isdigit()) else None
            except Exception:
                priority_val = None

            base = {
                "name": name_raw or ('open_action' if btype == 'action' else ('open_url' if btype == 'url' else 'button')),
                "label": label or ('Action' if btype == 'action' else ('Open URL' if btype == 'url' else 'Button')),
                "kind": "object",
                "level": lvl,
                "selection": selection,
                "groups": [],
                "visible": {"domain": [], "states": states, "attrs": visible_attrs},
                "intent": "execute",
                "icon": icon,
                "payload": {
                    "method": None,
                    "ref": None,
                    "url": '',
                    "confirm": confirm,
                    "groups_xmlids": groups_xmlids,
                    "priority": priority_val,
                    "type": btype,
                    "domain_raw": domain_raw,
                    "context_raw": context_raw,
                    "options_raw": options_raw,
                }
            }

            def _finalize(base, btype):
                if base.get("selection") not in ("single", "multi", "none"):
                    base["selection"] = "multi" if base.get("level") == "row" else "single"
                if btype == 'object':
                    base["kind"] = "server"; base["intent"] = "execute"
                    if not base["payload"].get("method"):
                        base["payload"]["method"] = "object_method"
                    if not base.get("name"):
                        base["name"] = base["payload"]["method"]
                if btype == 'action':
                    base["kind"] = "open"; base["intent"] = "open"
                    if base.get("level") != "row":
                        base["selection"] = "none"
                if btype == 'url' or base["payload"].get("url"):
                    base["kind"] = "url"; base["intent"] = "url"; base["selection"] = "none"
                if not (base.get("label") or '').strip():
                    base["label"] = (base["payload"].get("method") or base["payload"].get("ref") or base["payload"].get("url") or "Button")
                return base

            if btype == 'object':
                final_method = name_raw or 'object_method'
                base["name"] = final_method
                base["kind"] = "object"
                base["intent"] = "execute"
                base["payload"]["method"] = final_method
                if not (base["label"] or '').strip():
                    base["label"] = final_method
                return _finalize(base, btype)

            if btype == 'action':
                ref = name_raw or 'open_action'
                base["name"] = ref
                base["kind"] = "open"
                base["intent"] = "open"
                base["selection"] = "single" if level == 'row' else "none"
                base["payload"]["ref"] = ref
                if not (base["label"] or '').strip():
                    base["label"] = "Action"
                return _finalize(base, btype)

            if btype == 'url' or btn_node.get('url'):
                url_val = (btn_node.get('url') or name_raw or '').strip()
                if not url_val:
                    return None
                base["name"] = name_raw or 'open_url'
                base["kind"] = "url"
                base["intent"] = "url"
                base["selection"] = "none"
                base["payload"]["url"] = url_val
                if btn_node.get('target'):
                    base["payload"]["target"] = btn_node.get('target')
                if not (base["label"] or '').strip():
                    base["label"] = "Open"
                return _finalize(base, btype)

            if btype == 'workflow':
                ref = name_raw or 'workflow_action'
                base["name"] = ref
                base["kind"] = "open"
                base["intent"] = "open"
                base["payload"]["ref"] = ref
                if not (base["label"] or '').strip():
                    base["label"] = "Workflow"
                return _finalize(base, btype)

            # 样式提示（不改变语义）
            if 'oe_highlight' in classes:
                base["payload"]["level"] = "primary"
            if 'btn-danger' in classes:
                base["payload"]["level"] = "danger"
            if 'oe_link' in classes:
                base["payload"]["appearance"] = "link"

            if not base["name"]:
                base["name"] = 'button'
            if base["payload"]["method"] is None:
                base["payload"]["method"] = base["name"]

            return _finalize(base, btype)

        except Exception:
            _logger.exception("button to action failed")
            return None

    # ---------------- 表单布局（DOM 直读） ----------------
    def _extract_form_layout_dom(self, root, fields_info):
        if root is None:
            return []
        # 锚定 <form>
        form = root if root.tag == 'form' else (root.xpath('.//form') or [None])[0]
        if form is None:
            # 如果没有找到form节点，尝试直接使用root节点
            form = root if root.tag != 'form' else None
            if form is None:
                return []
        
        out = []
        for ch in form:
            node = self._node_to_layout_from_dom(ch, fields_info)
            if node:
                out.append(node)
        
        # 如果没有任何可识别子节点，给一个最小 sheet
        if not out:
            out = [{"type": "sheet", "children": []}]
        else:
            # 确保所有节点都有完整的结构
            for node in out:
                self._ensure_complete_layout_structure(node)
        
        _logger.info("FORM_PARSER_DEBUG: _extract_form_layout_dom result=%s", out)
        return out

    def _ensure_complete_layout_structure(self, node):
        """确保布局节点具有完整的结构，特别是 children 属性"""
        if not isinstance(node, dict):
            return
            
        # 确保节点有 children 属性
        if 'children' not in node:
            # 对于某些特殊节点类型，可能不需要children属性
            if node.get('type') in ('field', 'button'):
                # field和button节点通常不需要children属性
                pass
            elif node.get('type') == 'notebook':
                # notebook节点可能使用tabs而不是children
                if 'tabs' not in node:
                    node['tabs'] = []
            else:
                node['children'] = []
                
        # 递归处理子节点
        if 'children' in node and isinstance(node['children'], list):
            for child in node['children']:
                self._ensure_complete_layout_structure(child)
                
        # 特殊处理 notebook 节点
        if node.get('type') == 'notebook' and 'tabs' in node and isinstance(node['tabs'], list):
            for tab in node['tabs']:
                self._ensure_complete_layout_structure(tab)

    def _node_to_layout_from_dom(self, el, fields_info):
        tag = getattr(el, 'tag', '')
        if not tag:
            return None

        def _attrs(e):
            return {k: (v if v is None or not v.strip() else v) for k, v in (e.attrib or {}).items()}

        # 容器节点：sheet/group/notebook/page/div/header/footer/separator
        if tag in ('sheet', 'group', 'notebook', 'page', 'div', 'header', 'footer', 'separator'):
            node = {
                'type': self._layout_type(tag),
                'attributes': _attrs(el)
            }
            # 标签/列数等
            if tag in ('group', 'page', 'notebook'):
                node['label'] = el.get('string', '')
                node['name'] = el.get('name', '')
                if tag == 'group':
                    try:
                        node['cols'] = int(el.get('col', '2'))
                    except Exception:
                        node['cols'] = 2
            # 容器级修饰（显隐/只读）
            mods = {}
            for k in ('readonly', 'required', 'invisible'):
                v = el.get(k)
                if v:
                    mods[k] = self._safe_eval_expr(v) or v
            if el.get('attrs'):
                parsed = self._safe_eval_expr(el.get('attrs'))
                if isinstance(parsed, dict):
                    for k in ('readonly', 'required', 'invisible'):
                        if k in parsed:
                            mods[k] = parsed[k]
            if mods:
                node.setdefault('attributes', {})['modifiers'] = mods

            # 递归子节点
            children = []
            for ch in el:
                cv = self._node_to_layout_from_dom(ch, fields_info)
                if cv:
                    children.append(cv)
            if children:
                if tag == 'notebook':
                    # notebook → tabs
                    node['tabs'] = []
                    for cv in children:
                        if cv.get('type') == 'page':
                            node['tabs'].append(cv)
                    node['children'] = []  # 与 tabs 并存时保持空，避免前端重复
                else:
                    node['children'] = children
            else:
                # 确保所有容器节点都有 children 属性，即使为空
                node['children'] = []
            return node

        # 字段节点
        if tag == 'field':
            fname = el.get('name') or ''
            if not fname:
                return None
            node = {'type': 'field', 'name': fname}
            meta = self._field_info_for_layout(fname, fields_info)
            # 覆盖 label/help/widget
            if el.get('string'):
                meta['label'] = el.get('string')
            if el.get('help'):
                meta['help'] = el.get('help')
            if el.get('widget'):
                meta['widget'] = el.get('widget')
            # 局部修饰
            fmods = {}
            for k in ('readonly', 'required', 'invisible'):
                if el.get(k):
                    fmods[k] = self._safe_eval_expr(el.get(k)) or el.get(k)
            if el.get('attrs'):
                parsed = self._safe_eval_expr(el.get('attrs'))
                if isinstance(parsed, dict):
                    for k in ('readonly', 'required', 'invisible'):
                        if k in parsed:
                            fmods[k] = parsed[k]
            if fmods:
                meta.setdefault('modifiers', {}).update(fmods)
            node['fieldInfo'] = meta

            # inline 子视图在这里不展开（交给 _collect_x2many_subviews_from_dom）
            return node

        # 按钮占位（通常不把按钮放进布局树，header/smart 会单独抽取）
        if tag == 'button':
            return {'type': 'button', 'name': el.get('name', ''), 'label': el.get('string', ''), 'buttonType': el.get('type', 'object')}

        # 其他未知节点：以 container 兜底
        node = {'type': self._layout_type(tag), 'attributes': _attrs(el)}
        children = []
        for ch in el:
            cv = self._node_to_layout_from_dom(ch, fields_info)
            if cv:
                children.append(cv)
        # 确保所有节点都有 children 属性
        node['children'] = children
        return node

    # ---------------- 布局合并 ----------------
    def _merge_layout(self, primary, fallback):
        """优先使用 DOM 解析结果；DOM 为空时使用 lossless 兜底。"""
        if isinstance(primary, list) and primary:
            return primary
        if isinstance(fallback, list) and fallback:
            return fallback
        if isinstance(fallback, dict) and fallback:
            return [fallback]
        return [{"type": "sheet", "children": []}]

    # ---------------- 状态条构建 ----------------
    def _build_statusbar(self, root, fields_info, model_name):
        field_name = None
        if root is not None:
            sb = root.xpath(".//field[@widget='statusbar' and @name]")
            if sb:
                field_name = sb[0].get('name')
        if not field_name:
            if 'stage_id' in (fields_info or {}):
                field_name = 'stage_id'
            elif 'state' in (fields_info or {}):
                field_name = 'state'
        states = []
        # selection → 直接构造
        if field_name == 'state' and fields_info.get('state', {}).get('selection'):
            for v, lbl in (fields_info['state'].get('selection') or []):
                states.append({'value': v, 'label': lbl})
        # stage_id（many2one）→ 若能安全 name_search 就取若干候选
        try:
            if field_name == 'stage_id':
                # 尝试轻量取 20 个阶段作为候选；失败则留空由前端懒加载
                Stage = self.env.get((fields_info.get('stage_id') or {}).get('relation', ''))
                if Stage is not None:
                    for rec_id, name in (Stage.sudo().name_search('', operator='ilike', limit=20) or []):
                        states.append({'value': rec_id, 'label': name})
        except Exception:
            pass
        return {"field": field_name, "states": states}

    # ---------------- 头部按钮抽取 ----------------
    def _extract_header_buttons(self, root):
        """抽取 <header>//button → 归一化为契约按钮"""
        if root is None:
            return []
        btns = []
        for b in root.xpath('.//header//button'):
            entry = self._button_to_action(b, level='header')
            if entry:
                btns.append(entry)
        return btns

    # ---------------- Smart Buttons 抽取 ----------------
    def _extract_button_box(self, root):
        """抽取 oe_button_box 内的 oe_stat_button"""
        if root is None:
            return []
        stats = []
        for b in root.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_button_box ')]//button[contains(concat(' ', normalize-space(@class), ' '), ' oe_stat_button ')]"):
            norm = self._button_to_action(b, level='smart')
            if norm:
                # label/icon 兜底
                if not norm.get('label'):
                    norm['label'] = (b.get('string') or 'Stat')
                if not norm.get('icon'):
                    norm['icon'] = (b.get('icon') or '')
                stats.append(norm)
        return stats

    # ---------------- Chatter/Attachments（模型优先） ----------------
    def _detect_chatter_and_attachments_model_first(self, model_name, fields_info, root=None):
        chatter_enabled = any(k in (fields_info or {}) for k in ('message_ids', 'message_follower_ids', 'website_message_ids'))
        attach_enabled = any(k in (fields_info or {}) for k in ('message_attachment_count', 'doc_count'))
        # DOM 辅助探测
        if root is not None:
            try:
                has_chatter = bool(root.xpath(".//*[@widget='mail_thread']")) or bool(
                    root.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')]")
                )
                has_attachments = bool(root.xpath(".//*[@widget='many2many_binary']")) or bool(
                    root.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_attachment_box ')]")
                )
                chatter_enabled = chatter_enabled or has_chatter
                attach_enabled = attach_enabled or has_attachments
            except Exception:
                _logger.exception("detect chatter/attachments failed")
        chatter = {'enabled': bool(chatter_enabled)}
        if chatter['enabled']:
            chatter['features'] = {'message': True, 'activity': True}
        attachments = {'enabled': bool(attach_enabled)}
        return chatter, attachments

    # ---------------- 字段修饰聚合 ----------------
    def _collect_field_modifiers(self, fields_info, root):
        """
        合并两处信息：
        - fields_info[f]['modifiers'] / ['domain'] / ['context'] / ['groups']
        - arch 的 <field name="f"> 上的 @readonly/@required/@invisible/@widget/@domain/@context/@groups
        """
        out = {}
        # 先从 fields_info 带过来
        for fname, meta in (fields_info or {}).items():
            mods = {}
            base_mods = (meta or {}).get('modifiers') or {}
            for k in ('readonly', 'required', 'invisible', 'column_invisible'):
                if k in base_mods:
                    mods[k] = base_mods[k]
            for k in ('widget', 'domain', 'context', 'groups'):
                if k in (meta or {}):
                    mods[k] = meta.get(k)
            if mods:
                out[fname] = mods

        # 再从 arch 覆盖/补充
        if root is not None:
            for el in root.xpath(".//field[@name]"):
                fname = el.get('name')
                if not fname:
                    continue
                mods = out.setdefault(fname, {})
                for k in ('readonly', 'required', 'invisible', 'column_invisible'):
                    if el.get(k):
                        mods[k] = self._safe_eval_expr(el.get(k)) or el.get(k)
                if el.get('widget'):
                    mods['widget'] = el.get('widget')
                if el.get('domain'):
                    mods['domain'] = self._safe_eval_expr(el.get('domain')) or el.get('domain')
                if el.get('context'):
                    mods['context'] = self._safe_eval_expr(el.get('context')) or el.get('context')
                if el.get('groups'):
                    mods['groups_xmlids'] = [x.strip() for x in el.get('groups').split(',') if x.strip()]

        return out

    # ---------------- 子视图收集（inline + 引用） ----------------
    def _collect_x2many_subviews_from_dom(self, root, fields_info):
        sub = {}
        if root is None:
            return sub
        for el in root.xpath(".//field[@name]"):
            fname = el.get('name')
            finfo = (fields_info or {}).get(fname) or {}
            ftype = finfo.get('type')
            if ftype not in ('one2many', 'many2many'):
                continue
            entry = {}
            # 1) inline 定义
            inline_tree = el.xpath('./tree')
            inline_form = el.xpath('./form')
            if inline_tree:
                entry['tree'] = self._parse_inline_tree_columns(inline_tree[0])
            if inline_form:
                entry['form'] = {"layout": self._extract_form_layout_dom(inline_form[0], {})}

            # 2) 引用式（views/context）
            relation = finfo.get('relation')
            try:
                # views="[(tree,ref),(form,ref)]" 风格
                views_attr = (el.get('views') or '').strip()
                if views_attr:
                    views_spec = self._safe_eval_expr(views_attr)
                    if isinstance(views_spec, (list, tuple)):
                        for vt, vid in views_spec:
                            if vt in ('tree', 'form'):
                                blk = self._safe_get_view_data(self.env[relation], vt)
                                if vt == 'tree':
                                    entry['tree'] = self._parse_inline_tree_columns(etree.fromstring((blk or {}).get('arch', '').encode('utf-8'))) if (blk or {}).get('arch') else entry.get('tree')
                                else:
                                    entry['form'] = {"layout": self._extract_form_layout_dom(etree.fromstring((blk or {}).get('arch','').encode('utf-8')), {})} if (blk or {}).get('arch') else entry.get('form')
                # context="{'tree_view_ref': 'xmlid'}" 风格
                ctx = self._safe_eval_expr(el.get('context')) if el.get('context') else None
                xmlid = (isinstance(ctx, dict) and (ctx.get('tree_view_ref') or ctx.get('form_view_ref')))
                if relation and xmlid and not entry.get('tree'):
                    Model = self.env[relation]
                    # 通过 xmlid 解析（容错处理）
                    try:
                        res = self.env['ir.model.data']._xmlid_to_res_model_res_id(xmlid)
                        if res and res[0] == 'ir.ui.view':
                            view_rec = self.env['ir.ui.view'].browse(res[1])
                            if view_rec.type == 'tree':
                                entry['tree'] = self._parse_inline_tree_columns(etree.fromstring(view_rec.arch_db.encode('utf-8')))
                            elif view_rec.type == 'form':
                                entry['form'] = {"layout": self._extract_form_layout_dom(etree.fromstring(view_rec.arch_db.encode('utf-8')), {})}
                    except Exception:
                        pass
            except Exception:
                _logger.exception("collect x2many subviews (ref) failed for %s", fname)

            # 最小兜底
            if not entry.get('tree'):
                entry['tree'] = {'columns': ['display_name']}
            entry.setdefault('policies', {'inline_edit': True, 'can_create': True, 'can_unlink': True})
            sub[fname] = entry
        return sub

    def _parse_inline_tree_columns(self, tree_el):
        try:
            cols = []
            for f in tree_el.xpath('./field[@name]'):
                n = f.get('name')
                if n and n not in cols:
                    cols.append(n)
            return {'columns': cols or ['display_name']}
        except Exception:
            return {'columns': ['display_name']}

    # ---------------- 工具函数 ----------------
    def _convert_parsed_structure_to_layout(self, parsed_structure, fields_info=None):
        if not parsed_structure:
            return {'type': 'form', 'children': []}
        node = parsed_structure
        root_type = node.get('tag')
        if root_type != 'form':
            if root_type and node.get('children'):
                for ch in node['children']:
                    if ch.get('tag') == 'form':
                        node = ch
                        break
        return self._convert_node_to_layout(node, fields_info or {})

    def _convert_node_to_layout(self, node, fields_info):
        if not node:
            return None
        tag = node.get('tag', '')
        attrs = node.get('attributes', {}) or {}
        children = node.get('children', []) or []

        layout_node = {'type': self._layout_type(tag), 'attributes': dict(attrs)}

        if tag in ('group', 'page', 'notebook'):
            layout_node['label'] = attrs.get('string', '')
            layout_node['name'] = attrs.get('name', '')
            if tag == 'group':
                try:
                    layout_node['cols'] = int(attrs.get('col', '2'))
                except Exception:
                    layout_node['cols'] = 2
        elif tag == 'field':
            fname = attrs.get('name', '')
            layout_node['name'] = fname
            meta = self._field_info_for_layout(fname, fields_info)
            if attrs.get('string'):
                meta['label'] = attrs.get('string')
            if attrs.get('help'):
                meta['help'] = attrs.get('help')
            if attrs.get('widget'):
                meta['widget'] = attrs.get('widget')
            for key in ('readonly', 'required', 'invisible'):
                if attrs.get(key):
                    parsed = self._safe_eval_expr(attrs.get(key)) or attrs.get(key)
                    meta.setdefault('modifiers', {})[key] = parsed
            layout_node['fieldInfo'] = meta
        elif tag == 'button':
            layout_node['name'] = attrs.get('name', '')
            layout_node['label'] = attrs.get('string', '')
            layout_node['buttonType'] = attrs.get('type', 'object')

        ch_list = []
        for ch in children:
            cv = self._convert_node_to_layout(ch, fields_info)
            if cv:
                ch_list.append(cv)
        if ch_list:
            layout_node['children'] = ch_list

        return layout_node

    def _layout_type(self, tag):
        mapping = {
            'form': 'form', 'sheet': 'sheet', 'group': 'group', 'page': 'page',
            'notebook': 'notebook', 'field': 'field', 'button': 'button',
            'header': 'header', 'footer': 'footer', 'div': 'container',
            'separator': 'separator', 'newline': 'newline', 'label': 'label'
        }
        return mapping.get(tag, tag)

    def _field_info_for_layout(self, fname, fields_info):
        meta = (fields_info or {}).get(fname, {}) or {}
        return {
            'name': fname,
            'type': meta.get('type', 'char'),
            'label': meta.get('string') or fname,
            'help': meta.get('help') or '',
            'relation': meta.get('relation') or '',
            'required': bool(meta.get('required')),  # 仅供前端初始提示
            'readonly': bool(meta.get('readonly')),
            'widget': meta.get('widget') or '',
        }

    # ---------------- 推断x2many子视图 ----------------
    def _infer_x2many_subviews(self, fields_meta):
        """
        小工具：识别 x2many 并构造最小子视图
        """
        sub = {}
        for fname, meta in (fields_meta or {}).items():
            t = meta.get('type')
            if t in ('one2many', 'many2many'):
                sub[fname] = {
                    'tree': {'columns': ['display_name']},
                    'policies': {'inline_edit': True, 'can_create': True, 'can_unlink': True}
                }
        return sub

    # ---------------- 安全表达式求值 ----------------
    def _safe_eval_expr(self, text):
        if text is None:
            return None
        t = text.strip()
        if not t:
            return t
        # 已经是 JSON 的场景
        try:
            if (t.startswith('{') and t.endswith('}')) or (t.startswith('[') and t.endswith(']')):
                return json.loads(t)
        except Exception:
            pass
        # Python 风格 domain/attrs/context
        try:
            return ast.literal_eval(t)
        except Exception:
            return t
