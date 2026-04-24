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
    "odoo.addons.smart_core.core.workspace_home_contract_builder",
    CORE_DIR / "workspace_home_contract_builder.py",
)


class TestWorkspaceHomeContractBuilderSemantics(unittest.TestCase):
    def test_build_today_actions_normalizes_business_rows_for_block_ready_shape(self):
        rows = target._build_today_actions(
            {
                "today_actions": [
                    {
                        "id": "todo-contract-1",
                        "title": "补全收入合同",
                        "description": "缺少签约日期",
                        "scene_key": "contracts.list",
                        "entry_key": "contract_center",
                        "count": 3,
                    }
                ]
            },
            ready_caps=[],
            role_code="pm",
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("entry_key"), "contract_center")
        self.assertEqual(row.get("entry_id"), "contract_center")
        self.assertEqual(row.get("action_key"), "open_scene")
        self.assertEqual(row.get("action_label"), "查看详情")

    def test_build_today_actions_normalizes_capability_fallback_rows_for_block_ready_shape(self):
        rows = target._build_today_actions(
            {},
            ready_caps=[
                {
                    "key": "projects.list",
                    "ui_label": "项目台账",
                    "ui_hint": "进入项目列表查看待办",
                    "state": "READY",
                    "default_payload": {
                        "route": "/s/projects.list",
                        "menu_id": 278,
                        "action_id": 506,
                    },
                }
            ],
            role_code="pm",
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("entry_key"), "projects.list")
        self.assertEqual(row.get("entry_id"), "projects.list")
        self.assertEqual(row.get("action_key"), "open_scene")
        self.assertEqual(row.get("action_label"), "查看详情")

    def test_normalize_today_action_row_backfills_scene_identity(self):
        row = target._normalize_today_action_row(
            {
                "id": "action-risk",
                "title": "待处理风险事项",
                "entry_key": "project.risk.list",
                "source": "business",
                "source_detail": "factual_record",
                "scene_key": "",
                "route": "",
            }
        )

        expected_scene = target._route_scene_by_source("project.risk.list")
        self.assertEqual(row.get("scene_key"), expected_scene)
        self.assertEqual(row.get("route"), f"/s/{expected_scene}")
        self.assertEqual(row.get("entry_id"), "project.risk.list")
        self.assertEqual(row.get("action_key"), "open_scene")
