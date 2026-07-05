# -*- coding: utf-8 -*-
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
from ..utils.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)


class ChatterActivityUpdateHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.activity.update"
    DESCRIPTION = "Complete or cancel a collaboration activity for a record"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "Updating an activity changes collaboration todo state"
    SOURCE_AUTHORITY = "mail.activity"
    SOURCE_KIND = "odoo_collaboration_activity_state_proxy"
    SOURCE_AUTHORITIES = ("mail.activity", "mail.message", "ir.model", "odoo.orm", "ir.rule", "record_context_model")
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
        model = str(params.get("model") or "").strip()
        res_id_raw = params.get("res_id") if "res_id" in params else params.get("record_id")
        activity_id_raw = params.get("activity_id") if "activity_id" in params else params.get("id")
        action = str(params.get("action") or "").strip().lower()
        note = str(params.get("note") or "").strip()
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or _is_empty_param(res_id_raw) or _is_empty_param(activity_id_raw) or action not in {"done", "cancel"}:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/activity_id/action", 400, trace_id)
        res_id, res_id_error = parse_positive_int(res_id_raw)
        if res_id_error:
            return self._failure(REASON_USER_ERROR, "res_id 无效", 400, trace_id)
        activity_id, activity_id_error = parse_positive_int(activity_id_raw)
        if activity_id_error:
            return self._failure(REASON_USER_ERROR, "activity_id 无效", 400, trace_id)

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

            activity = self._load_activity(model, record.id, activity_id)
            if not activity:
                return self._failure(REASON_NOT_FOUND, "计划不存在或已处理", 404, trace_id)
            if action == "done":
                self._complete_activity(activity, note)
                message = "计划已完成"
            else:
                self._cancel_activity(activity, note)
                message = "计划已取消"

            return {
                "ok": True,
                "data": {
                    "result": {
                        "activity_id": activity_id,
                        "action": action,
                        "success": True,
                        "reason_code": REASON_OK,
                        "message": message,
                    }
                },
                "meta": {
                    "trace_id": trace_id,
                    "source_authority": self.source_authority_contract(),
                    "legacy_source_authority": self.SOURCE_AUTHORITY,
                },
            }
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限处理计划", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "处理计划失败", 500, trace_id)

    def _load_activity(self, model: str, res_id: int, activity_id: int):
        Activity = self.env.get("mail.activity")
        IrModel = self.env.get("ir.model")
        if Activity is None or IrModel is None:
            return None
        model_rec = IrModel.sudo().search([("model", "=", model)], limit=1)
        if not model_rec:
            return Activity.browse()
        return Activity.search(
            [
                ("id", "=", activity_id),
                ("res_model_id", "=", model_rec.id),
                ("res_id", "=", res_id),
            ],
            limit=1,
        )

    def _complete_activity(self, activity, note: str):
        feedback = note or "计划已完成。"
        activity.action_feedback(feedback=feedback)

    def _cancel_activity(self, activity, note: str):
        if note:
            activity.env[activity.res_model].browse(activity.res_id).message_post(
                body=note,
                subject="计划已取消",
                subtype_xmlid="mail.mt_note",
            )
        activity.unlink()

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


def _is_empty_param(value):
    return value is None or (isinstance(value, str) and not value.strip())
