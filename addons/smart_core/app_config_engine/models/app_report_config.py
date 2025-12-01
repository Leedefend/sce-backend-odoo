# -*- coding: utf-8 -*-
# models/app_report_config.py
from odoo import models, fields, api, _
import json, hashlib, logging

_logger = logging.getLogger(__name__)


class AppReportConfig(models.Model):
    """
    契约 2.0 · 报表聚合配置
    - 归一 ir.actions.report → 标准报表契约（前端零推理）
    - 支持 groups 运行态过滤
    """
    _name = 'app.report.config'
    _description = 'Application Report Configuration'
    _rec_name = 'model'
    _order = 'model'

    # ===== 基础 =====
    model = fields.Char('Model', required=True, index=True)

    # ===== 版本/缓存 =====
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ===== 契约定义 =====
    # 结构：见 _scan_reports() 返回的 entries 列表
    reports_def = fields.Json('Reports Definition')

    # 扩展
    meta_info = fields.Json('Meta Info')
    is_active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条报表配置。'),
    ]

    # ================== 生成（聚合报表） ==================

    @api.model
    def _generate_from_reports(self, model_name):
        """
        聚合 ir.actions.report（含 binding_model_id 兼容），仅变更时涨版
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            entries = self._scan_reports(model_name)

            # 稳定哈希：仅基于 reports_def
            payload = json.dumps(entries, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            cfg = self.sudo().search([('model', '=', model_name)], limit=1)
            vals = {
                "model": model_name,
                "reports_def": entries,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Report config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Report config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Report config created for %s → version 1", model_name)

            return cfg
        except Exception:
            _logger.exception("Failed to generate report config for %s", model_name)
            raise

    # ================== 标准化输出 ==================

    def get_report_contract(self, filter_runtime=True):
        """
        返回标准化报表契约（可直接渲染“打印/导出”菜单）
        - filter_runtime=True：按当前用户组过滤
        返回列表元素示例：
        {
          "key":"account.report_invoice",
          "label":"发票",
          "kind":"report",
          "model":"account.move",
          "report_type":"qweb-pdf",
          "template":"account.report_invoice",
          "paperformat":{"id":3,"xml_id":"base.paperformat_euro","orientation":"Portrait"},
          "output":{"default":"pdf","inline":True},
          "multi": true,
          "groups":[1,3],
          "groups_xmlids":["base.group_user"],
          "attachment":{"use":false,"expression":None},
          "payload":{"report_id":12,"xml_id":"account.report_invoice","print_report_name":"(object.name or 'Report')"}
        }
        """
        self.ensure_one()
        reps = list(self.reports_def or [])
        if not filter_runtime:
            return reps

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
        for r in reps:
            gx = set(r.get('groups_xmlids') or [])
            if not gx:
                filtered.append(r)
                continue
            gids = xmlids_to_ids(gx)
            if gids & user_groups:
                filtered.append(r)
        return filtered

    # ================== 内部：扫描 ir.actions.report ==================

    def _scan_reports(self, model_name):
        """
        统一抽取报表：
        - 兼容字段名：model / binding_model_id.model
        - 输出统一契约字段
        """
        res = []
        R = self.env['ir.actions.report'].sudo()
        domain = [('model', '=', model_name)]
        # 兼容绑定字段
        try:
            if 'binding_model_id' in R._fields:
                domain = ['|', ('model', '=', model_name), ('binding_model_id.model', '=', model_name)]
        except Exception:
            pass

        reps = R.search(domain)
        for r in reps:
            key = r._get_external_id()[r.id] if hasattr(r, '_get_external_id') else None
            if not key:
                # 通用 xmlid 获取（多记录兼容）
                try:
                    d = r.get_xml_id()
                    if isinstance(d, dict) and r.id in d and d[r.id]:
                        key = d[r.id]
                except Exception:
                    key = None
            key = key or f"report_{r.id}"

            # groups
            groups_ids = [g.id for g in getattr(r, 'groups_id', [])]
            groups_xmlids = []
            for g in getattr(r, 'groups_id', []):
                try:
                    pair = g.get_xml_id()
                    if isinstance(pair, tuple) and pair[1]:
                        groups_xmlids.append(pair[1])
                except Exception:
                    pass

            paper = {}
            pf = getattr(r, 'paperformat_id', False)
            if pf:
                xmlid = None
                try:
                    pair = pf.get_xml_id()
                    if isinstance(pair, tuple) and pair[1]:
                        xmlid = pair[1]
                except Exception:
                    xmlid = None
                paper = {
                    "id": pf.id,
                    "xml_id": xmlid,
                    "orientation": getattr(pf, 'orientation', None),
                    "page_height": getattr(pf, 'page_height', None),
                    "page_width": getattr(pf, 'page_width', None),
                    "format": getattr(pf, 'format', None),
                }

            entry = {
                "key": key,
                "label": r.name or key,
                "kind": "report",
                "model": getattr(r, 'model', model_name),
                "report_type": getattr(r, 'report_type', 'qweb-pdf'),
                "template": getattr(r, 'report_name', None),
                "paperformat": paper,
                "output": {
                    "default": "pdf" if getattr(r, 'report_type', '') in ('qweb-pdf', 'qweb-text') else "html",
                    "inline": True,  # 前端可切换为下载
                },
                "multi": bool(getattr(r, 'multi', True)),
                "groups": groups_ids,
                "groups_xmlids": groups_xmlids,
                "attachment": {
                    "use": bool(getattr(r, 'attachment_use', False)),
                    "expression": getattr(r, 'attachment', None),
                },
                "payload": {
                    "report_id": r.id,
                    "xml_id": key if ':' in key else None,
                    "print_report_name": getattr(r, 'print_report_name', None),
                    "raw": {
                        "report_name": getattr(r, 'report_name', None),
                        "report_type": getattr(r, 'report_type', None),
                    }
                }
            }
            res.append(entry)

        # 稳定排序
        res.sort(key=lambda x: (x.get('label') or '', x.get('key')))
        return res
