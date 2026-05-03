# 📁 smart_core/handlers/load_metadata.py
from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import UserError

class LoadMetadataHandler(BaseIntentHandler):
    INTENT_TYPE = "load_metadata"
    DESCRIPTION = "加载模型字段定义"
    SOURCE_KIND = "odoo_fields_get_projection"
    SOURCE_AUTHORITIES = ("ir.model.fields", "odoo.orm")

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
            raise UserError("缺少 model 参数")
        return self.env[model].fields_get()

    def run(self, **kwargs):
        payload = kwargs.get("payload")
        ctx = kwargs.get("ctx")
        return self.handle(payload=payload, ctx=ctx)
