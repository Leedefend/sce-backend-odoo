# 📁 smart_core/handlers/execute_button.py
from typing import Any, List, Optional

from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError
import logging

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
                    reason_code="MISSING_PARAMS",
                    message="缺少参数 model/button.name/res_id",
                )

            if button_type not in ("object", "action"):
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code="UNSUPPORTED_BUTTON_TYPE",
                    message=f"不支持的按钮类型: {button_type}",
                )

            self.env[model].check_access_rights("write")

            recordset = self.env[model].browse(res_ids)
            if not recordset.exists():
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code="NOT_FOUND",
                    message="记录不存在",
                )

            recordset.check_access_rule("write")

            method = getattr(recordset.with_context(self.context), method_name, None)
            if not callable(method):
                return _failure_result(
                    model=model,
                    res_id=res_ids[0],
                    reason_code="METHOD_NOT_CALLABLE",
                    message=f"方法不可调用: {method_name}",
                )

            if dry_run:
                payload = {
                    "type": "dry_run",
                    "status": "success",
                    "success": True,
                    "reason_code": "DRY_RUN",
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
                return {"result": payload, "effect": effect}, {}

            result = method()

            payload = {
                "type": "refresh",
                "status": "success",
                "success": True,
                "reason_code": "OK",
                "message": "Action executed successfully",
                "res_model": model,
                "res_id": res_ids[0],
            }
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

            return {"result": payload, "effect": effect}, {}
        except AccessError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code="PERMISSION_DENIED",
                message=str(exc) or "Permission denied",
            )
        except UserError as exc:
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code="BUSINESS_RULE_FAILED",
                message=str(exc) or "Business rule failed",
            )
        except Exception as exc:
            _logger.exception("execute_button failed: %s", exc)
            return _failure_result(
                model=model,
                res_id=res_ids[0] if res_ids else None,
                reason_code="SYSTEM_ERROR",
                message="Action execution failed",
            )

    # 兼容旧调用
    def run(self, **_kwargs):
        return self.handle()


def _coerce_ids(value: Any) -> List[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value if v is not None]
    try:
        return [int(value)]
    except Exception:
        return []


def _failure_result(model: Optional[str], res_id: Optional[int], reason_code: str, message: str):
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
    return {"result": payload, "effect": effect}, {}
