# -*- coding: utf-8 -*-

import json

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.reason_codes import (
    REASON_IDEMPOTENCY_CONFLICT,
    REASON_REPLAY_WINDOW_EXPIRED,
)
from odoo.addons.smart_core.handlers.api_data_batch import ApiDataBatchHandler
from odoo.addons.smart_core.utils.idempotency import (
    apply_replay_evidence,
    find_latest_audit_entry,
    has_latest_fingerprint_match,
    resolve_idempotency_decision,
)


@tagged("sc_smoke", "api_data_batch_backend")
class TestApiDataBatchContractBackend(TransactionCase):
    def _create_audit(self, *, event_code, model, idem_key, actor_uid, company_id):
        Audit = self.env.get("sc.audit.log")
        return Audit.sudo().create(
            {
                "event_code": event_code,
                "action": "test",
                "model": model,
                "res_id": 0,
                "actor_uid": int(actor_uid),
                "actor_login": "tester",
                "after_json": json.dumps(
                    {
                        "idempotency_key": idem_key,
                        "idempotency_fingerprint": "fp",
                        "result": {"ok": True},
                    },
                    ensure_ascii=True,
                ),
                "trace_id": "trace_test",
                "company_id": int(company_id) if company_id else False,
            }
        )

    def test_idempotency_fingerprint_normalizes_id_order(self):
        handler = ApiDataBatchHandler(self.env, payload={})
        first = handler._idempotency_fingerprint(
            model="res.partner",
            action="archive",
            ids=[5, 3, 9],
            vals={"active": False},
            idem_key="req-fp-1",
        )
        second = handler._idempotency_fingerprint(
            model="res.partner",
            action="archive",
            ids=[9, 5, 3],
            vals={"active": False},
            idem_key="req-fp-1",
        )
        self.assertEqual(first, second)

    def test_find_latest_audit_entry_extra_domain_applies(self):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            self.skipTest("sc.audit.log not available")
        key = "req-audit-domain-1"
        self._create_audit(
            event_code="API_DATA_BATCH",
            model="res.partner",
            idem_key=key,
            actor_uid=self.env.user.id,
            company_id=self.env.user.company_id.id,
        )
        self._create_audit(
            event_code="API_DATA_BATCH",
            model="project.project",
            idem_key=key,
            actor_uid=self.env.user.id,
            company_id=self.env.user.company_id.id,
        )
        entry = find_latest_audit_entry(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key=key,
            extra_domain=[("model", "=", "res.partner")],
        )
        self.assertTrue(bool(entry))
        payload = entry.get("payload") or {}
        self.assertEqual(str(payload.get("idempotency_key") or ""), key)

    def test_find_latest_audit_entry_enforces_actor_and_company(self):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            self.skipTest("sc.audit.log not available")
        key = "req-audit-scope-1"
        other_user = self.env["res.users"].sudo().search([("id", "!=", self.env.user.id)], limit=1)
        other_company = self.env["res.company"].sudo().search([("id", "!=", self.env.user.company_id.id)], limit=1)
        if not other_user or not other_company:
            self.skipTest("requires another user and company")
        self._create_audit(
            event_code="API_DATA_BATCH",
            model="res.partner",
            idem_key=key,
            actor_uid=other_user.id,
            company_id=other_company.id,
        )
        entry = find_latest_audit_entry(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key=key,
        )
        self.assertFalse(bool(entry))

    def test_has_latest_fingerprint_match_enforces_scope(self):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            self.skipTest("sc.audit.log not available")
        key = "req-fingerprint-scope-1"
        other_user = self.env["res.users"].sudo().search([("id", "!=", self.env.user.id)], limit=1)
        other_company = self.env["res.company"].sudo().search([("id", "!=", self.env.user.company_id.id)], limit=1)
        if not other_user or not other_company:
            self.skipTest("requires another user and company")
        self._create_audit(
            event_code="API_DATA_BATCH",
            model="res.partner",
            idem_key=key,
            actor_uid=other_user.id,
            company_id=other_company.id,
        )
        self.assertFalse(
            has_latest_fingerprint_match(
                self.env,
                event_code="API_DATA_BATCH",
                idempotency_key=key,
                fingerprint="fp",
                extra_domain=[("model", "=", "res.partner")],
            )
        )

    def test_resolve_idempotency_decision_returns_stable_empty_shape(self):
        decision = resolve_idempotency_decision(
            self.env,
            event_code="API_DATA_BATCH",
            idempotency_key="",
            fingerprint="fp",
            window_seconds=30,
        )
        self.assertEqual(
            decision,
            {
                "conflict": False,
                "replay_entry": None,
                "replay_payload": None,
                "replay_window_expired": False,
            },
        )

    def test_apply_replay_evidence_shape_and_defaults(self):
        base = apply_replay_evidence({"x": 1}, enabled=False)
        self.assertEqual(base, {"x": 1})
        enabled = apply_replay_evidence({"x": 1}, enabled=True)
        self.assertEqual(enabled.get("replay_from_audit_id"), 0)
        self.assertEqual(enabled.get("replay_original_trace_id"), "")
        self.assertEqual(enabled.get("replay_age_ms"), 0)
        replay = apply_replay_evidence(
            {"x": 1},
            enabled=True,
            idempotent_replay=True,
            replay_entry={"audit_id": 9, "trace_id": "t1"},
        )
        self.assertEqual(replay.get("replay_from_audit_id"), 9)
        self.assertEqual(replay.get("replay_original_trace_id"), "t1")
        self.assertTrue(int(replay.get("replay_age_ms") or 0) >= 0)

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
        self.assertFalse(bool(data.get("replay_window_expired")))
        self.assertEqual(data.get("idempotency_replay_reason_code"), "")
        self.assertEqual(int(data.get("replay_from_audit_id") or 0), 0)
        self.assertEqual(str(data.get("replay_original_trace_id") or ""), "")
        self.assertEqual(int(data.get("replay_age_ms") or 0), 0)
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

    def test_replay_window_expired_is_exposed_in_contract(self):
        if not self.env.get("sc.audit.log"):
            self.skipTest("sc.audit.log not available")
        partner = self.env["res.partner"].create({"name": "Batch Replay Window"})
        handler = ApiDataBatchHandler(self.env, payload={})
        payload = {
            "params": {
                "model": "res.partner",
                "ids": [partner.id],
                "action": "archive",
                "request_id": "req-batch-replay-expired-1",
            }
        }
        first = handler.handle(payload)
        self.assertTrue(first.get("ok"))
        original_window = handler.IDEMPOTENCY_WINDOW_SECONDS
        try:
            handler.IDEMPOTENCY_WINDOW_SECONDS = 0
            second = handler.handle(payload)
        finally:
            handler.IDEMPOTENCY_WINDOW_SECONDS = original_window
        self.assertTrue(second.get("ok"))
        data = second.get("data") or {}
        self.assertFalse(bool(data.get("idempotent_replay")))
        self.assertTrue(bool(data.get("replay_window_expired")))
        self.assertEqual(data.get("idempotency_replay_reason_code"), REASON_REPLAY_WINDOW_EXPIRED)

    def test_idempotent_replay_includes_replay_evidence(self):
        if not self.env.get("sc.audit.log"):
            self.skipTest("sc.audit.log not available")
        partner = self.env["res.partner"].create({"name": "Batch Replay Evidence"})
        handler = ApiDataBatchHandler(self.env, payload={})
        payload = {
            "params": {
                "model": "res.partner",
                "ids": [partner.id],
                "action": "archive",
                "request_id": "req-batch-replay-evidence-1",
            }
        }
        first = handler.handle(payload)
        self.assertTrue(first.get("ok"))
        second = handler.handle(payload)
        self.assertTrue(second.get("ok"))
        data = second.get("data") or {}
        self.assertTrue(bool(data.get("idempotent_replay")))
        self.assertTrue(int(data.get("replay_from_audit_id") or 0) > 0)
        self.assertTrue(bool(str(data.get("replay_original_trace_id") or "")))
        self.assertTrue(int(data.get("replay_age_ms") or 0) >= 0)

    def test_idempotency_conflict_returns_409(self):
        if not self.env.get("sc.audit.log"):
            self.skipTest("sc.audit.log not available")
        handler = ApiDataBatchHandler(self.env, payload={})
        first = handler.handle(
            {
                "params": {
                    "model": "res.partner",
                    "ids": [999999991],
                    "action": "archive",
                    "request_id": "req-batch-idem-conflict-1",
                }
            }
        )
        self.assertTrue(first.get("ok"))
        conflict = handler.handle(
            {
                "params": {
                    "model": "res.partner",
                    "ids": [999999992],
                    "action": "archive",
                    "request_id": "req-batch-idem-conflict-1",
                }
            }
        )
        self.assertFalse(conflict.get("ok"))
        self.assertEqual(int(conflict.get("code") or 0), 409)
        err = conflict.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_IDEMPOTENCY_CONFLICT)
        self.assertFalse(bool(err.get("retryable")))
        self.assertEqual(err.get("error_category"), "conflict")
        self.assertEqual(err.get("suggested_action"), "use_new_request_id")

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
