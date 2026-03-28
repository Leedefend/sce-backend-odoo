# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "ui_base_contract_canonicalizer.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ui_base_contract_canonicalizer_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


canonicalizer_module = _load_module()


class TestUiBaseContractCanonicalizer(unittest.TestCase):
    def test_canonicalizer_normalizes_group_bys_alias(self):
        canonical = canonicalizer_module.canonicalize_ui_base_contract(
            {
                "search": {
                    "group_bys": [{"name": "by_stage", "group_by": "stage_id", "string": "按阶段"}],
                    "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                }
            }
        )

        search = canonical.get("search") or {}
        self.assertEqual((search.get("group_by") or [])[0]["group_by"], "stage_id")
        self.assertEqual((search.get("searchpanel") or [])[0]["name"], "stage_id")


if __name__ == "__main__":
    unittest.main()
