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

    def test_summary_status_contract(self):
        handler = MyWorkSummaryHandler(self.env, payload={})
        empty_status = handler._build_status(total_before_filter=0, filtered_count=0)
        self.assertEqual(empty_status.get("state"), "EMPTY")
        self.assertEqual(empty_status.get("reason_code"), "NO_WORK_ITEMS")

        filter_empty_status = handler._build_status(total_before_filter=3, filtered_count=0)
        self.assertEqual(filter_empty_status.get("state"), "FILTER_EMPTY")
        self.assertEqual(filter_empty_status.get("reason_code"), "FILTER_NO_MATCH")

        ready_status = handler._build_status(total_before_filter=3, filtered_count=2)
        self.assertEqual(ready_status.get("state"), "READY")
        self.assertEqual(ready_status.get("reason_code"), "OK")

    def test_summary_sort_and_pagination_helpers(self):
        handler = MyWorkSummaryHandler(self.env, payload={})
        rows = [
            {"id": 3, "title": "Gamma", "deadline": "2026-02-03"},
            {"id": 1, "title": "Alpha", "deadline": ""},
            {"id": 2, "title": "Beta", "deadline": "2026-02-01"},
            {"id": 4, "title": "Delta", "deadline": "2026-02-04"},
            {"id": 5, "title": "Epsilon", "deadline": ""},
        ]
        sorted_rows = handler._apply_sort(rows, sort_by="title", sort_dir="asc")
        self.assertEqual([item["id"] for item in sorted_rows], [1, 2, 4, 5, 3])

        page_rows, total_pages, safe_page = handler._paginate_items(sorted_rows, page=2, page_size=2)
        self.assertEqual(total_pages, 3)
        self.assertEqual(safe_page, 2)
        self.assertEqual([item["id"] for item in page_rows], [4, 5])

        self.assertEqual(handler._normalize_sort_by("unknown"), "id")
        self.assertEqual(handler._normalize_sort_dir("up"), "desc")

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
