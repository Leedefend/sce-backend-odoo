# smart_core/core/context.py
from odoo.http import request
from ..security.auth import get_user_from_token
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
    def from_http_request(cls):
        params =  request.httprequest.get_json(force=True, silent=True) or dict(request.params)
        intent_name = (params.get("intent") or "").strip()

        if intent_name in {"login", "auth.login", "sys.intents", "session.bootstrap", "bootstrap"}:
            user = None
            env = request.env
        else:
            user = get_user_from_token()
            env = request.env(user=user) if user else request.env

        ctx = cls(env, user, params, request)
        try:
            ctx.trace_id = get_trace_id(request.httprequest.headers)
        except Exception:
            ctx.trace_id = None
        return ctx


    def has_param(self, key):
        return key in self.params

    def get(self, key, default=None):
        return self.params.get(key, default)
