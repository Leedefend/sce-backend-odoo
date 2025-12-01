# ✅ 文件路径建议：services/semantic/view/kanban_dynamic.py

from odoo import http, api
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from ..security.permission_service import PermissionService
from ..semantic.view.kanban_parser import KanbanViewParser
import json
import logging

_logger = logging.getLogger(__name__)

class KanbanDynamicService:
    def __init__(self, env):
        self.env = env
        self.user = getattr(request, '_secure_user', None) or env.user
        self.perm = PermissionService(env)

    def get_grouped_data(self, model, group_by, domain=None, limit=100):
        if not domain:
            domain = []
        filtered_domain = self.perm.apply_rules(model, domain)
        groups = self.env[model].read_group(filtered_domain, [group_by], [group_by], limit=limit)
        return [{
            "value": g[group_by][0] if isinstance(g[group_by], (list, tuple)) else g[group_by],
            "count": g.get(f"{group_by}_count", 0)
        } for g in groups]

    def update_sequence(self, model, ids, sequence_field="sequence"):
        if not self.perm.check_access(model, 'write'):
            return {"status": "error", "message": "无权限"}
        records = self.env[model].browse(ids)
        for index, record in enumerate(records):
            record.write({sequence_field: index})
        return {"status": "success"}

    def execute_action(self, action_name, context=None):
        try:
            action = self.env['ir.actions.actions']._for_xml_id(action_name)
            if not action or not self.perm.check_action_access(action.id):
                return {"status": "error", "message": "动作无效或无权限"}
            context = safe_eval(context or "{}")
            context.update(self.perm.get_context())
            return {
                "status": "success",
                "data": {
                    "type": action.type,
                    "res_model": action.res_model,
                    "res_id": context.get("active_id")
                }
            }
        except Exception as e:
            _logger.exception("执行动作失败")
            return {"status": "error", "message": str(e)}

    def quick_create(self, model, values):
        if not self.perm.check_access(model, 'create'):
            return {"status": "error", "message": "无权限"}
        new_record = self.env[model].create(values)
        return {"status": "success", "data": {"id": new_record.id}}