# -*- coding: utf-8 -*-
# models/app_search_config.py
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json, hashlib, logging

_logger = logging.getLogger(__name__)

try:
    from lxml import etree
except Exception:
    etree = None


class AppSearchConfig(models.Model):
    """
    契约 2.0 · 搜索配置聚合
    - 来源：search 视图(<filter/…>) + ir.filters（收藏/共享）
    - 输出：标准化搜索块（前端零推理）
    """
    _name = 'app.search.config'
    _description = 'Application Search Configuration'
    _rec_name = 'model'
    _order = 'model'

    # ===== 基础信息 =====
    model = fields.Char('Model', required=True, index=True)

    # ===== 版本/缓存 =====
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ===== 标准化搜索定义（契约直用）=====
    # 结构示例见 _build_search_def() 注释
    search_def = fields.Json('Search Definition')

    # ===== 扩展 =====
    meta_info = fields.Json('Meta Info')
    is_active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条搜索配置。'),
    ]

    # ======================= 生成（聚合） =======================

    @api.model
    def _generate_from_search(self, model_name):
        """
        生成/更新 “搜索契约”：
        1) 解析 search 视图：filters（含 domain/context/groups）、默认 group_by
        2) 汇入 ir.filters：用户收藏与共享过滤器
        3) 提供 group_by 候选：基于 fields_get 推断
        仅当结构变化时 +1 版本
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            # 1) 视图解析
            view = self._safe_get_search_view(model_name)
            arch = (view or {}).get('arch') or ''
            view_filters, view_groupbys, search_fields, searchpanel = self._parse_search_view(arch, model_name)

            # 2) ir.filters（收藏/共享）
            saved_filters = self._collect_ir_filters(model_name)

            # 3) 统一结构。Native list pages expose explicit search-view
            # group_by entries; inferred ORM groupability is not a toolbar.
            search_def = self._build_search_def(
                model_name=model_name,
                filters=view_filters,
                saved_filters=saved_filters,
                group_by=view_groupbys,
                fields=search_fields,
                searchpanel=searchpanel,
                facets={"enabled": True},
                defaults={"limit": 80, "order": getattr(self.env[model_name], "_order", "id desc") or "id desc"}
            )

            # 5) 稳定哈希并落库
            payload = json.dumps(search_def, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            cfg = self.sudo().search([('model', '=', model_name)], limit=1)
            vals = {
                "model": model_name,
                "search_def": search_def,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Search config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Search config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Search config created for %s → version 1", model_name)

            return cfg

        except Exception:
            _logger.exception("Failed to generate search config for %s", model_name)
            raise

    # ======================= 标准化输出 =======================

    def get_search_contract(self, filter_runtime=True, include_user_filters=True):
        """
        返回标准化搜索契约：
        - filter_runtime=True：按当前用户组过滤“视图内置 filter”（基于 groups_xmlids）
        - include_user_filters=True：附带当前用户可见的 ir.filters（本人 + 共享）
        结构示例：
        {
          "model":"sale.order",
          "version":3,
          "filters":[{"key":"my_orders","label":"我的订单","domain":[...],"domain_raw":"...","context_raw":"...","groups_xmlids":[...]}],
          "saved_filters":[{"id":12,"name":"本月客户","owner":3,"is_shared":true,"domain_raw":"[]","context_raw":"{}"}],
          "group_by":[{"field":"state","label":"状态","type":"selection","default":false}, ...],
          "facets":{"enabled":true},
          "defaults":{"limit":80,"order":"id desc"}
        }
        """
        self.ensure_one()
        block = dict(self.search_def or {})
        if not block:
            return {}

        if not filter_runtime and not include_user_filters:
            # 直接返回“全量定义”
            return {
                "model": self.model,
                "version": self.version,
                **block
            }

        # 深拷贝，避免污染存库
        data = json.loads(json.dumps(block, ensure_ascii=False))
        data = self._apply_action_search_view(data)

        # 运行态：过滤视图 filter 的 groups 限制
        if filter_runtime:
            user_groups = set(self.env.user.groups_id.ids)

            def xmlids_to_ids(xmlids):
                ids = set()
                for xid in (xmlids or []):
                    try:
                        g = self.env.ref(xid, raise_if_not_found=False)
                        if g and g._name == 'res.groups':
                            ids.add(g.id)
                    except Exception:
                        pass
                return ids

            filtered = []
            for f in data.get('filters', []):
                gx = set(f.get('groups_xmlids') or [])
                if not gx:
                    filtered.append(f)
                    continue
                gids = xmlids_to_ids(gx)
                if gids & user_groups:
                    filtered.append(f)
            data['filters'] = filtered

        # 只保留当前用户可见的 saved_filters（本人 + 共享）
        if include_user_filters:
            uid = self.env.uid
            visible_saved = []
            for sf in data.get('saved_filters', []):
                owner = sf.get('owner')
                shared = sf.get('is_shared', False)
                if shared or (owner and int(owner) == uid):
                    visible_saved.append(sf)
            data['saved_filters'] = visible_saved
        else:
            data['saved_filters'] = []

        data["interaction_model"] = "native_search_menu"
        data["native_search_menu"] = self._build_native_search_menu(
            filters=data.get("filters") if isinstance(data.get("filters"), list) else [],
            group_by=data.get("group_by") if isinstance(data.get("group_by"), list) else [],
            saved_filters=data.get("saved_filters") if isinstance(data.get("saved_filters"), list) else [],
            searchpanel=data.get("searchpanel") if isinstance(data.get("searchpanel"), list) else [],
        )

        return {
            "model": self.model,
            "version": self.version,
            **data
        }

    # ======================= 内部：统一结构构建 =======================

    def _build_search_def(self, model_name, filters, saved_filters, group_by, fields=None, searchpanel=None, facets=None, defaults=None):
        """
        统一结构（契约 2.0）：
        {
          "filters":       [ 视图内置过滤器（权限可控） ],
          "saved_filters": [ ir.filters 收藏/共享 ],
          "group_by":      [ group_by 候选 ],
          "facets":        { "enabled": true },
          "defaults":      { "limit":80, "order":"id desc" }
        }
        """
        # Preserve native search-view order. The payload hash is already stable
        # because XML traversal order is deterministic for a given view arch.
        filters_sorted = list(filters or [])
        saved_sorted = sorted(saved_filters or [], key=lambda x: (not x.get('is_shared', False), x.get('name') or ''))
        group_sorted = list(group_by or [])
        defaults = defaults or {"limit": 80, "order": "id desc"}

        return {
            "filters": filters_sorted,
            "saved_filters": saved_sorted,
            "group_by": group_sorted,
            "fields": list(fields or []),
            "searchpanel": list(searchpanel or []),
            "interaction_model": "native_search_menu",
            "native_search_menu": self._build_native_search_menu(
                filters=filters_sorted,
                group_by=group_sorted,
                saved_filters=saved_sorted,
                searchpanel=list(searchpanel or []),
            ),
            "facets": facets or {"enabled": True},
            "defaults": defaults,
            "default_sort": defaults.get("order") or "id desc",
        }

    def _build_native_search_menu(self, filters=None, group_by=None, saved_filters=None, searchpanel=None):
        def normalize_item(row, kind):
            if not isinstance(row, dict):
                return None
            if kind == "group_by":
                key = str(row.get("field") or row.get("key") or "").strip()
                label = str(row.get("label") or key).strip()
            elif kind == "favorites":
                key = str(row.get("key") or row.get("name") or row.get("id") or "").strip()
                label = str(row.get("label") or row.get("name") or key).strip()
            else:
                key = str(row.get("key") or row.get("name") or row.get("field") or "").strip()
                label = str(row.get("label") or row.get("string") or key).strip()
            if not key or not label:
                return None
            item = {
                "key": key,
                "label": label,
                "kind": kind,
            }
            for attr in ("field", "context_raw", "domain_raw", "select", "type", "default", "is_default"):
                if row.get(attr) not in (None, ""):
                    item[attr] = row.get(attr)
            return item

        controls = [
            {"key": "add_custom_filter", "label": _("添加自定义筛选"), "section": "filters", "kind": "control"},
            {"key": "add_custom_group", "label": _("添加自定义分组"), "section": "group_by", "kind": "control"},
            {"key": "save_current_search", "label": _("保存当前搜索"), "section": "favorites", "kind": "control"},
        ]

        section_defs = [
            ("filters", _("筛选"), filters or []),
            ("group_by", _("分组方式"), group_by or []),
            ("favorites", _("收藏夹"), saved_filters or []),
            ("searchpanel", _("搜索面板"), searchpanel or []),
        ]
        sections = []
        for key, label, rows in section_defs:
            items = [normalize_item(row, key) for row in rows if isinstance(row, dict)]
            items.extend([dict(control) for control in controls if control.get("section") == key])
            sections.append({
                "key": key,
                "label": label,
                "items": [item for item in items if item],
            })
        return {
            "interaction_model": "native_search_menu",
            "sections": sections,
            "controls": controls,
        }

    # ======================= 视图解析 =======================

    def _safe_get_search_view(self, model_name, prefer_action=False):
        """
        获取 search 视图（兼容 get_view / fields_view_get）
        返回：{"arch": "...", "fields": {...}, "toolbar": {...}}
        """
        ctx = dict(self.env.context or {})
        ModelRuntime = self.env[model_name].with_context(ctx)
        ModelSudo = self.env[model_name].sudo().with_context(ctx)

        def load_search_view(view_id=None, source="runtime_default"):
            try:
                data = ModelRuntime.with_context(load_all_views=True).get_view(view_id=view_id, view_type='search')
            except Exception as runtime_err:
                _logger.warning("runtime user search get_view failed, fallback sudo: %s", runtime_err)
                try:
                    data = ModelSudo.with_context(load_all_views=True).get_view(view_id=view_id, view_type='search')
                except Exception:
                    data = {}
            if isinstance(data, dict) and data.get('arch'):
                return {
                    "arch": data.get('arch'),
                    "fields": data.get('fields', {}),
                    "toolbar": data.get('toolbar', {}),
                    "_contract_view_id": view_id,
                    "_contract_view_source": source,
                }
            try:
                fv = ModelRuntime.fields_view_get(view_id=view_id, view_type='search', toolbar=False)
            except Exception as runtime_fv_err:
                _logger.warning("runtime user search fields_view_get failed, fallback sudo: %s", runtime_fv_err)
                try:
                    fv = ModelSudo.fields_view_get(view_id=view_id, view_type='search', toolbar=False)
                except Exception:
                    fv = {}
            if isinstance(fv, dict) and fv.get('arch'):
                return {
                    "arch": fv.get('arch'),
                    "fields": fv.get('fields', {}),
                    "toolbar": {},
                    "_contract_view_id": view_id,
                    "_contract_view_source": "%s_fields_view_get" % source,
                }
            return None

        if prefer_action:
            view_id = self._resolve_action_search_view_id()
            if view_id:
                selected = load_search_view(view_id=view_id, source="action_search")
                if selected:
                    return selected

        # 新接口
        selected = load_search_view(source="runtime_default")
        if selected:
            return selected
        return {"arch": "", "fields": {}, "toolbar": {}}

    def _resolve_action_search_view_id(self):
        """
        Resolve the native search view bound to the current action.
        Stored app.search.config remains model-scoped; action-specific search
        metadata is overlaid only at runtime.
        """
        try:
            action_id = int((self.env.context or {}).get('contract_action_id') or 0)
        except Exception:
            action_id = 0
        if not action_id or 'ir.actions.act_window' not in self.env:
            return None

        act = self.env['ir.actions.act_window'].sudo().browse(action_id)
        if not act.exists():
            return None

        action_context = {}
        try:
            action_context = safe_eval(act.context) if isinstance(act.context, str) and act.context.strip() else {}
        except Exception:
            action_context = {}

        search_view_ref = action_context.get('search_view_ref') if isinstance(action_context, dict) else None
        if search_view_ref:
            try:
                res = self.env['ir.model.data']._xmlid_to_res_model_res_id(search_view_ref)
                if res and res[0] == 'ir.ui.view':
                    return res[1]
            except Exception as e:
                _logger.warning("resolve search_view_ref failed: %s", e)

        search_view = getattr(act, 'search_view_id', False)
        if search_view:
            return search_view.id
        return None

    def _current_action(self):
        try:
            action_id = int((self.env.context or {}).get('contract_action_id') or 0)
        except Exception:
            action_id = 0
        if not action_id or 'ir.actions.act_window' not in self.env:
            return None
        act = self.env['ir.actions.act_window'].sudo().browse(action_id)
        return act if act.exists() else None

    def _dedupe_by_key(self, rows, key_name):
        out, seen = [], set()
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get(key_name) or row.get("key") or row.get("field") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(row)
        return out

    def _action_runtime_search_semantics(self, model_name, filters=None, group_by=None):
        act = self._current_action()
        if not act or act.res_model != model_name:
            return [], []
        filters = list(filters or [])
        group_by = list(group_by or [])
        filter_keys = {str(row.get("key") or "").strip() for row in filters if isinstance(row, dict)}
        group_fields = {str(row.get("field") or "").strip() for row in group_by if isinstance(row, dict)}

        action_filters = []
        action_groupbys = []
        domain_raw = str(getattr(act, "domain", "") or "").strip()
        domain_val = self._safe_eval_expr(domain_raw)
        if isinstance(domain_val, (list, tuple)) and domain_val:
            key = "__action_domain_%s" % act.id
            if key not in filter_keys:
                action_filters.append({
                    "key": key,
                    "label": act.name or _("当前入口"),
                    "help": _("来自当前原生动作的默认 domain"),
                    "domain": list(domain_val),
                    "domain_raw": domain_raw,
                    "context_raw": "{}",
                    "groups_xmlids": [],
                    "tags": ["native_action_domain"],
                    "default": True,
                    "source": "action_domain",
                })

        action_context = {}
        try:
            action_context = safe_eval(act.context) if isinstance(act.context, str) and act.context.strip() else {}
        except Exception:
            action_context = {}
        if not isinstance(action_context, dict):
            action_context = {}

        ctx_group_by = action_context.get("group_by")
        if isinstance(ctx_group_by, str):
            ctx_group_by = [ctx_group_by]
        if isinstance(ctx_group_by, (list, tuple)):
            fields_meta = {}
            try:
                fields_meta = self.env[model_name].sudo().fields_get()
            except Exception:
                fields_meta = {}
            for field in [str(item or "").strip() for item in ctx_group_by]:
                if not field or field in group_fields:
                    continue
                meta = fields_meta.get(field) or {}
                action_groupbys.append({
                    "field": field,
                    "label": meta.get("string") or field,
                    "type": meta.get("type") or "char",
                    "default": True,
                    "context_raw": "{'group_by': '%s'}" % field,
                    "source": "action_context",
                })
                group_fields.add(field)

        for key, value in action_context.items():
            text_key = str(key or "").strip()
            if not text_key.startswith("search_default_") or not value:
                continue
            token = text_key[len("search_default_"):]
            for row in filters:
                if isinstance(row, dict) and str(row.get("key") or "").strip() == token:
                    row["default"] = True
                    row["source"] = row.get("source") or "action_context"
            for row in group_by:
                if isinstance(row, dict) and str(row.get("field") or "").strip() == token:
                    row["default"] = True
                    row["source"] = row.get("source") or "action_context"

        return action_filters, action_groupbys

    def _apply_action_search_view(self, data):
        if not isinstance(data, dict) or not (self.env.context or {}).get('contract_action_id'):
            return data
        view = self._safe_get_search_view(self.model, prefer_action=True)
        arch = (view or {}).get('arch') or ''
        filters, groupbys, fields_out, searchpanel = self._parse_search_view(arch, self.model)
        if not any([filters, groupbys, fields_out, searchpanel]):
            return data
        action_filters, action_groupbys = self._action_runtime_search_semantics(self.model, filters=filters, group_by=groupbys)
        filters = self._dedupe_by_key(action_filters + filters, "key")
        groupbys = self._dedupe_by_key(groupbys + action_groupbys, "field")
        runtime_data = dict(data)
        runtime_data["filters"] = filters
        runtime_data["group_by"] = groupbys
        runtime_data["fields"] = fields_out
        runtime_data["searchpanel"] = searchpanel
        runtime_data["interaction_model"] = "native_search_menu"
        runtime_data["native_search_menu"] = self._build_native_search_menu(
            filters=filters,
            group_by=groupbys,
            saved_filters=runtime_data.get("saved_filters") if isinstance(runtime_data.get("saved_filters"), list) else [],
            searchpanel=searchpanel,
        )
        runtime_data.setdefault("facets", {"enabled": True})
        runtime_data.setdefault("defaults", data.get("defaults") or {"limit": 80, "order": "id desc"})
        runtime_data.setdefault("default_sort", runtime_data.get("defaults", {}).get("order") or "id desc")
        return runtime_data

    def _parse_search_view(self, arch, model_name=None):
        """
        解析 <search>：
        - filters: name/string/domain/context/groups -> 统一为标准项
        - groupbys: 从 filter 的 context 中抽取 group_by 值集合
        """
        filters, groupbys, fields_out, searchpanel_out = [], [], [], []
        if not arch or not etree:
            return filters, [], fields_out, searchpanel_out

        fields_meta = {}
        if model_name and model_name in self.env:
            try:
                fields_meta = self.env[model_name].sudo().fields_get()
            except Exception:
                fields_meta = {}

        def field_label(name, fallback=""):
            meta = fields_meta.get(name) or {}
            return meta.get("string") or fallback or name

        def field_type(name):
            return (fields_meta.get(name) or {}).get("type") or "char"

        def is_inside(node, tag_name):
            parent = node.getparent()
            while parent is not None:
                if getattr(parent, "tag", None) == tag_name:
                    return True
                parent = parent.getparent()
            return False

        def append_groupby(value, context_raw=None):
            if isinstance(value, str):
                values = [value]
            elif isinstance(value, (list, tuple)):
                values = [item for item in value if isinstance(item, str)]
            else:
                values = []
            for item in values:
                field = item.strip()
                if not field or field in [row.get("field") for row in groupbys]:
                    continue
                groupbys.append({
                    "field": field,
                    "label": field_label(field),
                    "type": field_type(field),
                    "default": False,
                    "context_raw": context_raw or "{'group_by': '%s'}" % field,
                })

        try:
            root = etree.fromstring(arch.encode('utf-8'))
            nodes = [root] if root.tag == 'search' else root.xpath('.//search')
            for s in nodes:
                for field_node in s.xpath('.//field[@name]'):
                    if is_inside(field_node, 'searchpanel'):
                        continue
                    name = (field_node.get('name') or '').strip()
                    if not name:
                        continue
                    groups_attr = field_node.get('groups') or ''
                    row = {
                        "name": name,
                        "field": name,
                        "label": field_node.get('string') or field_label(name),
                        "operator": field_node.get('operator') or '',
                        "filter_domain": field_node.get('filter_domain') or '',
                        "domain_raw": field_node.get('domain') or '',
                        "context_raw": field_node.get('context') or '',
                        "groups_xmlids": [x.strip() for x in groups_attr.split(',') if x.strip()],
                        "type": field_type(name),
                    }
                    if name not in [item.get("name") for item in fields_out]:
                        fields_out.append(row)

                for f in s.xpath('.//filter'):
                    name = f.get('name') or ''
                    label = f.get('string') or name
                    domain_raw = f.get('domain')
                    context_raw = f.get('context')
                    groups_attr = f.get('groups') or ''
                    help_txt = f.get('help') or ''

                    # 安全求值
                    dom_val = self._safe_eval_expr(domain_raw)
                    ctx_val = self._safe_eval_expr(context_raw)

                    # group_by 收集
                    gb = None
                    if isinstance(ctx_val, dict):
                        gb = ctx_val.get('group_by')
                        append_groupby(gb, context_raw)

                    filters.append({
                        "key": name or label,
                        "label": label or name or _("Filter"),
                        "help": help_txt,
                        "domain": dom_val if isinstance(dom_val, (list, tuple)) else [],
                        "domain_raw": domain_raw,
                        "context_raw": context_raw,
                        "groups_xmlids": [x.strip() for x in groups_attr.split(',') if x.strip()],
                        "tags": []  # 预留：可用于 UI tag
                    })

                for panel_field in s.xpath('.//searchpanel//field[@name]'):
                    name = (panel_field.get('name') or '').strip()
                    if not name:
                        continue
                    groups_attr = panel_field.get('groups') or ''
                    row = {
                        "name": name,
                        "field": name,
                        "label": panel_field.get('string') or field_label(name),
                        "select": panel_field.get('select') or '',
                        "icon": panel_field.get('icon') or '',
                        "domain_raw": panel_field.get('domain') or '',
                        "enable_counters": str(panel_field.get('enable_counters') or '').lower() in ('1', 'true'),
                        "groups_xmlids": [x.strip() for x in groups_attr.split(',') if x.strip()],
                        "type": field_type(name),
                    }
                    if name not in [item.get("name") for item in searchpanel_out]:
                        searchpanel_out.append(row)
        except Exception:
            _logger.exception("parse search view failed")
        return filters, groupbys, fields_out, searchpanel_out

    # ======================= ir.filters 收集 =======================

    def _collect_ir_filters(self, model_name):
        """
        收集 ir.filters（收藏筛选器）：
        - user_id = False → 共享
        - user_id = 当前用户 → 本人
        - 统一返回：id/name/is_shared/owner/domain_raw/context_raw
        """
        res = []
        if 'ir.filters' not in self.env:
            return res
        F = self.env['ir.filters'].sudo()
        # 只按 model_id 匹配；不过期望不同版本字段名相同
        flt = F.search([('model_id', '=', model_name)])
        for r in flt:
            # domain/context 在 ir.filters 中通常为字符串
            res.append({
                "id": r.id,
                "name": r.name or f"filter_{r.id}",
                "is_shared": not bool(getattr(r, 'user_id', False)),
                "owner": getattr(r.user_id, 'id', None),
                "domain_raw": getattr(r, 'domain', None),
                "context_raw": getattr(r, 'context', None),
            })
        return res

    # ======================= group_by 候选推断 =======================

    def _infer_groupby_candidates(self, model_name, prefer=None):
        """
        基于 fields_get 推断可 group_by 字段：
        - 优先：search 内显式提供的 group_by（prefer）
        - 推断规则（常见可分组字段）：
          many2one / selection / date / datetime / boolean
        返回：[{field,label,type,default}]
        """
        prefer = prefer or []
        Model = self.env[model_name].sudo()
        fget = Model.fields_get()
        candidates = []

        def add_field(fname, default=False):
            meta = fget.get(fname) or {}
            candidates.append({
                "field": fname,
                "label": meta.get('string', fname),
                "type": meta.get('type', 'char'),
                "default": bool(default),
            })

        # 1) 先加入显式 prefer 的字段
        seen = set()
        for gb in prefer:
            if isinstance(gb, dict):
                field = str(gb.get("field") or "").strip()
                if field in fget and field not in seen:
                    candidates.append({
                        "field": field,
                        "label": gb.get("label") or (fget.get(field) or {}).get("string", field),
                        "type": gb.get("type") or (fget.get(field) or {}).get("type", "char"),
                        "default": bool(gb.get("default")),
                        "context_raw": gb.get("context_raw") or "{'group_by': '%s'}" % field,
                    })
                    seen.add(field)
                continue
            if gb in fget and gb not in seen:
                add_field(gb, default=False)
                seen.add(gb)

        # 2) 再按类型规则补齐
        for fname, meta in fget.items():
            if fname in seen:
                continue
            t = meta.get('type')
            if t in ('many2one', 'selection', 'date', 'datetime', 'boolean'):
                add_field(fname, default=False)
                seen.add(fname)

        # 3) 若一个都没有，兜底给 state（如果存在）
        if not candidates and 'state' in fget:
            add_field('state', default=False)

        return candidates

    # ======================= 工具 =======================

    def _safe_eval_expr(self, expr):
        """安全求值：失败返回 None，不抛异常"""
        if not expr or not isinstance(expr, str):
            return None
        try:
            return safe_eval(expr, {})
        except Exception:
            return None
