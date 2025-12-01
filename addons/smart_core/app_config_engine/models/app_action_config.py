# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json, hashlib, logging

_logger = logging.getLogger(__name__)

try:
    # 解析视图按钮用（若环境缺 lxml，可按需降级）
    from lxml import etree
except Exception:
    etree = None


class AppActionConfig(models.Model):
    _name = 'app.action.config'
    _description = 'Application Action Configuration'
    _rec_name = 'label'
    _order = 'model'

    # ========= 基础信息（按模型聚合一份）=========
    name = fields.Char('Action Name', required=True)      # 记录名（例如 action_<model>）
    label = fields.Char('Label', required=True)           # 显示（例如 'Actions for sale.order'）
    model = fields.Char('Model', required=True, index=True)  # 关联模型（被聚合的“当前模型”）

    # 主类型字段保留，但真正的动作清单放到 actions_def
    action_type = fields.Selection([
        ('object', 'Object Method'),  # 调用服务器方法（按钮）
        ('action', 'Window Action'),  # 跳转到窗口（act_window）
        ('stat',   'Stat Button'),    # 统计按钮（视图上的 oe_stat_button）
        ('smart',  'Smart Button'),   # 智能按钮（同上/或移动端区域）
        ('url',    'External URL')    # 外部链接
    ], string='Action Type', default='action')

    # ========= 版本/缓存 =========
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # ========= 权限与扩展 =========
    groups_id = fields.Many2many('res.groups', string='Access Groups')  # 该聚合记录本身的可见组，通常不启用
    meta_info = fields.Json('Meta Info')   # 预留
    is_active = fields.Boolean('Active', default=True)

    # ========= 标准化动作清单（契约直用）=========
    actions_def = fields.Json('Actions Definition', help="""
    标准动作契约（列表）：
    [
      {
        "key": "open_sale_order",
        "label": "销售订单",
        "kind": "open",                     # open|object|server|url|report
        "model": "sale.order",              # 当前模型
        "target_model": "sale.order",       # 目标模型（open 时）
        "level": "toolbar",                 # toolbar|header|row|smart
        "selection": "none",                # none|single|multi
        "groups": [1,3],
        "groups_xmlids": ["base.group_user"],
        "visible": {"domain": [], "states": []},  # 可见性提示（前端可选用）
        "intent": "open",                   # open|execute|url
        "params": {"refresh": "list"},      # 附加参数（刷新策略/二次确认/对话框尺寸等）
        "payload": {
          "action_id": 123, "xml_id": "sale.action_orders",
          "view_mode": "tree,form", "view_id": 456,
          "context_raw": "{'search_default_my':1}", "domain_raw": "[]"
        }
      },
      ...
    ]
    """)

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条动作聚合配置（model 唯一）。'),
    ]

    # ================== 生成（聚合 Odoo 各类动作） ==================

    @api.model
    def _generate_from_ir_actions(self, model_name):
        """
        为“某个模型”聚合标准化动作清单，并持久化（不变更不涨版）。
        覆盖：
        - ir.actions.act_window（打开窗口）
        - ir.ui.view 上的按钮（type="object"|"action"，含 smart/stat)
        - ir.actions.server（服务端动作）
        - ir.actions.act_url（若存在绑定模型）
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            # 1) 各来源扫描（使用 sudo() 取全量定义）
            actions = []
            actions += self._scan_window_actions(model_name)
            actions += self._scan_view_buttons(model_name)     # 包含 object/smart/stat/行内按钮等
            actions += self._scan_server_actions(model_name)
            actions += self._scan_url_actions(model_name)

            # 2) 去重与稳定排序（按 key 去重；排序保证哈希稳定）
            uniq = {}
            for a in actions:
                uniq[a['key']] = a
            actions_def = sorted(uniq.values(), key=lambda x: (x.get('level') or '', x.get('label') or '', x.get('key') or ''))

            # 3) 计算哈希（仅依赖 actions_def）
            payload = json.dumps(actions_def, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            # 4) 写库（不变更不涨版）
            cfg = self.sudo().search([('model', '=', model_name)], limit=1)
            vals = {
                "name": f"action_{model_name}",
                "label": f"Actions for {model_name}",
                "model": model_name,
                "actions_def": actions_def,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Action config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Action config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Action config created for %s → version 1", model_name)

            return cfg

        except Exception as e:
            _logger.exception("Failed to generate action config for %s", model_name)
            raise

    # ================== 各来源扫描（内部） ==================

    def _scan_window_actions(self, model_name):
        """扫描 ir.actions.act_window（打开窗口类），统一为 kind='open'"""
        res = []
        Act = self.env['ir.actions.act_window'].sudo()
        acts = Act.search([('res_model', '=', model_name)])
        for a in acts:
            key = a.xml_id or f"aw_{a.id}"
            entry = {
                "key": key,
                "label": a.name or key,
                "kind": "open",
                "model": model_name,
                "target_model": a.res_model,
                "level": "toolbar",          # 缺省放工具栏；具体布局交给 view.config
                "selection": "none",
                "groups": [], "groups_xmlids": [],
                "visible": {"domain": [], "states": []},
                "intent": "open",
                "params": {"target": getattr(a, 'target', 'current')},
                "payload": {
                    "action_id": a.id,
                    "xml_id": a.xml_id or None,
                    "view_mode": a.view_mode or 'tree,form',
                    "view_id": a.view_id.id if a.view_id else None,
                    "context_raw": a.context or None,
                    "domain_raw": getattr(a, 'domain', None),
                    "help": a.help or None,
                }
            }
            res.append(entry)
        return res

    def _scan_server_actions(self, model_name):
        """扫描 ir.actions.server（服务端动作），统一为 kind='server'"""
        res = []
        Srv = self.env['ir.actions.server'].sudo()
        # 绑定到该模型或通用（binding_model_id 为空的视情况纳入）
        srvs = Srv.search(['|', ('binding_model_id.model', '=', model_name), ('model_id.model', '=', model_name)])
        for s in srvs:
            key = s.xml_id or f"srv_{s.id}"
            label = s.name or key
            # 选择约束：大多数 server action 允许多选；若 state 特殊可改
            selection = "multi"
            entry = {
                "key": key,
                "label": label,
                "kind": "server",
                "model": model_name,
                "target_model": model_name,
                "level": "toolbar",
                "selection": selection,
                "groups": [g.id for g in s.groups_id],
                "groups_xmlids": self._groups_xmlids(s.groups_id),
                "visible": {"domain": [], "states": []},
                "intent": "execute",
                "params": {"server_state": s.state},  # code/obj_create/obj_write/multi等
                "payload": {
                    "server_action_id": s.id,
                    "xml_id": s.xml_id or None
                }
            }
            res.append(entry)
        return res

    def _scan_url_actions(self, model_name):
        """扫描 ir.actions.act_url（若版本支持绑定模型），统一为 kind='url'"""
        res = []
        if not self._model_exists('ir.actions.act_url'):
            return res
        Url = self.env['ir.actions.act_url'].sudo()
        try:
            urls = Url.search([('binding_model_id.model', '=', model_name)])
        except Exception:
            # 某些版本没有 binding_model_id，跳过
            urls = Url.browse([])
        for u in urls:
            key = u.xml_id or f"url_{u.id}"
            entry = {
                "key": key,
                "label": u.name or key,
                "kind": "url",
                "model": model_name,
                "target_model": None,
                "level": "toolbar",
                "selection": "none",
                "groups": [], "groups_xmlids": [],
                "visible": {"domain": [], "states": []},
                "intent": "url",
                "params": {"target": getattr(u, 'target', 'new')},
                "payload": {
                    "url": u.url,
                    "action_id": u.id,
                    "xml_id": u.xml_id or None
                }
            }
            res.append(entry)
        return res

    def _scan_view_buttons(self, model_name):
        """
        扫描视图上的按钮（form/tree/kanban）：
        - <button type="object" name="method"> -> kind='object'
        - <button type="action" name="ir.actions.act_window xmlid or id"> -> kind='open'
        - class 含 oe_stat_button/oe_stat_info -> level='smart'/'stat'
        - row-level（tree view 中） -> level='row'
        说明：
        - 仅抽“定义层”，不做权限/域求值；groups 用视图按钮的 groups 属性解析为 xmlids→ids
        """
        res = []
        View = self.env['ir.ui.view'].sudo()
        # 仅扫描当前模型绑定的主视图
        views = View.search([('model', '=', model_name)])
        for v in views:
            try:
                arch = v.arch_db or ''
                if not arch:
                    continue
                if etree is None:
                    continue  # 环境缺 lxml 时略过（可改为简单字符串查找）
                root = etree.fromstring(arch.encode('utf-8'))
                # 找所有 button
                for btn in root.xpath('.//button'):
                    b_type = btn.get('type') or 'object'
                    name = btn.get('name') or ''
                    string = btn.get('string') or btn.get('title') or name
                    classes = (btn.get('class') or '').split()
                    groups_attr = btn.get('groups') or ''  # CSV xmlids
                    states = (btn.get('states') or '').split(',')
                    context_raw = btn.get('context') or None

                    # 粗判所在层级：在 tree 节点下且有 class o_list_button_* 视为 row；含 oe_stat_button 视为 smart/stat
                    level = 'header'
                    p = btn.getparent()
                    while p is not None:
                        tag = p.tag
                        if tag == 'tree':
                            level = 'row'
                            break
                        if tag == 'form':
                            level = 'header'
                            break
                        if tag == 'kanban':
                            level = 'header'
                            break
                        p = p.getparent()
                    if 'oe_stat_button' in classes or 'oe_stat_info' in classes:
                        level = 'smart'

                    # 解析 groups
                    groups_ids, groups_xmlids = self._parse_groups_attr(groups_attr)

                    # 选择约束：object 默认支持 multi；header 的部分按钮可能只支持 single（这里给提示位）
                    selection = 'multi' if level in ('row',) else 'single'

                    if b_type == 'object':
                        # 调用模型方法
                        key = f"obj_{name}" if string == name else f"obj_{name}_{string}"
                        entry = {
                            "key": key,
                            "label": string or name,
                            "kind": "object",
                            "model": model_name,
                            "target_model": model_name,
                            "level": level,
                            "selection": selection,
                            "groups": groups_ids,
                            "groups_xmlids": groups_xmlids,
                            "visible": {"domain": [], "states": [s for s in states if s]},
                            "intent": "execute",
                            "params": {"confirm": False},   # 可在 view.config 中细化
                            "payload": {
                                "method": name,
                                "context_raw": context_raw,
                                "view_id": v.id,
                                "view_xmlid": v.key or None
                            }
                        }
                        res.append(entry)

                    elif b_type == 'action':
                        # 跳转/执行动作（act_window/其他）
                        key = f"act_{name}" if string == name else f"act_{name}_{string}"
                        entry = {
                            "key": key,
                            "label": string or name,
                            "kind": "open",                 # 先按 open 归类，服务层可二次识别
                            "model": model_name,
                            "target_model": None,
                            "level": level,
                            "selection": selection if level == 'row' else 'none',
                            "groups": groups_ids,
                            "groups_xmlids": groups_xmlids,
                            "visible": {"domain": [], "states": [s for s in states if s]},
                            "intent": "open",
                            "params": {},
                            "payload": {
                                # name 可能是 xmlid 或 数字 id；服务层据此解析
                                "ref": name,
                                "context_raw": context_raw,
                                "view_id": v.id,
                                "view_xmlid": v.key or None
                            }
                        }
                        res.append(entry)
            except Exception:
                _logger.exception("Parse view buttons failed for view %s (%s)", v.id, model_name)
                continue
        return res

    # ================== 标准化输出 ==================

    def get_action_contract(self, filter_runtime=True, check_model_acl=False):
        """
        返回标准化动作契约列表。
        - filter_runtime=True：按当前用户组过滤不可见动作（groups 有交集或为空 → 可见）
        - check_model_acl=True：对 object/open 等再做一次 read/write ACL 粗校（可选，成本略高）
        """
        self.ensure_one()
        actions = list(self.actions_def or [])
        if not filter_runtime and not check_model_acl:
            return actions

        user_groups = set(self.env.user.groups_id.ids)

        def allowed_by_groups(a):
            ag = set(a.get('groups') or [])
            return (not ag) or bool(ag & user_groups)

        def allowed_by_acl(a):
            if not check_model_acl:
                return True
            kind = a.get('kind')
            mdl = a.get('model')
            if not mdl or mdl not in self.env:
                return True
            try:
                if kind in ('open', 'url', 'server'):
                    # 读权限足够
                    return bool(self.env[mdl].check_access_rights('read', raise_exception=False))
                if kind == 'object':
                    # 执行模型方法，多数情况下需要 write；这里取 write 作粗校
                    return bool(self.env[mdl].check_access_rights('write', raise_exception=False))
            except Exception:
                return False
            return True

        filtered = []
        for a in actions:
            if allowed_by_groups(a) and allowed_by_acl(a):
                filtered.append(a)
        return filtered

    # ================== 工具方法 ==================

    def _parse_groups_attr(self, groups_attr):
        """把视图上的 groups CSV(xmlid,xmlid2) 解析为 (ids, xmlids)"""
        if not groups_attr:
            return [], []
        xids = [g.strip() for g in groups_attr.split(',') if g.strip()]
        ids = []
        for xid in xids:
            try:
                rec = self.env.ref(xid, raise_if_not_found=False)
                if rec and rec._name == 'res.groups':
                    ids.append(rec.id)
            except Exception:
                continue
        return ids, xids

    def _groups_xmlids(self, groups):
        """把 groups 记录集转 xmlids 列表"""
        out = []
        for g in groups:
            try:
                pair = g.get_xml_id()
                if isinstance(pair, tuple) and pair[1]:
                    out.append(pair[1])
            except Exception:
                continue
        return out

    def _model_exists(self, name):
        try:
            self.env[name]
            return True
        except Exception:
            return False
