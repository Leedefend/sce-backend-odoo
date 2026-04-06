# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import Any, Dict, List, Tuple

from odoo.addons.smart_core.utils.extension_hooks import iter_extension_modules
from ..native.native_projection_service import load_native_capability_rows
from ..schema.capability_schema import validate_and_normalize_rows


def load_capability_contributions(env, user=None) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    native_rows, native_errors = load_native_capability_rows(env, user=user)
    normalized_native, native_schema_errors = validate_and_normalize_rows(
        native_rows,
        source_module="smart_core.native",
    )
    rows.extend(normalized_native)
    errors.extend(native_errors)
    for item in native_schema_errors:
        errors.append({"module": "smart_core.native", "stage": "schema", "error": item})

    for module_name in iter_extension_modules(env):
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception as exc:
            errors.append({"module": module_name, "stage": "import", "error": str(exc)})
            continue
        provider = getattr(module, "get_capability_contributions", None)
        if not callable(provider):
            continue
        try:
            payload = provider(env, user)
        except Exception as exc:
            errors.append({"module": module_name, "stage": "provider", "error": str(exc)})
            continue
        normalized, row_errors = validate_and_normalize_rows(payload, source_module=module_name)
        rows.extend(normalized)
        for item in row_errors:
            errors.append({"module": module_name, "stage": "schema", "error": item})
    return rows, errors
