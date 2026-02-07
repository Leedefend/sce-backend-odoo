# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError


class MyWorkCompleteHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.complete"
    DESCRIPTION = "Complete a todo item from my-work list"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        source = str(params.get("source") or "").strip()
        item_id = params.get("id")
        note = str(params.get("note") or "").strip()
        if source != "mail.activity":
            raise UserError("仅支持完成 mail.activity 类型待办")
        if not item_id:
            raise UserError("缺少待办 ID")
        try:
            activity_id = int(item_id)
        except Exception:
            raise UserError("待办 ID 无效")

        Activity = self.env["mail.activity"]
        activity = Activity.browse(activity_id).exists()
        if not activity:
            raise UserError("待办不存在")
        if activity.user_id.id != self.env.user.id and not self.env.user.has_group("base.group_system"):
            raise AccessError("只能完成分配给自己的待办")

        # action_done 会自动写入已完成反馈
        feedback = note or "Completed from my-work."
        activity.action_feedback(feedback=feedback)

        return {
            "ok": True,
            "data": {
                "id": activity_id,
                "source": source,
                "success": True,
                "reason_code": "DONE",
                "message": "待办已完成",
                "done_at": fields.Datetime.now(),
            },
            "meta": {"intent": self.INTENT_TYPE},
        }
