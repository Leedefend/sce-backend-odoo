# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_policy():
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

    module_name = "odoo.addons.smart_core.core.api_data_execution_policy"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "api_data_execution_policy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiDataExecutionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = _load_policy()

    def test_client_sudo_flag_is_detectable_for_audit(self):
        self.assertTrue(self.policy.client_requested_sudo({"sudo": True}))
        self.assertTrue(self.policy.client_requested_sudo({"params": {"sudo": "yes"}}))
        self.assertFalse(self.policy.client_requested_sudo({"params": {"sudo": "no"}}))

    def test_client_sudo_never_enables_api_data_sudo(self):
        self.assertFalse(self.policy.resolve_api_data_sudo({"sudo": True}))
        self.assertFalse(self.policy.resolve_api_data_sudo({"params": {"sudo": "1"}}))
        self.assertFalse(self.policy.resolve_api_data_sudo({}))


if __name__ == "__main__":
    unittest.main()
