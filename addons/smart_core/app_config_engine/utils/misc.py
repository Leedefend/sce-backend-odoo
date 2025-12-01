# -*- coding: utf-8 -*-
# smart_core/app_config_engine/utils/misc.py
# 【职责】通用方法：safe_eval/ETag/版本串/Domain 合并
import json, hashlib
from odoo.tools.safe_eval import safe_eval as _safe_eval

def safe_eval(expr):
    """
    仅用于解析 Odoo context/domain 这类静态表达式；
    - 失败返回 None，避免抛异常中断主链路。
    """
    if not expr or not isinstance(expr, str): return None
    try: return _safe_eval(expr, {})
    except Exception: return None

def stable_etag(data):
    """
    基于 data 的稳定 md5：用于缓存/304 对比；
    - sort_keys=True 确保键序稳定；
    - default=str 避免非可序列化类型报错。
    """
    raw = json.dumps(data or {}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def format_versions(versions):
    """
    将分块版本拼接成 Spec 推荐格式："model:12|view:34|perm:7|..."；
    - 未提供时返回 "1"。
    """
    keys = ["model","view","perm","search","actions","reports","workflow","validator"]
    parts = [f"{k}:{versions[k]}" for k in keys if k in versions]
    return "|".join(parts) if parts else "1"

def merge_domain_and(base, extra):
    """
    将两个 domain 用 AND 拼接：
    - domain 格式为 Odoo 列表表达式；
    - 兼容空列表。
    """
    base = base or []; extra = extra or []
    if not base:  return extra
    if not extra: return base
    return ['&'] + (base if isinstance(base,list) else [base]) + (extra if isinstance(extra,list) else [extra])
