# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import time
from typing import Any, Dict, List, Tuple

from odoo.addons.smart_core.utils.extension_hooks import iter_extension_modules
from ..native.native_projection_service import load_native_capability_rows
from ..schema.capability_schema import validate_and_normalize_rows


def load_capability_contributions(env, user=None) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    rows, errors, _timings = load_capability_contributions_with_timings(env, user=user)
    return rows, errors


def load_capability_contributions_with_timings(
    env, user=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    timings_ms: Dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    native_rows, native_errors = load_native_capability_rows(env, user=user)
    stage_ts = _mark("native_projection", stage_ts)
    normalized_native, native_schema_errors = validate_and_normalize_rows(
        native_rows,
        source_module="smart_core.native",
    )
    stage_ts = _mark("native_schema_normalize", stage_ts)
    rows.extend(normalized_native)
    errors.extend(native_errors)
    for item in native_schema_errors:
        errors.append({"module": "smart_core.native", "stage": "schema", "error": item})

    stage_ts = time.perf_counter()
    for module_name in iter_extension_modules(env):
        module_ts = time.perf_counter()
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception as exc:
            errors.append({"module": module_name, "stage": "import", "error": str(exc)})
            timings_ms[f"extension.{module_name}.import_and_provider"] = int((time.perf_counter() - module_ts) * 1000)
            continue
        provider = getattr(module, "get_capability_contributions", None)
        timed_provider = getattr(module, "get_capability_contributions_with_timings", None)
        module_extension = getattr(module, "core_extension", None)
        if not callable(provider) and module_extension is not None:
            provider = getattr(module_extension, "get_capability_contributions", None)
        if not callable(timed_provider) and module_extension is not None:
            timed_provider = getattr(module_extension, "get_capability_contributions_with_timings", None)
        payload = None
        if not callable(provider):
            timings_ms[f"extension.{module_name}.import_and_provider"] = int((time.perf_counter() - module_ts) * 1000)
            continue
        provider_timings: Dict[str, int] = {}
        if callable(timed_provider):
            try:
                payload, provider_timings = timed_provider(env, user)
            except Exception as exc:
                errors.append({"module": module_name, "stage": "provider", "error": str(exc)})
                timings_ms[f"extension.{module_name}.import_and_provider"] = int((time.perf_counter() - module_ts) * 1000)
                continue
        else:
            try:
                payload = provider(env, user)
            except Exception as exc:
                errors.append({"module": module_name, "stage": "provider", "error": str(exc)})
                timings_ms[f"extension.{module_name}.import_and_provider"] = int((time.perf_counter() - module_ts) * 1000)
                continue
        module_ts = _mark(f"extension.{module_name}.import_and_provider", module_ts)
        if isinstance(provider_timings, dict):
            for key, value in provider_timings.items():
                timings_ms[f"extension.{module_name}.provider.{key}"] = int(value)
        normalized, row_errors = validate_and_normalize_rows(payload, source_module=module_name)
        _mark(f"extension.{module_name}.schema_normalize", module_ts)
        rows.extend(normalized)
        for item in row_errors:
            errors.append({"module": module_name, "stage": "schema", "error": item})
    _mark("extension_loop_total", stage_ts)
    return rows, errors, timings_ms
