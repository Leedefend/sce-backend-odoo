# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.my_work_complete import (
    MyWorkCompleteHandler,
    _failure_meta_for_exception,
    _retryable_summary,
)
from odoo.addons.smart_construction_core.handlers.my_work_summary import MyWorkSummaryHandler


@tagged("sc_smoke", "my_work_backend")
class TestMyWorkBackend(TransactionCase):
    def test_summary_filters_apply_server_side(self):
        handler = MyWorkSummaryHandler(self.env, payload={})
        rows = [
            {"section": "todo", "source": "mail.activity", "reason_code": "A", "title": "Build contract", "model": "x", "action_label": ""},
            {"section": "owned", "source": "project.project", "reason_code": "B", "title": "Review budget", "model": "y", "action_label": ""},
            {"section": "todo", "source": "mail.activity", "reason_code": "B", "title": "Approve payment", "model": "z", "action_label": ""},
        ]
        filtered = handler._apply_filters(
            rows,
            section="todo",
            source="mail.activity",
            reason_code="B",
            search="approve",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "Approve payment")

    def test_failure_meta_classification(self):
        self.assertEqual(_failure_meta_for_exception(AccessError("no")).get("reason_code"), "PERMISSION_DENIED")
        self.assertFalse(_failure_meta_for_exception(UserError("待办不存在")).get("retryable"))
        self.assertEqual(_failure_meta_for_exception(Exception("x")).get("reason_code"), "INTERNAL_ERROR")
        self.assertTrue(_failure_meta_for_exception(Exception("x")).get("retryable"))

    def test_summary_facets_ranked(self):
        handler = MyWorkSummaryHandler(self.env, payload={})
        facets = handler._build_facets(
            [
                {"section": "todo", "source": "mail.activity", "reason_code": "A"},
                {"section": "todo", "source": "mail.activity", "reason_code": "B"},
                {"section": "owned", "source": "project.project", "reason_code": "B"},
            ]
        )
        self.assertEqual(facets["source_counts"][0]["key"], "mail.activity")
        self.assertEqual(facets["source_counts"][0]["count"], 2)
        self.assertEqual(facets["reason_code_counts"][0]["key"], "B")
        self.assertEqual(facets["reason_code_counts"][0]["count"], 2)
        self.assertEqual(facets["section_counts"][0]["key"], "todo")
        self.assertEqual(facets["section_counts"][0]["count"], 2)

    def test_complete_returns_structured_failure_payload(self):
        handler = MyWorkCompleteHandler(self.env, payload={})
        result = handler.handle({"id": "bad", "source": "mail.activity"})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("reason_code"), "INVALID_ID")
        self.assertEqual(data.get("error_category"), "validation")
        self.assertFalse(bool(data.get("retryable")))

    def test_retryable_summary_counts(self):
        summary = _retryable_summary(
            [
                {"retryable": True},
                {"retryable": False},
                {"retryable": True},
            ]
        )
        self.assertEqual(summary.get("retryable"), 2)
        self.assertEqual(summary.get("non_retryable"), 1)
