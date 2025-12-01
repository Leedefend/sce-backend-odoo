# -*- coding: utf-8 -*-
{
    "name": "Smart Core Engine",
    "summary": "Structure-Driven · Intent-Based · Contract API for Odoo",
    "description": """
基于契约（Contract）与意图（Intent）的轻量后端内核：
- 统一契约聚合接口（view/model/permission/action），支持 ETag/If-None-Match
- 意图调度总线（/api/intent），用于场景化业务动作
- 私有缓存与多公司/多语言上下文透传
""",
    "version": "17.0.1.0",
    "author": "Leedefend",
    "website": "https://example.com",
    "category": "Technical/Framework",
    "license": "LGPL-3",

    # 控制器与契约服务通常需要 web；建议保留
    "depends": ["base", "web"],

    # 安全文件先占位，后续可逐步加 ACL/参数
    "data": [
        "security/smart_core_security.xml",
        "security/ir.model.access.csv"
        # 可选：默认参数/开关
        # "data/smart_core_params.xml",
    ],

    # 如无 Odoo 前端资产，可留空；后续若加调试面板/Swagger 页面可在此挂载
    "assets": {
        "web.assets_backend": [
            # "smart_core/static/src/js/dev_console.js",
            # "smart_core/static/src/scss/dev_console.scss",
        ],
        "web.assets_frontend": [],
    },

    # 若启用 Token/JWT 鉴权，在此声明第三方库
    "external_dependencies": {
        "python": [
             "PyJWT",
        ],
    },

    "installable": True,
    "application": False,
    "auto_install": False,
}
