# 📄 smart_core/core/handler_registry.py
import importlib
import pkgutil
import logging
from typing import Dict, Type
from .base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)
HANDLER_REGISTRY: Dict[str, Type[BaseIntentHandler]] = {}

def _iter_modules_recursively(pkg):
    """递归遍历包及其子包"""
    for modinfo in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        yield modinfo

def _should_skip_module(fullname: str) -> bool:
    name = fullname.rsplit(".", 1)[-1]
    # 跳过私有、测试、临时模块（可按需调整）
    return name.startswith(("_", "test_", "tests", "tmp_")) or "enhanced_" in name

def register_all_handlers():
    from .. import handlers  # 确保 handlers 是个包（有 __init__.py）

    for modinfo in _iter_modules_recursively(handlers):
        if _should_skip_module(modinfo.name):
            continue
        module = importlib.import_module(modinfo.name)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if not (isinstance(attr, type) and issubclass(attr, BaseIntentHandler) and attr is not BaseIntentHandler):
                continue

            intent_type = getattr(attr, "INTENT_TYPE", None)
            if not intent_type:
                continue

            # 唯一性检查
            if intent_type in HANDLER_REGISTRY:
                _logger.warning("Duplicate INTENT_TYPE '%s' in %s; overwritten by %s",
                                intent_type, HANDLER_REGISTRY[intent_type].__module__, module.__name__)
            HANDLER_REGISTRY[intent_type] = attr

            # 别名支持（可选）
            aliases = []
            if hasattr(attr, "ALIASES"):
                try:
                    aliases = list(getattr(attr, "ALIASES") or [])
                except Exception as e:
                    _logger.error("Failed to read ALIASES for %s: %s", intent_type, e)
            elif hasattr(attr, "aliases") and callable(getattr(attr, "aliases")):
                try:
                    aliases = list(getattr(attr, "aliases")() or [])
                except Exception as e:
                    _logger.error("Failed to read aliases() for %s: %s", intent_type, e)

            for al in aliases:
                if al in HANDLER_REGISTRY:
                    _logger.warning("Alias '%s' conflicts; overwritten by %s", al, module.__name__)
                HANDLER_REGISTRY[al] = attr

# 在模块 import 时自动注册
register_all_handlers()
