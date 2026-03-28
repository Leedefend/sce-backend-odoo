# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "contract_governance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("contract_governance_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


governance_module = _load_module()


class TestNativeViewContractGovernance(unittest.TestCase):
    def test_apply_contract_governance_preserves_native_view_surface(self):
        payload = {
            "contract_version": "native_view.v1",
            "parser_contract": {"view_type": "form"},
            "view_semantics": {"source_view": "form"},
            "native_view": {"views": {"form": {"layout": []}}},
        }

        governed = governance_module.apply_contract_governance(payload, "user", contract_surface="native")

        self.assertEqual(governed["parser_contract"]["view_type"], "form")
        self.assertEqual(governed["parser_contract"]["contract_version"], "native_view.v1")
        self.assertEqual(governed["view_semantics"]["kind"], "view_semantics")
        self.assertEqual(governed["view_semantics"]["source_view"], "form")
        self.assertEqual(governed["view_semantics"]["capability_flags"], {})
        self.assertEqual(governed["view_semantics"]["semantic_meta"], {})
        self.assertIn("form", governed["native_view"]["views"])
        self.assertEqual(governed["native_view"]["search"], {})
        self.assertEqual(governed["native_view"]["toolbar"], {})


if __name__ == "__main__":
    unittest.main()
