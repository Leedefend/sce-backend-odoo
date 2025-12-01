# 意图路由版本控制使用指南

## 概述

版本控制机制允许您为意图处理程序定义版本，并支持向后兼容性检查。这使得API能够随着时间演进，同时保持与旧客户端的兼容性。

## 版本控制基础

### 1. 定义处理程序版本

在处理程序类中定义VERSION属性：

```python
from ..core.base_handler import BaseIntentHandler

class MyHandler(BaseIntentHandler):
    INTENT_TYPE = "my.api"
    VERSION = "1.0.0"  # 定义处理程序版本
    DESCRIPTION = "我的API处理程序"
```

### 2. 注册带版本的路由

```python
from ..core.enhanced_intent_router import enhanced_router

# 自动从处理程序类获取版本
enhanced_router.add_route("my.api", MyHandler)

# 或者手动指定版本
enhanced_router.add_route("my.api", MyHandler, version="1.0.0")
```

### 3. 客户端请求特定版本

客户端可以通过参数指定所需的API版本：

```json
{
  "intent": "my.api",
  "params": {
    "version": "1.0.0"
  }
}
```

## 版本兼容性规则

版本控制系统遵循以下兼容性规则：

1. **精确匹配**：请求版本与处理程序版本完全相同
2. **向后兼容**：请求版本大于或等于处理程序版本
   - 主版本号必须相同（例如1.x.x只能匹配1.x.x）
   - 次版本号处理程序版本不能大于请求版本
   - 修订版本号处理程序版本不能大于请求版本

### 兼容性示例

| 处理程序版本 | 请求版本 | 是否兼容 | 说明 |
|-------------|----------|----------|------|
| 1.0.0 | 1.0.0 | ✓ | 精确匹配 |
| 1.0.0 | 1.5.0 | ✓ | 向后兼容 |
| 1.0.0 | 2.0.0 | ✗ | 主版本号不同 |
| 1.5.0 | 1.0.0 | ✗ | 请求版本低于处理程序版本 |
| 2.0.0 | 1.5.0 | ✗ | 主版本号不同 |

## 在处理程序中使用版本控制

### 1. 检查版本兼容性

```python
class VersionedHandler(BaseIntentHandler):
    INTENT_TYPE = "api.data"
    VERSION = "2.0.0"
    
    def handle(self):
        # 获取客户端请求的版本
        required_version = self.get_str("version")
        
        # 检查版本兼容性
        if required_version and not self.check_version_compatibility(required_version):
            return self.err(400, f"不兼容的版本: {required_version}")
        
        # 根据版本提供不同的功能
        if self.is_version_compatible("2.0.0"):
            # 提供2.0.0版本的功能
            data = self._get_advanced_data()
        else:
            # 提供基础功能
            data = self._get_basic_data()
        
        return data, {"api_version": self.VERSION}
```

### 2. 强制要求特定版本

```python
class StrictVersionHandler(BaseIntentHandler):
    INTENT_TYPE = "api.strict"
    VERSION = "1.5.0"
    
    def handle(self):
        # 强制要求特定版本
        try:
            self.require_version("1.5.0")
        except ValueError as e:
            return self.err(400, str(e))
        
        # 处理逻辑
        return {"message": "版本检查通过"}, {}
```

## 多版本处理程序管理

### 1. 为同一意图注册多个版本

```python
# 注册同一意图的多个版本
enhanced_router.add_route("api.users", UserHandlerV1, version="1.0.0")
enhanced_router.add_route("api.users", UserHandlerV2, version="2.0.0")
enhanced_router.add_route("api.users", UserHandlerV21, version="2.1.0")
```

### 2. 版本化处理程序示例

