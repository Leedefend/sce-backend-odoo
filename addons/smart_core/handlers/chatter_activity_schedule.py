# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields
from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import record_scope_denied_response
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import project_scope_denied_response as record_scope_denied_response
try:
    from ..core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import record_in_project_scope
    try:
        from ..core.project_context import selected_record_context_id_from_context
    except ImportError:  # pragma: no cover - compatibility for older lightweight boundary tests
        from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_positive_int
from .collaboration_users import is_collaboration_visible_user
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
    SOURCE_AUTHORITY = "mail.activity"
    SOURCE_KIND = "odoo_collaboration_activity_write_proxy"
    SOURCE_AUTHORITIES = ("mail.activity", "mail.activity.type", "ir.model", "odoo.orm", "ir.rule", "record_context_model")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authority": cls.SOURCE_AUTHORITY,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        summary = str(params.get("summary") or "").strip()
        note = str(params.get("note") or "").strip()
        deadline_raw = str(params.get("date_deadline") or "").strip()
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""
        raw_user_id = params.get("user_id")
        user_id, user_id_error = parse_positive_int(raw_user_id, allow_empty=True)
        if user_id_error:
            return self._failure(REASON_USER_ERROR, "user_id 无效", 400, trace_id)
        user_id = user_id or self.env.user.id
        activity_type_xmlid = str(params.get("activity_type_xmlid") or "mail.mail_activity_data_todo").strip()

        if not model or _is_empty_param(res_id) or not summary:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/summary", 400, trace_id)
        res_id, res_id_error = parse_positive_int(res_id)
        if res_id_error:
            return self._failure(REASON_USER_ERROR, "res_id 无效", 400, trace_id)

        try:
            if model not in self.env:
                return self._failure(REASON_NOT_FOUND, "模型不存在", 404, trace_id)
            record = self.env[model].browse(res_id).exists()
            if not record:
                return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
            in_scope, scope_meta = record_in_business_scope(
                self.env[model],
                int(record.id),
                params,
                self.context if isinstance(self.context, dict) else {},
            )
            if not in_scope:
                return record_scope_denied_response(scope_meta)
            self.env[model].check_access_rights("write")
            record.check_access_rule("write")

            Activity = self.env.get("mail.activity")
            IrModel = self.env.get("ir.model")
            if Activity is None or IrModel is None:
                return self._failure(REASON_NOT_FOUND, "活动模型不存在", 404, trace_id)
            model_rec = IrModel.sudo().search([("model", "=", model)], limit=1)
            if not model_rec:
                return self._failure(REASON_NOT_FOUND, "模型元数据不存在", 404, trace_id)
            assignee = self._activity_assignee(user_id)
            if not assignee:
                return self._failure(REASON_PERMISSION_DENIED, "指派人无效或不可用", 403, trace_id)
            activity_type = self.env.ref(activity_type_xmlid, raise_if_not_found=False)
            if not activity_type:
                activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
            if not activity_type:
                return self._failure(REASON_NOT_FOUND, "活动类型不存在", 404, trace_id)

            activity = Activity.with_context(
                mail_create_nosubscribe=True,
                mail_notify_noemail=True,
                mail_notify_force_send=False,
                mail_post_autofollow=False,
                mail_activity_quick_update=True,
                tracking_disable=True,
            ).create(
                {
                    "res_model_id": model_rec.id,
                    "res_id": record.id,
                    "user_id": assignee.id,
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
                "meta": {
                    "trace_id": trace_id,
                    "source_authority": self.source_authority_contract(),
                    "legacy_source_authority": self.SOURCE_AUTHORITY,
                },
            }
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限安排活动", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "安排活动失败", 500, trace_id)

    def _activity_assignee(self, user_id: int):
        user = self.env["res.users"].browse(user_id).exists()
        if not user or not user.active:
            return self.env["res.users"]
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
        if internal_group and internal_group not in user.groups_id:
            return self.env["res.users"]
        if not is_collaboration_visible_user(user):
            return self.env["res.users"]
        return user

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
            "meta": {"trace_id": trace_id, "source_authority": self.source_authority_contract()},
        }


def _coerce_date(value, user):
    if not value:
        return fields.Date.context_today(user)
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except Exception:
        return fields.Date.context_today(user)


def _is_empty_param(value):
    return value is None or (isinstance(value, str) and not value.strip())
