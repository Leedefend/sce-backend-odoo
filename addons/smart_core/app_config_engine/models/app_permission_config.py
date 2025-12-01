# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json, hashlib, logging

_logger = logging.getLogger(__name__)


class AppPermissionConfig(models.Model):
    """
    契约 2.0 · 权限聚合配置
    - 一条记录表示一个 target（通常是某模型）的“权限契约”聚合结果
    - 生成阶段使用 sudo() 扫全量定义；运行态由服务层根据当前用户再做裁剪
    """
    _name = 'app.permission.config'
    _description = 'Application Permission Configuration'
    _rec_name = 'target_ref'
    _order = 'target_type, target_ref'

    # ========== 目标定义 ==========
    target_type = fields.Selection([
        ('model',  'Model'),
        ('view',   'View'),
        ('field',  'Field'),
        ('action', 'Action'),
    ], string='Target Type', required=True, index=True)

    target_ref = fields.Char('Target Reference', required=True, index=True)  # 模型名/视图XMLID或ID/动作XMLID或ID/字段"model.field"

    # ========== 版本与追踪 ==========
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ========== 运行时扩展 ==========
    groups_id = fields.Many2many('res.groups', string='Access Groups')  # 可用于“整包权限仅对这些组可见”，通常留空
    meta_info = fields.Json('Meta Info')                                 # 备注/标签
    is_active = fields.Boolean('Active', default=True)

    # ========== 规范化权限定义（契约直用）==========
    permission_def = fields.Json('Permission Definition', help="""
    统一权限契约（示例）：
    {
      "model": "sale.order",
      "perms_by_group": {                      # 按组的原子四权矩阵（来自 ir.model.access）
        "base.group_user": {"read": true, "write": true, "create": true, "unlink": false},
        "__all__": {"read": true}              # group_id 为空 → 面向所有用户
      },
      "field_groups": {                        # 字段级权限（来自 ir.model.fields.groups）
        "amount_total": {"groups_ids":[1,3], "groups_xmlids":["base.group_user"]},
        ...
      },
      "rules": {                               # 记录规则（来自 ir.rule），按操作桶分组
        "read": {
          "mode": "OR",
          "clauses": [
            {"id": 12, "name":"My Records", "domain_raw":"[('user_id','=',user.id)]", "domain":[["user_id","=",["uid"]]], "groups_xmlids": ["base.group_user"], "global": false}
          ]
        },
        "write": {"mode": "OR", "clauses": []},
        "create": {"mode": "OR", "clauses": []},
        "unlink": {"mode": "OR", "clauses": []}
      },
      "order_default": "id desc",
      "domain_default": []
    }
    """)

    _sql_constraints = [
        ('uniq_target_model', 'unique(target_type, target_ref)', '每个 (target_type,target_ref) 只允许一条权限配置。'),
    ]

    # ================== 生成契约 ==================

    @api.model
    def _generate_from_access_rights(self, model_name):
        """
        从 ir.model.access + ir.rule + ir.model.fields(groups) 生成“模型级”权限契约
        - 使用 sudo() 扫全量定义；不按当前用户过滤（运行态由服务层裁剪）
        - 不变更不涨版：通过 permission_def 的稳定 hash 判定
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            Model = self.env[model_name]

            # 1) 四权矩阵（按组）
            perms_by_group = self._collect_acl_matrix(model_name)

            # 2) 字段级 groups（字段可见/可写需结合视图 modifiers 最终下沉）
            field_groups = self._collect_field_groups(model_name)

            # 3) 记录规则（按操作桶分组，保留 raw + 可解析 domain）
            rules = self._collect_record_rules(model_name)

            # 4) 默认排序/默认域（与 model.config 呼应）
            order_default = getattr(Model, '_order', 'id desc') or 'id desc'
            domain_default = []  # 保持空，避免和 ir.rule 冲突；业务若有默认域应在 model.config 下发

            permission_def = {
                "model": model_name,
                "perms_by_group": perms_by_group,
                "field_groups": field_groups,
                "rules": rules,
                "order_default": order_default,
                "domain_default": domain_default
            }

            # 5) 计算稳定哈希并落库（不变更不涨版）
            payload = json.dumps(permission_def, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            cfg = self.sudo().search([('target_type', '=', 'model'), ('target_ref', '=', model_name)], limit=1)
            vals = {
                "target_type": "model",
                "target_ref": model_name,
                "permission_def": permission_def,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Permission config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Permission config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Permission config created for %s → version 1", model_name)

            return cfg

        except Exception as e:
            _logger.exception("Failed to generate permission config for %s", model_name)
            raise

    # ================== 标准化输出（服务层直接使用） ==================

    def get_permission_contract(self, filter_runtime=False):
        """
        返回标准化权限契约
        - filter_runtime=False：返回“全量定义”（服务层自行按用户裁剪）
        - filter_runtime=True ：返回“已按当前用户组简化”的权限摘要（四权 + 规则只保留命中的 clauses）
        """
        self.ensure_one()
        perm = dict(self.permission_def or {})

        if not filter_runtime:
            return perm

        # 运行态裁剪：按当前用户组聚合
        eff = self.compile_effective_for_user(uid=self.env.uid)
        # 将四权与命中规则回填到 permission_def 的副本上，便于服务层直用
        perm['effective'] = eff
        return perm

    # ================== 运行态：计算某用户的“生效权限摘要” ==================

    def compile_effective_for_user(self, uid=None):
        """
        生效权限摘要（给服务层快速下沉到契约）：
        {
          "groups": [1,3],
          "rights": {"read":true,"write":true,"create":true,"unlink":false},
          "rules": {
            "read": {"mode":"OR","clauses":[...]},   # 仅保留对该用户命中的规则子集
            "write": {...}, "create": {...}, "unlink": {...}
          }
        }
        说明：
        - ACL 合并策略：只要命中任一“允许该操作”的分组或 __all__，即该操作为 True
        - 规则合并策略：取 groups 为空（全局）或与用户组有交集的 rule，操作维度下用 OR 列表返回（不做求值）
        """
        self.ensure_one()
        uid = uid or self.env.uid
        user_groups = set(self.env['res.users'].browse(uid).groups_id.ids)

        perm = self.permission_def or {}
        by_group = perm.get('perms_by_group') or {}
        rules = perm.get('rules') or {}

        # 1) 计算四权（ACL）
        rights = {"read": False, "write": False, "create": False, "unlink": False}

        def _apply_acl_for(group_key):
            gperm = by_group.get(group_key) or {}
            for k in rights.keys():
                rights[k] = rights[k] or bool(gperm.get(k, False))

        # group_id 为空 → "__all__"
        if '__all__' in by_group:
            _apply_acl_for('__all__')

        # 命中的组（支持 xmlid 和 id 形式）
        all_groups = self.env['res.groups'].sudo().search([])
        xmlid_to_id = {}
        try:
            if hasattr(all_groups, 'get_external_id'):
                mapping = all_groups.get_external_id() or {}
            else:
                mapping = all_groups.get_xml_id() or {}
            if isinstance(mapping, dict):
                for gid, xid in mapping.items():
                    if xid:
                        xmlid_to_id[xid] = gid
        except Exception:
            pass

        for gkey in by_group.keys():
            if gkey == '__all__':
                continue
            # gkey 可能是 xmlid，也可能是 "id:14" 这样的自定义写法；两者都兼容
            gid = None
            if gkey.startswith('id:'):
                try:
                    gid = int(gkey.split(':', 1)[1])
                except Exception:
                    gid = None
            else:
                gid = xmlid_to_id.get(gkey)
            if gid and gid in user_groups:
                _apply_acl_for(gkey)

        # 2) 过滤命中记录规则（按操作分桶；规则域仍由服务层在具体查询时 AND/OR 计算）
        def _hit_clause(clause):
            xids = set(clause.get('groups_xmlids') or [])
            return (not xids) or bool({xmlid_to_id.get(x) for x in xids} & user_groups)

        eff_rules = {}
        for op in ('read', 'write', 'create', 'unlink'):
            bucket = rules.get(op) or {"mode": "OR", "clauses": []}
            clauses = [c for c in (bucket.get('clauses') or []) if _hit_clause(c)]
            eff_rules[op] = {"mode": bucket.get('mode') or 'OR', "clauses": clauses}

        return {
            "groups": list(user_groups),
            "rights": rights,
            "rules": eff_rules
        }

    # ================== 内部采集：ACL / 字段组 / 记录规则 ==================

    def _collect_acl_matrix(self, model_name):
        """
        采集 ir.model.access，得到“按组的四权矩阵”
        - group_id 为空 → '__all__'
        - key 尽量使用 group 的 xmlid；取不到时回退 'id:<id>'
        """
        res = {}
        Access = self.env['ir.model.access'].sudo()
        accs = Access.search([('model_id.model', '=', model_name)])
        for a in accs:
            key = '__all__'
            if a.group_id:
                xid = self._group_xmlid(a.group_id)
                key = xid or f'id:{a.group_id.id}'
            res.setdefault(key, {"read": False, "write": False, "create": False, "unlink": False})
            res[key]["read"]   = res[key]["read"]   or bool(a.perm_read)
            res[key]["write"]  = res[key]["write"]  or bool(a.perm_write)
            res[key]["create"] = res[key]["create"] or bool(a.perm_create)
            res[key]["unlink"] = res[key]["unlink"] or bool(a.perm_unlink)
        return res

    def _collect_field_groups(self, model_name):
        """
        采集字段级 groups（限制字段可见/可写的基础信息）
        - 仅下发 groups_ids / groups_xmlids；具体 readonly/invisible/required 由视图 modifiers 合并后下沉
        """
        out = {}
        IMF = self.env['ir.model.fields'].sudo()
        fields_rec = IMF.search([('model', '=', model_name)])
        for f in fields_rec:
            gids = f.groups.ids
            xids = []
            try:
                if hasattr(f.groups, 'get_external_id'):
                    mapping = f.groups.get_external_id() or {}
                else:
                    mapping = f.groups.get_xml_id() or {}
                if isinstance(mapping, dict):
                    xids = [x for x in mapping.values() if x]
            except Exception:
                xids = []
            out[f.name] = {"groups_ids": gids, "groups_xmlids": xids}
        return out

    def _collect_record_rules(self, model_name):
        """
        采集 ir.rule（记录规则），按操作分桶：
        - Odoo 的规则在同一操作上通常以 OR 组合（命中任一条即放行）
        - 这里不做求值，仅把 domain_raw 与可解析的 domain（若安全）都下发，交由服务层在具体场景组合
        """
        Rule = self.env['ir.rule'].sudo()
        rules = Rule.search([('model_id.model', '=', model_name), ('active', '=', True)]) if self._field_exists(Rule, 'active') \
                else Rule.search([('model_id.model', '=', model_name)])
        buckets = {op: {"mode": "OR", "clauses": []} for op in ('read', 'write', 'create', 'unlink')}

        for r in rules:
            # 规则绑定的组
            xids = []
            try:
                if hasattr(r.groups, 'get_external_id'):
                    mapping = r.groups.get_external_id() or {}
                else:
                    mapping = r.groups.get_xml_id() or {}
                if isinstance(mapping, dict):
                    xids = [x for x in mapping.values() if x]
            except Exception:
                xids = []
            # 域
            raw = r.domain_force or '[]'
            dom = []
            try:
                val = safe_eval(raw, {})
                if isinstance(val, (list, tuple)):
                    dom = list(val)
            except Exception:
                dom = []
            clause = {
                "id": r.id,
                "name": r.name or '',
                "domain_raw": raw,
                "domain": dom,
                "groups_xmlids": xids,
                "global": not bool(xids)  # 没有 groups → 全局规则
            }

            # 分配到操作桶
            has_perm_flags = False
            for op, fld in (('read', 'perm_read'), ('write', 'perm_write'), ('create', 'perm_create'), ('unlink', 'perm_unlink')):
                if self._field_exists(r, fld):
                    if getattr(r, fld):
                        buckets[op]["clauses"].append(dict(clause))
                        has_perm_flags = True
            # 兼容老版本：没有 perm_* 字段 → 默认归到 read
            if not has_perm_flags:
                buckets['read']["clauses"].append(dict(clause))

        return buckets

    # ================== 小工具 ==================

    def _group_xmlid(self, group):
        """返回单条 res.groups 的 xmlid（无则 None），兼容不同 Odoo 版本。"""
        try:
            if hasattr(group, 'get_external_id'):
                mapping = group.get_external_id() or {}
            elif hasattr(group, 'get_xml_id'):
                mapping = group.get_xml_id() or {}
            else:
                mapping = {}
            if isinstance(mapping, dict):
                xid = mapping.get(group.id)
                return xid or None
        except Exception:
            pass
        return None


    def _field_exists(self, record_or_model, field_name):
        """判断记录或模型是否存在给定字段（兼容不同 Odoo 版本）"""
        try:
            return field_name in record_or_model._fields
        except Exception:
            return False
