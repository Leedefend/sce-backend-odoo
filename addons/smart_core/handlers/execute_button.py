# 📁 smart_core/handlers/execute_button.py
from ..core.base_handler import BaseIntentHandler
from odoo.exceptions import AccessError, UserError

class ExecuteButtonHandler(BaseIntentHandler):
    INTENT_TYPE = "execute_button"
    DESCRIPTION = "执行模型按钮方法"

    def run(self):
         # 1. 获取参数
        model = self.params.get("model")
        method_name = self.params.get("method_name")
        record_id = self.context.get("record_id")

        if not model or not method_name or not record_id:
            raise UserError("缺少参数 model/method_name/record_id")

 # 2. 检查模型访问权限
        self.env[model].check_access_rights('write')

        record = self.env[model].browse(int(record_id))
        if not record.exists():
            raise UserError("记录不存在")

        record.check_access_rule('write')

        # 3. 检查方法安全性（可选：定义安全白名单）
        if not hasattr(record, method_name):
            raise AccessError(f"找不到可执行方法: {method_name}")

        method = getattr(record, method_name)
        if not callable(method):
            raise AccessError(f"方法不可调用: {method_name}")

        # 4. 执行方法
        result = method()

        # 5. 标准化返回
        return result or {"message": f"按钮 {method_name} 执行成功"}
