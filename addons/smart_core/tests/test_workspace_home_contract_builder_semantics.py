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
    def test_workspace_home_builder_declares_startup_projection_source(self):
        source = target.source_authority_contract()

        self.assertEqual(source.get("kind"), "workspace_home_startup_surface_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertIn("extension_fact_contributions", source.get("authorities") or [])
        self.assertEqual(source.get("legacy_workspace_keyword_policy"), "legacy_workspace_keyword_policy_projection")

    def test_workspace_home_keyword_policy_is_marked_as_legacy_projection(self):
        payload = target.build_workspace_home_contract(
            {
                "capabilities": [],
                "scenes": [],
                "workspace_keyword_overrides": {"token_sets": {"build_urgent_keywords": ["urgent"]}},
            }
        )

        keyword_policy = ((payload.get("diagnostics") or {}).get("keyword_policy") or {})
        self.assertTrue(keyword_policy.get("overrides_present"))
        self.assertEqual(
            ((keyword_policy.get("source_authority") or {}).get("kind")),
            "legacy_workspace_keyword_policy_projection",
        )
        self.assertTrue(((keyword_policy.get("source_authority") or {}).get("no_business_fact_authority")))

    def test_business_scope_metric_uses_record_scope_key_with_legacy_alias(self):
        business_metrics, _ = target._build_metric_sets(
            ready_count=1,
            locked_count=0,
            preview_count=0,
            scene_count=3,
            today_action_count=0,
            risk_action_count=0,
        )

        scope_metric = next((row for row in business_metrics if row.get("legacy_key") == "biz.project_scope"), {})
        self.assertEqual(scope_metric.get("key"), "biz.record_scope")
        self.assertEqual(scope_metric.get("legacy_key"), "biz.project_scope")

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
