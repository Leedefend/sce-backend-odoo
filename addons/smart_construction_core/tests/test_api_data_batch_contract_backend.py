# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.api_data_batch import ApiDataBatchHandler


@tagged("sc_smoke", "api_data_batch_backend")
class TestApiDataBatchContractBackend(TransactionCase):
    def test_not_found_failure_has_structured_contract(self):
        handler = ApiDataBatchHandler(self.env, payload={})
        result = handler.handle(
            {
                "params": {
                    "model": "res.partner",
                    "ids": [999999999],
                    "action": "archive",
                    "request_id": "req-batch-001",
                }
            }
        )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-batch-001")
        self.assertTrue(str(data.get("trace_id") or "").startswith("adb_"))
        self.assertEqual(data.get("idempotency_key"), "req-batch-001")
        self.assertEqual(data.get("failed"), 1)
        self.assertEqual(data.get("failed_retry_ids"), [])
        self.assertEqual(data.get("failed_retryable_summary"), {"retryable": 0, "non_retryable": 1})
        reason_rows = data.get("failed_reason_summary") or []
        self.assertEqual(reason_rows[0].get("reason_code"), "NOT_FOUND")
        self.assertEqual(reason_rows[0].get("count"), 1)
        rows = data.get("results") or []
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("reason_code"), "NOT_FOUND")
        self.assertFalse(bool(row.get("retryable")))
        self.assertEqual(row.get("error_category"), "not_found")
        self.assertEqual(row.get("suggested_action"), "refresh_list")
        self.assertTrue(str(row.get("trace_id") or "").startswith("adb_"))

    def test_conflict_is_retryable_and_collected_for_retry(self):
        partner = self.env["res.partner"].create({"name": "Batch Conflict Contract"})
        handler = ApiDataBatchHandler(self.env, payload={})
        result = handler.handle(
            {
                "params": {
                    "model": "res.partner",
                    "ids": [partner.id],
                    "action": "archive",
                    "request_id": "req-batch-002",
                    "if_match_map": {str(partner.id): "2000-01-01 00:00:00"},
                }
            }
        )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("failed"), 1)
        self.assertEqual(data.get("failed_retry_ids"), [partner.id])
        self.assertEqual(data.get("failed_retryable_summary"), {"retryable": 1, "non_retryable": 0})
        reason_rows = data.get("failed_reason_summary") or []
        self.assertEqual(reason_rows[0].get("reason_code"), "CONFLICT")
        self.assertEqual(reason_rows[0].get("count"), 1)
        rows = data.get("results") or []
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("reason_code"), "CONFLICT")
        self.assertTrue(bool(row.get("retryable")))
        self.assertEqual(row.get("error_category"), "conflict")
        self.assertEqual(row.get("suggested_action"), "reload_then_retry")

    def test_legacy_replay_result_is_backfilled_to_new_contract(self):
        handler = ApiDataBatchHandler(self.env, payload={})
        legacy = {
            "results": [
                {"id": 11, "ok": False, "reason_code": "CONFLICT", "message": "legacy"},
                {"id": 12, "ok": False, "reason_code": "NOT_FOUND", "message": "legacy"},
            ]
        }
        enriched = handler._ensure_result_contract(legacy, request_id="req-legacy-1", trace_id="adb_legacy")
        self.assertEqual(enriched.get("request_id"), "req-legacy-1")
        self.assertEqual(enriched.get("trace_id"), "adb_legacy")
        self.assertEqual(enriched.get("failed_retry_ids"), [11])
        self.assertEqual(enriched.get("failed_retryable_summary"), {"retryable": 1, "non_retryable": 1})
        reasons = enriched.get("failed_reason_summary") or []
        reason_codes = sorted([row.get("reason_code") for row in reasons])
        self.assertEqual(reason_codes, ["CONFLICT", "NOT_FOUND"])
        rows = enriched.get("results") or []
        self.assertEqual(len(rows), 2)
        self.assertTrue(bool(rows[0].get("trace_id")))
        self.assertIn("error_category", rows[0])
        self.assertIn("suggested_action", rows[0])
