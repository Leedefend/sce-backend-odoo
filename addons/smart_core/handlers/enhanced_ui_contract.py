# 📁 smart_core/handlers/enhanced_ui_contract.py
# -*- coding: utf-8 -*-
"""
增强的统一契约读取处理程序
展示如何使用增强的意图路由机制
"""

from ..core.base_handler import BaseIntentHandler
from ..core.middlewares import CachingMiddleware, RequestThrottlingMiddleware
from typing import Tuple, Dict, Any

class EnhancedUIContractHandler(BaseIntentHandler):
    """增强的统一契约读取处理程序（legacy/demo only）"""
    INTENT_TYPE = "ui.contract.enhanced"
    LEGACY_ONLY = True
    DESCRIPTION = "增强的统一契约读取处理程序"
    VERSION = "2.0.0"
    
    def handle(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理契约读取意图"""
        # 获取参数
        op = self.get_enum("op", ["menu", "model", "action_open", "nav"], "model")
        model_name = self.get_str("model")
        menu_id = self.get_int("menu_id")
        action_id = self.get_int("action_id")
        
        # 记录处理开始
        self.log_info(f"开始处理增强契约意图: op={op}, model={model_name}, menu_id={menu_id}")
        
        # 根据操作类型处理
        if op == "menu":
            return self._handle_menu_operation(menu_id)
        elif op == "model":
            return self._handle_model_operation(model_name)
        elif op == "action_open":
            return self._handle_action_operation(action_id)
        elif op == "nav":
            return self._handle_navigation_operation()
        else:
            return self.err(400, f"不支持的操作类型: {op}")
    
    def _handle_menu_operation(self, menu_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理菜单操作"""
        if not menu_id:
            return self.err(400, "菜单ID不能为空")
        
        # 模拟菜单数据获取
        menu_data = {
            "id": menu_id,
            "name": f"菜单项 {menu_id}",
            "children": [
                {"id": menu_id * 10 + 1, "name": "子菜单1"},
                {"id": menu_id * 10 + 2, "name": "子菜单2"}
            ]
        }
        
        # 检查ETag缓存
        etag = self.make_etag(view_hash="menu", extra={"menu_id": menu_id})
        not_modified_response = self.not_modified_if_match(etag)
        if not_modified_response:
            return not_modified_response
        
        data = {
            "operation": "menu",
            "menu_id": menu_id,
            "menu_data": menu_data
        }
        
        meta = {
            "etag": etag
        }
        
        return data, meta
    
    def _handle_model_operation(self, model_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理模型操作"""
        if not model_name:
            return self.err(400, "模型名称不能为空")
        
        # 验证模型访问权限
        try:
            self.check_model_access(model_name, "read")
        except Exception as e:
            return self.err(403, f"无权访问模型: {model_name}")
        
        # 模拟模型数据获取
        model_info = {
            "name": model_name,
            "fields": [
                {"name": "name", "type": "char", "string": "名称"},
                {"name": "description", "type": "text", "string": "描述"},
                {"name": "active", "type": "boolean", "string": "有效"}
            ],
            "views": [
                {"id": 1, "type": "form", "name": "表单视图"},
                {"id": 2, "type": "tree", "name": "列表视图"}
            ]
        }
        
        # 检查ETag缓存
        etag = self.make_etag(model_hash=model_name, extra={"model": model_name})
        not_modified_response = self.not_modified_if_match(etag)
        if not_modified_response:
            return not_modified_response
        
        data = {
            "operation": "model",
            "model_name": model_name,
            "model_info": model_info
        }
        
        meta = {
            "etag": etag
        }
        
        return data, meta
    
    def _handle_action_operation(self, action_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理动作操作"""
        if not action_id:
            return self.err(400, "动作ID不能为空")
        
        # 模拟动作数据获取
        action_data = {
            "id": action_id,
            "name": f"动作 {action_id}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form"
        }
        
        data = {
            "operation": "action_open",
            "action_id": action_id,
            "action_data": action_data
        }
        
        meta = {}
        
        return data, meta
    
    def _handle_navigation_operation(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理导航操作"""
        # 模拟导航数据获取
        nav_data = {
            "breadcrumbs": [
                {"name": "首页", "url": "/"},
                {"name": "应用", "url": "/apps"},
                {"name": "当前页面", "url": "/current"}
            ]
        }
        
        data = {
            "operation": "nav",
            "nav_data": nav_data
        }
        
        meta = {}
        
        return data, meta

# 带参数的路由示例处理程序
class EnhancedModelViewHandler(BaseIntentHandler):
    """增强的模型视图处理程序（legacy/demo only）"""
    INTENT_TYPE = "ui.contract.model.view"
    LEGACY_ONLY = True
    DESCRIPTION = "增强的模型视图处理程序"
    VERSION = "1.0.0"
    
    def handle(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理模型视图意图"""
        # 从路径参数获取模型名称
        model_name = self.get_path_param("model_name")
        view_type = self.get_path_param("view_type", "form")
        record_id = self.get_int("id")
        
        # 记录处理开始
        self.log_info(f"开始处理模型视图意图: model={model_name}, view_type={view_type}, id={record_id}")
        
        if not model_name:
            return self.err(400, "模型名称不能为空")
        
        # 验证模型访问权限
        try:
            self.check_model_access(model_name, "read")
        except Exception as e:
            return self.err(403, f"无权访问模型: {model_name}")
        
        # 根据视图类型处理
        if view_type == "form":
            return self._handle_form_view(model_name, record_id)
        elif view_type == "list":
            return self._handle_list_view(model_name)
        else:
            return self.err(400, f"不支持的视图类型: {view_type}")
    
    def _handle_form_view(self, model_name: str, record_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理表单视图"""
        # 模拟表单数据获取
        if record_id:
            # 编辑现有记录
            record_data = {
                "id": record_id,
                "name": f"记录 {record_id}",
                "description": f"这是记录 {record_id} 的描述"
            }
        else:
            # 创建新记录
            record_data = {
                "id": None,
                "name": "",
                "description": ""
            }
        
        # 获取模型字段信息
        fields_info = [
            {"name": "name", "type": "char", "string": "名称", "required": True},
            {"name": "description", "type": "text", "string": "描述"}
        ]
        
        data = {
            "view_type": "form",
            "model_name": model_name,
            "record_data": record_data,
            "fields_info": fields_info
        }
        
        meta = {
            "view_title": f"{model_name} - 表单视图"
        }
        
        return data, meta
    
    def _handle_list_view(self, model_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理列表视图"""
        # 模拟列表数据获取
        list_data = [
            {"id": 1, "name": "记录 1", "description": "描述 1"},
            {"id": 2, "name": "记录 2", "description": "描述 2"},
            {"id": 3, "name": "记录 3", "description": "描述 3"}
        ]
        
        # 获取模型字段信息
        fields_info = [
            {"name": "id", "type": "integer", "string": "ID"},
            {"name": "name", "type": "char", "string": "名称"},
            {"name": "description", "type": "text", "string": "描述"}
        ]
        
        data = {
            "view_type": "list",
            "model_name": model_name,
            "list_data": list_data,
            "fields_info": fields_info
        }
        
        meta = {
            "view_title": f"{model_name} - 列表视图"
        }
        
        return data, meta

# 注册额外的中间件
def register_middlewares(router):
    """注册额外的中间件"""
    # 添加缓存中间件
    router.add_middleware(CachingMiddleware("model_caching", cache_ttl=600))
    
    # 添加限流中间件
    router.add_middleware(RequestThrottlingMiddleware("model_throttling", max_requests=50, time_window=60))
