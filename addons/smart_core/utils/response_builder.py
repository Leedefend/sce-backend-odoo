# smart_core/utils/response_builder.py
from odoo import http
from odoo.http import request

SOURCE_KIND = "http_json_response_builder"
SOURCE_AUTHORITIES = ("odoo.http.response", "json_response_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract():
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "response_builder",
    }

def make_response(data=None, error=None, code=200, headers=None):
    result = {
        "status": "error" if error else "success",
        "message": error or "OK",
        "code": code,
        "data": None if error else data,
    }

    # 创建响应对象
    response = request.make_response(
        data=http.json.dumps(result, ensure_ascii=False),
        status=code,
    )
    
    # 设置默认的Content-Type头部
    response.headers.add("Content-Type", "application/json")
    
    # 添加额外的头部信息
    if headers:
        for key, value in headers.items():
            response.headers.add(key, value)
    
    return response
