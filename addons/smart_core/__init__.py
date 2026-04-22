# -*- coding: utf-8 -*-
"""
Smart Core Engine Module

智能核心引擎模块 - 提供契约驱动架构的核心服务
包含:
- 契约API控制器
- 意图路由调度
- 视图渲染引擎
- 配置引擎
"""

import logging

# 导入子模块
try:
    from . import controllers
    from . import app_config_engine
    from . import core
    from . import handlers
    from . import view
    from . import utils
    from . import models
    from . import delivery

    # Ensure intent controllers are registered on module load
    from .controllers import intent_dispatcher
except ModuleNotFoundError as exc:
    # Pure-Python bridge tests import smart_core without a live Odoo runtime.
    # In that mode the package must still be importable so isolated bridge
    # modules can be executed directly from their test loaders.
    if exc.name != "odoo":
        raise

# 设置日志
_logger = logging.getLogger(__name__)
_logger.info("✅ Smart Core Engine 模块已加载")
