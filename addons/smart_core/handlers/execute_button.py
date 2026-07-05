# 📁 smart_core/handlers/execute_button.py
from typing import Any, List, Optional

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
from ..core.navigation_entry_target import normalize_odoo_action_result
from ..core.request_params import parse_bool
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
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "button methods can trigger business side effects beyond replay-safe scope"
    SOURCE_KIND = "odoo_model_button_proxy"
    SOURCE_AUTHORITIES = ("odoo.model.method", "ir.actions", "ir.model.access", "ir.rule")

    def _source_authority_contract(self, model: str, method_name: str, button_type: str):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model or ""),
            "method": str(method_name or ""),
            "button_type": str(button_type or ""),
            "proxy_only": True,
        }

    def _button_access_mode(self, env_model, method_name: str) -> str:
        readonly_methods = getattr(env_model, "_sc_readonly_navigation_button_methods", ())
        if method_name in set(readonly_methods or ()):
            return "read"
        return "write"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model") or params.get("res_model")
        button = params.get("button") if isinstance(params.get("button"), dict) else {}

        button_type = button.get("type") or button.get("buttonType") or params.get("button_type") or "object"
        method_name = button.get("name") or params.get("method_name") or params.get("button_name")
        dry_run = parse_bool(params.get("dry_run"), False)

        res_id = params.get("res_id") or params.get("record_id") or self.context.get("record_id")
        res_ids, res_ids_error = _read_ids(res_id)
        if res_ids_error:
            return _failure_result(
                model=model,
                res_id=None,
                reason_code=REASON_MISSING_PARAMS,
                message="record_id 无效",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=400,
            )

        try:
            if not model or not method_name or not res_ids:
                return _failure_result(
                    model=model,
                    res_id=res_ids[0] if res_ids else None,
                    reason_code=REASON_MISSING_PARAMS,
                    message="后端未收到完整按钮执行参数",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            if button_type not in ("object", "action", "server", "server_action"):
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_UNSUPPORTED_BUTTON_TYPE,
                    message=f"后端不支持按钮类型: {button_type}",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            if model not in self.env:
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_NOT_FOUND,
                    message="后端目标模型不存在",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=404,
                )

            env_model = self.env[model]
            access_mode = self._button_access_mode(env_model, method_name)
            env_model.check_access_rights(access_mode)

            recordset = env_model.browse(res_ids)
            if not recordset.exists():
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_NOT_FOUND,
                    message="后端未找到目标记录",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=404,
                )
            for record in recordset:
                in_scope, scope_meta = record_in_business_scope(
                    env_model,
                    int(record.id),
                    params,
                    self.context if isinstance(self.context, dict) else {},
                )
                if not in_scope:
                    return record_scope_denied_response(scope_meta)

            recordset.check_access_rule(access_mode)

            method = getattr(recordset.with_context(self.context), method_name, None)
            if not callable(method):
                server_action_result = self._run_server_action(button, model=model, res_ids=res_ids)
                if server_action_result is not None:
                    return server_action_result
                server_action_id = button.get("server_action_id") or button.get("serverActionId")
                if server_action_id and not _positive_int(server_action_id):
                    return _failure_result(
                        model=model,
                        res_id=res_ids[0],
                        reason_code=REASON_MISSING_PARAMS,
                        message="server_action_id 无效",
                        trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                        status_code=400,
                    )
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code=REASON_METHOD_NOT_CALLABLE,
                    message=f"后端不可调用按钮方法: {method_name}",
                    trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                    status_code=400,
                )

            if dry_run:
                payload = {
                    "type": "dry_run",
                    "status": "success",
                    "success": True,
                    "reason_code": REASON_DRY_RUN,
                    "message": "后端已完成 dry run 校验",
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
                    "meta": {"trace_id": self.context.get("trace_id") if isinstance(self.context, dict) else "", "source_authority": self._source_authority_contract(model, method_name, button_type)},
                }

            result = method()

            payload = {
                "type": "refresh",
                "status": "success",
                "success": True,
                "reason_code": REASON_OK,
                "message": "后端已执行动作",
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
                normalized_action = normalize_odoo_action_result(
                    self.env,
                    result,
                    source_model=model,
                    source_record_id=res_ids[0],
                ) or result
                _enrich_payload_with_action_navigation(payload, normalized_action)
                payload["raw_action"] = normalized_action
                entry_target = normalized_action.get("entry_target") if isinstance(normalized_action.get("entry_target"), dict) else {}
                if entry_target:
                    payload["entry_target"] = entry_target
                effect = _effect_from_normalized_action(normalized_action, fallback_effect=effect)

            return {
                "ok": True,
                "data": {"result": payload, "effect": effect},
                "meta": {"trace_id": self.context.get("trace_id") if isinstance(self.context, dict) else "", "source_authority": self._source_authority_contract(model, method_name, button_type)},
            }
        except AccessError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_PERMISSION_DENIED,
                message=str(exc) or "后端拒绝本次按钮执行",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=403,
            )
        except UserError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_BUSINESS_RULE_FAILED,
                message=str(exc) or "后端业务规则拒绝本次按钮执行",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=400,
            )
        except Exception as exc:
            _logger.exception("execute_button failed: %s", exc)
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code=REASON_SYSTEM_ERROR,
                message="后端执行按钮动作失败",
                trace_id=self.context.get("trace_id") if isinstance(self.context, dict) else "",
                status_code=500,
            )

    # 兼容旧调用
    def run(self, **_kwargs):
        return self.handle()

    def _run_server_action(self, button: dict, *, model: str, res_ids: List[int]):
        server_action_id = button.get("server_action_id") or button.get("serverActionId")
        xml_id = str(button.get("xml_id") or button.get("xmlId") or button.get("name") or "").strip()
        action = None
        if server_action_id:
            try:
                action = self.env["ir.actions.server"].sudo().browse(int(server_action_id)).exists()
            except Exception:
                action = None
        if not action and xml_id:
            try:
                resolved = self.env.ref(xml_id, raise_if_not_found=False)
                if resolved and resolved._name == "ir.actions.server":
                    action = resolved.sudo()
            except Exception:
                action = None
        if not action or not _server_action_matches_model(action, model):
            return None
        result = action.with_context(
            dict(
                self.context if isinstance(self.context, dict) else {},
                active_model=model,
                active_id=res_ids[0] if res_ids else False,
                active_ids=res_ids,
            )
        ).run()
        payload = {
            "type": "refresh",
            "status": "success",
            "success": True,
            "reason_code": REASON_OK,
            "message": "后端已执行服务端动作",
            "res_model": model,
            "res_id": res_ids[0] if res_ids else None,
            "server_action_id": int(action.id),
        }
        effect = {
            "type": "reload_record",
            "target": {"kind": "record", "model": model, "id": res_ids[0] if res_ids else None},
        }
        if isinstance(result, dict):
            normalized_action = normalize_odoo_action_result(
                self.env,
                result,
                source_model=model,
                source_record_id=res_ids[0] if res_ids else None,
            ) or result
            _enrich_payload_with_action_navigation(payload, normalized_action)
            payload["raw_action"] = normalized_action
            entry_target = normalized_action.get("entry_target") if isinstance(normalized_action.get("entry_target"), dict) else {}
            if entry_target:
                payload["entry_target"] = entry_target
            effect = _effect_from_normalized_action(normalized_action, fallback_effect=effect)
        return {
            "ok": True,
            "data": {"result": payload, "effect": effect},
            "meta": {
                "trace_id": self.context.get("trace_id") if isinstance(self.context, dict) else "",
                "source_authority": self._source_authority_contract(model, str(action.id), "server_action"),
            },
        }

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
    ids, _error = _read_ids(value)
    return ids


