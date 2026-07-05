# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "reason_codes.py"


def _load_reason_codes():
    spec = importlib.util.spec_from_file_location("smart_core_reason_codes_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ReasonCodeLegacyMetaRegistryTests(unittest.TestCase):
    def test_core_default_has_no_legacy_payment_reason_metadata(self):
        reason_codes = _load_reason_codes()

        self.assertEqual(reason_codes.legacy_business_reason_meta_mapping(), {})
        meta = reason_codes.failure_meta_for_reason(reason_codes.REASON_PAYMENT_NOT_FULLY_PAID)

        self.assertEqual(meta, {"retryable": False, "error_category": "", "suggested_action": ""})

    def test_legacy_payment_reason_metadata_must_be_registered_explicitly(self):
        reason_codes = _load_reason_codes()

        reason_codes.register_legacy_business_reason_meta(
            reason_codes.REASON_PAYMENT_NOT_FULLY_PAID,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "complete_payment_execution",
            },
        )
        meta = reason_codes.failure_meta_for_reason(reason_codes.REASON_PAYMENT_NOT_FULLY_PAID)

        self.assertEqual(meta.get("error_category"), "business_state")
        self.assertEqual(meta.get("suggested_action"), "complete_payment_execution")
        self.assertEqual(
            (meta.get("source_authority") or {}).get("kind"),
            "legacy_business_reason_metadata_provider",
        )


if __name__ == "__main__":
    unittest.main()
