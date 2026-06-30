#!/usr/bin/env python3
import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
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
    sys.modules["odoo.osv"] = types.ModuleType("odoo.osv")
    sys.modules["odoo.osv.expression"] = types.SimpleNamespace(AND=lambda domains: domains, OR=lambda domains: domains)
    try:
        spec = importlib.util.spec_from_file_location("legacy_direct_acceptance_fact_test", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop("odoo", None)
        sys.modules.pop("odoo.osv", None)
        sys.modules.pop("odoo.osv.expression", None)


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

    def test_direct_attachment_label_from_payload_is_displayed(self):
        module = _load_module()
        payload = {"FJ": "7c728a58b0962153c6663b05e2192d01", "f_FJ": "附件(1)"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FJ",
            acceptance_label="材料结算单",
            attachment_ref="7c728a58b0962153c6663b05e2192d01",
        )

        self.assertEqual(value, "附件(1)")

    def test_raw_attachment_id_matching_record_ref_is_displayed_as_one_attachment(self):
        module = _load_module()
        payload = {"FJ": "172ebd3a702bb774da4b2d1ef419465e"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FJ",
            acceptance_label="项目费用报销单",
            attachment_ref="172ebd3a702bb774da4b2d1ef419465e",
        )

        self.assertEqual(value, "附件(1)")

    def test_raw_attachment_hash_without_record_ref_is_displayed_as_one_attachment(self):
        module = _load_module()
        payload = {"FJ": "fed85f8d2066871e2d2037ffcadfd7fd"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FJ",
            acceptance_label="工程进度收款",
        )

        self.assertEqual(value, "附件(1)")

    def test_subcontract_usage_raw_attachment_hash_without_old_label_is_hidden(self):
        module = _load_module()
        payload = {"FJ": "f965ab7575498081ce6b291f989923fb", "f_FJ": None}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "f_FJ",
            acceptance_label="分包方单",
            attachment_ref="f965ab7575498081ce6b291f989923fb",
        )

        self.assertEqual(value, "")

    def test_negative_legacy_unpaid_amount_falls_back_to_balance(self):
        module = _load_module()
        payload = {"ZJE": "2450", "CCCC_FKJE": "0", "WFKJE": "-2450"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_common_computed_visible_value(
            payload,
            "CCCC_WFKJE",
        )

        self.assertEqual(value, "2450.0")

    def test_input_tax_line_rate_is_formatted_as_percent(self):
        module = _load_module()
        payload = {"SLV$C_JXXP_ZYFPJJD_CB": "0.13"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "SLV$C_JXXP_ZYFPJJD_CB",
            acceptance_label="进项上报",
        )

        self.assertEqual(value, "13%")

    def test_general_contract_input_tax_rate_falls_back_to_amount_ratio(self):
        module = _load_module()
        payload = {"BHSJE": "22591.74", "ZSE": "2711.01"}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "SLVS",
            acceptance_label="总包进项上报",
        )

        self.assertEqual(value, "12%")

    def test_nested_legacy_payload_value_serializes_projection_scalars(self):
        module = _load_module()
        payload = {"BZ": {"day": date(2026, 6, 30), "amount": Decimal("12.30")}}

        value = module.ScLegacyDirectAcceptanceFact._legacy_payload_value(
            payload,
            "BZ",
            acceptance_label="施工日志（新）",
        )

        self.assertEqual(value, '{"amount": "12.30", "day": "2026-06-30"}')


if __name__ == "__main__":
    unittest.main()
