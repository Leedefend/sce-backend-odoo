# -*- coding: utf-8 -*-
# smart_core/app_config_engine/utils/http.py
# 【职责】HTTP 工具：读取请求体 JSON
import json, logging
from odoo.http import request
_logger = logging.getLogger(__name__)

def read_json_body():
    """
    安全读取 body：
    - Content-Type 为 application/json|text/json：解析原始 body；
    - 否则回退 request.params（支持 x-www-form-urlencoded/form-data）；
    - 兼容 form 里 payload=JSON 字符串的情况；
    - 出错时返回 {}。
    """
    req = request.httprequest
    mimetype = (req.mimetype or '').lower()
    try:
        if mimetype in ('application/json', 'text/json'):
            raw = req.get_data(cache=False, as_text=True)
            if not raw: return {}
            try:
                return json.loads(raw)
            except Exception:
                _logger.warning("Invalid JSON body, first 200 chars: %s", raw[:200])
                return {}
        params = request.params or {}
        if isinstance(params, dict):
            p = dict(params)
            val = p.get('payload')
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return p
        return {}
    except Exception:
        _logger.exception("read_json_body failed")
        return {}
