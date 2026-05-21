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
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)


class AppModelConfig(models.Model):
    _name = 'app.model.config'
    _description = 'Application Model Configuration'
    _rec_name = 'name'
    _order = 'model'
    SOURCE_KIND = "odoo_model_fields_projection"
    SOURCE_AUTHORITIES = ("ir.model", "ir.model.fields", "odoo.orm")

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
    def _source_contract(self, model_name):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model_name or ""),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": True,
        }

    @api.model
    def _stable_hash(self, payload):
        raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()

    @api.model
    def _lock_generation(self, model_name):
        """Serialize lazy generation per model to keep the unique model row idempotent."""
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s), hashtext(%s))",
            ("app.model.config", str(model_name or "")),
        )

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

        self._lock_generation(model_name)

        Model = self.env[model_name].sudo()
        fields_get = Model.fields_get()

        def to_item(name, spec):
            help_text = spec.get('help') or ''
            return {
                'name': name,
                'string': spec.get('string') or name,
                'type': spec.get('type') or 'char',
                'required': bool(spec.get('required')),
                'readonly': bool(spec.get('readonly')),
                'relation': spec.get('relation') or None,
                'help': help_text,
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
            'meta_info': {'source': self._source_contract(model_name)},
            'config_hash': new_hash,
            'last_generated': fields.Datetime.now(),
        }
        if self.env.context.get('contract_projection_readonly'):
            vals['version'] = cfg.version if cfg else 0
            vals['meta_info'] = {
                'source': self._source_contract(model_name),
                'transient': True,
                'runtime_readonly': True,
            }
            return self.new(vals)
        if cfg:
            if (cfg.config_hash or '') != new_hash:
                vals['version'] = (cfg.version or 0) + 1
                cfg.write(vals)
                _logger.info('Model config updated for %s → version %s', model_name, cfg.version)
            else:
                _logger.info('Model config unchanged for %s, keep version %s', model_name, cfg.version)
        else:
            vals['version'] = 1
            try:
                with self.env.cr.savepoint():
                    cfg = self.sudo().create(vals)
                _logger.info('Model config created for %s → version 1', model_name)
            except IntegrityError:
                cfg = self.sudo().search([('model', '=', model_name)], limit=1)
                if not cfg:
                    raise
                if (cfg.config_hash or '') != new_hash:
                    vals['version'] = (cfg.version or 0) + 1
                    cfg.write(vals)
                    _logger.info('Model config recovered and updated for %s → version %s', model_name, cfg.version)
                else:
                    _logger.info('Model config recovered unchanged for %s, keep version %s', model_name, cfg.version)

        return cfg

    def get_model_contract(self):
        """返回标准化模型契约块：{ 'fields': [...] }"""
        self.ensure_one()
        return dict(self.fields_def or {'fields': []})
