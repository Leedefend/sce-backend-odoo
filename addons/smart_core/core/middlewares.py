# 📁 smart_core/core/middlewares.py
# -*- coding: utf-8 -*-
"""
意图中间件机制
支持权限检查、日志记录、性能监控等
"""

import time
import logging
from typing import Callable, Dict, Any, List
from functools import wraps

_logger = logging.getLogger(__name__)
SOURCE_KIND = "intent_middleware_runtime_pipeline"
SOURCE_AUTHORITIES = ("intent_request_context", "handler_result", "in_memory_runtime_cache")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "write_proxy": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "intent_middlewares",
    }

class BaseMiddleware:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> Dict[str, Any]:
        return source_authority_contract()

    """中间件基类"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
    
    def process_request(self, intent_name: str, context: Any) -> bool:
        """
        处理请求前的中间件逻辑
        返回True表示继续处理，返回False表示中断处理
        """
        return True
    
    def process_response(self, intent_name: str, context: Any, result: Dict) -> Dict:
        """处理响应后的中间件逻辑"""
        return result
    
    def process_exception(self, intent_name: str, context: Any, exception: Exception) -> Exception:
        """处理异常的中间件逻辑"""
        return exception

class LoggingMiddleware(BaseMiddleware):
    """日志记录中间件"""
    
    def process_request(self, intent_name: str, context: Any) -> bool:
        params = getattr(context, "params", {})
        _logger.info(f"开始处理意图: {intent_name}, 参数: {params}")
        return True
    
    def process_response(self, intent_name: str, context: Any, result: Dict) -> Dict:
        _logger.info(f"意图处理完成: {intent_name}")
        return result
    
    def process_exception(self, intent_name: str, context: Any, exception: Exception) -> Exception:
        _logger.error(f"意图处理异常: {intent_name}, 错误: {str(exception)}")
        return exception

class PerformanceMonitoringMiddleware(BaseMiddleware):
    """性能监控中间件"""
    
    def process_request(self, intent_name: str, context: Any) -> bool:
        setattr(context, "_start_time", time.time())
        return True
    
    def process_response(self, intent_name: str, context: Any, result: Dict) -> Dict:
        start_time = getattr(context, "_start_time", None)
        if start_time:
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            _logger.info(f"意图 {intent_name} 处理耗时: {elapsed_time:.2f}ms")
            
            # 将性能数据添加到结果中
            if isinstance(result, dict):
                meta = result.setdefault("meta", {})
                meta["elapsed_time_ms"] = round(elapsed_time, 2)
        
        return result

class RequestThrottlingMiddleware(BaseMiddleware):
    """请求限流中间件"""
    
    def __init__(self, name: str = None, max_requests: int = 100, time_window: int = 60):
        super().__init__(name)
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_counts = {}  # 简单的内存存储，生产部署中应使用 Redis 等
    
    def process_request(self, intent_name: str, context: Any) -> bool:
        # 获取用户ID
        uid = getattr(context, "uid", None)
        if uid is None:
            return True  # 无法识别用户，不限流
        
        current_time = time.time()
        window_key = f"{uid}:{int(current_time // self.time_window)}"
        
        # 更新请求计数
        self.request_counts[window_key] = self.request_counts.get(window_key, 0) + 1
        
        # 检查是否超过限制
        if self.request_counts[window_key] > self.max_requests:
            _logger.warning(f"用户 {uid} 超过请求限制: {self.request_counts[window_key]} > {self.max_requests}")
            # 在生产部署中，这里应该抛出一个限流异常
            # raise ThrottlingException("请求过于频繁，请稍后再试")
            return False  # 中断处理
        
        return True

class ExceptionHandlingMiddleware(BaseMiddleware):
    """异常处理中间件"""
    
    def process_exception(self, intent_name: str, context: Any, exception: Exception) -> Exception:
        # 记录异常详细信息
        _logger.exception(f"意图 {intent_name} 处理过程中发生异常")
        
        # 可以在这里进行异常转换或添加额外信息
        # 例如，将特定异常转换为用户友好的错误信息
        
        return exception

class CachingMiddleware(BaseMiddleware):
    """缓存中间件"""
    
    def __init__(self, name: str = None, cache_ttl: int = 300):
        super().__init__(name)
        self.cache_ttl = cache_ttl
        self.cache = {}  # 简单的内存缓存，生产部署中应使用 Redis 等
    
    def process_request(self, intent_name: str, context: Any) -> bool:
        # 生成缓存键
        cache_key = self._generate_cache_key(intent_name, context)
        
        # 检查缓存
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            # 将缓存结果附加到上下文，供后续处理使用
            setattr(context, "_cached_result", cached_result)
            return False  # 中断处理，直接返回缓存结果
        
        # 继续处理
        setattr(context, "_cache_key", cache_key)
        return True
    
    def process_response(self, intent_name: str, context: Any, result: Dict) -> Dict:
        # 获取缓存键
        cache_key = getattr(context, "_cache_key", None)
        if cache_key:
            # 缓存结果
            self._set_to_cache(cache_key, result, self.cache_ttl)
        
        return result
    
    def _generate_cache_key(self, intent_name: str, context: Any) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        params = getattr(context, "params", {})
        ctx = getattr(context, "ctx", {})
        
        # 创建缓存键
        key_data = {
            "intent": intent_name,
            "params": params,
            "ctx": ctx
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str, separators=(',', ':'))
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, key: str) -> Dict:
        """从缓存获取数据"""
        cached = self.cache.get(key)
        if cached:
            data, expires_at = cached
            if time.time() < expires_at:
                return data
            else:
                # 缓存过期，删除它
                del self.cache[key]
        return None
    
    def _set_to_cache(self, key: str, data: Dict, ttl: int):
        """设置缓存数据"""
        expires_at = time.time() + ttl
        self.cache[key] = (data, expires_at)

# 内置中间件实例
DEFAULT_MIDDLEWARES = [
    LoggingMiddleware("logging"),
    PerformanceMonitoringMiddleware("performance"),
    ExceptionHandlingMiddleware("exception"),
    # RequestThrottlingMiddleware("throttling"),  # 默认不启用限流
    # CachingMiddleware("caching"),  # 默认不启用缓存
]

def apply_middlewares(middlewares: List[BaseMiddleware]):
    """应用中间件的装饰器工厂"""
    def decorator(handler_func: Callable):
        @wraps(handler_func)
        def wrapper(intent_name: str, context: Any):
            # 请求处理阶段
            for middleware in middlewares:
                try:
                    if not middleware.process_request(intent_name, context):
                        # 如果中间件返回False，检查是否有缓存结果
                        cached_result = getattr(context, "_cached_result", None)
                        if cached_result is not None:
                            return cached_result
                        # 否则中断处理
                        return {"ok": False, "error": "处理被中间件中断", "code": 400}
                except Exception as e:
                    _logger.error(f"中间件 {middleware.name} 处理请求时发生异常: {str(e)}")
                    # 可以选择是否继续处理
            
            # 执行实际的处理函数
            try:
                result = handler_func(intent_name, context)
            except Exception as e:
                # 异常处理阶段
                processed_exception = e
                for middleware in reversed(middlewares):  # 反向处理异常
                    try:
                        processed_exception = middleware.process_exception(intent_name, context, processed_exception)
                    except Exception as middleware_exception:
                        _logger.error(f"中间件 {middleware.name} 处理异常时发生异常: {str(middleware_exception)}")
                
                # 重新抛出处理后的异常
                raise processed_exception
            
            # 响应处理阶段
            processed_result = result
            for middleware in reversed(middlewares):  # 反向处理响应
                try:
                    processed_result = middleware.process_response(intent_name, context, processed_result)
                except Exception as e:
                    _logger.error(f"中间件 {middleware.name} 处理响应时发生异常: {str(e)}")
                    # 可以选择是否继续处理
            
            return processed_result
        
        return wrapper
    return decorator
