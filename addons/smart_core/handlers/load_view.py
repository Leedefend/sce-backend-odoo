# 📁 smart_core/handlers/load_view.py
from ..core.base_handler import BaseIntentHandler
from ..view.universal_parser import UniversalViewSemanticParser

class LoadModelViewHandler(BaseIntentHandler):
    INTENT_TYPE = "load_view"
    DESCRIPTION = "加载模型视图结构"

    def run(self, **_kwargs):
        model_name = self.params.get("model")
        view_type = self.params.get("view_type")
        view_id = self.params.get("view_id")

        if not model_name or not view_type:
            return {
                "status": "error",
                "code": 400,
                "message": "缺少必要参数 model 或 view_type",
                "data": None
            }

        View = self.env["ir.ui.view"]

        try:
            if view_id:
                # 直接用给定 ID
                view = self.env[model_name].get_view(view_id=int(view_id), view_type=view_type)
            else:

                # 如果默认视图类型不匹配，则用 search 找对应类型
                default_view = View.search([("model", "=", model_name), ("type", "=", view_type)], limit=1)
                if not default_view:
                    return {"status": "error", "code": 404, "message": f"未找到模型 {model_name} 的 {view_type} 视图"}
                view = self.env[model_name].get_view(view_id=default_view.id, view_type=view_type)
                

            if not view:
                return {
                    "status": "error",
                    "code": 404,
                    "message": f"未找到模型 {model_name} 的 {view_type} 视图",
                    "data": None
                }


           # 2. 调用解析器
            parser = UniversalViewSemanticParser(
                self.env,
                model=model_name,
                view_type=view_type,
                view_id=view_id,
                context=self.params
            )
            result = parser.parse()

            # 3. 返回结果
            return result

        except Exception as e:
            return {
                "status": "error",
                "code": 500,
                "message": str(e),
                "data": None
            }
