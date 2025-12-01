# -*- coding: utf-8 -*-
# smart_core/handlers/app_open.py
import json, hashlib, logging, time
from typing import Any, Dict
from odoo import api, SUPERUSER_ID
from ..core.base_handler import BaseIntentHandler
from .app_catalog import APP_DEFS, _xmlid_to_id, _current_perms

# 如需直接执行契约，可引入：
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService

_logger = logging.getLogger(__name__)

def _md5(d: Any) -> str:
    return hashlib.md5(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

class AppOpenHandler(BaseIntentHandler):
    """
    意图：app.open
    打开指定应用的某个 feature：
      - odoo_menu_xmlid  → 返回 menu 契约目标
      - odoo_action_xmlid→ 返回 action 契约目标（也可直接执行并回传契约）
      - internal_route    → 返回内部路由（前端按 ui.contract 渲染）
      - workflow_id       → 触发工作流引擎
    """
    INTENT_TYPE = "app.open"
    DESCRIPTION = "打开应用功能（统一入口）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = []  # 具体的权限在 feature.required_permissions 内校验

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        ts0 = time.time()
        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        app_id = payload.get("app")
        feature_key = payload.get("feature")
        if not app_id or not feature_key:
            raise ValueError("missing param: app / feature")

        app = next((a for a in APP_DEFS if a["id"] == app_id), None)
        if not app:
            raise ValueError(f"unknown app: {app_id}")
        f = next((x for x in app.get("features", []) if x["key"] == feature_key), None)
        if not f:
            raise ValueError(f"unknown feature: {app_id}:{feature_key}")

        # 权限二次校验
        need = set(f.get("required_permissions") or [])
        have = _current_perms(env)
        if need and not need.issubset(have):
            raise PermissionError(f"permission denied for {app_id}:{feature_key}")

        o = f.get("open") or {}
        # 1) 菜单：返回前端可直接 contract.get('menu', {id})
        if o.get("odoo_menu_xmlid"):
            mid = _xmlid_to_id(su_env, o["odoo_menu_xmlid"])
            data = {"subject": "menu", "id": int(mid)}  # 零推理：前端直接把这个交回 contract
            return {"status":"success","data":data,"meta":{"intent":self.INTENT_TYPE,"elapsed_ms":int((time.time()-ts0)*1000)},"ok":True}

        # 2) 动作：这里演示“直接执行并回传契约（无数据）”，也可只返回目标让前端再调
        if o.get("odoo_action_xmlid"):
            aid = _xmlid_to_id(su_env, o["odoo_action_xmlid"])
            p = {"subject": "action", "action_id": int(aid), "with_data": False}
            ad = ActionDispatcher(env, su_env)
            data, versions = ad.dispatch(p)
            fixed = ContractService(su_env).finalize_contract({"ok": True, "data": data, "meta": {"subject":"action"}})
            return {"status":"success","data":fixed.get("data"),"meta":{"intent":self.INTENT_TYPE,"elapsed_ms":int((time.time()-ts0)*1000)},"ok":True}

        # 3) 内部路由：交给前端 ui.contract
        if o.get("internal_route"):
            data = {"subject": "ui.contract", "route": o["internal_route"], "args": payload.get("args") or {}}
            return {"status":"success","data":data,"meta":{"intent":self.INTENT_TYPE,"elapsed_ms":int((time.time()-ts0)*1000)},"ok":True}

        # 4) 工作流：直接触发
        if o.get("workflow_id"):
            res = self.env["workflow.engine"].run(o["workflow_id"], payload.get("args") or {})
            return {"status":"success","data":res,"meta":{"intent":self.INTENT_TYPE,"elapsed_ms":int((time.time()-ts0)*1000)},"ok":True}

        raise ValueError(f"unknown open mapping for {app_id}:{feature_key}")
