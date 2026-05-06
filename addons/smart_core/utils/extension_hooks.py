# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import Any, List

SOURCE_KIND = "smart_core_extension_hook_resolver"
SOURCE_AUTHORITIES = ("ir.config_parameter", "odoo.addons", "extension_hook")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "extension_hooks",
    }


def _parse_extension_modules(raw: str) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in str(raw).split(",") if str(item).strip()]


def iter_extension_modules(env) -> List[str]:
    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
    except Exception:
        return []
    return _parse_extension_modules(raw)


def call_extension_hook_first(env, hook_name: str, *args, **kwargs) -> Any:
    for module_name in iter_extension_modules(env):
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception:
            continue
        hook = getattr(module, hook_name, None)
        if callable(hook):
            try:
                result = hook(*args, **kwargs)
            except Exception:
                continue
            if result is not None:
                return result
    return None
