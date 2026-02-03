# -*- coding: utf-8 -*-
# 文件：smart_core/app_config_engine/models/app_menu_config.py
# 职责：
# - 将 ir.ui.menu + ir.actions.* 解析为“标准化全量菜单树”（不按用户过滤），持久化为配置缓存
# - 运行态在该全量树上执行可逆裁剪（叶子/动作/ACL/白黑名单/深度/单链折叠），输出“导航契约”
# 设计要点：
# - 生成阶段使用 sudo() 拉满信息；运行阶段再按用户/过滤器裁剪
# - 轻量动作摘要（避免把巨大的 context/domain 持久化）
# - 多维唯一键（target_model+scene+company+lang）便于按场景/公司/语言分片缓存
# - 版本化与 ETag：config_hash 标识结构版本；运行态叠加 filters+uid 产生 etag

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json, hashlib, logging, re

_logger = logging.getLogger(__name__)
def _ext_id(rec):
    """安全获取记录的外部ID（module.name），没有则返回 None"""
    try:
        return (rec.get_external_id() or {}).get(rec.id)
    except Exception:
        return None

class AppMenuConfig(models.Model):
    _name = 'app.menu.config'
    _description = 'Application Menu Configuration'
    _rec_name = 'target_model'
    _order = 'scene, target_model, id'

    # —— 维度键：用于切分缓存与唯一性 —— #
    # target_model: '__all__' 表示全量导航；也可指定某模型，仅保留关联该模型的分支（精简生成量）
    target_model = fields.Char('Target Model', required=True, index=True)

    # scene：场景（如 web/pm/finance/mobile），便于按角色或端来切分导航
    scene = fields.Selection(
        [('web', 'Web'), ('pm', 'ProjectManager'), ('finance', 'Finance'), ('mobile', 'Mobile')],
        string='Scene', default='web', required=True, index=True
    )

    # company/lang：公司与语言维度（不同公司/语言菜单文本与显示策略可能不同）
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda s: s.env.company, index=True)
    lang = fields.Char('Language', default=lambda s: s.env.lang or 'zh_CN', index=True)

    # —— 版本与缓存标识 —— #
    version = fields.Integer('Version', default=1)         # 自增版本：仅当结构 hash 变化时 +1
    config_hash = fields.Char('Config Hash', readonly=True, index=True)  # 生成期全量树哈希
    etag = fields.Char('ETag', readonly=True, index=True)  # 运行期可重用（默认等于 config_hash）
    last_generated = fields.Datetime('Last Generated', readonly=True)
    is_active = fields.Boolean('Active', default=True, index=True)

    # —— 数据主体 —— #
    menu_tree = fields.Json('Menu Tree')           # 全量标准化菜单树（未按用户过滤、轻量动作摘要）
    action_index = fields.Json('Action Index')     # {action_id: {type,res_model,view_mode,view_id}} 索引，便于快速查表
    meta_info = fields.Json('Meta Info')           # 生成期统计信息（根节点数量等）

    _sql_constraints = [
        # 每个 target_model+scene+company+lang 仅存一份缓存
        ('uniq_dim', 'unique(target_model, scene, company_id, lang)',
         '每个 target_model+scene+company+lang 仅允许一条菜单配置。'),
    ]

    


    # ======================= 工具：哈希与动作摘要 =======================

    @api.model
    def _hash(self, payload_dict) -> str:
        """对给定 dict 做稳定哈希，用于版本/ETag 计算"""
        s = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def _action_summary(self, act):
        """
        将 ir.actions.* 压缩成“轻量动作摘要”，避免把 context/domain 等大字段持久化。
        仅保留路由所需关键字段（type/res_model/view_mode/view_id/views）。
        """
        if not act:
            return None

        base = {
            'id': act.id,
            'type': act._name,                     # e.g. 'ir.actions.act_window'
            'name': act.name or None,
            'res_model': getattr(act, 'res_model', None),
        }

        # 仅对 act_window 扩展视图信息（其它类型按需再扩展）
        if act._name == 'ir.actions.act_window':
            view_id = act.view_id.id if act.view_id else None
            view_mode = (act.view_mode or 'tree,form')

            # 若未指定 view_id，则选取与 view_mode 首项匹配的第一视图
            if not view_id and act.view_ids:
                first_mode = view_mode.split(',')[0]
                for av in act.view_ids:
                    if av.view_id and av.view_id.type == first_mode:
                        view_id = av.view_id.id
                        break

            base.update({
                'view_mode': view_mode,
                'view_id': view_id,
                'views': [(v.view_id.id, v.view_id.type) for v in act.view_ids] if act.view_ids else [],
            })
        return base

    def _head_from_act_window(self, act):
        """
        可选：为叶子 act_window 提供“首屏提示头”（仅提示用，不承诺与运行态上下文完全一致）。
        内容：模型/首视图类型/首视图ID/标题 + 基础 CRUD 权限探测（check_access_rights）。
        """
        if not act or act._name != 'ir.actions.act_window':
            return None

        summ = self._action_summary(act)
        perms = {}
        if summ.get('res_model') and self.env.get(summ['res_model']):
            m = self.env[summ['res_model']]
            perms = {
                'read':   m.check_access_rights('read',   raise_exception=False),
                'write':  m.check_access_rights('write',  raise_exception=False),
                'create': m.check_access_rights('create', raise_exception=False),
                'unlink': m.check_access_rights('unlink', raise_exception=False),
            }

        return {
            'model': summ.get('res_model'),
            'view_type': (summ.get('view_mode') or 'tree,form').split(',')[0],
            'view_id': summ.get('view_id'),
            'title': act.name or _('Untitled'),
            'permissions': perms,
        }

    # ======================= 生成阶段：sudo 全量标准化并持久化 =======================

    @api.model
    def _generate_from_menus(self, model_name=None, scene='web'):
        """
        从 ir.ui.menu 全量生成“标准化菜单树”，并持久化为 app.menu.config。
        - 生成阶段使用 sudo：不受用户组限制，确保元数据完整；
        - model_name=None → 生成全量（target='__all__'）；否则仅保留 res_model==model_name 的分支；
        - 仅持久化“轻量动作摘要”，避免把 context/domain 等变量态带入缓存。
        """
        def annotate(node, parent_stack):
            """补充 level/path/breadcrumbs/leaf 等衍生信息，便于运行态裁剪与前端使用。"""
            node['level'] = len(parent_stack)
            node['path_ids'] = [p['id'] for p in parent_stack] + [node['id']]
            node['breadcrumbs'] = [{'id': p['id'], 'name': p['name']} for p in parent_stack] + \
                                  [{'id': node['id'], 'name': node['name']}]
            node['leaf'] = len(node.get('children') or []) == 0
            return node

        def collect(menu, parent_stack):
            """
            递归构建标准化节点：
            - action 用 _action_summary 压缩
            - groups 保留为 id 列表，运行态再按用户过滤
            - related: 若指定 model_name，仅保留与之相关的节点/祖先
            """
            act = menu.action
            action_summary = self._action_summary(act)
            menu_xml_id = _ext_id(menu)

            node = {
                'id': menu.id,
                'menu_id': menu.id,                # 前端约定键
                'name': menu.name,
                'title': menu.name,
                'sequence': menu.sequence,
                'parent_id': menu.parent_id.id if menu.parent_id else None,
                'xml_id': menu_xml_id or None,
                'module': (menu_xml_id or '').split('.')[0] if menu_xml_id else None,
                'web_icon': getattr(menu, 'web_icon', None),
                'groups': [g.id for g in menu.groups_id],   # 运行态过滤依据
                'action': action_summary,                   # 轻量动作摘要
                'children': [],
            }

            any_child_related = False
            for c in menu.child_id.sorted(key=lambda m: (m.sequence, m.id)):
                cnode, c_related = collect(c, parent_stack + [{'id': node['id'], 'name': node['name']}])
                if c_related:
                    node['children'].append(cnode)
                    any_child_related = True

            # 自身是否“与指定模型相关”
            self_related = (model_name is None) or (action_summary and action_summary.get('res_model') == model_name)
            related = self_related or any_child_related

            # 叶子 + act_window：补首屏提示头与契约直达路由
            if node['children'] == [] and action_summary and action_summary.get('type') == 'ir.actions.act_window':
                head = self._head_from_act_window(act)
                if head:
                    node['head'] = head
                node['contract_route'] = {'subject': 'action', 'action_id': action_summary['id'], 'with_data': True}

            node = annotate(node, parent_stack)
            return node, related

        try:
            # 1) 全量抓取菜单（sudo，避免 groups 限制影响元数据完整性）
            all_menus = self.env['ir.ui.menu'].sudo().with_context(**{'ir.ui.menu.full_list': True}).search([], order='sequence,id')
            roots = all_menus.filtered(lambda m: not m.parent_id).sorted(key=lambda m: (m.sequence, m.id))

            tree, action_index = [], {}
            kept_roots = 0
            for r in roots:
                n, rel = collect(r, [])
                if rel:
                    tree.append(n)
                    kept_roots += 1

            # 2) 构建动作索引（便于服务层快速查找 action 元信息）
            def index_actions(nodes):
                for n in nodes:
                    a = n.get('action')
                    if a and a.get('id'):
                        action_index[str(a['id'])] = {
                            'type': a.get('type'),
                            'res_model': a.get('res_model'),
                            'view_mode': a.get('view_mode'),
                            'view_id': a.get('view_id'),
                        }
                    if n.get('children'):
                        index_actions(n['children'])
            index_actions(tree)

            # 3) 版本哈希：仅依赖结构（与 scene/target 组合）
            payload_for_hash = {'tree': tree, 'scene': scene, 'target': model_name or '__all__'}
            new_hash = self._hash(payload_for_hash)
            target_key = model_name or '__all__'

            # 4) upsert 到 app.menu.config（唯一维度键）
            cfg = self.sudo().search([
                ('target_model', '=', target_key),
                ('scene', '=', scene),
                ('company_id', '=', self.env.company.id),
                ('lang', '=', self.env.lang or 'zh_CN'),
            ], limit=1)

            vals = {
                'target_model': target_key,
                'scene': scene,
                'company_id': self.env.company.id,
                'lang': self.env.lang or 'zh_CN',
                'menu_tree': tree,
                'action_index': action_index,
                'config_hash': new_hash,          # 结构版号
                'etag': new_hash,                 # 运行态默认可用；真正响应会再叠加 filters 与 uid
                'last_generated': fields.Datetime.now(),
                'meta_info': {'roots': len(roots), 'kept_roots': kept_roots},
            }

            if cfg:
                if cfg.config_hash != new_hash:
                    vals['version'] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Menu config updated: %s/%s v%s", target_key, scene, cfg.version)
                else:
                    _logger.info("Menu config unchanged: %s/%s v%s", target_key, scene, cfg.version)
            else:
                vals['version'] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Menu config created: %s/%s v1", target_key, scene)

            return cfg

        except Exception:
            _logger.exception("Failed to generate menu config for %s (scene=%s)", model_name, scene)
            raise

    # ======================= 运行阶段：裁剪 + 统计 + ETag =======================

    def get_menu_contract(self, model_name=None, filter_runtime=True, check_model_acl=False, scene='web', filters=None):
        """
        输出“菜单契约”：在全量标准化树基础上，按运行态过滤策略进行可逆裁剪，返回带统计与 etag 的结构。
        参数：
          - model_name：None 取全量；否则仅使用 target=该模型 的缓存
          - filter_runtime=True：按当前用户组过滤（节点 groups 与用户 groups 求交），并可选检查模型读权限
          - check_model_acl=True：对叶子关联 res_model 的菜单做 read 权限探测（有性能代价）
          - scene：场景；与缓存维度一致
          - filters：运行态裁剪参数字典（详见下方“裁剪参数”注释）
        返回：
          {
            "nav": [... pruned tree ...],
            "meta": {
              "scene": "...",
              "filters": {...},
              "stats": {...各原因计数...},
              "version": <int>,
              "config_hash": "<str>",
              "etag": "<str>",         # 用于 If-None-Match/304
            }
          }
        """
        cfg = self._generate_from_menus(model_name=model_name, scene=scene)
        tree = cfg.menu_tree or []
        filters = filters or {}

        # —— 用户组缓存 —— #
        uid_groups = set(self.env.user.groups_id.ids)

        def allowed_by_groups(node):
            """groups 为空表示公开；否则用户组与节点 groups 至少命中一个"""
            g = set(node.get('groups') or [])
            return (not g) or bool(uid_groups & g)

        def allowed_by_acl(node):
            """
            可选的模型读权限检测（仅对 act_window 的叶子菜单有效）：
            - 只检查 check_access_rights('read')，不做 search()，避免对大表产生性能压力
            - 注意：这不是 ir.rule 的完整模拟；只作为“是否值得显示”的二次保险
            """
            if not check_model_acl:
                return True
            a = node.get('action') or {}
            m = a.get('res_model')
            if not m or m not in self.env:
                return True
            try:
                return bool(self.env[m].check_access_rights('read', raise_exception=False))
            except Exception:
                return False

        # —— 裁剪参数（默认即“开箱即瘦”） —— #
        # leaf_only：仅保留可点击叶子（目录只在有有用子孙时作为过桥保留）
        # hide_without_action：无动作的纯目录若无有用后代则剔除
        # only_act_window：仅保留 act_window 动作（过滤掉 server/action_url 等）
        # hide_unreadable_model：读权限不可用的模型叶子剔除（需注意性能）
        # model_whitelist：模型白名单（正则数组），不命中则剔除
        # exclude_modules：模块黑名单（按菜单 xml_id 的 module 前缀）
        # max_depth：深度上限（超过则剔除）
        # prune_single_chain：单子节点目录折叠（减少“套娃”）
        leaf_only = bool(filters.get('leaf_only', True))
        hide_without_action = bool(filters.get('hide_without_action', True))
        only_act_window = bool(filters.get('only_act_window', True))
        hide_unreadable_model = bool(filters.get('hide_unreadable_model', True))
        model_whitelist = [re.compile(x) for x in filters.get('model_whitelist', [r'^project\.', r'^smart_', r'^oa\.'])]
        exclude_modules = set(filters.get('exclude_modules', []))
        max_depth = int(filters.get('max_depth', 3)) if filters.get('max_depth', 3) else 0
        prune_single_chain = bool(filters.get('prune_single_chain', True))

        # —— 统计计数：便于观察调参效果 —— #
        stats = {"total": 0, "kept": 0, "no_groups": 0, "no_action": 0, "not_leaf": 0,
                 "not_act_window": 0, "black_module": 0, "no_model": 0, "model_not_whitelist": 0,
                 "unreadable": 0, "over_depth": 0, "pruned_empty_folder": 0, "folded_single_chain": 0}

        def rx_match_any(rx_list, s):
            return s and any(r.search(s) for r in rx_list)

        def prune(node, depth=1):
            """
            运行态裁剪核心：
            - 先处理 groups/深度等前置条件
            - 针对目录节点：在“保留自身”与“折叠保留子孙”之间做取舍
            - 针对叶子节点：动作类型、模块黑名单、模型白名单、读权限等判定
            """
            stats["total"] += 1
            children = node.get('children') or []
            action = node.get('action') or {}
            module = node.get('module')
            res_model = action.get('res_model')

            # A. groups（用户组可见性）
            if filter_runtime and not allowed_by_groups(node):
                stats["no_groups"] += 1
                return None

            # B. 深度限制
            if max_depth and depth > max_depth:
                stats["over_depth"] += 1
                return None

            # C. 纯目录（无动作）处理：尝试保留其“有用的后代”，否则剪
            is_leaf = len(children) == 0
            if hide_without_action and not action:
                kept_children = [c for c in (prune(x, depth+1) for x in children) if c]
                if not kept_children:
                    stats["no_action"] += 1
                    return None
                node = dict(node); node['children'] = kept_children
                if prune_single_chain and len(kept_children) == 1:
                    stats["folded_single_chain"] += 1
                    return kept_children[0]   # 折叠“单链目录”
                stats["kept"] += 1
                return node

            # D. 非叶子但要求 leaf_only：同样只保留其“有用后代”，必要时折叠
            if leaf_only and not is_leaf:
                kept_children = [c for c in (prune(x, depth+1) for x in children) if c]
                if not kept_children:
                    stats["not_leaf"] += 1
                    return None
                node = dict(node); node['children'] = kept_children
                if prune_single_chain and len(kept_children) == 1 and not action:
                    stats["folded_single_chain"] += 1
                    return kept_children[0]
                stats["kept"] += 1
                return node

            # E. 动作类型限制：仅保留 act_window
            if only_act_window and action and action.get('type') != 'ir.actions.act_window':
                stats["not_act_window"] += 1
                return None

            # F. 模块黑名单（按 xml_id 前缀判定）
            if module and module in exclude_modules:
                stats["black_module"] += 1
                return None

            # G. 叶子模型过滤（白名单 + 可读权限）
            if action and action.get('type') == 'ir.actions.act_window':
                if not res_model:
                    stats["no_model"] += 1
                    return None
                if model_whitelist and not rx_match_any(model_whitelist, res_model):
                    stats["model_not_whitelist"] += 1
                    return None
                if hide_unreadable_model and not allowed_by_acl(node):
                    stats["unreadable"] += 1
                    return None

            # H. 递归孩子（对带动作的父节点仍可保留其“有用后代”）
            if children:
                kept_children = [c for c in (prune(x, depth+1) for x in children) if c]
                node = dict(node); node['children'] = kept_children
                if hide_without_action and not action and not kept_children:
                    stats["pruned_empty_folder"] += 1
                    return None

            stats["kept"] += 1
            return node

        # —— 从根开始裁剪 —— #
        out = []
        for root in tree:
            r = prune(root, 1)
            if r:
                out.append(r)

        # —— 运行态 ETag：基于结构版号+filters+uid 计算（不同用户/不同过滤组合相互独立缓存） —— #
        runtime_etag = self._hash({'base': cfg.config_hash, 'filters': filters, 'uid': self.env.uid})

        return {
            'nav': out,
            'meta': {
                'scene': scene,
                'filters': filters,
                'stats': stats,
                'version': cfg.version,
                'config_hash': cfg.config_hash,
                'etag': runtime_etag,
            }
        }
