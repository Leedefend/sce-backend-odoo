# -*- coding: utf-8 -*-
# smart_core/app_config_engine/controllers/contract_controller.py
# 【职责】HTTP 路由最薄层：仅负责接收请求 → 委托 Service 完成业务处理 → 返回响应
#       - 不做参数解析/分发/装配，避免控制器肥大、难测。
import logging, time
from odoo import http
from odoo.http import request
# 业务入口服务：封装契约处理主流程（解析payload、分发subject、组装meta/etag等）
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService

BUILD_TAG = "contract-ctlr-2025-08-30-02"  # 版本定位标签，便于日志定位
_logger = logging.getLogger(__name__)

class SmartCoreContractController(http.Controller):

    @http.route('/api/contract/get', type='http', auth='user', methods=['POST'], csrf=False)
    def contract_get(self, **kwargs):
        """
        统一契约接口（Contract 2.0）
        - 只保留一个 POST 路由；
        - 控制器只做转发与异常兜底，保证职责单一。
        """
        _logger.warning("CTRL_ENTER %s file=%s", BUILD_TAG, __file__)
        _logger.warning("已更新客户端动作处理逻辑 - 生效时间: %s", time.strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 将当前请求的 env 传给 Service（避免在 Service 内 import request）
            svc = ContractService(request_env=request.env)
            ok, status, headers, body = svc.handle_request()
            # 由 Service 返回 (状态码、响应头、body)，控制器直接透传
            return request.make_response(body, headers=headers, status=status)
        except Exception as e:
            # 兜底日志 + 500 错误结构
            _logger.exception("contract_get failed (controller)")
            return request.make_response(
                ('{"ok": false, "error": "%s"}' % str(e)).encode('utf-8'),
                headers=[('Content-Type', 'application/json; charset=utf-8')],
                status=500
            )
