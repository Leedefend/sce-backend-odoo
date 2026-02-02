# 📁 smart_core/handlers/execute_button.py
from typing import Any, Dict, List, Optional

from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError

class ExecuteButtonHandler(BaseIntentHandler):
    INTENT_TYPE = "execute_button"
    DESCRIPTION = "执行模型按钮方法"

    def run(self):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model") or params.get("res_model")
        button = params.get("button") if isinstance(params.get("button"), dict) else {}

        button_type = button.get("type") or button.get("buttonType") or params.get("button_type") or "object"
        method_name = button.get("name") or params.get("method_name") or params.get("button_name")

        res_id = params.get("res_id") or params.get("record_id") or self.context.get("record_id")
        res_ids = _coerce_ids(res_id)

        if not model or not method_name or not res_ids:
            raise UserError("缺少参数 model/button.name/res_id")

        if button_type not in ("object", "action"):
            raise UserError(f"不支持的按钮类型: {button_type}")

        # 2. 检查模型访问权限
        self.env[model].check_access_rights("write")

        recordset = self.env[model].browse(res_ids)
        if not recordset.exists():
            raise UserError("记录不存在")

        recordset.check_access_rule("write")

        # 3. 检查方法安全性
        method = getattr(recordset.with_context(self.context), method_name, None)
        if not callable(method):
            raise AccessError(f"方法不可调用: {method_name}")

        # 4. 执行方法
        result = method()

        # 5. 标准化返回（MVP 统一 refresh）
        payload = {
            "type": "refresh",
            "res_model": model,
            "res_id": res_ids[0],
        }
        if isinstance(result, dict):
            payload["raw_action"] = result

        return {"result": payload}, {}


def _coerce_ids(value: Any) -> List[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value if v is not None]
    try:
        return [int(value)]
    except Exception:
        return []
