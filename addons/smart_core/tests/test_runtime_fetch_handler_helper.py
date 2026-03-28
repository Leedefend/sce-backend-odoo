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
build_runtime_fetch_meta = TARGET.build_runtime_fetch_meta
parse_runtime_fetch_params = TARGET.parse_runtime_fetch_params


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


if __name__ == "__main__":
    unittest.main()
