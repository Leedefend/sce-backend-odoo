# -*- coding: utf-8 -*-
import importlib.util
import re
import sys
import unittest
from pathlib import Path


def _load_normalizer():
    root = Path(__file__).resolve().parents[1]
    module_name = "smart_core_contract_normalizer_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(
        module_name,
        root / "app_config_engine" / "services" / "normalizer.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestContractNormalizerBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_normalizer()

    def test_default_meta_timestamp_is_utc_z_contract(self):
        payload = {
            "ok": True,
            "data": {
                "head": {},
                "permissions": {},
                "rules": {},
                "search": {},
                "views": {},
                "fields": {},
                "buttons": {},
                "workflow": {},
                "collab": {},
                "reports": {},
                "ui": {},
                "data": {},
                "meta": {},
            },
            "meta": {},
        }

        result = self.module.ContractNormalizer().normalize(payload)

        self.assertRegex(result["meta"]["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertNotRegex(result["meta"]["ts"], re.escape("+00:00"))


if __name__ == "__main__":
    unittest.main()
