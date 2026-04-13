# -*- coding: utf-8 -*-
# smart_core/core/load_contract_boundary_helper.py

from __future__ import annotations

from typing import Any, Dict


def read_module_install_state(env, module_name: str = "project") -> str:
    try:
        module = env["ir.module.module"].sudo().search([("name", "=", module_name)], limit=1)
        return module.state if module else "not found"
    except Exception:
        return "unknown"


def build_unknown_model_message(*, model_name: str, raw_model: str, dbname: str, module_state: str) -> str:
    target_name = model_name or str(raw_model or "").strip()
    return f"未知模型: {target_name} (db={dbname}, module(project)={module_state})"


def build_contract_response_payload(
    *,
    status: str,
    data: Dict[str, Any],
    meta: Dict[str, Any],
    etag: str,
    if_none_match: str,
    force_refresh: bool,
) -> Dict[str, Any]:
    if if_none_match and if_none_match == etag and not force_refresh:
        return {"status": "not_modified", "code": 304, "data": None, "meta": {"etag": etag}}

    meta_out = dict(meta or {})
    meta_out["etag"] = etag
    return {"status": status, "code": 200, "data": data or {}, "meta": meta_out}
