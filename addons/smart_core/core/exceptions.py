# 📁 smart_core/core/exceptions.py
# -*- coding: utf-8 -*-
"""
自定义异常类
用于增强错误处理和异常管理机制
"""

# Error codes (contract v0.1)
BAD_REQUEST = "BAD_REQUEST"
AUTH_REQUIRED = "AUTH_REQUIRED"
PERMISSION_DENIED = "PERMISSION_DENIED"
INTENT_NOT_FOUND = "INTENT_NOT_FOUND"
VALIDATION_ERROR = "VALIDATION_ERROR"
FEATURE_DISABLED = "FEATURE_DISABLED"
LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
INTERNAL_ERROR = "INTERNAL_ERROR"

DEFAULT_API_VERSION = "v1"
DEFAULT_CONTRACT_VERSION = "1.0.0"

_HTTP_STATUS_TO_CODE = {
    400: BAD_REQUEST,
    401: AUTH_REQUIRED,
    403: PERMISSION_DENIED,
    404: INTENT_NOT_FOUND,
    422: VALIDATION_ERROR,
    429: LIMIT_EXCEEDED,
    500: INTERNAL_ERROR,
}


def map_http_status_to_code(status: int, default: str = INTERNAL_ERROR) -> str:
    try:
        return _HTTP_STATUS_TO_CODE.get(int(status), default)
    except Exception:
        return default


def build_error_envelope(
    *,
    code: str,
    message: str,
    trace_id: str | None = None,
    details: dict | None = None,
    hint: str | None = None,
    fields: dict | None = None,
    retryable: bool | None = None,
    api_version: str = DEFAULT_API_VERSION,
    contract_version: str = DEFAULT_CONTRACT_VERSION,
) -> dict:
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    if hint:
        error["hint"] = hint
    if fields:
        error["fields"] = fields
    if retryable is not None:
        error["retryable"] = bool(retryable)

    meta = {
        "trace_id": trace_id,
        "api_version": api_version,
        "contract_version": contract_version,
    }
    return {"ok": False, "error": error, "meta": meta}

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
