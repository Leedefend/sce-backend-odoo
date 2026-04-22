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

scene_dsl_compiler = types.ModuleType("odoo.addons.smart_core.core.scene_dsl_compiler")
scene_dsl_compiler.scene_compile = lambda scene_payload, **_kwargs: {
    "scene": {"key": scene_payload.get("code") or scene_payload.get("key"), "title": scene_payload.get("name")},
    "page": {"mode": "", "route": ((scene_payload.get("target") or {}).get("route") or "")},
    "surface": {},
    "actions": list(scene_payload.get("actions") or []),
    "workflow_surface": {},
    "validation_surface": {},
    "meta": {},
}
sys.modules["odoo.addons.smart_core.core.scene_dsl_compiler"] = scene_dsl_compiler
core_pkg.scene_dsl_compiler = scene_dsl_compiler

ui_base_contract_adapter = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_adapter")
ui_base_contract_adapter.adapt_ui_base_contract = lambda payload, **_kwargs: {
    "normalized_contract": dict(payload or {}),
    "orchestrator_input": {"view_fact": True},
}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_adapter"] = ui_base_contract_adapter
core_pkg.ui_base_contract_adapter = ui_base_contract_adapter

parser_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_parser_semantic_bridge",
    CORE_DIR / "scene_ready_parser_semantic_bridge.py",
)
entry_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_entry_semantic_bridge",
    CORE_DIR / "scene_ready_entry_semantic_bridge.py",
)
orchestration_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_semantic_orchestration_bridge",
    CORE_DIR / "scene_ready_semantic_orchestration_bridge.py",
)
core_pkg.scene_ready_parser_semantic_bridge = parser_bridge
core_pkg.scene_ready_entry_semantic_bridge = entry_bridge
core_pkg.scene_ready_semantic_orchestration_bridge = orchestration_bridge

target = _load_module(
    "odoo.addons.smart_core.core.scene_ready_contract_builder",
    CORE_DIR / "scene_ready_contract_builder.py",
)


