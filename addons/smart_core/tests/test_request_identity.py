# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_identity():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "request_identity.py"
    spec = importlib.util.spec_from_file_location("request_identity_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _User:
    id = 9


class _Env:
    uid = 5


class _Request:
    def __init__(self, uid=None, env=None):
        self.uid = uid
        self.env = env


class TestRequestIdentity(unittest.TestCase):
    def setUp(self):
        self.identity = _load_identity()

    def test_identity_id_accepts_records_and_raw_ids(self):
        self.assertEqual(self.identity.identity_id(_User()), 9)
        self.assertEqual(self.identity.identity_id("8"), 8)
        self.assertIsNone(self.identity.identity_id("bad"))

    def test_request_uid_prefers_request_uid_then_env_uid(self):
        self.assertEqual(self.identity.request_uid(_Request(uid=7, env=_Env())), 7)
        self.assertEqual(self.identity.request_uid(_Request(uid=None, env=_Env())), 5)

    def test_request_uid_uses_default_when_no_identity_exists(self):
        self.assertEqual(self.identity.request_uid(_Request(uid=None, env=None), default=3), 3)


if __name__ == "__main__":
    unittest.main()
