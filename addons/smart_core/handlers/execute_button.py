# 📁 smart_core/handlers/execute_button.py
from typing import Any, List, Optional

from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError
from odoo import fields
import logging
from ..utils.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_DRY_RUN,
    REASON_METHOD_NOT_CALLABLE,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_BUTTON_TYPE,
    failure_meta_for_reason,
)

_logger = logging.getLogger(__name__)

class ExecuteButtonHandler(BaseIntentHandler):
    INTENT_TYPE = "execute_button"
    DESCRIPTION = "执行模型按钮方法"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model") or params.get("res_model")
        button = params.get("button") if isinstance(params.get("button"), dict) else {}

        button_type = button.get("type") or button.get("buttonType") or params.get("button_type") or "object"
        method_name = button.get("name") or params.get("method_name") or params.get("button_name")
        dry_run = bool(params.get("dry_run"))

        res_id = params.get("res_id") or params.get("record_id") or self.context.get("record_id")
        res_ids = _coerce_ids(res_id)

        try:
            if not model or not method_name or not res_ids:
                return _failure_result(
                    model=model,
                    res_id=res_ids[0] if res_ids else None,
                    reason_code=REASON_MISSING_PARAMS,
                    message="缺少参数 model/button.name/res_id",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            if button_type not in ("object", "action"):
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_UNSUPPORTED_BUTTON_TYPE,
                    message=f"不支持的按钮类型: {button_type}",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            self.env[model].check_access_rights("write")

            recordset = self.env[model].browse(res_ids)
            if not recordset.exists():
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_NOT_FOUND,
                    message="记录不存在",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=404,
                )

            recordset.check_access_rule("write")

            method = getattr(recordset.with_context(self.context), method_name, None)
            if not callable(method):
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_METHOD_NOT_CALLABLE,
                    message=f"方法不可调用: {method_name}",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            if dry_run:
                payload = {
                    "type": "dry_run",
                    "status": "success",
                    "success": True,
                    "reason_code": REASON_DRY_RUN,
                    "message": "Dry run completed",
                    "res_model": model,
                    "res_id": res_ids[0],
                    "method": method_name,
                    "button_type": button_type,
                }
                effect = {
                    "type": "toast",
                    "message": "dry_run",
                }
                return {
                    "ok": True,
                    "data": {"result": payload, "effect": effect},
                    "meta": {"trace_id": self.context.get("trace_id") if isinstance(self.context, dict) else ""},
                }

            result = method()

            payload = {
                "type": "refresh",
                "status": "success",
                "success": True,
                "reason_code": REASON_OK,
                "message": "Action executed successfully",
                "res_model": model,
                "res_id": res_ids[0],
            }
            self._maybe_create_followup(recordset, method_name, payload)
            effect = {
                "type": "reload_record",
                "target": {
                    "kind": "record",
                    "model": model,
                    "id": res_ids[0],
                },
            }
            if isinstance(result, dict):
                payload["raw_action"] = result
                action_type = result.get("type")
                action_id = result.get("id")
                action_model = result.get("res_model")
                action_res_id = result.get("res_id")
                action_url = result.get("url")
                if action_model and action_res_id:
                    effect = {
                        "type": "navigate",
                        "target": {
                            "kind": "record",
                            "model": action_model,
                            "id": action_res_id,
                        },
                    }
                elif action_id:
                    effect = {
                        "type": "navigate",
                        "target": {
                            "kind": "action",
                            "action_id": action_id,
                        },
                    }
                elif action_type == "ir.actions.act_url" and action_url:
                    effect = {
                        "type": "navigate",
                        "target": {
                            "kind": "url",
                            "url": action_url,
                        },
                    }

            return {
                "ok": True,
                "data": {"result": payload, "effect": effect},
                "meta": {"trace_id": self.context.get("trace_id") if isinstance(self.context, dict) else ""},
            }
        except AccessError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_PERMISSION_DENIED,
                message=str(exc) or "Permission denied",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=403,
            )
        except UserError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_BUSINESS_RULE_FAILED,
                message=str(exc) or "Business rule failed",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=400,
            )
        except Exception as exc:
            _logger.exception("execute_button failed: %s", exc)
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_SYSTEM_ERROR,
                message="Action execution failed",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=500,
            )

    # 兼容旧调用
    def run(self, **_kwargs):
        return self.handle()

    def _maybe_create_followup(self, recordset, method_name: str, payload: dict):
        if not _should_generate_todo(method_name):
            return
        if not recordset or not recordset.exists():
            return
        record = recordset[0]
        assignee = _resolve_assignee(record, self.env.user)
        if not assignee:
            return
        Activity = self.env.get("mail.activity")
        IrModel = self.env.get("ir.model")
        if not Activity or not IrModel:
            return
        model_rec = IrModel.sudo().search([("model", "=", record._name)], limit=1)
        if not model_rec:
            return
        todo_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not todo_type:
            return
        summary = _build_activity_summary(method_name, record)
        note = _build_activity_note(method_name, payload, self.env.user)
        deadline = fields.Date.context_today(self.env.user)
        existing = Activity.sudo().search(
            _followup_activity_domain(
                model_rec_id=model_rec.id,
                res_id=record.id,
                assignee_id=assignee.id,
                activity_type_id=todo_type.id,
                summary=summary,
                deadline=deadline,
            ),
            limit=1,
        )
        if existing:
            return
        try:
            Activity.sudo().create(
                {
                    "res_model_id": model_rec.id,
                    "res_id": record.id,
                    "user_id": assignee.id,
                    "activity_type_id": todo_type.id,
                    "summary": summary,
                    "note": note,
                    "date_deadline": deadline,
                }
            )
        except Exception as exc:
            _logger.warning("execute_button followup activity skipped: %s", exc)
            return
        try:
            if hasattr(record, "message_post"):
                partner_ids = [assignee.partner_id.id] if assignee.partner_id else []
                record.message_post(
                    body=note,
                    subject=summary,
                    partner_ids=partner_ids,
                )
        except Exception as exc:
            _logger.warning("execute_button followup notify skipped: %s", exc)


