# 📁 smart_core/handlers/load_view.py
# 说明：load_view 旧入口统一代理到 load_contract 主链路，
# 以收敛契约出口并避免 legacy 解析栈继续分叉。

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_positive_int
from ..security.platform_admin import user_is_platform_admin
from .load_contract import LoadContractHandler


SENSITIVE_SYSTEM_MODELS = {
    "ir.actions.actions",
    "ir.actions.act_window",
    "ir.config_parameter",
    "ir.model",
    "ir.model.access",
    "ir.model.fields",
    "ir.rule",
    "ir.ui.menu",
    "ir.ui.view",
    "res.groups",
    "res.users",
}


class LoadModelViewHandler(BaseIntentHandler):
    INTENT_TYPE = "load_view"
    DESCRIPTION = "兼容入口：统一代理到 load_contract"
    SOURCE_KIND = "load_contract_legacy_proxy"
    SOURCE_AUTHORITY = "load_contract"

    def run(self, **_kwargs):
        params = dict(self.params or {})
        model = str(params.get("model") or params.get("model_code") or "").strip()
        if model in SENSITIVE_SYSTEM_MODELS and not user_is_platform_admin(
            getattr(self.env, "user", None),
            include_legacy=True,
            include_system=True,
        ):
            return self._permission_denied(model)
        payload = {
            "params": {
                "model": params.get("model"),
                "model_code": params.get("model_code"),
                "menu_id": params.get("menu_id"),
                "action_id": params.get("action_id"),
                "view_type": params.get("view_type"),
                "include": params.get("include") or "all",
                "force_refresh": params.get("force_refresh"),
                "version": params.get("version"),
                "if_none_match": params.get("if_none_match"),
                "lang": params.get("lang"),
                "tz": params.get("tz"),
                "company_id": params.get("company_id"),
            }
        }
        # 兼容传入 view_id：转为 context 线索，供主链路在后续扩展使用。
        view_id, view_id_error = parse_positive_int(params.get("view_id"), allow_empty=True)
        if view_id_error:
            return self._err(400, "view_id 无效")
        if view_id:
            payload["params"]["context"] = {"requested_view_id": view_id}

        proxied = LoadContractHandler(
            env=self.env,
            su_env=self.su_env,
            context=self.context,
            payload=payload,
        ).handle(payload=payload, ctx=self.context)

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
                    "source_authority": {
                        "kind": self.SOURCE_KIND,
                        "authority": self.SOURCE_AUTHORITY,
                        "proxy_only": True,
                    },
                },
            }

        return {
            "ok": True,
            "data": (proxied or {}).get("data") or {},
            "meta": {
                **((proxied or {}).get("meta") or {}),
                "intent": self.INTENT_TYPE,
                "legacy_proxy": "load_contract",
            },
            "code": code,
        }

    def _err(self, code, message):
        return {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
            },
            "code": code,
            "meta": {
                "intent": self.INTENT_TYPE,
                "legacy_proxy": "load_contract",
                "source_authority": {
                    "kind": self.SOURCE_KIND,
                    "authority": self.SOURCE_AUTHORITY,
                    "proxy_only": True,
                },
            },
        }

    def _permission_denied(self, model):
        return {
            "ok": False,
            "error": {
                "code": "PERMISSION_DENIED",
                "message": "permission denied",
                "reason_code": "PERMISSION_DENIED",
                "model": model,
            },
            "code": 403,
            "meta": {
                "intent": self.INTENT_TYPE,
                "legacy_proxy": "load_contract",
                "source_authority": {
                    "kind": self.SOURCE_KIND,
                    "authority": self.SOURCE_AUTHORITY,
                    "proxy_only": True,
                    "system_model_guard": True,
                },
            },
        }
