# -*- coding: utf-8 -*-
import importlib
import logging

_logger = logging.getLogger(__name__)

_loaded = False
_loaded_modules = set()


def _parse_modules(raw: str):
    if not raw:
        return []
    return [m.strip() for m in raw.split(",") if m.strip()]


def load_extensions(env, registry):
    """
    Load external modules and let them register handlers into registry.
    Expected hook: smart_core_register(registry)
    """
    global _loaded
    if _loaded:
        return
    if env is None:
        _logger.warning("[extension_loader] env is None, skip")
        return

    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.core.extension_modules") or ""
    except Exception as e:
        _logger.warning("[extension_loader] failed to read config: %s", e)
        return

    modules = _parse_modules(raw)
    if not modules:
        _loaded = True
        return

    for mod in modules:
        if mod in _loaded_modules:
            continue
        try:
            m = importlib.import_module(f"odoo.addons.{mod}")
        except Exception as e:
            _logger.warning("[extension_loader] import failed: %s (%s)", mod, e)
            continue

        hook = getattr(m, "smart_core_register", None)
        if callable(hook):
            try:
                hook(registry)
                _logger.info("[extension_loader] registered module: %s", mod)
            except Exception as e:
                _logger.warning("[extension_loader] hook failed: %s (%s)", mod, e)
                continue
        else:
            _logger.warning("[extension_loader] no smart_core_register in %s", mod)

        _loaded_modules.add(mod)

    _loaded = True
