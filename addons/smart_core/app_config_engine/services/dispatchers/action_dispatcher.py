# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/dispatchers/action_dispatcher.py
# 【职责】subject=action/model/operation 的统一分发处理：
#   - model：直接按模型与视图类型装配页面契约
#   - operation：execute/onchange/validate/report 四类网关/校验/报表
#   - action：解析动作类型 → act_window/client/server/url/report
import logging
from odoo.addons.smart_core.app_config_engine.services.resolvers.action_resolver import ActionResolver
from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler
from odoo.addons.smart_core.app_config_engine.services.assemblers.client_url_report import ClientUrlReportAssembler

_logger = logging.getLogger(__name__)

class ActionDispatcher:
    def __init__(self, env, su_env):
        self.env = env
        self.su_env = su_env
        self.resolver = ActionResolver(env)

    def dispatch(self, p):
        subject = p.get('subject')

        # ---- 1) model：直接按模型构造页面契约
        if subject == 'model':
            if not p.get("model"):
                raise ValueError("model subject 需要提供 model 名")
            p["view_types"] = PageAssembler.normalize_view_types(p.get('view_type') or 'tree,form')
            return PageAssembler(self.env, self.su_env).assemble_page_contract(p)

        # ---- 2) operation：execute/onchange/validate/report
        if subject == 'operation':
            op = (p.get("op") or "").lower()
            if op == 'execute':
                gw = self.env['app.action.gateway']  # 走用户权限
                res = gw.run_object_method(p["model"], p.get("method"), p.get("record_ids"),
                                           p.get("args"), p.get("kwargs"), p.get("action_key"))
                return {"result": res}, {"op": 1}
            if op == 'onchange':
                gw = self.env['app.action.gateway']
                res = gw.run_onchange(p["model"], p.get("values") or {}, p.get("changed") or {})
                return {"result": res}, {"op": 1}
            if op == 'validate':
                v = self.env['app.validator.config'].sudo()
                res = v.preflight_check(p["model"], p.get("values") or {})
                return {"result": res}, {"op": 1}
            if op == 'report':
                reps = self.env['app.report.config'].sudo()\
                        ._generate_from_reports(p["model"])\
                        .get_report_contract(filter_runtime=True)
                return {"reports": reps}, {"report": len(reps)}
            raise ValueError("operation 仅支持：execute/onchange/validate/report")

        # ---- 3) action：解析并下钻动作
        aid    = p.get('action_id') or p.get('id') or None
        axmlid = p.get('action_xmlid') or p.get('action_xml_id') or None
        amid   = p.get('menu_id') or None

        info = self.resolver.as_action_info(self.resolver.resolve_action(aid, axmlid, amid))
        atype = (info.get('type') or info.get('_name') or '').strip()
        _logger.info("ACTION_RESOLVED action_id=%s action_xmlid=%s menu_id=%s -> %s",
                     aid, axmlid, amid, info)

        # act_window：必须有 res_model
        if atype == 'ir.actions.act_window':
            if not info.get('res_model'):
                return ClientUrlReportAssembler(self.env).assemble_diagnostic_contract(p, info, issue="窗口动作必须配置 res_model")
            p['model'] = info.get('res_model')
            p['view_types'] = PageAssembler.normalize_view_types(info.get('view_mode') or p.get('view_type') or 'tree,form')
            if amid:
                # 把 active_menu_id 放入上下文，利于 domain/context 计算
                ctx = p.setdefault('context', {})
                ctx.setdefault('active_menu_id', amid)
            return PageAssembler(self.env, self.su_env).assemble_page_contract(p, action=info)

        # client：不需要模型
        if atype == 'ir.actions.client':
            return ClientUrlReportAssembler(self.env).assemble_client_contract(p, info)

        # server：先执行物化；若失败 → 诊断契约
        if atype == 'ir.actions.server':
            materialized = self.resolver.materialize_server_action(info, p)
            if not materialized:
                return ClientUrlReportAssembler(self.env).assemble_diagnostic_contract(p, info, issue="服务端动作执行失败或未返回可显示的结果")
            return self._dispatch_resolved(materialized, p)

        # url/report：分别走专用装配
        if atype == 'ir.actions.act_url':
            return ClientUrlReportAssembler(self.env).assemble_url_contract(p, info)

        if atype == 'ir.actions.report':
            return ClientUrlReportAssembler(self.env).assemble_report_contract(p, info)

        # 其他未知类型：统一诊断
        _logger.warning("UNSUPPORTED_ACTION_TYPE action_id=%s type=%s", aid, atype)
        return ClientUrlReportAssembler(self.env).assemble_diagnostic_contract(p, info, issue=f"不支持的动作类型: {atype}")

    def _dispatch_resolved(self, info, p):
        """
        给已物化的 server 动作再次分发（仅支持 act_window/client）
        """
        atype = (info.get('type') or info.get('_name') or '').strip()
        if atype == 'ir.actions.act_window':
            p['model'] = info.get('res_model') or p.get('model')
            p['view_types'] = PageAssembler.normalize_view_types(info.get('view_mode') or p.get('view_type') or 'tree,form')
            return PageAssembler(self.env).assemble_page_contract(p, action=info)
        if atype == 'ir.actions.client':
            return ClientUrlReportAssembler(self.env, self.su_env).assemble_client_contract(p, info)
        raise ValueError(f"server 动作返回了不支持的类型：{atype}")
