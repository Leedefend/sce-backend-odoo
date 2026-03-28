# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "ui_base_contract_adapter.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ui_base_contract_adapter_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


adapter_module = _load_module()


class TestUiBaseContractAdapter(unittest.TestCase):
    def test_adapter_preserves_parser_semantic_surface(self):
        payload = {
            "model": "project.project",
            "views": {"form": {"layout": []}},
            "search": {
                "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                "mode": "faceted",
            },
            "parser_contract": {"view_type": "form", "layout": {"kind": "form"}},
            "view_semantics": {"source_view": "form", "capability_flags": {"has_title": True}},
            "native_view": {"views": {"form": {"layout": []}}},
            "semantic_page": {"list_semantics": {"columns": []}},
        }

        adapted = adapter_module.adapt_ui_base_contract(payload, scene_key="workspace.home")

        parser_fact = adapted["orchestrator_input"]["parser_fact"]
        normalized = adapted["normalized_contract"]

        self.assertEqual(parser_fact["parser_contract"]["view_type"], "form")
        self.assertEqual(parser_fact["view_semantics"]["source_view"], "form")
        self.assertIn("form", parser_fact["native_view"]["views"])
        self.assertEqual((adapted["orchestrator_input"]["search_fact"]["searchpanel"] or [])[0]["name"], "stage_id")
        self.assertEqual((adapted["orchestrator_input"]["search_fact"]["group_by"] or [])[0]["group_by"], "stage_id")
        self.assertEqual(adapted["orchestrator_input"]["search_fact"]["mode"], "faceted")
        self.assertIn("semantic_page", normalized)
        self.assertEqual(normalized["parser_contract"]["view_type"], "form")


if __name__ == "__main__":
    unittest.main()
