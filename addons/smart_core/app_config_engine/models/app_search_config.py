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
            view_filters, view_groupbys = self._parse_search_view(arch)

            # 2) ir.filters（收藏/共享）
            saved_filters = self._collect_ir_filters(model_name)

            # 3) group_by 候选（基于字段元数据）
            groupby_candidates = self._infer_groupby_candidates(model_name, prefer=view_groupbys)

            # 4) 统一结构
            search_def = self._build_search_def(
                model_name=model_name,
                filters=view_filters,
                saved_filters=saved_filters,
                group_by=groupby_candidates,
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

        return {
            "model": self.model,
            "version": self.version,
            **data
        }

    # ======================= 内部：统一结构构建 =======================

    def _build_search_def(self, model_name, filters, saved_filters, group_by, facets, defaults):
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
        # 稳定排序（避免哈希抖动）
        filters_sorted = sorted(filters or [], key=lambda x: (x.get('label') or '', x.get('key') or ''))
        saved_sorted = sorted(saved_filters or [], key=lambda x: (not x.get('is_shared', False), x.get('name') or ''))
        group_sorted = sorted(group_by or [], key=lambda x: (not x.get('default', False), x.get('label') or '', x.get('field') or ''))

        return {
            "filters": filters_sorted,
            "saved_filters": saved_sorted,
            "group_by": group_sorted,
            "facets": facets or {"enabled": True},
            "defaults": defaults or {"limit": 80, "order": "id desc"}
        }

    # ======================= 视图解析 =======================

    def _safe_get_search_view(self, model_name):
        """
        获取 search 视图（兼容 get_view / fields_view_get）
        返回：{"arch": "...", "fields": {...}, "toolbar": {...}}
        """
        Model = self.env[model_name].sudo()
        # 新接口
        try:
            data = Model.get_view(view_type='search')
            if isinstance(data, dict) and data.get('arch'):
                return {"arch": data.get('arch'), "fields": data.get('fields', {}), "toolbar": data.get('toolbar', {})}
        except Exception:
            pass
        # 旧接口
        try:
            fv = Model.fields_view_get(view_type='search', toolbar=False)
            return {"arch": fv.get('arch'), "fields": fv.get('fields', {}), "toolbar": {}}
        except Exception:
            return {"arch": "", "fields": {}, "toolbar": {}}

    def _parse_search_view(self, arch):
        """
        解析 <search>：
        - filters: name/string/domain/context/groups -> 统一为标准项
        - groupbys: 从 filter 的 context 中抽取 group_by 值集合
        """
        filters, groupbys = [], set()
        if not arch or not etree:
            return filters, []

        try:
            root = etree.fromstring(arch.encode('utf-8'))
            nodes = [root] if root.tag == 'search' else root.xpath('.//search')
            for s in nodes:
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
                        if isinstance(gb, str):
                            groupbys.add(gb)
                        elif isinstance(gb, (list, tuple)):
                            for g in gb:
                                if isinstance(g, str):
                                    groupbys.add(g)

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
        except Exception:
            _logger.exception("parse search view failed")
        return filters, sorted(groupbys)

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
