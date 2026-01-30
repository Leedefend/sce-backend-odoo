# 📁 smart_core/tests/test_enhanced_intent_router.py
# -*- coding: utf-8 -*-
"""
增强意图路由器测试
"""

import unittest
import json
from unittest.mock import Mock, patch

from ..core.enhanced_intent_router import EnhancedIntentRouter, RouteRule
from ..core.middlewares import LoggingMiddleware, PerformanceMonitoringMiddleware

class TestHandler:
    """测试处理程序"""
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def run(self):
        return {"ok": True, "data": {"message": "test"}, "meta": {}}

class TestParamHandler:
    """带参数的测试处理程序"""
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def run(self):
        params = getattr(self.context, "path_params", {}) or {}
        model_name = params.get("model_name", "default")
        return {"ok": True, "data": {"model_name": model_name}, "meta": {}}

class TestEnhancedIntentRouter(unittest.TestCase):
    """增强意图路由器测试用例"""
    
    def setUp(self):
        """测试初始化"""
        self.router = EnhancedIntentRouter()
        # 清空路由缓存
        self.router.routes.clear()
        self.router.route_cache.clear()
        self.router.cache_timestamps.clear()
        # 清空中件间
        self.router.middlewares.clear()
    
    def test_add_route(self):
        """测试添加路由"""
        # 添加路由
        self.router.add_route("test.route", TestHandler)
        
        # 验证路由已添加
        self.assertIn("test.route", self.router.routes)
        route_rules = self.router.routes["test.route"]
        self.assertTrue(route_rules)
        route_rule = route_rules[0]
        self.assertEqual(route_rule.pattern, "test.route")
        self.assertEqual(route_rule.handler_cls, TestHandler)
    
    def test_remove_route(self):
        """测试移除路由"""
        # 添加路由
        self.router.add_route("test.route", TestHandler)
        self.assertIn("test.route", self.router.routes)
        
        # 移除路由
        self.router.remove_route("test.route")
        self.assertNotIn("test.route", self.router.routes)
    
    def test_match_route_exact(self):
        """测试精确路由匹配"""
        # 添加路由
        self.router.add_route("test.intent", TestHandler)
        
        # 匹配路由
        route_rule, params = self.router.match_route("test.intent")
        
        # 验证匹配结果
        self.assertIsNotNone(route_rule)
        self.assertEqual(route_rule.handler_cls, TestHandler)
        self.assertEqual(params, {})
    
    def test_match_route_parameterized(self):
        """测试参数化路由匹配"""
        # 添加参数化路由
        self.router.add_route("test.model.{model_name}", TestParamHandler)
        
        # 匹配路由
        route_rule, params = self.router.match_route("test.model.res.partner")
        
        # 验证匹配结果
        self.assertIsNotNone(route_rule)
        self.assertEqual(route_rule.handler_cls, TestParamHandler)
        self.assertEqual(params, {"model_name": "res.partner"})
    
    def test_add_middleware(self):
        """测试添加中间件"""
        # 创建中间件实例
        middleware = LoggingMiddleware()
        
        # 添加中间件
        self.router.add_middleware(middleware)
        
        # 验证中间件已添加
        self.assertIn(middleware, self.router.middlewares)
        self.assertEqual(len(self.router.middlewares), 1 + len(self.router.middlewares) - 1)  # 考虑默认中间件
    
    def test_remove_middleware(self):
        """测试移除中间件"""
        # 创建中间件实例
        middleware = LoggingMiddleware()
        
        # 添加中间件
        self.router.add_middleware(middleware)
        self.assertIn(middleware, self.router.middlewares)
        
        # 移除中间件
        result = self.router.remove_middleware(middleware.name)
        self.assertTrue(result)
    
    def test_dispatch_success(self):
        """测试成功分发意图"""
        # 添加路由
        self.router.add_route("test.intent", TestHandler)
        
        # 创建模拟上下文
        context = Mock()
        context.params = {}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("test.intent", context)
        
        # 验证结果
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["message"], "test")
    
    def test_dispatch_not_found(self):
        """测试分发不存在的意图"""
        # 创建模拟上下文
        context = Mock()
        context.params = {}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发不存在的意图
        result = self.router.dispatch("nonexistent.intent", context)
        
        # 验证结果
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertIn("找不到意图对应 Handler", result["error"]["message"])
    
    def test_middleware_process_request(self):
        """测试中间件请求处理"""
        # 添加性能监控中间件
        middleware = PerformanceMonitoringMiddleware()
        self.router.add_middleware(middleware)
        
        # 添加路由
        self.router.add_route("test.intent", TestHandler)
        
        # 创建模拟上下文
        context = Mock()
        context.params = {}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test_trace_id"
        
        # 分发意图
        result = self.router.dispatch("test.intent", context)
        
        # 验证中间件是否正常工作
        self.assertTrue(result["ok"])
        self.assertIn("meta", result)
        self.assertIn("elapsed_time_ms", result["meta"])
    
    def test_route_caching(self):
        """测试路由缓存"""
        # 添加路由
        self.router.add_route("test.intent", TestHandler)
        
        # 第一次匹配
        route_rule1, params1 = self.router.match_route("test.intent")
        
        # 第二次匹配（应该从缓存获取）
        route_rule2, params2 = self.router.match_route("test.intent")
        
        # 验证两次匹配结果相同
        self.assertEqual(route_rule1, route_rule2)
        self.assertEqual(params1, params2)
    
    def test_version_control(self):
        """测试版本控制"""
        # 添加带版本的路由
        self.router.add_route("test.versioned", TestHandler, version="1.0.0")
        
        # 验证路由已添加
        self.assertIn("test.versioned", self.router.routes)
        route_rules = self.router.routes["test.versioned"]
        self.assertTrue(route_rules)
        self.assertEqual(route_rules[0].version, "1.0.0")

if __name__ == '__main__':
    unittest.main()
