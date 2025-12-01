# 📁 smart_core/tests/test_version_control.py
# -*- coding: utf-8 -*-
"""
版本控制功能测试
"""

import unittest
from unittest.mock import Mock

from ..core.enhanced_intent_router import EnhancedIntentRouter
from ..core.base_handler import BaseIntentHandler
from ..handlers.versioned_handler import VersionedDataHandlerV1, VersionedDataHandlerV2, VersionedDataHandlerV21

class TestVersionControl(unittest.TestCase):
    """版本控制测试用例"""
    
    def setUp(self):
        """测试初始化"""
        self.router = EnhancedIntentRouter()
        # 清空路由缓存
        self.router.routes.clear()
        self.router.route_cache.clear()
        self.router.cache_timestamps.clear()
        # 清空中件间
        self.router.middlewares.clear()
    
    def test_version_compatibility_exact_match(self):
        """测试版本精确匹配"""
        # 添加版本1的路由
        self.router.add_route("api.data", VersionedDataHandlerV1, version="1.0.0")
        
        # 创建模拟上下文
        context = Mock()
        context.params = {"version": "1.0.0"}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("api.data", context)
        
        # 验证结果
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "1.0.0")
    
    def test_version_compatibility_backward_compatible(self):
        """测试版本向后兼容"""
        # 添加版本2的路由
        self.router.add_route("api.data", VersionedDataHandlerV2, version="2.0.0")
        
        # 创建模拟上下文，请求1.x版本
        context = Mock()
        context.params = {"version": "1.5.0"}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("api.data", context)
        
        # 验证结果 - 应该匹配到2.0.0版本的处理程序
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "2.0.0")
    
    def test_version_compatibility_incompatible(self):
        """测试版本不兼容"""
        # 添加版本1的路由
        self.router.add_route("api.data", VersionedDataHandlerV1, version="1.0.0")
        
        # 创建模拟上下文，请求2.x版本
        context = Mock()
        context.params = {"version": "2.0.0"}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("api.data", context)
        
        # 验证结果 - 应该找不到匹配的处理程序
        self.assertFalse(result["ok"])
        self.assertIn("找不到意图对应 Handler", result["error"]["message"])
    
    def test_multiple_versions_same_intent(self):
        """测试同一意图的多个版本"""
        # 添加多个版本的路由
        self.router.add_route("api.data", VersionedDataHandlerV1, version="1.0.0")
        self.router.add_route("api.data", VersionedDataHandlerV2, version="2.0.0")
        self.router.add_route("api.data", VersionedDataHandlerV21, version="2.1.0")
        
        # 测试版本1.0.0
        context = Mock()
        context.params = {"version": "1.0.0"}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        result = self.router.dispatch("api.data", context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "1.0.0")
        
        # 测试版本2.0.0
        context.params = {"version": "2.0.0"}
        result = self.router.dispatch("api.data", context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "2.0.0")
        
        # 测试版本2.1.0
        context.params = {"version": "2.1.0"}
        result = self.router.dispatch("api.data", context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "2.1.0")
    
    def test_no_version_specified(self):
        """测试未指定版本"""
        # 添加版本2的路由
        self.router.add_route("api.data", VersionedDataHandlerV2, version="2.0.0")
        
        # 创建模拟上下文，不指定版本
        context = Mock()
        context.params = {}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("api.data", context)
        
        # 验证结果
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "2.0.0")
    
    def test_versioned_parameterized_route(self):
        """测试带版本的参数化路由"""
        # 添加带版本的参数化路由
        self.router.add_route("api.model.{model_name}", VersionedDataHandlerV1, version="1.0.0")
        
        # 创建模拟上下文
        context = Mock()
        context.params = {"version": "1.0.0"}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("api.model.res.partner", context)
        
        # 验证结果
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["model"], "res.partner")
        self.assertEqual(result["data"]["version"], "1.0.0")

if __name__ == '__main__':
    unittest.main()