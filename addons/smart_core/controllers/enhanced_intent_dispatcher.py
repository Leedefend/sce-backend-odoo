# smart_core/controllers/enhanced_intent_dispatcher.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import uuid

class IntentDispatcher(http.Controller):
    @http.route('/api/v1/intent_enhanced', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_intent(self, **kwargs):
        trace_id = uuid.uuid4().hex[:12]
        return request.make_json_response(
            {
                "ok": False,
                "error": {
                    "code": 410,
                    "message": "intent_enhanced endpoint is decommissioned; use /api/v1/intent",
                },
                "code": 410,
                "meta": {"trace_id": trace_id},
            },
            status=410,
        )
    
    @http.route('/api/v2/intent', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_enhanced_intent(self, **kwargs):
        """增强意图处理端点（decommissioned）"""
        trace_id = uuid.uuid4().hex[:12]
        return request.make_json_response(
            {
                "ok": False,
                "error": {
                    "code": 410,
                    "message": "enhanced intent router is decommissioned; use /api/v1/intent",
                },
                "code": 410,
                "meta": {"trace_id": trace_id},
            },
            status=410,
        )
