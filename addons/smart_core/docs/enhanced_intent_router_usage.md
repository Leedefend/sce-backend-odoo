# 增强意图路由机制使用指南

## 概述

增强意图路由机制提供了比基础路由更强大的功能，包括：
- 参数化路由支持
- 中间件机制
- 性能监控
- 缓存机制
- 版本控制

## 快速开始

### 1. 创建处理程序

```python
from ..core.base_handler import BaseIntentHandler
from typing import Tuple, Dict, Any

class MyEnhancedHandler(BaseIntentHandler):
    """示例增强处理程序"""
    INTENT_TYPE = "my.enhanced.intent"
    DESCRIPTION = "示例增强意图处理程序"
    VERSION = "1.0.0"
    
    def handle(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # 获取参数
        param1 = self.get_str("param1", "default_value")
        param2 = self.get_int("param2", 0)
        
        # 处理业务逻辑
        data = {
            "param1": param1,
            "param2": param2,
            "message": "处理成功"
        }
        
        meta = {
            "processed_at": time.time()
        }
        
        return data, meta
```

### 2. 注册路由

路由可以通过两种方式注册：

#### 方式一：在处理程序中定义INTENT_TYPE（推荐）

```python
class MyEnhancedHandler(BaseIntentHandler):
    INTENT_TYPE = "my.enhanced.intent"  # 自动注册
```

#### 方式二：手动注册

```python
from ..core.enhanced_intent_router import enhanced_router

# 手动注册路由
enhanced_router.add_route("my.custom.route", MyEnhancedHandler)
```

### 3. 参数化路由

支持带参数的路由模式：

```python
# 注册参数化路由
enhanced_router.add_route("model/{model_name}/view/{view_type}", ModelViewHandler)

# 对应的处理程序
class ModelViewHandler(BaseIntentHandler):
    def handle(self):
        # 从路径参数获取值
        model_name = self.get_path_param("model_name")
        view_type = self.get_path_param("view_type")
        
        # 处理逻辑
        return {"model": model_name, "view": view_type}, {}
```

## 中间件机制

### 内置中间件

系统提供了以下内置中间件：

1. **日志记录中间件** - 记录请求和响应日志
2. **性能监控中间件** - 监控处理耗时
3. **异常处理中间件** - 统一异常处理
4. **请求限流中间件** - 限制请求频率
5. **缓存中间件** - 缓存响应结果

### 自定义中间件

创建自定义中间件：

```python
from ..core.middlewares import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    def process_request(self, intent_name: str, context: Any) -> bool:
        # 请求处理前的逻辑
        # 返回True继续处理，返回False中断处理
        return True
    
    def process_response(self, intent_name: str, context: Any, result: Dict) -> Dict:
        # 响应处理后的逻辑
        return result
    
    def process_exception(self, intent_name: str, context: Any, exception: Exception) -> Exception:
        # 异常处理逻辑
        return exception
```

### 注册中间件

```python
from ..core.enhanced_intent_router import enhanced_router
from .middlewares import CustomMiddleware

# 注册中间件
enhanced_router.add_middleware(CustomMiddleware("custom_middleware"))
```

## 高级功能

### 1. 缓存机制

处理程序可以利用缓存提高性能：

```python
class CachedHandler(BaseIntentHandler):
    def handle(self):
        # 生成缓存键
        cache_key = self.get_cache_key("my_data")
        
        # 尝试从缓存获取数据
        cached_data = self.cache_get(cache_key)
        if cached_data is not None:
            return cached_data, {}
        
        # 执行实际业务逻辑
        data = self._fetch_data_from_database()
        
        # 缓存结果
        self.cache_set(cache_key, data, ttl=300)  # 缓存5分钟
        
        return data, {}
```

### 2. 版本控制

处理程序支持版本控制：

```python
class VersionedHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data"
    VERSION = "2.1.0"
    
    def handle(self):
        # 检查客户端请求的版本
        required_version = self.get_str("version")
        if required_version and not self.is_version_compatible(required_version):
            return self.err(400, f"不兼容的版本: {required_version}")
        
        # 处理逻辑
        return {"version": self.VERSION}, {}
```

