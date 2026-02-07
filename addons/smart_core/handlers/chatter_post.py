# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/chatter_post.py
import re
from typing import List

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler

class ChatterPostHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.post"
    DESCRIPTION = "Post a chatter message (mail.thread)"

    def handle(self, payload=None, ctx=None):
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

        mention_partner_ids = self._resolve_mentions(str(body or ""))
        post_kwargs = {"body": body, "subject": subject}
        if mention_partner_ids:
            post_kwargs["partner_ids"] = mention_partner_ids

        message = record.message_post(**post_kwargs)
        return {
            "result": {
                "message_id": message.id,
                "success": True,
                "reason_code": "OK",
                "message": "Comment posted",
                "mentioned_partner_ids": mention_partner_ids,
            }
        }, {}

    def _resolve_mentions(self, body: str) -> List[int]:
        tokens = set(re.findall(r"@([A-Za-z0-9_.-]{2,64})", body or ""))
        if not tokens:
            return []
        users = self.env["res.users"].search([("login", "in", list(tokens))], limit=20)
        partner_ids = users.mapped("partner_id").ids
        return [int(pid) for pid in partner_ids if pid]
