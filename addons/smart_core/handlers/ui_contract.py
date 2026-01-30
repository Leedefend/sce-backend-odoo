# -*- coding: utf-8 -*-
# 统一契约读取（P0：menu → entry 指针；兼容 nav/model/view/action_open），只读意图
import json, re, hashlib, time, logging
from collections.abc import Mapping
from typing import Any, Dict, Optional
from odoo import api
from odoo.tools.safe_eval import safe_eval
from ..core.base_handler import BaseIntentHandler

# ✅ 直接用你的统一服务与分发器
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher import MenuDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher

_logger = logging.getLogger(__name__)

CONTRACT_VERSION = "v0.1"
API_VERSION = "v1"

VALID_VIEWS = {
    "form","tree","kanban","search","pivot","graph","calendar","gantt","activity","dashboard"
}
_VIEW_MAP = {  # Odoo -> 前端别名
    "tree":"list","form":"form","kanban":"kanban","graph":"graph","pivot":"pivot",
    "calendar":"calendar","gantt":"gantt","search":"search","activity":"activity","dashboard":"dashboard",
}
_VIEW_INV = {v:k for k,v in _VIEW_MAP.items()}  # 前端别名 -> Odoo

def _json(o): return json.dumps(o, ensure_ascii=False, default=str, separators=(",", ":"))

def _normalize_meta(meta):
    if not meta: return {}
    if isinstance(meta, Mapping): return dict(meta)
    if isinstance(meta, str):
        s = meta.strip()
        if s[:1] in "{[}":
            try:
                obj = json.loads(s);  return obj if isinstance(obj, Mapping) else {}
            except Exception:
                return {}
        return {"flags":[s]}
    if isinstance(meta, (list, tuple)):
        if all(isinstance(it,(list,tuple)) and len(it)==2 for it in meta):
            try: return dict(meta)
            except Exception: pass
        merged, flags = {}, []
        for it in meta:
            if isinstance(it, Mapping): merged.update(it)
            elif isinstance(it, str): flags.append(it)
            elif isinstance(it,(list,tuple)) and len(it)==1 and isinstance(it[0],str): flags.append(it[0])
        return merged or ({"flags":flags} if flags else {})
    return {}

class UiContractHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.contract"
    DESCRIPTION = "统一契约读取（nav/menu/view/model/action_open），只读，支持 ETag/304"
    VERSION = "1.0.0"
    ETAG_ENABLED = True

    # ---------------- 参数挖掘器（兼容前端请求形状） ----------------
    @staticmethod
    def _as_dict(maybe) -> dict:
        if isinstance(maybe, dict): return maybe
        if isinstance(maybe, str):
            s = maybe.strip()
            if s and s[0] in "{[":
                try:
                    obj = json.loads(s);  return obj if isinstance(obj, dict) else {}
                except Exception: return {}
        return {}

    def _collect_layers(self, p: dict):
        layers = []
        layers.append(self._as_dict(p))
        for k in ("payload","params","data","args"):
            layers.append(self._as_dict(p.get(k)))
        try:
            if self.request is not None:
                jr = getattr(self.request, "jsonrequest", None)
                if jr: layers.append(self._as_dict(jr))
                rq = getattr(self.request, "params", None)
                if rq:
                    try: layers.append(dict(rq))
                    except Exception: pass
        except Exception:
            pass
        return [ly for ly in layers if isinstance(ly, dict) and ly]

    def _dig(self, p: dict, key: str):
        for layer in self._collect_layers(p):
            if key in layer:
                return layer.get(key)
        return None

    def _get_param(self, p: dict, *keys: str):
        for k in keys:
            v = self._dig(p, k)
            if v is None: continue
            if isinstance(v, str) and v.strip()=="": continue
            return v
        return None

    # ---------------- 主入口 ----------------
    def handle(self, payload: Optional[Dict[str, Any]] = None, ctx: Optional[Dict[str, Any]] = None):
        p = payload or {}

        # 智能推断 op/subject（兼容你的前端请求形状）
        op = (self._get_param(p, "op", "subject") or "").strip().lower()
        if not op:
            has_menu   = self._get_param(p, "menu_id", "menuId", "id")
            has_action = self._get_param(p, "action_id", "actionId")
            has_model  = self._get_param(p, "model", "model_code", "modelCode")
            if has_menu is not None:   op = "menu"
            elif has_action is not None: op = "action_open"
            elif has_model is not None:  op = "model"
            else:
                return self._err(400, "缺少 op/subject 或无法从参数推断（需要 menu_id / action_id / model）")

        # 上下文透传
        ctx = (self.env.context or {}).copy()
        lang = self._get_param(p, "lang"); tz = self._get_param(p, "tz")
        if lang: ctx["lang"] = lang
        if tz:   ctx["tz"] = tz
        company_id = self._get_param(p, "company_id", "companyId")
        if company_id:
            try: ctx["allowed_company_ids"] = [int(company_id)]
            except Exception: pass

        if_none_match = self._read_if_none_match(p)
        force_refresh = str(self._get_param(p, "force_refresh") or "").lower() in ("1","true","yes")
        t0 = time.time()

        # 分派
        if op == "nav":
            res = self._op_nav(ctx)
        elif op == "menu":
            res = self._op_menu(p, ctx)
        elif op == "model":
            res = self._op_model(p, ctx)
        elif op == "action_open":
            res = self._op_action_open(p, ctx)
        elif op == "view":
            res = self._op_view(p, ctx)  # ✅ 新增/修复：走统一服务的 model 分派
        else:
            return self._err(400, f"unsupported op: {op}")

        # 错误透传
        if isinstance(res, dict) and res.get("ok") is False:
            return res

        data, meta = (res if isinstance(res, tuple) else (res or {}, {}))
        meta = _normalize_meta(meta)
        etag = self._make_etag(meta=meta, ctx=ctx, op=op, p=p)

        if if_none_match and if_none_match == etag and not force_refresh:
            return {"ok": True, "data": None,
                    "meta": {"intent": self.INTENT_TYPE, "op": op, "etag": etag,
                             "version": self.VERSION, "elapsed_ms": int((time.time()-t0)*1000),
                             "contract_version": CONTRACT_VERSION, "api_version": API_VERSION},
                    "code": 304}

        meta_out = dict(meta)
        meta_out.update({"intent": self.INTENT_TYPE, "op": op, "version": self.VERSION,
                         "etag": etag, "elapsed_ms": int((time.time()-t0)*1000),
                         "contract_version": CONTRACT_VERSION, "api_version": API_VERSION})
        return {"ok": True, "data": data or {}, "meta": meta_out}

    # ---------------- op 实现 ----------------
    def _op_nav(self, ctx):
        data, versions = NavDispatcher(self.env, api.Environment(self.env.cr, self.env.user.id, ctx)).build_nav({"subject":"nav"})
        # 统一服务 finalize（轻量清洗）
        cs = ContractService(self.env)
        fixed = cs.finalize_contract({"ok": True, "data": {"nav": data.get("nav")}, "meta": {"subject": "nav", "version": format_versions_safe(versions)}})
        return fixed.get("data") or {"nav": data.get("nav")}, {"schema_version": "nav-1"}

    def _op_menu(self, p, ctx):
        raw_menu = self._get_param(p, "menu_id", "menuId", "id")
        try:
            menu_id = int(raw_menu)
        except Exception:
            return self._err(400, "缺少或非法的 menu_id")

        Menu = self.env["ir.ui.menu"].with_context(ctx)
        menu = Menu.browse(menu_id)
        if not menu.exists():
            return self._err(404, f"未知菜单: {menu_id}")

        action = menu.action and self.env[menu.action._name].browse(menu.action.id) or None
        if not action or action._name != "ir.actions.act_window":
            data = {"subject":"menu","menu_id":menu_id,"action":None,"entry":None}
            return data, {"schema_version":"menu-entry-1"}

        model = action.res_model
        primary_vm = (action.view_mode or "tree,form").split(",")[0].strip() or "tree"
        norm_type = _VIEW_MAP.get(primary_vm, primary_vm)

        view_id = action.view_id.id if action.view_id else None
        if not view_id:
            View = self.env["ir.ui.view"].with_context(ctx)
            v = View.search([("model","=",model),("type","=",primary_vm)], limit=1, order="priority,id")
            view_id = v.id or None

        view_modes = [ _VIEW_MAP.get(x.strip(), x.strip()) for x in (action.view_mode or "tree,form").split(",") if x.strip() ]
        # 收集各类视图 id
        view_ids_by_type = {}
        try:
            View = self.env["ir.ui.view"].with_context(ctx)
            for v in view_modes:
                odoo_type = _VIEW_INV.get(v, v)
                vv = View.search([("model","=",model),("type","=",odoo_type)], limit=1, order="priority,id")
                view_ids_by_type[v] = vv.id or None
        except Exception:
            pass

        data = {
            "subject":"menu",
            "menu_id":menu_id,
            "action":{
                "id": action.id,
                "type":"ir.actions.act_window",
                "res_model":model,
                "view_mode":action.view_mode or "tree,form",
                "view_modes": view_modes,
                "context": _safe_eval_or(action.context, {}),
                "domain": _safe_eval_or(action.domain, []),
            },
            "entry":{"model":model,"view_type":norm_type,"view_id":view_id},
            "view_ids_by_type": view_ids_by_type,
        }
        meta = {"schema_version":"menu-entry-1","action_hash":action.id,
                "entry_model":model,"entry_view_id":view_id}
        return data, meta

    def _op_model(self, p, ctx):
        model = (self._get_param(p, "model", "model_code", "modelCode") or "").strip()
        if not model:
            return self._err(400, "缺少参数 model 或 model_code")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")

        view_type = (self._get_param(p, "view_type", "viewType") or "form").strip().lower()
        view_id = self._get_param(p, "view_id", "viewId")

        # ✅ 统一服务分发：subject 固定为 'model'
        p2 = {"subject":"model","model":model,"view_type":_VIEW_INV.get(view_type, view_type),"view_id":view_id,"with_data":False}
        data, versions = ActionDispatcher(self.env, api.Environment(self.env.cr, self.env.user.id, ctx)).dispatch(p2)

        # finalize（统一化）
        cs = ContractService(self.env)
        fixed = cs.finalize_contract({"ok": True, "data": data, "meta": {"subject":"model"}})
        return fixed.get("data", {}), {"schema_version":"view-contract-1", "version": format_versions_safe(versions)}

    def _op_view(self, p, ctx):
        """前端传 subject:'view' 时，等价于按模型获取视图契约（无数据）"""
        model = (self._get_param(p, "model") or "").strip()
        if not model:
            return self._err(400, "缺少参数 model")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")

        view_type = (self._get_param(p, "view_type", "viewType") or "form").strip().lower()
        view_id = self._get_param(p, "view_id", "viewId")

        # ✅ 映射到统一服务的 'model' subject
        p2 = {"subject":"model","model":model,"view_type":_VIEW_INV.get(view_type, view_type),"view_id":view_id,"with_data":False}
        data, versions = ActionDispatcher(self.env, api.Environment(self.env.cr, self.env.user.id, ctx)).dispatch(p2)

        cs = ContractService(self.env)
        fixed = cs.finalize_contract({"ok": True, "data": data, "meta": {"subject":"model"}})
        return fixed.get("data", {}), {"schema_version":"view-contract-1", "version": format_versions_safe(versions)}

    def _op_action_open(self, p, ctx):
        raw_act = self._get_param(p, "action_id", "actionId")
        try:
            action_id = int(raw_act)
        except Exception:
            return self._err(400, "缺少或非法的 action_id")

        # 统一服务的 action 分发
        p2 = {"subject":"action","action_id": action_id, "with_data": False}
        data, versions = ActionDispatcher(self.env, api.Environment(self.env.cr, self.env.user.id, ctx)).dispatch(p2)

        cs = ContractService(self.env)
        fixed = cs.finalize_contract({"ok": True, "data": data, "meta": {"subject":"action"}})
        return fixed.get("data", {}), {"schema_version":"view-contract-1", "version": format_versions_safe(versions)}

    # ---------------- 工具 ----------------
    def _read_if_none_match(self, p) -> str:
        hdr = ""
        if self.request is not None:
            try: hdr = (self.request.httprequest.headers.get("If-None-Match") or "").strip().strip('"')
            except Exception: hdr = ""
        param = self._get_param(p, "if_none_match", "ifNoneMatch")
        param = (str(param or "")).strip().strip('"')
        return hdr or param

    def _make_etag(self, meta, ctx, op, p):
        meta = _normalize_meta(meta)
        etag_src = _json({
            "view_hash": meta.get("view_hash"),
            "model_hash": meta.get("model_hash"),
            "perm_key": meta.get("perm_key"),
            "action_hash": meta.get("action_hash"),
            "schema_version": meta.get("schema_version"),
            "uid": self.env.user.id if getattr(self.env, "user", None) else None,
            "company": getattr(getattr(self.env, "company", None), "id", None),
            "lang": ctx.get("lang"),
            "op": op,
            "menu_id": self._get_param(p, "menu_id","menuId","id"),
            "model": self._get_param(p, "model","model_code","modelCode"),
            "action_id": self._get_param(p, "action_id","actionId"),
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
        })
        return hashlib.sha1(etag_src.encode("utf-8")).hexdigest()

    def _err(self, code, msg):
        return {"ok": False, "error": {"code": code, "message": msg}}

def _safe_eval_or(val, default):
    try:
        if isinstance(val, str):
            return safe_eval(val) if val.strip() else default
        return val if val is not None else default
    except Exception:
        return default

def format_versions_safe(v):
    try:
        from odoo.addons.smart_core.app_config_engine.utils.misc import format_versions
        return format_versions(v)
    except Exception:
        return v
