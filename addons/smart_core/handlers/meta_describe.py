# -*- coding: utf-8 -*-
# 统一元数据描述（只读意图）：返回字段定义 + 可选展开
from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_bool, parse_positive_int
from odoo.http import request
import hashlib, json, time

def _json(o): return json.dumps(o, ensure_ascii=False, default=str, separators=(",",":"))

class MetaDescribeHandler(BaseIntentHandler):
    INTENT_TYPE = "meta.describe_model"
    DESCRIPTION = "加载模型字段定义（可展开 selection/关系/约束），支持 ETag/304"
    SOURCE_KIND = "odoo_fields_get_projection"
    SOURCE_AUTHORITIES = ("ir.model.fields", "odoo.orm")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def run(self, **_kwargs):
        p = self.params or {}
        if not isinstance(p, dict):
            return self._err(400, "params 无效")
        model, model_error = self._text_param(p, "model")
        if model_error:
            return model_error
        if not model:
            return self._err(400, "缺少 model 参数")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")

        # 上下文：lang/tz/company 可选
        ctx = (self.env.context or {}).copy()
        lang, lang_error = self._text_param(p, "lang", allow_empty=True)
        if lang_error:
            return lang_error
        tz, tz_error = self._text_param(p, "tz", allow_empty=True)
        if tz_error:
            return tz_error
        if lang: ctx["lang"] = lang
        if tz:   ctx["tz"] = tz
        company_id, company_error = parse_positive_int(p.get("company_id"), allow_empty=True)
        if company_error:
            return self._err(400, "company_id 无效")
        if company_id:
            ctx["allowed_company_ids"] = [company_id]
            ctx["company_id"] = company_id
        operation_strategy = str(p.get("operation_strategy") or p.get("operationStrategy") or "").strip()
        if operation_strategy:
            ctx["operation_strategy"] = operation_strategy
        t0 = time.time()

        try:
            hdr_if_none_match = (request.httprequest.headers.get("If-None-Match") or "").strip().strip('"')
        except Exception:
            hdr_if_none_match = ""
        if_none_match, if_none_match_error = self._text_param(p, "if_none_match", allow_empty=True)
        if if_none_match_error:
            return if_none_match_error
        if_none_match = if_none_match.strip('"') or hdr_if_none_match

        env = self.env[model].with_context(ctx)
        fields = env.fields_get()  # 原始字段定义

        # 可选展开
        expand_selection = parse_bool(p.get("expand_selection"), True)
        expand_relation = parse_bool(p.get("expand_relation"), True)
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
            meta = {"intent":"meta.describe_model","etag":etag,"elapsed_ms":int((time.time()-t0)*1000)}
            meta.update(self._source_meta())
            return {"ok": True, "data": None, "meta": meta, "code":304}

        meta = {"intent":"meta.describe_model","etag":etag,"elapsed_ms":int((time.time()-t0)*1000)}
        meta.update(self._source_meta())
        return {"ok": True, "data": data, "meta": meta}

    def _text_param(self, params, key, *, allow_empty: bool = False):
        raw = params.get(key)
        if raw is None or raw == "":
            return "", None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{key} 无效")
        text = str(raw).strip()
        if not text and not allow_empty:
            return "", None
        return text, None

    def _err(self, code, message):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "code": code,
            "meta": self._source_meta(),
        }

    def _source_meta(self):
        return {
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }
