# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

assembler = _load_module(
    "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
    CORE_DIR / "unified_page_contract_v2_assembler.py",
)
client = _load_module(
    "odoo.addons.smart_core.core.unified_page_contract_v2_client",
    CORE_DIR / "unified_page_contract_v2_client.py",
)


class TestUnifiedPageContractV2MobileCompact(unittest.TestCase):
    def test_mobile_compact_preserves_create_business_context_outside_compat(self):
        source = {
            "ui_contract": {
                "model": "project.project",
                "view_type": "form",
                "head": {
                    "render_profile": "create",
                    "context": {
                        "default_manager_id": 43,
                        "default_user_id": 43,
                        "default_phase_key": "initiation",
                        "sc_return_to_overview": 1,
                    },
                },
                "fields": {
                    "name": {"name": "name", "type": "char"},
                    "manager_id": {"name": "manager_id", "type": "many2one"},
                    "user_id": {"name": "user_id", "type": "many2one"},
                    "phase_key": {"name": "phase_key", "type": "selection"},
                },
            },
            "model": "project.project",
            "view_type": "form",
            "render_profile": "create",
            "context_raw": "{'default_manager_id': uid, 'default_phase_key': 'initiation'}",
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="harmony_h5",
            request_id="test.mobile.compact.create",
        )
        trimmed = client.trim_unified_page_contract_v2(
            full,
            client_type="harmony_h5",
            delivery_profile="mobile_compact",
            include_source_compat=False,
        )

        data_contract = trimmed["dataContract"]
        source_context = data_contract["dataMeta"]["sourceContext"]
        self.assertTrue(trimmed["meta"]["sourceCompatTrimmed"])
        self.assertEqual(trimmed["meta"]["compat"]["ui_contract"]["delivery"], "omitted_for_mobile_compact")
        self.assertEqual(source_context["renderProfile"], "create")
        self.assertEqual(source_context["context"]["default_phase_key"], "initiation")
        self.assertEqual(data_contract["mainData"]["manager_id"], 43)
        self.assertEqual(data_contract["mainData"]["user_id"], 43)
        self.assertEqual(data_contract["mainData"]["phase_key"], "initiation")
        self.assertEqual(trimmed["statusContract"]["globalStatus"]["pageAuth"], "edit")


if __name__ == "__main__":
    unittest.main()
