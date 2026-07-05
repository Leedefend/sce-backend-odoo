# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    utils_pkg = sys.modules.setdefault("odoo.addons.smart_core.utils", types.ModuleType("odoo.addons.smart_core.utils"))
    utils_pkg.__path__ = [str(CORE_DIR.parent / "utils")]

    source_authority = types.ModuleType("odoo.addons.smart_core.core.source_authority")
    source_authority.build_source_authority_contract = lambda **kwargs: dict(kwargs)
    sys.modules["odoo.addons.smart_core.core.source_authority"] = source_authority

    extension_hooks = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
    extension_hooks.iter_extension_modules = lambda env: []
    sys.modules["odoo.addons.smart_core.utils.extension_hooks"] = extension_hooks

    module_name = "odoo.addons.smart_core.core.system_init_extension_fact_merger"
    spec = importlib.util.spec_from_file_location(module_name, CORE_DIR / "system_init_extension_fact_merger.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSystemInitExtensionFactMerger(unittest.TestCase):
    def test_default_workspace_collection_export_keys_are_platform_generic(self):
        module = _load_module()
        data = {
            "ext_facts": {
                "x": {
                    "workspace_collections": {
                        "task_items": [{"id": 1}],
                        "risk_actions": [{"id": 2}],
                        "payment_requests": [{"id": 3}],
                        "project_actions": [{"id": 4}],
                    }
                }
            }
        }

        module.merge_extension_facts(data)

        self.assertEqual(data.get("task_items"), [{"id": 1}])
        self.assertEqual(data.get("risk_actions"), [{"id": 2}])
        self.assertNotIn("payment_requests", data)
        self.assertNotIn("project_actions", data)

    def test_extension_can_declare_workspace_collection_export_keys(self):
        module = _load_module()
        data = {
            "ext_facts": {
                "x": {
                    "workspace_collection_export_keys": ["payment_requests", "project_actions"],
                    "workspace_collections": {
                        "payment_requests": [{"id": 3}],
                        "project_actions": [{"id": 4}],
                    },
                }
            }
        }

        module.merge_extension_facts(data)

        self.assertEqual(data.get("payment_requests"), [{"id": 3}])
        self.assertEqual(data.get("project_actions"), [{"id": 4}])


if __name__ == "__main__":
    unittest.main()
