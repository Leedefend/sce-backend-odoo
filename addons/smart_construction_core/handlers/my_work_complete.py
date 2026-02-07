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
        activity_id = _coerce_activity_id(item_id)
        _complete_activity(self.env, source=source, activity_id=activity_id, note=note)

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


class MyWorkCompleteBatchHandler(BaseIntentHandler):
    INTENT_TYPE = "my.work.complete_batch"
    DESCRIPTION = "Complete multiple todo items from my-work list"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        source = str(params.get("source") or "").strip()
        ids = params.get("ids") if isinstance(params.get("ids"), list) else []
        note = str(params.get("note") or "").strip()
        if not ids:
            raise UserError("缺少待办 ID 列表")

        completed = []
        failed = []
        for raw_id in ids:
            try:
                activity_id = _coerce_activity_id(raw_id)
                _complete_activity(self.env, source=source, activity_id=activity_id, note=note)
                completed.append(activity_id)
            except Exception as exc:
                failed.append({"id": _safe_int(raw_id), "message": str(exc) or "failed"})

        ok = len(failed) == 0
        data = {
            "source": source,
            "success": ok,
            "reason_code": "DONE" if ok else "PARTIAL_FAILED",
            "message": "批量完成成功" if ok else "部分待办完成失败",
            "done_count": len(completed),
            "failed_count": len(failed),
            "completed_ids": completed,
            "failed_items": failed,
            "done_at": fields.Datetime.now(),
        }
        return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE}}


def _coerce_activity_id(item_id):
    if not item_id:
        raise UserError("缺少待办 ID")
    try:
        return int(item_id)
    except Exception:
        raise UserError("待办 ID 无效")


def _complete_activity(env, *, source, activity_id, note):
    if source != "mail.activity":
        raise UserError("仅支持完成 mail.activity 类型待办")
    Activity = env["mail.activity"]
    activity = Activity.browse(activity_id).exists()
    if not activity:
        raise UserError("待办不存在")
    if activity.user_id.id != env.user.id and not env.user.has_group("base.group_system"):
        raise AccessError("只能完成分配给自己的待办")
    feedback = note or "Completed from my-work."
    activity.action_feedback(feedback=feedback)


def _safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0
