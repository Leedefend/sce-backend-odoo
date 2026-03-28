# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "runtime_fetch_handler_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("runtime_fetch_handler_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_runtime_fetch_error_response = TARGET.build_runtime_fetch_error_response
build_runtime_fetch_meta = TARGET.build_runtime_fetch_meta
build_runtime_fetch_success_response = TARGET.build_runtime_fetch_success_response
parse_runtime_fetch_params = TARGET.parse_runtime_fetch_params
resolve_runtime_fetch_collection_keys = TARGET.resolve_runtime_fetch_collection_keys
resolve_runtime_fetch_page_key = TARGET.resolve_runtime_fetch_page_key


class TestRuntimeFetchHandlerHelper(unittest.TestCase):
    def test_parse_runtime_fetch_params_prefers_nested_params(self):
        params = parse_runtime_fetch_params(
            {"params": {"page_key": "my_work", "keys": ["overview"]}},
            {"page_key": "ignored"},
        )

        self.assertEqual(params, {"page_key": "my_work", "keys": ["overview"]})

    def test_parse_runtime_fetch_params_falls_back_to_direct_payload(self):
        params = parse_runtime_fetch_params({"page_key": "my_work"}, None)

        self.assertEqual(params, {"page_key": "my_work"})

    def test_build_runtime_fetch_meta_keeps_intent_and_trace(self):
        meta = build_runtime_fetch_meta("page.contract", {"trace_id": "trace-123"})

        self.assertEqual(meta, {"intent": "page.contract", "trace_id": "trace-123"})

    def test_build_runtime_fetch_error_response_keeps_standard_shape(self):
        payload = build_runtime_fetch_error_response(
            intent="page.contract",
            context={"trace_id": "trace-123"},
            code="NOT_FOUND",
            message="missing",
            suggested_action="open_workspace_overview",
        )

        self.assertFalse(payload.get("ok"))
        self.assertEqual((payload.get("error") or {}).get("code"), "NOT_FOUND")
        self.assertEqual((payload.get("meta") or {}).get("trace_id"), "trace-123")

    def test_build_runtime_fetch_success_response_keeps_standard_shape(self):
        payload = build_runtime_fetch_success_response(
            intent="workspace.collections",
            context={"trace_id": "trace-456"},
            data={"count": 2},
        )

        self.assertTrue(payload.get("ok"))
        self.assertEqual((payload.get("data") or {}).get("count"), 2)
        self.assertEqual((payload.get("meta") or {}).get("intent"), "workspace.collections")

    def test_resolve_runtime_fetch_page_key_uses_page_key_or_key(self):
        self.assertEqual(resolve_runtime_fetch_page_key({"page_key": " My_Work "}), "my_work")
        self.assertEqual(resolve_runtime_fetch_page_key({"key": "Overview"}), "overview")

    def test_resolve_runtime_fetch_collection_keys_requires_list(self):
        self.assertEqual(resolve_runtime_fetch_collection_keys({"keys": ["overview", "alerts"]}), ["overview", "alerts"])
        self.assertEqual(resolve_runtime_fetch_collection_keys({"keys": "overview"}), [])


if __name__ == "__main__":
    unittest.main()
