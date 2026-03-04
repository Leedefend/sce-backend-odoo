# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from odoo import api, models
from odoo.exceptions import UserError
from odoo.models import BaseModel

from ..handlers.api_onchange import ApiOnchangeHandler


class AppActionGateway(models.AbstractModel):
    _name = "app.action.gateway"
    _description = "Smart Core Operation Gateway"

    @api.model
    def _normalize_ids(self, record_ids: Any) -> List[int]:
        if isinstance(record_ids, int):
            return [record_ids]
        if isinstance(record_ids, (tuple, list)):
            out: List[int] = []
            for item in record_ids:
                try:
                    val = int(item)
                except Exception:
                    continue
                if val > 0:
                    out.append(val)
            return out
        return []

    @api.model
    def _serialize_result(self, value: Any):
        if isinstance(value, BaseModel):
            return {
                "model": value._name,
                "ids": value.ids,
                "count": len(value.ids),
            }
        if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
            return value
        return str(value)

    @api.model
    def run_object_method(
        self,
        model: str,
        method: str = "",
        record_ids: Any = None,
        args: Any = None,
        kwargs: Any = None,
        action_key: str = "",
    ):
        model_name = str(model or "").strip()
        method_name = str(method or "").strip()
        if not model_name:
            raise UserError("run_object_method 缺少 model")
        if model_name not in self.env:
            raise UserError("run_object_method 模型不存在: %s" % model_name)
        if not method_name:
            raise UserError("run_object_method 缺少 method（action_key=%s）" % str(action_key or ""))

        env_model = self.env[model_name]
        call_args = args if isinstance(args, list) else []
        call_kwargs = kwargs if isinstance(kwargs, dict) else {}
        ids = self._normalize_ids(record_ids)
        target = env_model.browse(ids).exists() if ids else env_model
        fn = getattr(target, method_name, None)
        if not callable(fn):
            raise UserError("method 不存在或不可调用: %s.%s" % (model_name, method_name))
        result = fn(*call_args, **call_kwargs)
        return self._serialize_result(result)

    @api.model
    def run_onchange(self, model: str, values: Dict[str, Any] = None, changed: Any = None, context: Dict[str, Any] = None):
        model_name = str(model or "").strip()
        if not model_name:
            raise UserError("run_onchange 缺少 model")
        if model_name not in self.env:
            raise UserError("run_onchange 模型不存在: %s" % model_name)
        changed_fields = changed if isinstance(changed, list) else []
        handler = ApiOnchangeHandler(self.env)
        result = handler.handle(
            payload={
                "params": {
                    "model": model_name,
                    "values": values if isinstance(values, dict) else {},
                    "changed_fields": changed_fields,
                    "context": context if isinstance(context, dict) else {},
                }
            },
            ctx=self.env.context,
        )
        if isinstance(result, dict) and result.get("ok"):
            data = result.get("data")
            if isinstance(data, dict):
                return data
            return {}
        error = result.get("error") if isinstance(result, dict) else {}
        return {
            "patch": {},
            "modifiers_patch": {},
            "line_patches": [],
            "warnings": [
                {
                    "title": "Onchange failed",
                    "message": str((error or {}).get("message") or "onchange handler failed"),
                    "reason_code": "ONCHANGE_FAILED",
                }
            ],
            "applied_fields": changed_fields,
        }
