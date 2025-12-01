# 📁 smart_core/handlers/load_metadata.py
from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import UserError

class LoadMetadataHandler(BaseIntentHandler):
    INTENT_TYPE = "load_metadata"
    DESCRIPTION = "加载模型字段定义"

    def run(self):
         # 从 self.params 获取 model
        model = self.params.get("model")
        if not model:
            raise UserError("缺少 model 参数")
        return self.env[model].fields_get()