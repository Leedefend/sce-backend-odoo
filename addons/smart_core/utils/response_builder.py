# smart_core/utils/response_builder.py
import json

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


def _iter_headers(headers):
    if not headers:
        return []
    if isinstance(headers, dict):
        return list(headers.items())
    return list(headers)


def make_response(data=None, error=None, code=200, headers=None):
    result = {
        "status": "error" if error else "success",
        "message": error or "OK",
        "code": code,
        "data": None if error else data,
    }

    response = request.make_response(
        data=json.dumps(result, ensure_ascii=False, default=str),
        status=code,
    )

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    for key, value in _iter_headers(headers):
        response.headers[str(key)] = str(value)

    return response
