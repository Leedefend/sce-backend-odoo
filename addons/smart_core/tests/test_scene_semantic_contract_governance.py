# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "contract_governance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("contract_governance_scene_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


governance_module = _load_module()


class TestSceneSemanticContractGovernance(unittest.TestCase):
    def test_apply_contract_governance_preserves_scene_semantic_surfaces(self):
        payload = {
            "contract_version": "native_view.v1",
            "scene_contract_standard_v1": {
                "page": {
                    "surface": {
                        "view_type": "kanban",
                        "semantic_view": {"source_view": "kanban"},
                        "semantic_page": {"kanban_semantics": {"lane_count": 3}},
                    }
                },
                "governance": {
                    "parser_semantic_surface": {
                        "parser_contract": {"view_type": "kanban"},
                        "view_semantics": {"source_view": "kanban"},
                        "native_view": {"views": {"kanban": {"layout": []}}},
                    }
                },
            },
            "semantic_runtime": {
                "view_type": "kanban",
                "semantic_view": {"source_view": "kanban"},
                "parser_semantic_surface": {
                    "parser_contract": {"view_type": "kanban"},
                    "view_semantics": {"source_view": "kanban"},
                },
            },
            "released_scene_semantic_surface": {
                "scene_key": "workspace.home",
                "page_surface": {"view_type": "kanban", "semantic_view": {"source_view": "kanban"}},
                "parser_semantic_surface": {
                    "parser_contract": {"view_type": "kanban"},
                    "view_semantics": {"source_view": "kanban"},
                },
            },
        }

        governed = governance_module.apply_contract_governance(payload, "user", contract_surface="native")

        self.assertEqual(
            (((governed.get("scene_contract_standard_v1") or {}).get("page") or {}).get("surface") or {}).get("view_type"),
            "kanban",
        )
        self.assertEqual(
            (((((governed.get("scene_contract_standard_v1") or {}).get("governance") or {}).get("parser_semantic_surface") or {}).get("view_semantics") or {}).get("kind")),
            "view_semantics",
        )
        self.assertEqual(
            ((((governed.get("semantic_runtime") or {}).get("semantic_view") or {}).get("source_view"))),
            "kanban",
        )
        self.assertEqual(
            ((((governed.get("released_scene_semantic_surface") or {}).get("page_surface") or {}).get("view_type"))),
            "kanban",
        )


if __name__ == "__main__":
    unittest.main()
