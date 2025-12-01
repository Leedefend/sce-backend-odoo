# -*- coding: utf-8 -*-
# 统一元数据描述（只读意图）：返回字段定义 + 可选展开
from ..core.base_handler import BaseIntentHandler
from odoo.http import request
import hashlib, json, time

def _json(o): return json.dumps(o, ensure_ascii=False, default=str, separators=(",",":"))

class MetaDescribeHandler(BaseIntentHandler):
    INTENT_TYPE = "meta.describe_model"
    DESCRIPTION = "加载模型字段定义（可展开 selection/关系/约束），支持 ETag/304"

    def run(self):
        p = self.params or {}
        model = p.get("model")
        if not model:
            return {"ok": False, "error": {"code":400, "message":"缺少 model 参数"}}

        # 上下文：lang/tz/company 可选
        ctx = (self.env.context or {}).copy()
        if p.get("lang"): ctx["lang"] = p["lang"]
        if p.get("tz"):   ctx["tz"] = p["tz"]
        if p.get("company_id"):
            try: ctx["allowed_company_ids"] = [int(p["company_id"])]
            except: pass
        t0 = time.time()

        hdr_if_none_match = (request.httprequest.headers.get("If-None-Match") or "").strip().strip('"')
        if_none_match = (p.get("if_none_match") or "").strip().strip('"') or hdr_if_none_match

        env = self.env[model].with_context(ctx)
        fields = env.fields_get()  # 原始字段定义

        # 可选展开
        expand_selection = bool(p.get("expand_selection", True))
        expand_relation  = bool(p.get("expand_relation", True))
        for fname, f in fields.items():
            # 统一布尔化
            f["required"] = bool(f.get("required"))
            f["readonly"] = bool(f.get("readonly"))
            # selection 展开
            if expand_selection and f.get("type") in ("selection",):
                # 已有 selection 就直接返回；若为 callable 则尝试解析（一般 fields_get 已处理）
                pass
            # 关系展开（只返回关系模型名，避免递归爆炸；需要详细时另起意图）
            if expand_relation and f.get("type") in ("many2one","one2many","many2many"):
                rel = f.get("relation")
                if rel:
                    f["relation_model"] = rel

        data = {"model": model, "fields": fields, "schema_version":"model-fields-v1"}
        etag_src = _json({"model": model, "fields_count": len(fields), "lang": ctx.get("lang"), "uid": self.env.user.id})
        etag = hashlib.sha1(etag_src.encode("utf-8")).hexdigest()

        if if_none_match and if_none_match == etag:
            return {"ok": True, "data": None, "meta": {"intent":"meta.describe_model","etag":etag,"elapsed_ms":int((time.time()-t0)*1000)}, "code":304}

        meta = {"intent":"meta.describe_model","etag":etag,"elapsed_ms":int((time.time()-t0)*1000)}
        return {"ok": True, "data": data, "meta": meta}
