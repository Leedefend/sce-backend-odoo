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


odoo_module = sys.modules.setdefault("odoo", types.ModuleType("odoo"))
odoo_module.fields = types.SimpleNamespace(
    Datetime=types.SimpleNamespace(now=lambda: None),
)
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

target = _load_module(
    "odoo.addons.smart_core.core.workspace_home_contract_builder_provider_shapes",
    CORE_DIR / "workspace_home_contract_builder.py",
)


class TestWorkspaceHomeProviderShapes(unittest.TestCase):
    def test_build_workspace_home_contract_exposes_provider_ready_shapes(self):
        payload = target.build_workspace_home_contract(
            {
                "capabilities": [
                    {
                        "key": "project.risk.list",
                        "label": "风险台账",
                        "capability_state": "allow",
                        "state": "READY",
                        "group_key": "risk",
                        "group_label": "风险",
                    },
                    {
                        "key": "contract.center",
                        "label": "合同中心",
                        "capability_state": "readonly",
                        "state": "PREVIEW",
                        "group_key": "contract",
                        "group_label": "合同",
                    },
                ],
                "capability_groups": [
                    {
                        "key": "risk",
                        "label": "风险",
                        "sequence": 10,
                        "capability_count": 1,
                        "state_counts": {"READY": 1},
                        "capability_state_counts": {"allow": 1, "readonly": 0, "deny": 0},
                    }
                ],
                "scenes": [
                    {
                        "key": "risk.center",
                        "label": "风险中心",
                        "tiles": [
                            {
                                "key": "project.risk.list",
                                "title": "待处理风险事项",
                                "subtitle": "进入风险中心处理事项",
                                "state": "READY",
                                "status": "ga",
                                "payload": {
                                    "route": "/s/risk.center",
                                    "action_id": 901,
                                    "menu_id": 801,
                                    "query": {"section": "todo"},
                                },
                            }
                        ],
                    }
                ],
                "today_actions": [
                    {"id": "todo-1", "title": "处理风险", "entry_key": "project.risk.list", "count": 2}
                ],
                "risk_actions": [
                    {"id": "risk-1", "title": "风险超期", "entry_key": "project.risk.list", "count": 1}
                ],
            }
        )

        metrics = payload.get("metrics") or []
        self.assertTrue(metrics)
        self.assertIn("tone", metrics[0])
        self.assertIn("progress", metrics[0])

        ops = payload.get("ops") or {}
        self.assertTrue(str(ops.get("summary") or "").strip())

        risk = payload.get("risk") or {}
        actions = risk.get("actions") or []
        self.assertTrue(actions)
        self.assertEqual(actions[0].get("action_key"), "open_scene")
        self.assertTrue(str(actions[0].get("action_label") or "").strip())
        self.assertTrue(str(actions[0].get("path") or "").strip())

        scene_groups = payload.get("scene_groups") or []
        self.assertTrue(scene_groups)
        self.assertEqual(scene_groups[0].get("scene_key"), "risk.center")
        self.assertEqual(scene_groups[0].get("action_id"), 901)
        self.assertEqual(scene_groups[0].get("menu_id"), 801)

        group_overview = payload.get("group_overview") or []
        self.assertTrue(group_overview)
        self.assertEqual(group_overview[0].get("key"), "risk")
        self.assertEqual(group_overview[0].get("allow_count"), 1)