```python
class UserHandlerV1(BaseIntentHandler):
    INTENT_TYPE = "api.users"
    VERSION = "1.0.0"
    
    def handle(self):
        # 版本1的功能
        users = self._get_basic_user_list()
        return {
            "users": users,
            "version": self.VERSION
        }, {}

class UserHandlerV2(BaseIntentHandler):
    INTENT_TYPE = "api.users"
    VERSION = "2.0.0"
    
    def handle(self):
        # 版本2的功能
        users = self._get_enhanced_user_list()
        return {
            "users": users,
            "version": self.VERSION,
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": 100
            }
        }, {}
```

## 参数化路由与版本控制

版本控制也适用于参数化路由：

```python
class VersionedModelHandler(BaseIntentHandler):
    INTENT_TYPE = "api.model.{model_name}"
    VERSION = "1.5.0"
    
    def handle(self):
        # 获取路径参数
        model_name = self.get_path_param("model_name")
        
        # 检查版本兼容性
        required_version = self.get_str("version")
        if required_version and not self.check_version_compatibility(required_version):
            return self.err(400, f"不兼容的版本: {required_version}")
        
        # 根据版本提供不同的模型信息
        if self.is_version_compatible("1.5.0"):
            model_info = self._get_detailed_model_info(model_name)
        else:
            model_info = self._get_basic_model_info(model_name)
        
        return {
            "model": model_name,
            "info": model_info,
            "version": self.VERSION
        }, {}
```

注册参数化路由：

```python
# 注册参数化路由
enhanced_router.add_route("api.model.{model_name}", VersionedModelHandler, version="1.5.0")
```

## 最佳实践

### 1. 版本规划

```python
# 遵循语义化版本控制
class GoodVersionHandler(BaseIntentHandler):
    INTENT_TYPE = "api.good"
    VERSION = "2.1.3"  # 主版本.次版本.修订版本
    # 主版本：不兼容的API修改
    # 次版本：向后兼容的功能性新增
    # 修订版本：向后兼容的问题修正
```

### 2. 版本弃用策略

```python
class DeprecationHandler(BaseIntentHandler):
    INTENT_TYPE = "api.deprecated"
    VERSION = "2.0.0"
    
    def handle(self):
        # 检查是否使用了已弃用的版本
        required_version = self.get_str("version")
        if required_version and required_version.startswith("1."):
            self.log_warning(f"使用已弃用的版本: {required_version}")
            # 可以在响应中添加弃用警告
            return {
                "data": self._process_data(),
                "warning": f"版本 {required_version} 已弃用，请升级到 2.x"
            }, {"deprecated_version": required_version}
        
        return self._process_data(), {}
```

### 3. 版本迁移指南

```python
class MigrationHandler(BaseIntentHandler):
    INTENT_TYPE = "api.migration"
    VERSION = "3.0.0"
    
    def handle(self):
        # 提供版本迁移信息
        required_version = self.get_str("version")
        
        if required_version and required_version.startswith("2."):
            return self.err(400, {
                "message": "请升级到API v3",
                "migration_guide": "/docs/migration/v2-to-v3",
                "changelog": "/docs/changelog/v3.0.0"
            })
        
        return self._process_data(), {}
```

## 测试版本控制

### 单元测试示例

```python
import unittest
from unittest.mock import Mock

from ..core.enhanced_intent_router import EnhancedIntentRouter
from ..handlers.my_handler import MyHandlerV1, MyHandlerV2

class TestVersionControl(unittest.TestCase):
    def setUp(self):
        self.router = EnhancedIntentRouter()
        self.router.routes.clear()
    
    def test_version_compatibility(self):
        # 注册多个版本
        self.router.add_route("api.test", MyHandlerV1, version="1.0.0")
        self.router.add_route("api.test", MyHandlerV2, version="2.0.0")
        
        # 测试版本1
        context = Mock()
        context.params = {"version": "1.0.0"}
        result = self.router.dispatch("api.test", context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "1.0.0")
        
        # 测试版本2
        context.params = {"version": "2.0.0"}
        result = self.router.dispatch("api.test", context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["version"], "2.0.0")
```

通过以上指南，您可以有效地使用版本控制机制来管理意图处理程序的演进，确保API的稳定性和兼容性。