def _coerce_ids(value: Any) -> List[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value if v is not None]
    try:
        return [int(value)]
    except Exception:
        return []


def _failure_result(
    model: Optional[str],
    res_id: Optional[int],
    reason_code: str,
    message: str,
    trace_id: str = "",
    status_code: int = 400,
):
    payload = {
        "type": "noop",
        "status": "failure",
        "success": False,
        "reason_code": reason_code,
        "message": message or "Action failed",
        "res_model": model,
        "res_id": res_id,
    }
    effect = {"type": "toast", "message": payload["message"]}
    return {
        "ok": False,
        "error": {
            "code": reason_code,
            "message": payload["message"],
            "reason_code": reason_code,
            **failure_meta_for_reason(reason_code),
        },
        "data": {"result": payload, "effect": effect},
        "code": int(status_code),
        "meta": {"trace_id": trace_id},
    }


def _should_generate_todo(method_name: str) -> bool:
    value = str(method_name or "").lower()
    keywords = ("submit", "confirm", "approve", "reject", "done", "complete")
    return any(token in value for token in keywords)


def _resolve_assignee(record, fallback_user):
    user_field = getattr(record, "_fields", {}).get("user_id")
    if user_field and getattr(user_field, "comodel_name", "") == "res.users":
        assignee = getattr(record, "user_id", False)
        if assignee:
            return assignee
    return fallback_user


def _build_activity_summary(method_name: str, record) -> str:
    label = _semantic_action_label(method_name)
    name = getattr(record, "display_name", "") or getattr(record, "name", "") or f"{record._name}#{record.id}"
    return f"{label}待处理: {name}"


def _build_activity_note(method_name: str, payload: dict, actor) -> str:
    reason = payload.get("reason_code") or "OK"
    actor_name = actor.display_name or actor.login or "System"
    action_key = str(method_name or "")
    action_label = _semantic_action_label(method_name)
    # 结构化首行，供 my.work.summary 解析并展示可解释字段
    structured = f"SC_FOLLOWUP action_key={action_key} action_label={action_label} reason_code={reason}"
    detail = f"{actor_name} 执行了“{action_label}”操作。reason={reason}"
    return f"{structured}\n{detail}"


def _semantic_action_label(method_name: str) -> str:
    name = str(method_name or "").lower()
    if "submit" in name:
        return "提交"
    if "confirm" in name:
        return "确认"
    if "approve" in name:
        return "审批"
    if "reject" in name:
        return "退回"
    if "done" in name or "complete" in name:
        return "完成"
    return "处理"


def _followup_activity_domain(
    *,
    model_rec_id: int,
    res_id: int,
    assignee_id: int,
    activity_type_id: int,
    summary: str,
    deadline,
):
    return [
        ("res_model_id", "=", model_rec_id),
        ("res_id", "=", res_id),
        ("user_id", "=", assignee_id),
        ("activity_type_id", "=", activity_type_id),
        ("summary", "=", summary),
        ("date_deadline", "=", deadline),
    ]
