# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/resolvers/action_resolver.py
# 【职责】动作解析与下钻：
#   - resolve_action：通过 xmlid/id/menu 定位动作记录（含 base->specific）
#   - drill_down_action：将 server 安全探测物化为 act_window；client/url/report 原样返回
#   - materialize_server_action：执行 server.run() 并规范化返回
#   - safe_probe_server_action：在独立游标/上下文探测 server.run()，只取返回 dict，不提交副作用
import logging, odoo
from odoo import api
from odoo.http import request

_logger = logging.getLogger(__name__)

class ActionResolver:
    def __init__(self, env):
        self.env = env

    # ----------------- 外部调用入口 -----------------

    def resolve_action(self, action_id=None, action_xmlid=None, menu_id=None):
        """
        解析动作优先级：
        1) xmlid → 直接 ref；
        2) action_id → ir.actions.actions（base）→ specific（如 ir.actions.act_window）；
           若 base 找不到 specific，再穷举常见模型；
        3) menu_id → 从菜单取 action；
        """
        _logger.info("RESOLVE_ACTION_ENTER action_id=%s action_xmlid=%s menu_id=%s",
                     action_id, action_xmlid, menu_id)
        # a) xmlid 优先
        if action_xmlid:
            rec = self.env.ref(str(action_xmlid), raise_if_not_found=False)
            if rec and rec.exists():
                return rec
        # b) id：先 base，再 specific，下沉到具体类型
        if action_id:
            base = self.env['ir.actions.actions'].sudo().browse(int(action_id))
            if base and base.exists():
                a_type = getattr(base, 'type', None)
                if a_type and a_type != 'ir.actions.actions':
                    try:
                        specific = self.env[a_type].sudo().browse(int(action_id))
                        if specific and specific.exists():
                            _logger.info("DRILL_DOWN: specific %s #%s name=%s", a_type, action_id, getattr(specific,'name',None))
                            return specific
                    except Exception as e:
                        _logger.info("DRILL_DOWN: specific fail %s #%s: %s", a_type, action_id, e)
                _logger.info("DRILL_DOWN: fallback base actions #%s", action_id)
                return base
            # c) 直查常见模型（防越库/脏数据）
            for mdl in ('ir.actions.act_window','ir.actions.server','ir.actions.client','ir.actions.report','ir.actions.act_url'):
                try:
                    rec = self.env[mdl].sudo().browse(int(action_id))
                    if rec and rec.exists():
                        _logger.info("DRILL_DOWN: found directly in %s #%s", mdl, action_id)
                        return rec
                except Exception:
                    pass
        # d) 从 menu_id 回退
        if menu_id:
            menu = self.env['ir.ui.menu'].browse(int(menu_id))
            return menu.action if menu and menu.exists() else None
        return None

    def resolve_action_from_menu(self, menu, safe_server_run=True):
        """
        从菜单解析动作（含 server 下钻物化）
        """
        action = menu.action
        if not action:
            return None
        raw = self.resolve_action(action_id=action.id)
        final = self.drill_down_action(raw, safe_server_run=safe_server_run)
        return final

    def as_action_info(self, act):
        """
        将 record/dict 统一转为标准 dict 结构（便于下游装配使用）
        """
        if not act:
            return {'type': None, '_name': None, 'id': None, 'xml_id': None, 'exists': False}
        # 如果是父 actions，先下钻到具体动作
        try:
            if not isinstance(act, dict) and getattr(act, '_name', '') == 'ir.actions.actions':
                act_type = (getattr(act, 'type', None) or '').strip()
                if act_type:
                    act = self.env[act_type].sudo().browse(int(getattr(act, 'id', 0)))
        except Exception:
            pass
        # dict → 归一化
        if isinstance(act, dict):
            d = dict(act)
            d.setdefault('type', d.get('type') or d.get('_name'))
            d.setdefault('_name', d.get('_name') or d.get('type'))
            d.setdefault('exists', True)
            return d
        # recordset → 提取关键属性/外部 xmlid
        try:
            _name = getattr(act, '_name', None)
            _type = getattr(act, 'type', None) or _name
            xmlid = None
            try:
                ext = act.get_external_id()
                if ext and act.id in ext and ext[act.id]:
                    xmlid = ext[act.id]
            except Exception:
                pass
            return {
                'type': _type, '_name': _name, 'id': getattr(act, 'id', None),
                'xml_id': xmlid, 'res_model': getattr(act, 'res_model', None),
                'view_mode': getattr(act, 'view_mode', None), 'tag': getattr(act, 'tag', None),
                'exists': True,
            }
        except Exception:
            return {'type': None, '_name': None, 'id': None, 'xml_id': None, 'exists': False}

    # ----------------- 下钻 / 物化 -----------------

    def drill_down_action(self, act_or_dict, safe_server_run=False):
        """
        将动作统一下钻为可渲染的标准动作 dict：
        - act_window：直接返回；
        - server：优先映射；必要时安全探测 run() 以期返回 act_window；
        - client/url/report：原样返回交给上层。
        """
        if not act_or_dict:
            return None
        d = self.normalize_action_dict(act_or_dict)
        a_type = d.get('type')

        if a_type == 'ir.actions.act_window':
            _logger.info("FINAL_ACTION: act_window model=%s view_mode=%s", d.get('res_model'), d.get('view_mode'))
            return d

        if a_type == 'ir.actions.server':
            # 1) 自定义映射（避免执行 server 代码）
            mapped = self.map_server_to_window(d.get('id'), d.get('xml_id'))
            if mapped:
                dd = self.normalize_action_dict(mapped)
                _logger.info("FINAL_ACTION: server→mapped act_window model=%s", dd.get('res_model'))
                return dd
            # 2) 安全探测运行 server.run()（独立游标/上下文）
            if safe_server_run and d.get('id'):
                sa = self.env['ir.actions.server'].sudo().browse(int(d['id']))
                if sa.exists():
                    try:
                        res = self.safe_probe_server_action(sa)
                        if isinstance(res, dict) and res.get('type') == 'ir.actions.act_window':
                            dd = self.normalize_action_dict(res)
                            _logger.info("FINAL_ACTION: server→run act_window model=%s", dd.get('res_model'))
                            return dd
                    except Exception as e:
                        _logger.warning("FINAL_ACTION: server run fail #%s: %s", d['id'], e)
            _logger.warning("FINAL_ACTION: server not resolvable id=%s xml_id=%s", d.get('id'), d.get('xml_id'))
            return d

        # client/url/report：交由上层装配
        _logger.info("FINAL_ACTION: non-window type=%s", a_type)
        return d

    def materialize_server_action(self, info, payload, *, _depth=0, _max=2):
        """
        执行 ir.actions.server 并将返回动作“物化”为标准 dict。
        - 设置小的递归深度上限，防止 server 动作链过长；
        - 若返回仍是 server，则递归一次。
        """
        if _depth >= _max:
            _logger.warning("SERVER_ACTION_MAX_DEPTH id=%s", info.get('id')); return None
        sid = info.get('id')
        if not sid: return None
        try:
            srv = self.env['ir.actions.server'].sudo().browse(int(sid))
            if not srv or not srv.exists(): return None
            action = srv.run()
            if not action: return None
            kind = action.get('type') or action.get('_name')
            conv = {
                'type': kind, '_name': kind, 'id': action.get('id'),
                'xml_id': action.get('xml_id') or action.get('xmlid'),
                'res_model': action.get('res_model'),
                'view_mode': action.get('view_mode'),
                'tag': action.get('tag'),
                'exists': True,
            }
            if conv['type'] == 'ir.actions.server':
                return self.materialize_server_action(conv, payload, _depth=_depth+1, _max=_max)
            return conv
        except Exception as e:
            _logger.exception("SERVER_ACTION_RUN_FAILED id=%s error=%s", sid, e)
            return None

    # ----------------- 工具 -----------------

    def safe_probe_server_action(self, sa):
        """
        在独立游标与降噪上下文中运行 server.run()：
        - 只读取返回 dict；不写任何数据；
        - 若返回 act_window 且缺失 res_model，则补齐关键信息。
        """
        db = sa._cr.dbname
        with odoo.registry(db).cursor() as cr:
            base_ctx = dict(sa.env.context or {})
            base_ctx.update({
                "contract_probe": True,            # 标记为契约探测，便于 server 内部判断减少副作用
                "tracking_disable": True,          # 关闭追踪
                "mail_notify_force_send": False,   # 禁止强发送
                "mail_create_nolog": True,         # 不记录日志
            })
            env2 = api.Environment(cr, sa.env.uid, base_ctx)
            res = sa.sudo().with_env(env2).run()
            if isinstance(res, dict):
                t = res.get("type")
                _logger.info("SERVER_PROBE_OK: type=%s id=%s res_model=%s view_mode=%s",
                             t, res.get("id"), res.get("res_model"), res.get("view_mode"))
                # 若只有 id，无 res_model，则再补齐一次
                if t == "ir.actions.act_window" and res.get("id") and not res.get("res_model"):
                    act = env2["ir.actions.act_window"].sudo().browse(int(res["id"]))
                    if act.exists():
                        res = {
                            "type":"ir.actions.act_window", "id":act.id,
                            "xml_id": (act.get_xml_id() or {}).get(act.id),
                            "res_model": act.res_model, "view_mode": act.view_mode or "tree,form",
                            "domain": act.domain or [], "context": act.context or {},
                            "target": act.target, "name": act.name,
                        }
            else:
                _logger.warning("SERVER_PROBE_NONE_OR_NON_DICT: id=%s res=%s", sa.id, res)
            return res if isinstance(res, dict) else None

    def normalize_action_dict(self, act):
        """
        将 record 或 dict 统一转换为标准动作字典，确保存在基础键位。
        """
        if hasattr(act, '_name'):
            out = {
                "type": act.type, "id": act.id,
                "res_model": getattr(act, 'res_model', None),
                "view_mode": getattr(act, 'view_mode', None),
                "domain": getattr(act, 'domain', None) or [],
                "context": getattr(act, 'context', None) or {},
                "target": getattr(act, 'target', None),
                "name": getattr(act, 'name', None), "xml_id": None,
            }
            try:
                xid = act.get_xml_id()
                out["xml_id"] = xid.get(act.id) if isinstance(xid, dict) else xid
            except Exception:
                pass
            return out
        out = dict(act or {})
        out.setdefault("domain", []); out.setdefault("context", {})
        out.setdefault("view_mode", out.get("view_mode") or "tree,form")
        return out

    def map_server_to_window(self, server_id=None, server_xmlid=None):
        """
        可选：将某些 server 动作映射为固定 act_window，避免执行代码。
        - 如无定制映射，返回 None。
        """
        return None
