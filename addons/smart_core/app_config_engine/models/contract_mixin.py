# -*- coding: utf-8 -*-
# models/contract_mixin.py
from odoo import models, api
import copy, json

class ContractSchemaMixin(models.AbstractModel):
    _name = 'contract.schema.mixin'
    _description = 'Contract Schema & Merge Mixin'

    # ---- 契约白名单（与前端约定保持一致）----
    @api.model
    def _allowed_keys_common(self):
        return {'modifiers', 'toolbar', 'search', 'order', 'meta'}

    @api.model
    def _allowed_keys_by_view(self, vt):
        table = {
            'tree': {'columns', 'row_actions', 'page_size', 'row_classes'},
            'form': {'layout', 'statusbar'},
            'kanban': {'kanban'},
            'pivot': {'pivot'},
            'graph': {'graph'},
            'calendar': {'calendar'},
            'gantt': {'gantt'},
            'search': set(), 'activity': set(), 'dashboard': set(),
        }
        return table.get(vt, set())

    @api.model
    def sanitize_contract(self, vt, data):
        """仅保留白名单键，并回填通用默认结构"""
        common = self._allowed_keys_common()
        specific = self._allowed_keys_by_view(vt)
        keep = set(common) | set(specific)

        def _prune(obj):
            if isinstance(obj, dict):
                return {k: _prune(v) for k, v in obj.items()
                        if (k in keep) or not isinstance(v, (dict, list))}
            if isinstance(obj, list):
                return [_prune(x) for x in obj]
            return obj

        cleaned = _prune(dict(data or {}))
        cleaned.setdefault('modifiers', {})
        cleaned.setdefault('toolbar', {"header": [], "sidebar": [], "footer": []})
        cleaned.setdefault('search', {"filters": [], "group_by": [], "facets": {"enabled": True}})
        return cleaned

    # ---- 深合并策略（dict 递归；list 基于 name 键对齐，否则后者覆盖）----
    @api.model
    def deep_merge(self, base, patch, list_key='name'):
        """将 patch 合并到 base，返回新对象（不修改入参）"""
        if patch is None:
            return copy.deepcopy(base)
        if base is None:
            return copy.deepcopy(patch)

        if isinstance(base, dict) and isinstance(patch, dict):
            out = copy.deepcopy(base)
            for k, v in patch.items():
                out[k] = self.deep_merge(base.get(k), v, list_key=list_key)
            return out

        if isinstance(base, list) and isinstance(patch, list):
            # 若元素是 dict 且含有唯一键（默认 name），则按键合并；否则直接覆盖
            def _index(lst):
                ok = all(isinstance(x, dict) and list_key in x for x in lst)
                return {x[list_key]: x for x in lst} if ok else None

            idx_base, idx_patch = _index(base), _index(patch)
            if idx_base is None or idx_patch is None:
                return copy.deepcopy(patch)  # 不可对齐，整体覆盖
            keys = list(dict.fromkeys(list(idx_base.keys()) + list(idx_patch.keys())))
            result = []
            for k in keys:
                if k in idx_base and k in idx_patch:
                    result.append(self.deep_merge(idx_base[k], idx_patch[k], list_key=list_key))
                elif k in idx_patch:
                    result.append(copy.deepcopy(idx_patch[k]))
                else:
                    result.append(copy.deepcopy(idx_base[k]))
            return result

        # 标量或类型不匹配 → 以 patch 覆盖
        return copy.deepcopy(patch)

    @api.model
    def json_clone(self, data):
        """JSON 方式深复制，便于去除 Odoo 的特殊对象"""
        return json.loads(json.dumps(data or {}, ensure_ascii=False))
