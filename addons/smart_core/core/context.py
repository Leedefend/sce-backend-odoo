# smart_core/core/context.py
from odoo.http import request
from ..security.auth import get_user_from_token

class RequestContext:
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

        if intent_name == "login":
            user = None
            env = request.env
        else:
            user = get_user_from_token()
            env = request.env(user=user) if user else request.env

        # 把全局 request 传进去
        return cls(env, user, params, request)


    def has_param(self, key):
        return key in self.params

    def get(self, key, default=None):
        return self.params.get(key, default)
