# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields
from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
from ..core.project_context import (
    project_scope_denied_response,
    record_in_project_scope,
    selected_project_id_from_context,
)
from ..utils.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)


class ChatterActivityScheduleHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.activity.schedule"
    DESCRIPTION = "Schedule a mail activity for a record"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "Scheduling an activity creates a collaboration todo"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") or params.get("record_id")
        summary = str(params.get("summary") or "").strip()
        note = str(params.get("note") or "").strip()
        deadline_raw = str(params.get("date_deadline") or "").strip()
        user_id = _coerce_int(params.get("user_id")) or self.env.user.id
        activity_type_xmlid = str(params.get("activity_type_xmlid") or "mail.mail_activity_data_todo").strip()
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or not res_id or not summary:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/summary", 400, trace_id)

        try:
            if model not in self.env:
                return self._failure(REASON_NOT_FOUND, "模型不存在", 404, trace_id)
            record = self.env[model].browse(int(res_id)).exists()
            if not record:
                return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
            current_project_id = selected_project_id_from_context(params, self.context if isinstance(self.context, dict) else {})
            in_scope, scope_meta = record_in_project_scope(self.env[model], int(record.id), current_project_id)
            if not in_scope:
                return project_scope_denied_response(scope_meta)
            self.env[model].check_access_rights("write")
            record.check_access_rule("write")

            Activity = self.env.get("mail.activity")
            IrModel = self.env.get("ir.model")
            if Activity is None or IrModel is None:
                return self._failure(REASON_NOT_FOUND, "活动模型不存在", 404, trace_id)
            model_rec = IrModel.sudo().search([("model", "=", model)], limit=1)
            if not model_rec:
                return self._failure(REASON_NOT_FOUND, "模型元数据不存在", 404, trace_id)
            activity_type = self.env.ref(activity_type_xmlid, raise_if_not_found=False)
            if not activity_type:
                activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
            if not activity_type:
                return self._failure(REASON_NOT_FOUND, "活动类型不存在", 404, trace_id)

            activity = Activity.create(
                {
                    "res_model_id": model_rec.id,
                    "res_id": record.id,
                    "user_id": user_id,
                    "activity_type_id": activity_type.id,
                    "summary": summary,
                    "note": note,
                    "date_deadline": _coerce_date(deadline_raw, self.env.user),
                }
            )
            return {
                "ok": True,
                "data": {
                    "result": {
                        "activity_id": activity.id,
                        "success": True,
                        "reason_code": REASON_OK,
                        "message": "Activity scheduled",
                    }
                },
                "meta": {"trace_id": trace_id},
            }
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限安排活动", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "安排活动失败", 500, trace_id)

    def _failure(self, reason_code: str, message: str, status_code: int, trace_id: str):
        return {
            "ok": False,
            "error": {
                "code": reason_code,
                "message": message,
                "reason_code": reason_code,
                **failure_meta_for_reason(reason_code),
            },
            "data": {"result": {"success": False, "reason_code": reason_code, "message": message}},
            "code": status_code,
            "meta": {"trace_id": trace_id},
        }


def _coerce_int(value):
    try:
        parsed = int(value)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _coerce_date(value, user):
    if not value:
        return fields.Date.context_today(user)
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except Exception:
        return fields.Date.context_today(user)
