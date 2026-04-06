# -*- coding: utf-8 -*-
import importlib
import logging

from .intent_contribution_loader import (
    final_register_contributions,
    merge_contributions,
    validate_contributions,
)

_logger = logging.getLogger(__name__)

_loaded = False
_loaded_modules = set()


def _parse_modules(raw: str):
    if not raw:
        return []
    return [m.strip() for m in raw.split(",") if m.strip()]

def _is_true(val: str | None) -> bool:
    if not val:
        return False
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def load_extensions(env, registry):
    """
    Load external modules and register intent handlers into registry.
    Preferred hook: get_intent_handler_contributions()
    Legacy hook: smart_core_register(registry)
    """
    global _loaded
    if _loaded:
        return
    if env is None:
        _logger.warning("[extension_loader] env is None, skip")
        return

    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
        debug_raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_debug") or ""
    except Exception as e:
        _logger.warning("[extension_loader] failed to read config: %s", e)
        return
    debug = _is_true(debug_raw)
    log = _logger.info if debug else _logger.debug

    modules = _parse_modules(raw)
    if not modules:
        log("[extension_loader] extension_modules empty, skip")
        _loaded = True
        return

    log("[extension_loader] modules=%s", ",".join(modules))
    total_before = len(registry or {})
    loaded_ok = 0
    loaded_fail = 0
    skipped = 0
    contribution_rows = []

    for mod in modules:
        if mod in _loaded_modules:
            skipped += 1
            continue
        try:
            m = importlib.import_module(f"odoo.addons.{mod}")
        except Exception as e:
            _logger.warning("[extension_loader] import failed: %s (%s)", mod, e)
            loaded_fail += 1
            continue

        contribution_hook = getattr(m, "get_intent_handler_contributions", None)
        if callable(contribution_hook):
            try:
                raw_rows = contribution_hook()
                rows, row_errors = validate_contributions(mod, raw_rows)
                for row_error in row_errors:
                    _logger.warning("[extension_loader] contribution invalid: %s", row_error)
                contribution_rows.extend(rows)
                loaded_ok += 1
                log("[extension_loader] contribution module: %s (rows=%s)", mod, len(rows))
            except Exception as e:
                _logger.warning("[extension_loader] contribution hook failed: %s (%s)", mod, e)
                loaded_fail += 1
                continue
            _loaded_modules.add(mod)
            continue

        legacy_hook = getattr(m, "smart_core_register", None)
        if callable(legacy_hook):
            try:
                before = len(registry or {})
                legacy_hook(registry)
                after = len(registry or {})
                loaded_ok += 1
                log("[extension_loader] legacy module: %s (handlers +%s)", mod, after - before)
            except Exception as e:
                _logger.warning("[extension_loader] legacy hook failed: %s (%s)", mod, e)
                loaded_fail += 1
                continue
            _loaded_modules.add(mod)
            continue

        _logger.warning("[extension_loader] no contribution/legacy hook in %s", mod)
        loaded_fail += 1

    if contribution_rows:
        merged_rows, merge_errors = merge_contributions(contribution_rows)
        for merge_error in merge_errors:
            _logger.warning("[extension_loader] contribution merge conflict: %s", merge_error)
        final_stats = final_register_contributions(registry, merged_rows)
        log(
            "[extension_loader] contribution register added=%s skipped_existing=%s",
            final_stats.get("added", 0),
            final_stats.get("skipped_existing", 0),
        )

    total_after = len(registry or {})
    log(
        "[extension_loader] summary ok=%s failed=%s skipped=%s handlers=%s->%s",
        loaded_ok,
        loaded_fail,
        skipped,
        total_before,
        total_after,
    )
    _loaded = True


def run_extension_hooks(env, hook_name: str, *args, **kwargs):
    if env is None:
        return
    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
    except Exception as e:
        _logger.warning("[extension_loader] failed to read config: %s", e)
        return

    modules = _parse_modules(raw)
    if not modules:
        return

    for mod in modules:
        try:
            m = importlib.import_module(f"odoo.addons.{mod}")
        except Exception as e:
            _logger.debug("[extension_loader] hook import failed: %s (%s)", mod, e)
            continue
        hook = getattr(m, hook_name, None)
        if callable(hook):
            try:
                hook(*args, **kwargs)
            except Exception as e:
                _logger.warning("[extension_loader] hook %s failed: %s (%s)", hook_name, mod, e)


def collect_extension_hook_results(env, hook_name: str, *args, **kwargs):
    results = []
    if env is None:
        return results
    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
    except Exception as e:
        _logger.warning("[extension_loader] failed to read config: %s", e)
        return results

    modules = _parse_modules(raw)
    if not modules:
        return results

    for mod in modules:
        try:
            m = importlib.import_module(f"odoo.addons.{mod}")
        except Exception as e:
            _logger.debug("[extension_loader] hook import failed: %s (%s)", mod, e)
            continue
        hook = getattr(m, hook_name, None)
        if callable(hook):
            try:
                results.append(hook(*args, **kwargs))
            except Exception as e:
                _logger.warning("[extension_loader] hook %s failed: %s (%s)", hook_name, mod, e)
    return results


def call_extension_hook_first(env, hook_name: str, *args, **kwargs):
    for result in collect_extension_hook_results(env, hook_name, *args, **kwargs):
        if result is not None:
            return result
    return None