### 3. 权限控制

```python
class SecureHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["base.group_user"]  # 需要的用户组
    
    def handle(self):
        # 检查特定模型权限
        self.check_model_access("res.partner", "read")
        
        # 动态添加权限要求
        self.require_groups(["base.group_system"])
        
        # 处理逻辑
        return {"data": "secure_data"}, {}
```

## API端点

### 基础路由端点

```
POST /api/v1/intent
Content-Type: application/json

{
  "intent": "my.enhanced.intent",
  "params": {
    "param1": "value1",
    "param2": 123
  },
  "ctx": {
    "lang": "zh_CN",
    "tz": "Asia/Shanghai"
  }
}
```

### 增强路由端点

```
POST /api/v2/intent
Content-Type: application/json

{
  "intent": "model/res.partner/view/form",
  "params": {
    "id": 1
  },
  "ctx": {
    "lang": "zh_CN",
    "tz": "Asia/Shanghai"
  }
}
```

## 最佳实践

### 1. 处理程序设计

```python
class BestPracticeHandler(BaseIntentHandler):
    INTENT_TYPE = "best.practice"
    DESCRIPTION = "最佳实践示例"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]
    ETAG_ENABLED = True
    
    def handle(self):
        # 1. 参数验证
        required_params = ["name", "email"]
        missing_params = self.validate_params(required_params)
        if missing_params:
            return self.err(400, f"缺少必需参数: {missing_params}")
        
        # 2. 权限检查
        self.check_model_access("res.partner", "write")
        
        # 3. ETag检查
        etag = self.make_etag(view_hash="partner_form")
        not_modified_response = self.not_modified_if_match(etag)
        if not_modified_response:
            return not_modified_response
        
        # 4. 业务逻辑
        data = self._process_data()
        
        # 5. 返回结果
        return data, {"etag": etag}
    
    def _process_data(self):
        # 实际业务逻辑
        return {"status": "success"}
```

### 2. 错误处理

```python
class ErrorHandler(BaseIntentHandler):
    def handle(self):
        try:
            # 可能出错的逻辑
            result = self._risky_operation()
            return result, {}
        except ValueError as e:
            return self.err(400, f"参数错误: {str(e)}")
        except PermissionError as e:
            return self.err(403, f"权限不足: {str(e)}")
        except Exception as e:
            self.log_error(f"处理异常: {str(e)}")
            return self.err(500, "服务器内部错误")
```

### 3. 日志记录

```python
class LoggingHandler(BaseIntentHandler):
    def handle(self):
        # 开始处理
        self.log_info("开始处理业务逻辑")
        
        # 计时器
        self.start_timer("data_processing")
        
        # 处理逻辑
        data = self._process_data()
        
        # 停止计时器
        elapsed = self.stop_timer("data_processing")
        
        # 完成处理
        self.log_info(f"业务逻辑处理完成，耗时: {elapsed}ms")
        
        return data, {"processing_time": elapsed}
```

## 测试

### 单元测试示例

```python
import unittest
from unittest.mock import Mock

from ..core.enhanced_intent_router import EnhancedIntentRouter
from ..core.base_handler import BaseIntentHandler

class TestHandler(BaseIntentHandler):
    INTENT_TYPE = "test.handler"
    
    def handle(self):
        return {"message": "test"}, {}

class TestEnhancedRouter(unittest.TestCase):
    def setUp(self):
        self.router = EnhancedIntentRouter()
        self.router.routes.clear()
    
    def test_route_dispatch(self):
        # 注册路由
        self.router.add_route("test.handler", TestHandler)
        
        # 创建上下文
        context = Mock()
        context.params = {}
        context.ctx = {}
        context.options = {}
        context.trace_id = "test"
        
        # 分发意图
        result = self.router.dispatch("test.handler", context)
        
        # 验证结果
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["message"], "test")
```

通过以上指南，您可以充分利用增强意图路由机制提供的强大功能，构建高效、可维护的后端服务。