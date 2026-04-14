# 📁 smart_core/handlers/load_view.py
# 说明：load_view 旧入口统一代理到 load_contract 主链路，
# 以收敛契约出口并避免 legacy 解析栈继续分叉。

from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import adapt_handler_result
from ..core.load_contract_proxy_payload import build_load_contract_proxy_payload
from ..core.native_view_contract_projection import inject_primary_view_projection
from .load_contract import LoadContractHandler


class LoadModelViewHandler(BaseIntentHandler):
    INTENT_TYPE = "load_view"
    DESCRIPTION = "兼容入口：统一代理到 load_contract"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        payload = build_load_contract_proxy_payload(params)
        proxied = adapt_handler_result(LoadContractHandler(
            env=self.env,
            su_env=self.su_env,
            context=self.context,
            payload=payload,
        ).handle(payload=payload, ctx=ctx or self.context))

        status = str((proxied or {}).get("status") or "").lower()
        code = int((proxied or {}).get("code") or (304 if status == "not_modified" else 200))

        if status == "error" or code >= 400:
            return {
                "ok": False,
                "error": {
                    "code": code,
                    "message": (proxied or {}).get("message") or "load_view unified proxy failed",
                },
                "code": code,
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "legacy_proxy": "load_contract",
                },
            }

        return {
            "ok": True,
            "data": self._build_legacy_view_data((proxied or {}).get("data") or {}),
            "meta": {
                **((proxied or {}).get("meta") or {}),
                "intent": self.INTENT_TYPE,
                "canonical_intent": "load_contract",
                "legacy_proxy": "load_contract",
            },
            "code": code,
        }

    def _build_legacy_view_data(self, proxied_data):
        data = dict(proxied_data or {})
        requested_view_type = None
        if isinstance(self.params, dict):
            requested_view_type = self.params.get("view_type")
        return inject_primary_view_projection(data, requested_view_type=requested_view_type)