class TestSceneReadyContractBuilderSemanticConsumption(unittest.TestCase):
    def test_scene_ready_promotes_provider_delivery_handoff_surface(self):
        original = target._resolve_scene_provider_payload
        target._resolve_scene_provider_payload = lambda _scene_key, _runtime_ctx=None: {
            "guidance": {
                "title": "合同中心",
                "message": "先进入合同中心场景总览，再按工作台或监控分支继续处理合同任务。",
            },
            "primary_action": {
                "label": "进入合同中心",
                "route": "/s/contract.center",
                "semantic": "contract_root_scene_entry",
            },
            "fallback_strategy": {
                "type": "native_menu_compat",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
            },
            "next_scene": "contracts.workspace",
            "next_scene_route": "/s/contracts.workspace",
            "delivery_handoff_v1": {
                "family": "contracts",
                "runtime_entry_type": "governed_user_flow",
                "runtime_consumer": "family_runtime_consumer",
                "runtime_mode": "direct",
                "user_entry": "menu:smart_construction_core.menu_sc_contract_center",
                "final_scene": "contract.center",
                "primary_action": {
                    "route": "/s/contract.center",
                },
                "acceptance": {
                    "runtime_ready": True,
                    "workflow_ready": True,
                    "advisory_only": False,
                },
            },
        }
        try:
            contract = target.build_scene_ready_contract_v1(
                scenes=[
                    {
                        "code": "contract.center",
                        "name": "合同中心",
                        "layout": {"kind": "workspace"},
                        "target": {"route": "/s/contract.center"},
                    }
                ],
                role_surface={"landing_scene_key": "contract.center"},
            )
        finally:
            target._resolve_scene_provider_payload = original
        row = (contract.get("scenes") or [])[0]

        self.assertEqual(((row.get("guidance") or {}).get("title")), "合同中心")
        self.assertEqual(((row.get("primary_action") or {}).get("route")), "/s/contract.center")
        self.assertEqual(((row.get("fallback_strategy") or {}).get("type")), "native_menu_compat")
        self.assertEqual(row.get("next_scene"), "contracts.workspace")
        self.assertEqual(row.get("next_scene_route"), "/s/contracts.workspace")
        self.assertEqual(((row.get("delivery_handoff_v1") or {}).get("family")), "contracts")
        self.assertEqual(((row.get("runtime_handoff_surface") or {}).get("final_scene")), "contract.center")
        self.assertEqual(((row.get("product_delivery_surface") or {}).get("family")), "contracts")

    def test_workspace_scene_ready_prefers_parser_semantic_view_mode(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "workspace.home",
                    "name": "工作台",
                    "layout": {"kind": "workspace"},
                    "target": {"route": "/my-work"},
                    "ui_base_contract": {
                        "parser_contract": {"view_type": "form"},
                        "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                        "native_view": {"views": {"form": {"layout": []}, "search": {"layout": []}}},
                        "semantic_page": {"title_node": {"text": "工作台"}},
                    },
                }
            ],
            role_surface={"landing_scene_key": "workspace.home"},
        )
        row = (contract.get("scenes") or [])[0]

        self.assertEqual(((row.get("view_modes") or [])[0] or {}).get("key"), "form")
        self.assertEqual(((row.get("action_surface") or {}).get("selection_mode")), "single")

    def test_form_scene_ready_emits_form_surface_native_truth(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.detail",
                    "name": "项目详情",
                    "layout": {"kind": "detail"},
                    "target": {"route": "/r/project.project/3"},
                    "ui_base_contract": {
                        "parser_contract": {"view_type": "form"},
                        "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                        "views": {
                            "form": {
                                "layout": [{"type": "sheet", "children": [{"type": "field", "name": "name"}]}],
                                "header_buttons": [{"key": "save", "label": "保存"}],
                                "button_box": [{"key": "stat_tasks", "label": "任务"}],
                                "stat_buttons": [{"key": "stat_docs", "label": "文档"}],
                            }
                        },
                        "semantic_page": {
                            "form_semantics": {
                                "layout_section_count": 1,
                                "has_statusbar": True,
                                "has_notebook": False,
                                "has_chatter": True,
                                "has_attachments": False,
                                "relation_fields": [{"field": "task_ids", "takeover_hint": "frontend"}],
                                "field_behavior_map": {"name": {"readonly": False}},
                            }
                        },
                    },
                }
            ],
            role_surface={"landing_scene_key": "projects.detail"},
        )
        row = (contract.get("scenes") or [])[0]
        form_surface = row.get("form_surface") or {}

        self.assertEqual((((form_surface.get("layout") or [])[0]).get("type")), "sheet")
        self.assertEqual((((form_surface.get("header_actions") or [])[0]).get("key")), "save")
        self.assertEqual(len(form_surface.get("stat_actions") or []), 2)
        self.assertEqual((((form_surface.get("relation_fields") or [])[0]).get("field")), "task_ids")
        self.assertTrue(((form_surface.get("flags") or {}).get("has_statusbar")))

    def test_list_scene_ready_emits_optimization_composition_batch1(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.list",
                    "name": "项目列表",
                    "layout": {"kind": "list"},
                    "target": {"route": "/a/449"},
                    "search_surface": {
                        "fields": [{"name": "name", "string": "名称"}],
                        "filters": [
                            {"key": "activities_today", "label": "今日活动", "kind": "filter"},
                            {"key": "mine", "label": "我的项目", "kind": "filter"},
                            {"key": "unassigned", "label": "未分派", "kind": "filter"},
                        ],
                        "group_by": [{"key": "stage_id", "label": "阶段", "field": "stage_id", "kind": "group_by"}],
                        "searchpanel": [{"name": "stage_id", "string": "阶段", "multi": True}],
                        "default_state": {
                            "filters": [{"key": "activities_today", "label": "今日活动", "kind": "filter"}],
                        },
                    },
                    "list_surface": {
                        "columns": [{"field": "name", "label": "名称"}],
                        "default_sort": {"raw": "write_date desc", "display_label": "更新时间 降序"},
                        "available_view_modes": [{"key": "tree", "label": "列表"}],
                        "default_mode": "tree",
                    },
                    "related_scenes": ["projects.ledger"],
                },
                {
                    "code": "projects.ledger",
                    "name": "项目台账",
                    "layout": {"kind": "ledger"},
                    "target": {"route": "/s/projects.ledger"},
                }
            ],
            role_surface={"landing_scene_key": "projects.list"},
        )
        row = next(
            (
                item
                for item in (contract.get("scenes") or [])
                if ((item.get("scene") or {}).get("key")) == "projects.list"
            ),
            {},
        )
        optimization = row.get("optimization_composition") or {}
        switch_surface = row.get("switch_surface") or {}
        switch_items = switch_surface.get("items") or []

        self.assertEqual((((optimization.get("toolbar_sections") or [])[0]).get("key")), "search")
        self.assertEqual((((optimization.get("toolbar_sections") or [])[1]).get("key")), "active_conditions")
        self.assertTrue(((optimization.get("active_conditions") or {}).get("visible")))
        self.assertEqual((((optimization.get("high_frequency_filters") or [])[0]).get("key")), "activities_today")
        self.assertTrue(((optimization.get("advanced_filters") or {}).get("collapsible")))
        self.assertEqual(((switch_items[0] or {}).get("key")), "projects.list")
        self.assertEqual(((switch_items[0] or {}).get("label")), "项目列表")
        self.assertTrue(bool((switch_items[0] or {}).get("active")))
        self.assertEqual(((switch_items[1] or {}).get("route")), "/s/projects.ledger")
        self.assertEqual(((switch_items[1] or {}).get("label")), "项目台账")


if __name__ == "__main__":
    unittest.main()
