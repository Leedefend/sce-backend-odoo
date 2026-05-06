# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    sys.modules.update(
        {
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
        }
    )
    module_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "request_params.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestRequestParams(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_parse_bool_string_false_values(self):
        for value in ("false", "0", "no", "off", ""):
            self.assertFalse(self.module.parse_bool(value, True))

    def test_parse_bool_string_true_values(self):
        for value in ("true", "1", "yes", "on"):
            self.assertTrue(self.module.parse_bool(value, False))

    def test_parse_bool_unknown_uses_default(self):
        self.assertTrue(self.module.parse_bool("unknown", True))
        self.assertFalse(self.module.parse_bool("unknown", False))


if __name__ == "__main__":
    unittest.main()
