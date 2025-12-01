# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/dispatchers/menu_dispatcher.py
# 【职责】subject=menu：根据 menu_id 解析可用动作；若当前菜单无动作，BFS 向下找第一个可用叶子；
#       - act_window → 页面契约
#       - client → 客户端契约
#       - 无可用动作 → 空契约提示
import logging
from odoo.http import request
from odoo import _
from ..resolvers.action_resolver import ActionResolver
from ..assemblers.page_assembler import PageAssembler
from ..assemblers.client_url_report import ClientUrlReportAssembler

_logger = logging.getLogger(__name__)

class MenuDispatcher:
    def __init__(self, env, su_env):
        self.env = env
        self.su_env = su_env
        self.resolver = ActionResolver(env)

    def open_menu(self, p):
        # 1) 参数校验
        menu_id = p.get("menu_id") or p.get("id")
        if not menu_id:
            raise ValueError("menu subject 需要提供 menu_id")
        menu = self.su_env['ir.ui.menu'].browse(int(menu_id))
        if not menu.exists():
            raise ValueError(f"menu {menu_id} 不存在")

        # 2) 解析当前菜单的动作（含 server 下钻）
        act = self.resolver.resolve_action_from_menu(menu, safe_server_run=True)
        resolved_menu = menu

        # 3) 若无动作，BFS 向下搜索第一个可点击叶子
        if not act:
            resolved_menu, act = self._find_first_actionable_leaf(menu)
            if not act:
                # 返回一个“可渲染的空契约”，前端展示友好提示
                data = {
                    "head": {"title": menu.name or "未命名", "model": None, "view_type": "none"},
                    "ui": {"i18n": {"empty_state": "该菜单无可用动作，请联系管理员配置。"}},
                    "data": {"type": "records", "records": [], "next_offset": None}
                }
                return data, {"menu": int(menu.write_date.timestamp()) if menu.write_date else 1}

        # 4) 根据动作类型装配契约
        p["action_id"] = act.get('id')
        if act.get('type') == 'ir.actions.client':
            data, versions = ClientUrlReportAssembler(self.env).assemble_client_contract(p, act)
        else:
            p["model"] = act.get('res_model')
            p["view_types"] = PageAssembler.normalize_view_types(act.get('view_mode') or 'tree,form')
            data, versions = PageAssembler(self.env).assemble_page_contract(p, action=act)

        # 5) 补充溯源信息（原菜单/解析到的菜单/动作）
        versions.update({
            "menu_origin": int(menu.id),
            "menu_resolved": int(resolved_menu.id),
            "action": int(act.get('id') or 0),
        })
        return data, versions

    def _find_first_actionable_leaf(self, root_menu):
        """
        自顶向下 BFS：找到第一个“对当前用户可见且可读”的叶子动作。
        - 菜单可见性：用用户 env 检查 menu.exists()
        - 客户端动作：不要求模型权限
        - 窗口动作：检查 res_model 的 read 权限
        """
        queue = [root_menu]; seen = set()
        user_env = self.env
        while queue:
            m = queue.pop(0)
            if m.id in seen: continue
            seen.add(m.id)

            act = self.resolver.resolve_action_from_menu(m, safe_server_run=True)
            if act:
                try:
                    if not user_env['ir.ui.menu'].browse(m.id).exists():
                        raise Exception("menu invisible for user")
                    if act.get('type') == 'ir.actions.client':
                        return m, act
                    model_name = act.get('res_model')
                    if model_name:
                        user_env[model_name].check_access_rights('read')
                    return m, act
                except Exception:
                    # 无权限则忽略，继续下层
                    pass

            children = self.su_env['ir.ui.menu'].search([('parent_id', '=', m.id)], order='sequence,id')
            queue.extend(children)
        return None, None
