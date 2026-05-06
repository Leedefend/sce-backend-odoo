# smart_core/core/context.py
from odoo.http import request
from ..security.auth import get_user_from_token
from odoo.exceptions import AccessDenied
from .intent_access_policy import is_public_context_intent
from .request_identity import identity_id
from .trace import get_trace_id

SOURCE_KIND = "http_request_context_projection"
SOURCE_AUTHORITIES = ("odoo.http.request", "auth_token", "res.users")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "request_context",
    }

class RequestContext:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict:
        return source_authority_contract()

    def __init__(self, env, user, params, request_obj=None):
        self.env = env
        self.user = user
        self.uid = user.id if user else None
        self.params = params
        self.request = request_obj  # 新增

    @classmethod
    def from_payload(cls, payload, request_obj=None):
        params = payload if isinstance(payload, dict) else {}
        intent_name = (params.get("intent") or "").strip()
        req = request_obj or request

        if is_public_context_intent(intent_name):
            user = None
            env = req.env
        else:
            user = get_user_from_token()
            user_id = identity_id(user)
            if not user_id:
                raise AccessDenied("Token 无效或缺少 user_id")
            env = req.env(user=user_id)

        ctx = cls(env, user, params, req)
        try:
            ctx.trace_id = get_trace_id(req.httprequest.headers)
        except Exception:
            ctx.trace_id = None
        return ctx

    @classmethod
    def from_http_request(cls):
        params =  request.httprequest.get_json(force=True, silent=True) or dict(request.params)
        return cls.from_payload(params, request)


    def has_param(self, key):
        return key in self.params

    def get(self, key, default=None):
        return self.params.get(key, default)
