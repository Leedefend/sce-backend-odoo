# -*- coding: utf-8 -*-
"""
App Model Config

为契约控制器提供“模型与字段”配置：
- _generate_from_ir_model(model_name): 从 Odoo 模型元数据生成（或更新）字段定义
- get_model_contract(): 返回最小字段契约结构，供控制器拼装页面契约

说明：此前文件误放了视图配置内容，现已修正为模型配置实现。
"""

from odoo import models, fields, api, _
import json, hashlib, logging

_logger = logging.getLogger(__name__)


class AppModelConfig(models.Model):
    _name = 'app.model.config'
    _description = 'Application Model Configuration'
    _rec_name = 'name'
    _order = 'model'

    # 基础
    name = fields.Char('Name', required=True)
    model = fields.Char('Model', required=True, index=True)

    # 版本与追踪
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # 字段定义（标准化后的轻量结构，契约直用）
    fields_def = fields.Json('Fields Definition')
    meta_info = fields.Json('Meta Info')

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条模型配置（model 唯一）。'),
    ]

    @api.model
    def _stable_hash(self, payload):
        raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()

    @api.model
    def _generate_from_ir_model(self, model_name):
        """
        扫描 Odoo 模型字段，生成标准化字段清单：
        fields_def = { 'fields': [ {name, string, type, required, readonly, relation?}, ... ] }
        若结构未变化则不涨版本。
        返回：记录本身（recordset，单条）。
        """
        if not model_name:
            raise ValueError('model_name is required')
        if model_name not in self.env:
            raise ValueError(_('模型不存在：%s') % model_name)

        Model = self.env[model_name].sudo()
        fields_get = Model.fields_get()

        def to_item(name, spec):
            return {
                'name': name,
                'string': spec.get('string') or name,
                'type': spec.get('type') or 'char',
                'required': bool(spec.get('required')),
                'readonly': bool(spec.get('readonly')),
                'relation': spec.get('relation') or None,
            }

        items = [to_item(k, v) for k, v in fields_get.items()]
        # 稳定排序，保证哈希稳定
        items.sort(key=lambda x: x['name'])

        payload = { 'fields': items }
        new_hash = self._stable_hash(payload)

        cfg = self.sudo().search([('model', '=', model_name)], limit=1)
        vals = {
            'name': f'{model_name} fields',
            'model': model_name,
            'fields_def': payload,
            'config_hash': new_hash,
            'last_generated': fields.Datetime.now(),
        }
        if cfg:
            if (cfg.config_hash or '') != new_hash:
                vals['version'] = (cfg.version or 0) + 1
                cfg.write(vals)
                _logger.info('Model config updated for %s → version %s', model_name, cfg.version)
            else:
                _logger.info('Model config unchanged for %s, keep version %s', model_name, cfg.version)
        else:
            vals['version'] = 1
            cfg = self.sudo().create(vals)
            _logger.info('Model config created for %s → version 1', model_name)

        return cfg

    def get_model_contract(self):
        """返回标准化模型契约块：{ 'fields': [...] }"""
        self.ensure_one()
        return dict(self.fields_def or {'fields': []})

