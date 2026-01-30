# 📄 smart_core/core/enhanced_intent_router.py
import re
import logging
import time
import hashlib
import json
from typing import Dict, Type, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .base_handler import BaseIntentHandler
from .exceptions import IntentNotFound, IntentBadRequest
from .middlewares import BaseMiddleware, DEFAULT_MIDDLEWARES

_logger = logging.getLogger(__name__)

@dataclass
class RouteRule:
    """路由规则数据类"""
    pattern: str
    handler_cls: Type[BaseIntentHandler]
    methods: List[str]
    priority: int
    version: Optional[str]
    is_regex: bool = False
    compiled_pattern: Optional[re.Pattern] = None
    param_names: List[str] = None

class TrieNode:
    """前缀树节点"""
    def __init__(self):
        self.children = {}
        self.handlers = []  # 存储匹配的处理器
        self.param_name = None  # 参数名称
        self.is_param = False  # 是否是参数节点

class RouteTrie:
    """路由前缀树"""
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, pattern: str, handler: RouteRule):
        """插入路由规则"""
        parts = pattern.split('/')
        node = self.root
        
        for i, part in enumerate(parts):
            if part.startswith('{') and part.endswith('}'):
                # 参数节点
                param_name = part[1:-1]
                if ':' in param_name:
                    param_name = param_name.split(':')[0]
                
                # 检查是否已存在参数节点
                param_node = None
                for child_name, child_node in node.children.items():
                    if child_node.is_param:
                        param_node = child_node
                        break
                
                if not param_node:
                    param_node = TrieNode()
                    param_node.is_param = True
                    param_node.param_name = param_name
                    node.children['*'] = param_node  # 使用*表示参数节点
                node = param_node
            else:
                # 普通节点
                if part not in node.children:
                    node.children[part] = TrieNode()
                node = node.children[part]
        
        # 在叶子节点添加处理器
        node.handlers.append(handler)
    
    def match(self, path: str) -> Tuple[List[RouteRule], Dict[str, str]]:
        """匹配路由路径"""
        parts = path.split('/')
        return self._match_recursive(self.root, parts, 0, {})
    
    def _match_recursive(self, node: TrieNode, parts: List[str], index: int,
                        params: Dict[str, str]) -> Tuple[List[RouteRule], Dict[str, str]]:
        """递归匹配路由"""
        if index == len(parts):
            # 匹配成功，返回全部处理器列表
            return list(node.handlers or []), params
        
        part = parts[index]
        
        # 精确匹配
        if part in node.children:
            handlers, out_params = self._match_recursive(node.children[part], parts, index + 1, params)
            if handlers:
                return handlers, out_params
        
        # 参数匹配
        if '*' in node.children:
            param_node = node.children['*']
            new_params = params.copy()
            new_params[param_node.param_name] = part
            handlers, out_params = self._match_recursive(param_node, parts, index + 1, new_params)
            if handlers:
                return handlers, out_params
        
        return [], params

class Middleware:
    """中间件基类"""
    async def process_request(self, context: Any) -> Optional[Dict]:
        """处理请求前调用"""
        return None
    
    async def process_response(self, context: Any, response: Dict) -> Dict:
        """处理响应后调用"""
        return response

