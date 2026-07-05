# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_assembler():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    for module_name in (
        "odoo.addons.smart_core.core.source_authority",
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
    ):
        sys.modules.pop(module_name, None)
    source_spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.source_authority",
        CORE_DIR / "source_authority.py",
    )
    source_module = importlib.util.module_from_spec(source_spec)
    assert source_spec and source_spec.loader
    sys.modules["odoo.addons.smart_core.core.source_authority"] = source_module
    source_spec.loader.exec_module(source_module)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
        CORE_DIR / "unified_page_contract_v2_assembler.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["odoo.addons.smart_core.core.unified_page_contract_v2_assembler"] = module
    spec.loader.exec_module(module)
    return module


def _kanban_source():
    return {
        "model": "project.project",
        "view_type": "kanban",
        "fields": {"name": {"name": "name", "type": "char"}},
        "views": {"kanban": {"fields": [{"name": "name", "label": "名称"}]}},
    }


class UnifiedPageContractV2KanbanActionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.assembler = _load_assembler()

    def test_core_has_no_default_business_kanban_row_actions(self):
        self.assertEqual(self.assembler._KANBAN_ROW_ACTION_REGISTRY, {})

        contract = self.assembler.assemble_unified_page_contract_v2(
            _kanban_source(),
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.kanban.no.default",
        )

        actions = (contract.get("actionContract") or {}).get("actionRuleList") or []
        self.assertEqual(actions, [])

    def test_business_kanban_row_action_must_be_registered_explicitly(self):
        self.assembler.register_kanban_row_action(
            "project.project",
            {
                "key": "open_project_dashboard",
                "name": "open_project_dashboard",
                "label": "进入项目驾驶舱",
                "intent": "open_scene",
                "target": {"route": "/s/project.management", "scene_key": "project.management"},
                "trigger": "row_click",
                "level": "row",
                "target_scope": "row",
            },
        )

        contract = self.assembler.assemble_unified_page_contract_v2(
            _kanban_source(),
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.kanban.registered",
        )

        actions = (contract.get("actionContract") or {}).get("actionRuleList") or []
        self.assertEqual(actions[0]["actionKey"], "open_project_dashboard")
        self.assertEqual(actions[0]["sourceWidgetId"], "page.row")
        self.assertEqual(actions[0]["triggerType"], "row_click")


if __name__ == "__main__":
    unittest.main()
