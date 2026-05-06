# 📁 smart_core/handlers/load_metadata.py
from ..core.base_handler import BaseIntentHandler

class LoadMetadataHandler(BaseIntentHandler):
    INTENT_TYPE = "load_metadata"
    DESCRIPTION = "加载模型字段定义"
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

    def _resolve_model(self, payload=None):
        params = {}
        if isinstance(payload, dict):
            if isinstance(payload.get("params"), dict):
                params.update(payload.get("params") or {})
            params.update(payload)
        if isinstance(self.params, dict):
            params.update(self.params)
        model = params.get("model")
        return model

    def handle(self, payload=None, ctx=None):
        model = self._resolve_model(payload)
        if not model:
            return self._err(400, "缺少 model 参数")
        if model not in self.env:
            return self._err(404, f"未知模型: {model}")
        return self.env[model].fields_get(), {
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }

    def _err(self, code: int, message: str):
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

    def run(self, **kwargs):
        payload = kwargs.get("payload")
        ctx = kwargs.get("ctx")
        return self.handle(payload=payload, ctx=ctx)
