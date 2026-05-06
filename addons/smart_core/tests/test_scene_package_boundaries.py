# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, context=None):
        self.env = env
        self.context = context or {}


class _Service:
    calls = []

    def __init__(self, env, user):
        self.env = env
        self.user = user

    def export_package(self, **kwargs):
        self.calls.append(("export", kwargs))
        return kwargs

    def dry_run_import(self, package_json):
        self.calls.append(("dry_run", package_json))
        return {"ok": True}

    def import_package(self, **kwargs):
        self.calls.append(("import", kwargs))
        return {"ok": True}


class _Env:
    user = types.SimpleNamespace(id=9)


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]
    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda env, hook, *args, **kwargs: _Service,
    )

    module_name = "odoo.addons.smart_core.handlers.scene_package"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "scene_package.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestScenePackageBoundaries(unittest.TestCase):
    def setUp(self):
        _Service.calls = []
        self.module = _load_handler()

    def test_export_rejects_invalid_scene_channel(self):
        handler = self.module.ScenePackageExportHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"scene_channel": "nightly"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "scene_channel 无效")
        self.assertEqual(_Service.calls, [])

    def test_export_rejects_non_text_package_name(self):
        handler = self.module.ScenePackageExportHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"package_name": ["core"]}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "package_name 无效")
        self.assertEqual(_Service.calls, [])

    def test_dry_run_import_rejects_invalid_json(self):
        handler = self.module.ScenePackageDryRunImportHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"package_json": "not-json"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "package_json 无效")
        self.assertEqual(_Service.calls, [])

    def test_import_accepts_json_string_package(self):
        handler = self.module.ScenePackageImportHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"package_json": "{\"name\":\"core\"}", "strategy": "skip_existing"}})

        self.assertTrue(result["ok"])
        self.assertEqual(_Service.calls[0][0], "import")
        self.assertEqual(_Service.calls[0][1]["package_json"], {"name": "core"})


if __name__ == "__main__":
    unittest.main()
