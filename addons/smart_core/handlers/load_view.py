# 📁 smart_core/handlers/load_view.py
# 说明：load_view 旧入口统一代理到 load_contract 主链路，
# 以收敛契约出口并避免 legacy 解析栈继续分叉。

from ..core.base_handler import BaseIntentHandler
from ..core.load_contract_proxy_payload import build_load_contract_proxy_payload
from .load_contract import LoadContractHandler


class LoadModelViewHandler(BaseIntentHandler):
    INTENT_TYPE = "load_view"
    DESCRIPTION = "兼容入口：统一代理到 load_contract"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        payload = build_load_contract_proxy_payload(params)
        proxied = LoadContractHandler(
            env=self.env,
            su_env=self.su_env,
            context=self.context,
            payload=payload,
        ).handle(payload=payload, ctx=ctx or self.context)

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
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}

        requested_view_type = None
        if isinstance(self.params, dict):
            requested_view_type = self.params.get("view_type")
        primary_view_type = self._resolve_primary_view_type(requested_view_type, head, views)
        primary_view = views.get(primary_view_type) if isinstance(views.get(primary_view_type), dict) else {}

        if "layout" not in data and primary_view.get("layout") is not None:
            data["layout"] = primary_view.get("layout")
        if "model" not in data and head.get("model"):
            data["model"] = head.get("model")
        if "view_type" not in data and primary_view_type:
            data["view_type"] = primary_view_type
        if "permissions" not in data and isinstance(proxied_data, dict) and isinstance(proxied_data.get("permissions"), dict):
            data["permissions"] = proxied_data.get("permissions")
        if "fields" not in data and isinstance(proxied_data, dict) and isinstance(proxied_data.get("fields"), dict):
            data["fields"] = proxied_data.get("fields")
        return data

    def _resolve_primary_view_type(self, requested_view_type, head, views):
        if isinstance(requested_view_type, str) and requested_view_type.strip():
            return requested_view_type.split(",")[0].strip()
        if isinstance(requested_view_type, (list, tuple)):
            for item in requested_view_type:
                key = str(item or "").strip()
                if key:
                    return key
        head_view_type = str((head or {}).get("view_type") or "").strip()
        if head_view_type:
            return head_view_type
        for candidate in ("form", "tree", "kanban", "search", "pivot", "graph", "calendar", "gantt", "activity", "dashboard"):
            if candidate in (views or {}):
                return candidate
        return "form"
