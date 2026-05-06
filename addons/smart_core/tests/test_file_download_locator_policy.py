# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.context = context or {}


class _Env(dict):
    def __init__(self):
        super().__init__()
        self.attachment_lookup_count = 0

    def __getitem__(self, key):
        if key == "ir.attachment":
            self.attachment_lookup_count += 1
        return super().__getitem__(key)


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    odoo_mod = types.ModuleType("odoo")
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = type("AccessError", (Exception,), {})
    odoo_mod.exceptions = exc_mod

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    handlers_mod = types.ModuleType("odoo.addons.smart_core.handlers")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    utils_mod = types.ModuleType("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    base_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    project_mod = types.ModuleType("odoo.addons.smart_core.core.project_context")
    project_mod.project_scope_denied_response = lambda meta: {"ok": False, "meta": meta}
    project_mod.record_in_project_scope = lambda model, record_id, project_id: (True, {"applied": False})
    project_mod.selected_project_id_from_context = lambda params, context: None
    hooks_mod = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
    hooks_mod.call_extension_hook_first = lambda *args, **kwargs: None

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.utils": utils_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
            "odoo.addons.smart_core.core.project_context": project_mod,
            "odoo.addons.smart_core.utils.extension_hooks": hooks_mod,
        }
    )

    module_name = "odoo.addons.smart_core.handlers.file_download"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "file_download.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestFileDownloadLocatorPolicy(unittest.TestCase):
    def test_fallback_locator_rejects_disallowed_model_before_attachment_lookup(self):
        module = _load_handler()
        env = _Env()
        handler = module.FileDownloadHandler(
            env=env,
            params={"model": "project.task", "res_id": 7, "name": "secret.pdf"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 403)
        self.assertEqual(env.attachment_lookup_count, 0)


if __name__ == "__main__":
    unittest.main()
