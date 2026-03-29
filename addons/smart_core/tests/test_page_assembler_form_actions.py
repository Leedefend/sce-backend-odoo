# -*- coding: utf-8 -*-
import importlib.util
import pathlib
import sys
import types
import unittest


def _load_page_assembler():
    module_path = pathlib.Path(__file__).resolve().parents[1] / "app_config_engine" / "services" / "assemblers" / "page_assembler.py"
    package_root = "addons.smart_core.app_config_engine.services.assemblers"
    parents = [
        "addons",
        "addons.smart_core",
        "addons.smart_core.app_config_engine",
        "addons.smart_core.app_config_engine.services",
        package_root,
        "addons.smart_core.app_config_engine.utils",
    ]
    for name in parents:
        if name not in sys.modules:
            pkg = types.ModuleType(name)
            pkg.__path__ = []
            sys.modules[name] = pkg

    if "odoo" not in sys.modules:
        odoo_mod = types.ModuleType("odoo")
        http_mod = types.ModuleType("odoo.http")
        http_mod.request = None
        odoo_mod.http = http_mod
        sys.modules["odoo"] = odoo_mod
        sys.modules["odoo.http"] = http_mod

    misc_name = "addons.smart_core.app_config_engine.utils.misc"
    if misc_name not in sys.modules:
        misc_mod = types.ModuleType(misc_name)
        misc_mod.safe_eval = lambda value=None: value
        sys.modules[misc_name] = misc_mod

    view_utils_name = "addons.smart_core.app_config_engine.utils.view_utils"
    if view_utils_name not in sys.modules:
        vu_mod = types.ModuleType(view_utils_name)
        vu_mod.extract_tree_columns_strict = lambda *args, **kwargs: ([], None)
        vu_mod.normalize_cols_safely = lambda *args, **kwargs: []
        sys.modules[view_utils_name] = vu_mod

    spec = importlib.util.spec_from_file_location(package_root + ".page_assembler", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.PageAssembler


PageAssembler = _load_page_assembler()


class _FakeViewConfig:
    def __init__(self, arch_parsed):
        self.arch_parsed = arch_parsed


class TestPageAssemblerFormActions(unittest.TestCase):
    def setUp(self):
        self.assembler = PageAssembler.__new__(PageAssembler)

    def test_extract_form_action_rows_from_arch_parsed(self):
        rows = self.assembler._extract_form_action_rows_from_view_config(
            _FakeViewConfig(
                {
                    "header_buttons": [{"key": "obj_action_sc_submit_进入下一阶段", "payload": {"method": "action_sc_submit"}}],
                    "button_box": [{"key": "obj_action_view_tasks_任务", "payload": {"method": "action_view_tasks"}}],
                }
            )
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["key"], "obj_action_sc_submit_进入下一阶段")
        self.assertEqual(rows[1]["key"], "obj_action_view_tasks_任务")

    def test_filter_form_actions_prefers_parsed_form_facts(self):
        source_rows = [
            {
                "key": "obj_action_sc_submit_进入下一阶段",
                "label": "进入下一阶段",
                "kind": "object",
                "level": "header",
                "selection": "single",
                "payload": {"method": "action_sc_submit"},
            },
            {
                "key": "obj_action_view_tasks_任务",
                "label": "任务",
                "kind": "object",
                "level": "smart",
                "selection": "single",
                "payload": {"method": "action_view_tasks"},
            },
        ]
        buttons_data = [
            {
                "key": "obj_action_view_tasks_Create project",
                "label": "Create project",
                "kind": "object",
                "level": "header",
                "selection": "single",
                "payload": {"method": "action_view_tasks"},
            },
            {
                "key": "obj_action_sc_submit_进入下一阶段",
                "label": "进入下一阶段",
                "kind": "object",
                "level": "header",
                "selection": "single",
                "payload": {"method": "action_sc_submit"},
            },
            {
                "key": "act_536_快速创建项目",
                "label": "快速创建项目",
                "kind": "open",
                "level": "header",
                "selection": "single",
                "payload": {"action_id": 536},
            },
        ]

        filtered = self.assembler._filter_form_actions_to_source_rows(buttons_data, source_rows)

        self.assertEqual(
            [row.get("key") for row in filtered],
            [
                "obj_action_sc_submit_进入下一阶段",
                "obj_action_view_tasks_Create project",
            ],
        )
        self.assertEqual(filtered[1]["label"], "任务")
        self.assertEqual(filtered[1]["level"], "smart")
        self.assertEqual(filtered[1]["selection"], "single")

    def test_filter_form_actions_noops_without_form_button_facts(self):
        buttons_data = [
            {
                "key": "obj_action_view_tasks_Create project",
                "label": "Create project",
                "kind": "object",
                "level": "header",
                "selection": "single",
                "payload": {"method": "action_view_tasks"},
            }
        ]

        filtered = self.assembler._filter_form_actions_to_source_rows(buttons_data, [])

        self.assertEqual(filtered, buttons_data)


if __name__ == "__main__":
    unittest.main()
