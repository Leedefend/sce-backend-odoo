# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "native_view_contract_projection.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("native_view_contract_projection_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


projection_module = _load_module()


class TestNativeViewContractProjection(unittest.TestCase):
    def test_inject_primary_view_projection_promotes_primary_semantics(self):
        payload = {
            "head": {"model": "project.project", "view_type": "form"},
            "views": {
                "form": {
                    "layout": [{"kind": "group"}],
                    "parser_contract": {"view_type": "form", "layout": {"kind": "form"}},
                    "view_semantics": {
                        "kind": "view_semantics",
                        "source_view": "form",
                        "capability_flags": {"has_title": True},
                        "semantic_meta": {"header_button_count": 1},
                    },
                }
            },
            "fields": {"name": {"string": "Name"}},
            "permissions": {"write": True},
            "native_view": {"views": {"form": {"layout": [{"kind": "group"}]}}},
        }

        projection_module.inject_primary_view_projection(payload)

        self.assertEqual(payload["layout"], [{"kind": "group"}])
        self.assertEqual(payload["view_type"], "form")
        self.assertEqual(payload["model"], "project.project")
        self.assertEqual(payload["parser_contract"]["view_type"], "form")
        self.assertEqual(payload["view_semantics"]["source_view"], "form")
        self.assertEqual(payload["view_semantics"]["semantic_meta"]["header_button_count"], 1)
        self.assertTrue(payload["permissions"]["write"])
        self.assertIn("native_view", payload)

    def test_inject_primary_view_projection_backfills_semantics_from_legacy_layout(self):
        payload = {
            "head": {"model": "project.project", "view_type": "form"},
            "views": {
                "form": {
                    "layout": [{"name": "name", "type": "field"}],
                }
            },
        }

        projection_module.inject_primary_view_projection(payload)

        self.assertEqual(payload["parser_contract"]["view_type"], "form")
        self.assertEqual(payload["parser_contract"]["projection_source"], "legacy_primary_view_fallback")
        self.assertEqual(payload["view_semantics"]["source_view"], "form")
        self.assertEqual(payload["view_semantics"]["semantic_meta"]["projection_source"], "legacy_primary_view_fallback")


if __name__ == "__main__":
    unittest.main()
