# -*- coding: utf-8 -*-
# models/app_validator_config.py
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import re, json, hashlib, logging

_logger = logging.getLogger(__name__)


class AppValidatorConfig(models.Model):
    """
    契约 2.0 · 预校验规则配置
    - 来自 fields_get + _sql_constraints 的可前置校验
    - 提供轻量级 preflight 校验方法（不落库、不写表）
    """
    _name = 'app.validator.config'
    _description = 'Application Validator Configuration'
    _rec_name = 'model'
    _order = 'model'

    # ===== 基础 =====
    model = fields.Char('Model', required=True, index=True)

    # ===== 版本/缓存 =====
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ===== 契约定义 =====
    validators_def = fields.Json('Validators Definition')  # 见 _build_validators_def

    # 扩展
    meta_info = fields.Json('Meta Info')
    is_active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条校验配置。'),
    ]

    # ================== 生成（聚合校验规则） ==================

    @api.model
    def _generate_from_validators(self, model_name):
        """
        基于 fields_get + _sql_constraints 生成可前置校验规则
        - 注意：不尝试解析 @api.constrains（无法可靠枚举）
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            Model = self.env[model_name].sudo()
            fget = Model.fields_get()
            sql_constraints = getattr(Model, '_sql_constraints', []) or []

            field_rules = self._collect_field_rules(fget)
            record_rules = self._collect_record_rules(sql_constraints)

            validators_def = self._build_validators_def(
                model_name=model_name,
                field_rules=field_rules,
                record_rules=record_rules,
                # 默认值样本不进入哈希，避免动态值导致版本抖动
                defaults_sample=self._safe_defaults_sample(Model, fget)
            )

            # 稳定哈希：排除 defaults_sample
            payload = json.dumps({
                "model": validators_def["model"],
                "field_rules": validators_def["field_rules"],
                "record_rules": validators_def["record_rules"],
            }, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            cfg = self.sudo().search([('model', '=', model_name)], limit=1)
            vals = {
                "model": model_name,
                "validators_def": validators_def,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Validator config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Validator config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Validator config created for %s → version 1", model_name)

            return cfg
        except Exception:
            _logger.exception("Failed to generate validator config for %s", model_name)
            raise

    # ================== 标准化输出 ==================

    def get_validator_contract(self):
        """
        返回标准化预校验契约：
        {
          "model":"sale.order",
          "version":3,
          "field_rules":{"name":{"type":"char","required":true,"size":64,"selection":[],"digits":null,"relation":null,"domain_raw":None}},
          "record_rules":{"unique":[{"fields":["name"],"message":"Name must be unique"}],"sql_checks":[{"name":"positive_amount","definition":"CHECK(amount_total>=0)","message":"..."}]},
          "defaults_sample":{"name":"","company_id":"dynamic"}
        }
        """
        self.ensure_one()
        return {
            "model": self.model,
            "version": self.version,
            **(self.validators_def or {})
        }

    # ================== 对外：轻量级预校验 ==================

    @api.model
    def preflight_check(self, model_name, values, context=None):
        """
        轻量级预校验（不创建记录）：
        - 必填、类型/选择、长度、关系存在性、唯一性(基于 _sql_constraints 可解析的 unique)
        - 注意：不能替代后端最终约束，作用是前端提前提示 & 降少失败请求
        返回：
        {
          "ok": true/false,
          "errors": [{"field":"name","code":"required","message":"必填"}],
          "hints": []
        }
        """
        out = {"ok": True, "errors": [], "hints": []}
        try:
            cfg = self._generate_from_validators(model_name)
            rules = cfg.validators_def or {}
            field_rules = rules.get('field_rules') or {}
            record_rules = rules.get('record_rules') or {}

            # 1) 字段级
            for fname, fr in field_rules.items():
                if fr.get('required') and not self._has_value(values.get(fname)):
                    out["errors"].append({"field": fname, "code": "required", "message": _("必填")})
                # selection
                if fr.get('type') == 'selection' and self._has_value(values.get(fname)):
                    allowed = [v[0] for v in (fr.get('selection') or []) if isinstance(v, (list, tuple)) and len(v) >= 1]
                    if values.get(fname) not in allowed:
                        out["errors"].append({"field": fname, "code": "selection", "message": _("不在允许的取值范围")})
                # 长度（char）
                if fr.get('type') == 'char' and fr.get('size'):
                    v = values.get(fname)
                    if isinstance(v, str) and len(v) > int(fr['size']):
                        out["errors"].append({"field": fname, "code": "max_length", "message": _("长度超出限制 %s") % fr['size']})
                # 关系存在性（many2one）
                if fr.get('type') == 'many2one' and self._has_value(values.get(fname)):
                    rel = fr.get('relation')
                    if rel and rel in self.env:
                        rel_id = values.get(fname)
                        if isinstance(rel_id, (list, tuple)) and rel_id:
                            rel_id = rel_id[0]
                        if isinstance(rel_id, int) and rel_id > 0:
                            exists = bool(self.env[rel].browse(rel_id).exists())
                            if not exists:
                                out["errors"].append({"field": fname, "code": "fk_missing", "message": _("关联记录不存在")})

            # 2) 记录级：唯一性（best-effort）
            uniq_rules = record_rules.get('unique') or []
            if uniq_rules:
                Model = self.env[model_name]
                # 更新场景：允许 values 带 id，用于排除自己
                current_id = values.get('id')
                for ur in uniq_rules:
                    fields_set = ur.get('fields') or []
                    if not fields_set:
                        continue
                    dom = []
                    ok_fields = True
                    for f in fields_set:
                        if f not in field_rules:
                            ok_fields = False
                            break
                        dom.append((f, '=', values.get(f)))
                    if not ok_fields:
                        continue
                    if current_id:
                        dom.append(('id', '!=', current_id))
                    # 注意：此处不 sudo，让实际访问控制生效
                    cnt = Model.search_count(dom)
                    if cnt > 0:
                        out["errors"].append({"field": '+'.join(fields_set), "code": "unique", "message": ur.get('message') or _("唯一性约束冲突")})

            out["ok"] = len(out["errors"]) == 0
            return out
        except Exception:
            _logger.exception("preflight_check failed for %s", model_name)
            out["ok"] = False
            out["errors"].append({"field": None, "code": "internal", "message": _("内部校验失败")})
            return out

    # ================== 规则采集：字段/记录 ==================

    def _collect_field_rules(self, fget):
        """
        字段级规则：类型、必填、长度、选择、digits、关系、domain_raw
        """
        field_rules = {}
        for fname, meta in (fget or {}).items():
            t = meta.get('type')
            rule = {
                "type": t,
                "required": bool(meta.get('required', False)),
                "size": meta.get('size', None),                 # char 长度
                "selection": meta.get('selection', []),         # selection 列表
                "digits": meta.get('digits', None),             # float/monetary
                "relation": meta.get('relation', None),         # m2o/m2m/o2m
                "domain_raw": meta.get('domain', None),         # 仅当字段定义上声明
                "string": meta.get('string', fname),
                "help": meta.get('help', ''),
            }
            field_rules[fname] = rule
        return field_rules

    def _collect_record_rules(self, sql_constraints):
        """
        记录级规则：从 _sql_constraints 推断
        - 唯一性：解析 UNIQUE(...) 字段集
        - 其他 CHECK：原样下发 definition + message（仅提示）
        """
        uniques, checks = [], []
        for tup in (sql_constraints or []):
            # 规范：(name, definition, message)
            if not isinstance(tup, (list, tuple)) or len(tup) < 3:
                continue
            name, definition, message = tup[0], tup[1], tup[2]
            if not isinstance(definition, str):
                continue
            def_str = definition.upper()
            # UNIQUE 解析（简易）：匹配 UNIQUE(name1,name2)
            m = re.search(r'UNIQUE\s*\(([^)]+)\)', def_str, flags=re.I)
            if m:
                cols = [c.strip().strip('"').strip("'") for c in m.group(1).split(',') if c.strip()]
                if cols:
                    uniques.append({"name": name, "fields": cols, "message": message})
                continue
            # 其他 CHECK/约束
            if 'CHECK' in def_str or '>' in def_str or '<' in def_str or '=' in def_str:
                checks.append({"name": name, "definition": definition, "message": message})
        return {"unique": uniques, "sql_checks": checks}

    # ================== 统一结构 ==================

    def _build_validators_def(self, model_name, field_rules, record_rules, defaults_sample):
        """
        validators_def 统一结构
        """
        return {
            "model": model_name,
            "field_rules": field_rules or {},
            "record_rules": record_rules or {"unique": [], "sql_checks": []},
            "defaults_sample": defaults_sample or {}
        }

    # ================== 工具 ==================

    def _safe_defaults_sample(self, Model, fget):
        """
        获取 default_get 的“示例值”
        - 仅包含 key，不计入哈希，避免动态值抖动
        - 动态值统一标记为 'dynamic'（datetime/uid/company 等）
        """
        sample = {}
        try:
            names = list((fget or {}).keys())
            d = Model.default_get(names) if names else {}
            for k, v in (d or {}).items():
                # 抽象化：避免具体值（例如当前用户/时间）
                sample[k] = 'dynamic' if v not in (False, 0, '', None) else v
        except Exception:
            pass
        return sample

    def _has_value(self, v):
        return v not in (None, False, '', [], {})
