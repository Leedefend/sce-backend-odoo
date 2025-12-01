# 📁 smart_core/core/exceptions.py
# -*- coding: utf-8 -*-
"""
自定义异常类
用于增强错误处理和异常管理机制
"""

class SmartCoreException(Exception):
    """智能核心异常基类"""
    def __init__(self, message: str, code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class IntentException(SmartCoreException):
    """意图处理异常"""
    def __init__(self, message: str, code: int = 500, details: dict = None):
        super().__init__(message, code, details)

class IntentNotFoundException(IntentException):
    """意图未找到异常"""
    def __init__(self, intent_name: str, details: dict = None):
        message = f"找不到意图对应 Handler：{intent_name}"
        super().__init__(message, 404, {"intent": intent_name, **(details or {})})

class IntentBadRequestException(IntentException):
    """意图请求格式错误异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 400, details)

class IntentPermissionException(IntentException):
    """意图权限异常"""
    def __init__(self, message: str, required_groups: list = None, details: dict = None):
        super().__init__(message, 403, {"required_groups": required_groups, **(details or {})})

class IntentVersionException(IntentException):
    """意图版本异常"""
    def __init__(self, message: str, handler_version: str = None, requested_version: str = None, details: dict = None):
        super().__init__(message, 400, {
            "handler_version": handler_version,
            "requested_version": requested_version,
            **(details or {})
        })

class IntentValidationException(IntentException):
    """意图参数验证异常"""
    def __init__(self, message: str, missing_params: list = None, invalid_params: dict = None, details: dict = None):
        super().__init__(message, 400, {
            "missing_params": missing_params,
            "invalid_params": invalid_params,
            **(details or {})
        })

class IntentProcessingException(IntentException):
    """意图处理过程异常"""
    def __init__(self, message: str, error_type: str = None, details: dict = None):
        super().__init__(message, 500, {"error_type": error_type, **(details or {})})

class IntentThrottlingException(IntentException):
    """意图限流异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 429, details)  # 429 Too Many Requests

class IntentCacheException(IntentException):
    """意图缓存异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 500, details)

class IntentMiddlewareException(IntentException):
    """意图中间件异常"""
    def __init__(self, message: str, middleware_name: str = None, details: dict = None):
        super().__init__(message, 500, {"middleware_name": middleware_name, **(details or {})})

# 兼容性异常类（保持与原有代码的兼容性）
class IntentNotFound(Exception): 
    """兼容性异常类"""
    pass

class IntentBadRequest(Exception): 
    """兼容性异常类"""
    pass