#!/usr/bin/env python3
import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_construction_core/models/support/legacy_direct_acceptance_fact.py"


def _load_module():
    fake_odoo = types.ModuleType("odoo")
    fake_api = types.SimpleNamespace(depends=lambda *args: (lambda method: method))

    class _Fields:
        def __getattr__(self, _name):
            return lambda *args, **kwargs: None

    class _Model:
        pass

    fake_odoo.api = fake_api
    fake_odoo.fields = _Fields()
    fake_odoo.models = types.SimpleNamespace(Model=_Model)
    sys.modules["odoo"] = fake_odoo
    try:
        spec = importlib.util.spec_from_file_location("legacy_direct_acceptance_fact_test", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop("odoo", None)


class TestLegacyDirectAcceptanceAttachmentDisplay(unittest.TestCase):
    def test_inline_attachment_display_field_does_not_expose_raw_id(self):
        module = _load_module()
        payload = {
            "f_FDWB": "648de2ebffb0562545d750d3ba05642a",
            "f_FDWB_FJ": "附件(1)",
        }

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FDWB",
            acceptance_label="方单",
        )

        self.assertEqual(value, "附件(1)")

    def test_non_attachment_display_value_is_hidden_for_attachment_field(self):
        module = _load_module()
        payload = {"f_FJ": "abc123", "f_FJ_FJ": "abc123"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FJ",
            acceptance_label="分包方单",
        )

        self.assertEqual(value, "")


if __name__ == "__main__":
    unittest.main()
