# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.api_data_unlink import ApiDataUnlinkHandler
from odoo.addons.smart_core.handlers.api_data_write import ApiDataWriteHandler
from odoo.addons.smart_core.handlers.reason_codes import REASON_IDEMPOTENCY_CONFLICT


@tagged("sc_smoke", "api_data_batch_backend")
class TestApiDataWriteUnlinkIdempotencyBackend(TransactionCase):
    def _ensure_audit_model(self):
        if not self.env.get("sc.audit.log"):
            self.skipTest("sc.audit.log not available")

    def test_api_data_write_same_key_same_payload_is_deduplicated(self):
        self._ensure_audit_model()
        project = self.env["project.project"].create({"name": "Write Idem Original"})
        handler = ApiDataWriteHandler(self.env, payload={})
        payload = {
            "intent": "api.data.write",
            "params": {
                "model": "project.project",
                "id": project.id,
                "values": {"name": "Write Idem Updated"},
                "request_id": "req-write-idem-1",
            },
        }
        first = handler.handle(payload)
        self.assertTrue(first.get("ok"))
        first_data = first.get("data") or {}
        self.assertFalse(bool(first_data.get("idempotency_deduplicated")))
        self.assertFalse(bool(first_data.get("idempotent_replay")))
        self.assertFalse(bool(first_data.get("replay_supported")))

        first_row = self.env["project.project"].browse(project.id).read(["name", "write_date"])[0]
        first_write_date = first_row.get("write_date")

        second = handler.handle(payload)
        self.assertTrue(second.get("ok"))
        second_data = second.get("data") or {}
        self.assertTrue(bool(second_data.get("idempotency_deduplicated")))
        self.assertEqual(second_data.get("request_id"), "req-write-idem-1")
        self.assertEqual(second_data.get("idempotency_key"), "req-write-idem-1")
        self.assertFalse(bool(second_data.get("idempotent_replay")))
        self.assertFalse(bool(second_data.get("replay_supported")))

        second_row = self.env["project.project"].browse(project.id).read(["name", "write_date"])[0]
        self.assertEqual(second_row.get("name"), "Write Idem Updated")
        self.assertEqual(second_row.get("write_date"), first_write_date)

    def test_api_data_write_contract_contains_idempotency_fields_without_audit(self):
        project = self.env["project.project"].create({"name": "Write Contract Fields"})
        handler = ApiDataWriteHandler(self.env, payload={})
        result = handler.handle(
            {
                "intent": "api.data.write",
                "params": {
                    "model": "project.project",
                    "id": project.id,
                    "values": {"name": "Write Contract Fields Updated"},
                    "request_id": "req-write-contract-1",
                },
            }
        )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-write-contract-1")
        self.assertEqual(data.get("idempotency_key"), "req-write-contract-1")
        self.assertTrue(bool(data.get("idempotency_fingerprint")))
        self.assertFalse(bool(data.get("idempotent_replay")))
        self.assertFalse(bool(data.get("replay_supported")))
        self.assertFalse(bool(data.get("replay_window_expired")))
        self.assertEqual(data.get("idempotency_replay_reason_code"), "")
        self.assertFalse(bool(data.get("idempotency_deduplicated")))

    def test_api_data_write_same_key_diff_payload_returns_conflict(self):
        self._ensure_audit_model()
        project = self.env["project.project"].create({"name": "Write Conflict Original"})
        handler = ApiDataWriteHandler(self.env, payload={})
        first = handler.handle(
            {
                "intent": "api.data.write",
                "params": {
                    "model": "project.project",
                    "id": project.id,
                    "values": {"name": "Write Conflict A"},
                    "request_id": "req-write-idem-conflict-1",
                },
            }
        )
        self.assertTrue(first.get("ok"))
        conflict = handler.handle(
            {
                "intent": "api.data.write",
                "params": {
                    "model": "project.project",
                    "id": project.id,
                    "values": {"name": "Write Conflict B"},
                    "request_id": "req-write-idem-conflict-1",
                },
            }
        )
        self.assertFalse(conflict.get("ok"))
        self.assertEqual(int(conflict.get("code") or 0), 409)
        err = conflict.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_IDEMPOTENCY_CONFLICT)
        data = conflict.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-write-idem-conflict-1")
        self.assertEqual(data.get("idempotency_key"), "req-write-idem-conflict-1")
        self.assertFalse(bool(data.get("replay_supported")))

    def test_api_data_unlink_same_key_same_payload_is_deduplicated(self):
        self._ensure_audit_model()
        project = self.env["project.project"].create({"name": "Unlink Idem Project"})
        task = self.env["project.task"].create({"name": "Unlink Idem Task", "project_id": project.id})
        handler = ApiDataUnlinkHandler(self.env, payload={})
        payload = {
            "params": {
                "model": "project.task",
                "ids": [task.id],
                "request_id": "req-unlink-idem-1",
            }
        }
        first = handler.handle(payload)
        self.assertTrue(first.get("ok"))
        first_data = first.get("data") or {}
        self.assertFalse(bool(first_data.get("idempotency_deduplicated")))
        self.assertEqual(first_data.get("idempotency_key"), "req-unlink-idem-1")

        second = handler.handle(payload)
        self.assertTrue(second.get("ok"))
        second_data = second.get("data") or {}
        self.assertTrue(bool(second_data.get("idempotency_deduplicated")))
        self.assertFalse(bool(second_data.get("replay_supported")))
        self.assertFalse(bool(self.env["project.task"].browse(task.id).exists()))

    def test_api_data_unlink_contract_contains_idempotency_fields_without_audit(self):
        project = self.env["project.project"].create({"name": "Unlink Contract Project"})
        task = self.env["project.task"].create({"name": "Unlink Contract Task", "project_id": project.id})
        handler = ApiDataUnlinkHandler(self.env, payload={})
        result = handler.handle(
            {
                "params": {
                    "model": "project.task",
                    "ids": [task.id],
                    "request_id": "req-unlink-contract-1",
                }
            }
        )
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-unlink-contract-1")
        self.assertEqual(data.get("idempotency_key"), "req-unlink-contract-1")
        self.assertTrue(bool(data.get("idempotency_fingerprint")))
        self.assertFalse(bool(data.get("idempotent_replay")))
        self.assertFalse(bool(data.get("replay_supported")))
        self.assertFalse(bool(data.get("replay_window_expired")))
        self.assertEqual(data.get("idempotency_replay_reason_code"), "")
        self.assertFalse(bool(data.get("idempotency_deduplicated")))

    def test_api_data_unlink_same_key_diff_payload_returns_conflict(self):
        self._ensure_audit_model()
        project = self.env["project.project"].create({"name": "Unlink Conflict Project"})
        task_1 = self.env["project.task"].create({"name": "Unlink Conflict Task 1", "project_id": project.id})
        task_2 = self.env["project.task"].create({"name": "Unlink Conflict Task 2", "project_id": project.id})
        handler = ApiDataUnlinkHandler(self.env, payload={})
        first = handler.handle(
            {
                "params": {
                    "model": "project.task",
                    "ids": [task_1.id],
                    "request_id": "req-unlink-idem-conflict-1",
                }
            }
        )
        self.assertTrue(first.get("ok"))
        conflict = handler.handle(
            {
                "params": {
                    "model": "project.task",
                    "ids": [task_2.id],
                    "request_id": "req-unlink-idem-conflict-1",
                }
            }
        )
        self.assertFalse(conflict.get("ok"))
        self.assertEqual(int(conflict.get("code") or 0), 409)
        err = conflict.get("error") or {}
        self.assertEqual(err.get("reason_code"), REASON_IDEMPOTENCY_CONFLICT)
        data = conflict.get("data") or {}
        self.assertEqual(data.get("request_id"), "req-unlink-idem-conflict-1")
        self.assertEqual(data.get("idempotency_key"), "req-unlink-idem-conflict-1")
        self.assertFalse(bool(data.get("replay_supported")))