def _read_ids(value: Any):
    if value is None:
        return [], None
    if isinstance(value, (list, tuple)):
        out = []
        for raw in value:
            if raw is None:
                continue
            try:
                item = int(raw)
            except Exception:
                return [], "invalid"
            if item <= 0:
                return [], "invalid"
            out.append(item)
        return out, None
    try:
        item = int(value)
    except Exception:
        return [], "invalid"
    if item <= 0:
        return [], "invalid"
    return [item], None


def _server_action_matches_model(action, model: str) -> bool:
    action_model = str(getattr(getattr(action, "model_id", None), "model", "") or "").strip()
    if not action_model:
        return False
    return action_model == str(model or "").strip()


def _positive_int(value) -> int:
    try:
        parsed = int(value)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _query_literal(value) -> str:
    if value in (None, False, ""):
        return ""
    if isinstance(value, str):
        return value.strip()
    return repr(value)


def _enrich_payload_with_action_navigation(payload: dict, action: dict) -> None:
    action_id = _positive_int(action.get("id") or action.get("action_id"))
    if action_id:
        payload["action_id"] = action_id
    domain_raw = _query_literal(action.get("domain_raw") or action.get("domain"))
    context_raw = _query_literal(action.get("context_raw") or action.get("context"))
    if domain_raw:
        payload["domain_raw"] = domain_raw
    if context_raw:
        payload["context_raw"] = context_raw
    entry_target = action.get("entry_target") if isinstance(action.get("entry_target"), dict) else {}
    refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
    if refs:
        if domain_raw:
            refs["domain_raw"] = domain_raw
        if context_raw:
            refs["context_raw"] = context_raw


def _effect_from_normalized_action(action: dict, *, fallback_effect: dict) -> dict:
    entry_target = action.get("entry_target") if isinstance(action.get("entry_target"), dict) else {}
    action_type = action.get("type")
    action_id = _positive_int(action.get("id") or action.get("action_id"))
    action_model = str(action.get("res_model") or "").strip()
    action_res_id = _positive_int(action.get("res_id"))
    action_url = str(action.get("url") or "").strip()
    if entry_target:
        target = {
            "kind": "entry_target",
            "entry_target": entry_target,
        }
        domain_raw = _query_literal(action.get("domain_raw") or action.get("domain"))
        context_raw = _query_literal(action.get("context_raw") or action.get("context"))
        if domain_raw:
            target["domain_raw"] = domain_raw
        if context_raw:
            target["context_raw"] = context_raw
        return {
            "type": "navigate",
            "target": target,
        }
    if action_model and action_res_id:
        return {"type": "navigate", "target": {"kind": "record", "model": action_model, "id": action_res_id}}
    if action_id:
        return {"type": "navigate", "target": {"kind": "action", "action_id": action_id}}
    if action_type == "ir.actions.act_url" and action_url:
        return {"type": "navigate", "target": {"kind": "url", "url": action_url}}
    return fallback_effect


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
