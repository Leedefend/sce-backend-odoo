# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/chatter_post.py
from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError

class ChatterPostHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.post"
    DESCRIPTION = "Post a chatter message (mail.thread)"

    def run(self):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") or params.get("record_id")
        body = params.get("body")
        subject = params.get("subject")

        if not model or not res_id or not body:
            raise UserError("缺少参数 model/res_id/body")

        self.env[model].check_access_rights("write")
        record = self.env[model].browse(int(res_id))
        if not record.exists():
            raise UserError("记录不存在")
        record.check_access_rule("write")

        if not hasattr(record, "message_post"):
            raise AccessError("模型不支持 chatter")

        message = record.message_post(body=body, subject=subject)
        return {
            "result": {
                "message_id": message.id,
            }
        }, {}