class EnhancedIntentRouter:
    """增强的意图路由器"""
    
    def __init__(self):
        self.routes: Dict[str, List[RouteRule]] = {}
        self.trie = RouteTrie()
        self.middlewares: List[BaseMiddleware] = []
        self.route_cache: Dict[str, Tuple[RouteRule, Dict[str, str]]] = {}
        self.cache_ttl = 300  # 缓存5分钟
        self.cache_timestamps: Dict[str, float] = {}
        
        # 添加默认中间件
        for middleware in DEFAULT_MIDDLEWARES:
            self.add_middleware(middleware)
    
    def add_route(self, pattern: str, handler_cls: Type[BaseIntentHandler], 
                  methods: List[str] = None, priority: int = 0,
                  version: str = None) -> None:
        """添加路由规则"""
        if methods is None:
            methods = ['GET', 'POST']
        
        # 如果处理程序类有VERSION属性，使用它作为默认版本
        if version is None and hasattr(handler_cls, 'VERSION'):
            version = getattr(handler_cls, 'VERSION', None)
        
        # 处理参数化路由
        param_names = []
        clean_pattern = pattern
        if '{' in pattern and '}' in pattern:
            # 提取参数名称
            import re
            param_matches = re.findall(r'\{([^}]+)\}', pattern)
            for match in param_matches:
                if ':' in match:
                    param_name = match.split(':')[0]
                else:
                    param_name = match
                param_names.append(param_name)
            # 清理模式用于存储
            clean_pattern = re.sub(r'\{[^}]+\}', '*', pattern)
        
        route_rule = RouteRule(
            pattern=pattern,
            handler_cls=handler_cls,
            methods=methods,
            priority=priority,
            version=version,
            param_names=param_names
        )
        
        # 添加到路由表（支持同一 intent 多版本）
        self.routes.setdefault(pattern, [])
        self.routes[pattern].append(route_rule)
        
        # 添加到前缀树
        self.trie.insert(pattern, route_rule)
        
        _logger.info(f"Added route: {pattern} -> {handler_cls.__name__} (version: {version})")
    
    def add_versioned_route(self, pattern: str, handler_cls: Type[BaseIntentHandler], 
                           methods: List[str] = None, priority: int = 0) -> None:
        """添加带版本的路由规则"""
        # 从处理程序类获取版本
        version = getattr(handler_cls, 'VERSION', None)
        
        # 添加路由
        self.add_route(pattern, handler_cls, methods, priority, version)
        
        # 如果有版本信息，也注册一个带版本参数的路由
        if version:
            versioned_pattern = f"{pattern}:version:{version}"
            self.add_route(versioned_pattern, handler_cls, methods, priority, version)
    
    def remove_route(self, pattern: str) -> None:
        """移除路由规则"""
        if pattern in self.routes:
            del self.routes[pattern]
            # 清理缓存
            self.route_cache.clear()
            self.cache_timestamps.clear()
            _logger.info(f"Removed route: {pattern}")
    
    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """添加中间件"""
        self.middlewares.append(middleware)
        _logger.info(f"Added middleware: {middleware.name}")
    
    def remove_middleware(self, middleware_name: str) -> bool:
        """移除中间件"""
        for i, middleware in enumerate(self.middlewares):
            if middleware.name == middleware_name:
                del self.middlewares[i]
                _logger.info(f"Removed middleware: {middleware_name}")
                return True
        return False
    
    def _attach_to_context(self, context: Any, *, intent: str, params: Dict, 
                          ctx: Dict, options: Dict, trace_id: str, path_params: Dict = None) -> None:
        """将解析好的参数挂到 context"""
        setattr(context, "intent", intent)
        setattr(context, "params", params or {})
        setattr(context, "ctx", ctx or {})
        setattr(context, "options", options or {})
        setattr(context, "trace_id", trace_id)
        if path_params:
            setattr(context, "path_params", path_params)
    
    def _get_cached_route(self, intent_name: str) -> Optional[Tuple[RouteRule, Dict[str, str]]]:
        """获取缓存的路由匹配结果"""
        if intent_name in self.route_cache:
            timestamp = self.cache_timestamps.get(intent_name, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self.route_cache[intent_name]
            else:
                # 缓存过期，清理
                del self.route_cache[intent_name]
                del self.cache_timestamps[intent_name]
        return None
    
    def _cache_route(self, intent_name: str, route_rule: RouteRule, params: Dict[str, str]) -> None:
        """缓存路由匹配结果"""
        self.route_cache[intent_name] = (route_rule, params)
        self.cache_timestamps[intent_name] = time.time()
    
    def _pick_best_version(self, rules: List[RouteRule], requested_version: Optional[str]) -> Optional[RouteRule]:
        """从候选规则中选择最合适版本"""
        if not rules:
            return None

        def _version_key(v: Optional[str]) -> Tuple[int, ...]:
            if not v:
                return (0,)
            try:
                return tuple(int(x) for x in v.split("."))
            except Exception:
                return (0,)

        if requested_version:
            compat = [r for r in rules if r.version and self._is_version_compatible(r.version, requested_version)]
            if compat:
                return sorted(compat, key=lambda r: _version_key(r.version), reverse=True)[0]
            # 若无兼容版本，尝试无版本路由
            nov = [r for r in rules if not r.version]
            if nov:
                return nov[0]
            return None

        # 未指定版本：优先最高版本
        versioned = [r for r in rules if r.version]
        if versioned:
            return sorted(versioned, key=lambda r: _version_key(r.version), reverse=True)[0]
        return rules[0]

    def match_route(self, intent_name: str, version: str = None) -> Tuple[Optional[RouteRule], Dict[str, str]]:
        """匹配路由规则"""
        # 构造缓存键，包含版本信息
        cache_key = f"{intent_name}:{version or 'default'}"
        
        # 检查缓存
        cached = self._get_cached_route(cache_key)
        if cached:
            return cached
        
        # 先精确匹配
        if intent_name in self.routes:
            route_rule = self._pick_best_version(self.routes[intent_name], version)
            if route_rule:
                self._cache_route(cache_key, route_rule, {})
                return route_rule, {}
        
        # 使用前缀树匹配
        route_rules, params = self.trie.match(intent_name)
        route_rule = self._pick_best_version(route_rules, version)
        if route_rule:
            self._cache_route(cache_key, route_rule, params)
            return route_rule, params
        
        # 如果指定了版本但没有找到匹配的路由，尝试查找不带版本的路由
        if version and intent_name in self.routes:
            route_rule = self._pick_best_version(self.routes[intent_name], version)
            if route_rule:
                self._cache_route(cache_key, route_rule, {})
                return route_rule, {}
        
        # 如果指定了版本但没有找到匹配的路由，尝试使用前缀树查找不带版本的路由
        if version:
            route_rules, params = self.trie.match(intent_name)
            route_rule = self._pick_best_version(route_rules, version)
            if route_rule:
                self._cache_route(cache_key, route_rule, params)
                return route_rule, params
        
        return None, {}
    
    def _is_version_compatible(self, handler_version: str, requested_version: str) -> bool:
        """检查版本兼容性"""
        # 简单的版本比较，实际项目中可能需要更复杂的版本比较逻辑
        # 支持精确匹配和向后兼容匹配
        if handler_version == requested_version:
            return True
        
        # 检查是否是向后兼容的版本
        # 例如：请求版本1.2.0，处理器版本1.0.0是兼容的
        try:
            handler_parts = [int(x) for x in handler_version.split('.')]
            requested_parts = [int(x) for x in requested_version.split('.')]
            
            # 主版本号必须匹配
            if handler_parts[0] != requested_parts[0]:
                return False
            
            # 次版本号处理器版本不能大于请求版本
            if len(handler_parts) > 1 and len(requested_parts) > 1:
                if handler_parts[1] > requested_parts[1]:
                    return False
            
            # 修订版本号处理器版本不能大于请求版本
            if len(handler_parts) > 2 and len(requested_parts) > 2:
                if handler_parts[2] > requested_parts[2]:
                    return False
            
            return True
        except (ValueError, IndexError):
            # 如果版本号格式不正确，回退到精确匹配
            return handler_version == requested_version
    
    def dispatch(self, intent_name: str, context: Any, request: Any = None) -> Dict:
        """分发意图请求"""
        try:
            # 获取请求的版本
            requested_version = getattr(context, "params", {}).get("version")
            
            # 运行前置中间件
            for middleware in self.middlewares:
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
            
            # 匹配路由
            route_rule, path_params = self.match_route(intent_name, requested_version)
            if not route_rule:
                raise IntentNotFound(f"找不到意图对应 Handler：{intent_name}")
            
            # 附加路径参数到上下文
            if path_params:
                setattr(context, "path_params", path_params)
            
            # 创建处理器实例
            handler = route_rule.handler_cls(context, request)
            
            # 执行处理器
            t0 = time.time()
            result = handler.run()
            
            # 统一记录耗时
            _logger.debug("intent %s done in %dms", intent_name, int((time.time()-t0)*1000))
            
            # 运行后置中间件
            for middleware in reversed(self.middlewares):
                try:
                    result = middleware.process_response(intent_name, context, result)
                except Exception as e:
                    _logger.error(f"中间件 {middleware.name} 处理响应时发生异常: {str(e)}")
                    # 可以选择是否继续处理
            
            return result
            
        except Exception as e:
            # 异常处理中间件
            processed_exception = e
            for middleware in reversed(self.middlewares):
                try:
                    processed_exception = middleware.process_exception(intent_name, context, processed_exception)
                except Exception as middleware_exception:
                    _logger.error(f"中间件 {middleware.name} 处理异常时发生异常: {str(middleware_exception)}")
            
            _logger.exception("Intent dispatch failed: %s", str(processed_exception))
            return {
                "ok": False, 
                "error": {"code": 500, "message": f"执行异常: {str(processed_exception)}"}, 
                "code": 500
            }

# 全局路由器实例
enhanced_router = EnhancedIntentRouter()

def route_intent_enhanced(payload: dict, context: Any) -> Dict:
    """增强的意图路由入口"""
    if not isinstance(payload, dict):
        raise IntentBadRequest("payload 必须为 dict")

    intent = (payload.get("intent") or "").strip()
    if not intent:
        raise IntentBadRequest("缺少 intent")

    params = payload.get("params") or {}
    ctx = payload.get("ctx") or {}
    options = payload.get("options") or {}
    trace_id = payload.get("trace_id")

    # 生成追踪ID
    if not trace_id:
        import hashlib
        import json
        import time
        trace_id = hashlib.md5(f"{intent}{json.dumps(params, sort_keys=True)}{time.time()}".encode()).hexdigest()[:16]

    # 附加参数到上下文
    setattr(context, "intent", intent)
    setattr(context, "params", params)
    setattr(context, "ctx", ctx)
    setattr(context, "options", options)
    setattr(context, "trace_id", trace_id)

    # 使用增强路由器分发
    return enhanced_router.dispatch(intent, context)
