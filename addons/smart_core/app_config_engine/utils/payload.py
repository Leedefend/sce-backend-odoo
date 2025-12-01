# -*- coding: utf-8 -*-
# smart_core/app_config_engine/utils/payload.py
# 【职责】请求体 payload 的规范化解析/兜底
def _as_list(v):
    """将字符串/列表/单值统一为扁平的字符串列表"""
    if not v: return []
    if isinstance(v, str): return [x.strip() for x in v.split(',') if x.strip()]
    if isinstance(v, (list, tuple)): return [str(x).strip() for x in v if str(x).strip()]
    return [str(v)]

def parse_payload(payload):
    """
    按《Contract-2.0-Spec》约定解析关键字段；设置兜底默认值。
    """
    return {
        "subject": (payload.get("subject") or "model").lower(),
        "menu_id": payload.get("menu_id"),
        "action_id": payload.get("action_id"),
        "action_xmlid": payload.get("action_xmlid"),
        "model": payload.get("model"),
        "view_type": payload.get("view_type"),
        "view_types": _as_list(payload.get("view_types") or payload.get("view_type")),
        "record_id": payload.get("record_id"),
        "with_data": bool(payload.get("with_data", False)),
        "domain": payload.get("domain") or [],
        "order": payload.get("order"),
        "limit": payload.get("limit", 50),
        "offset": payload.get("offset", 0),
        "op": payload.get("op"),
        "method": payload.get("method"),
        "record_ids": payload.get("record_ids"),
        "args": payload.get("args") or [],
        "kwargs": payload.get("kwargs") or {},
        "values": payload.get("values") or {},
        "changed": payload.get("changed") or {},
        "action_key": payload.get("action_key"),
        "context": payload.get("context") or {},
        "breadcrumbs": payload.get("breadcrumbs") or [],
    }
