# -*- coding: utf-8 -*-
# models/app_view_variant.py
from odoo import models, fields, api
from .contract_mixin import ContractSchemaMixin

class AppViewVariant(models.Model, ContractSchemaMixin):
    _name = 'app.view.variant'
    _description = 'Conditional View Variant (Overlay Patch)'
    _order = 'priority desc, version desc, id desc'

    name = fields.Char(required=True)
    model = fields.Char(required=True, index=True)
    view_type = fields.Selection([
        ('form','Form'),('tree','Tree'),('kanban','Kanban'),
        ('pivot','Pivot'),('graph','Graph'),('calendar','Calendar'),
        ('gantt','Gantt'),('search','Search'),
    ], required=True, index=True)

    # 条件维度：与 app.view.config 的 scope 对齐，可更细
    scope_type = fields.Selection([
        ('model','Model'),('action','Action'),('menu','Menu'),('profile','Profile')
    ], default='model', index=True)
    scope_ref_id = fields.Reference(
        selection=[('ir.actions.act_window','Action'),('ir.ui.menu','Menu')],
        index=True)
    company_ids = fields.Many2many('res.company')
    lang = fields.Char(size=5, index=True)
    groups_id = fields.Many2many('res.groups', string='Visible to Groups')

    # 触发条件：domain 与 context_tags 二选一或并用
    user_domain = fields.Json(string='User Domain')     # 例如 [["groups_id","in",[grp_id]]]
    context_tags = fields.Json(string='Context Tags')   # 例如 ["mobile","partner_portal"]

    # 覆盖内容：一个“契约补丁”，将按深合并策略叠加到基础视图契约上
    patch = fields.Json(required=True)
    version = fields.Integer(default=1)
    priority = fields.Integer(default=10)
    is_active = fields.Boolean(default=True)

    def _match_scope(self, subject=None, action_id=None, menu_id=None):
        self.ensure_one()
        if self.scope_type == 'action' and action_id:
            return self.scope_ref_id and self.scope_ref_id._name == 'ir.actions.act_window' and self.scope_ref_id.id == action_id
        if self.scope_type == 'menu' and menu_id:
            return self.scope_ref_id and self.scope_ref_id._name == 'ir.ui.menu' and self.scope_ref_id.id == menu_id
        return self.scope_type == 'model'

    def _match_env(self, lang=None, company=None, user=None, ctx=None):
        self.ensure_one()
        # 语言
        if self.lang and self.lang != (lang or ''):
            return False
        # 公司
        if self.company_ids and (not company or company.id not in self.company_ids.ids):
            return False
        # 用户组
        if self.groups_id and (not user or not (set(user.groups_id.ids) & set(self.groups_id.ids))):
            return False
        # 用户 domain
        if self.user_domain and user:
            # 简易匹配：仅支持 groups_id in [] 场景为例（可按需扩展）
            try:
                for cond in self.user_domain or []:
                    if cond[0] == 'groups_id' and cond[1] == 'in':
                        if not (set(user.groups_id.ids) & set(cond[2] or [])):
                            return False
            except Exception:
                return False
        # 上下文标签
        if self.context_tags and ctx:
            tags = set(ctx.get('tags') or [])
            if not set(self.context_tags or []) <= tags:
                return False
        return True

    def applicable(self, model_name, view_type, subject=None, action_id=None, menu_id=None, lang=None, company=None, user=None, ctx=None):
        self.ensure_one()
        if not self.is_active or self.model != model_name or self.view_type != view_type:
            return False
        return self._match_scope(subject, action_id, menu_id) and self._match_env(lang, company, user, ctx)

    def materialize_patch(self, view_type):
        self.ensure_one()
        # 白名单清洗，避免污染
        return self.sanitize_contract(view_type, self.patch or {})
