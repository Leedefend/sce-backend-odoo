# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _AccessDenied(Exception):
    pass


class _FakeCursor:
    def __init__(self, dbname):
        self.dbname = dbname


class _FakeEnv:
    def __init__(self, dbname="db_a"):
        self.cr = _FakeCursor(dbname)


class _FakeRequest:
    def __init__(self, dbname="db_a", *, header_db=None, query_db=None, session_db=None):
        self.env = _FakeEnv(dbname)
        self.session = types.SimpleNamespace(db=session_db)
        self.httprequest = types.SimpleNamespace(
            headers={
                key: value
                for key, value in {
                    "X-Odoo-DB": header_db,
                }.items()
                if value is not None
            },
            args={
                key: value
                for key, value in {
                    "db": query_db,
                }.items()
                if value is not None
            },
        )


def _load_auth(fake_request):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "security" / "auth.py"

    jwt_mod = types.ModuleType("jwt")
    jwt_mod.ExpiredSignatureError = type("ExpiredSignatureError", (Exception,), {})
    jwt_mod.MissingRequiredClaimError = type("MissingRequiredClaimError", (Exception,), {})
    jwt_mod.InvalidTokenError = type("InvalidTokenError", (Exception,), {})
    jwt_mod.decode = lambda *args, **kwargs: {}
    jwt_mod.encode = lambda *args, **kwargs: "token"

    http_mod = types.ModuleType("odoo.http")
    http_mod.request = fake_request
    odoo_mod = types.ModuleType("odoo")
    odoo_mod.http = http_mod
    odoo_mod.SUPERUSER_ID = 1
    odoo_mod.api = types.SimpleNamespace(Environment=lambda *args, **kwargs: None)
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessDenied = _AccessDenied
    registry_mod = types.ModuleType("odoo.modules.registry")
    registry_mod.Registry = lambda db: None
    tools_mod = types.ModuleType("odoo.tools")
    tools_mod.config = {}

    sys.modules.update(
        {
            "jwt": jwt_mod,
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.exceptions": exc_mod,
            "odoo.modules.registry": registry_mod,
            "odoo.tools": tools_mod,
        }
    )

    name = "auth_token_boundary_test_module"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestAuthTokenBoundaries(unittest.TestCase):
    def setUp(self):
        self.auth = _load_auth(_FakeRequest("db_a"))

    def test_extract_bearer_token_requires_bearer_scheme(self):
        self.assertEqual(self.auth._extract_bearer_token("Bearer abc.def"), "abc.def")
        with self.assertRaises(_AccessDenied):
            self.auth._extract_bearer_token("Basic abc.def")
        with self.assertRaises(_AccessDenied):
            self.auth._extract_bearer_token("Bearer")

    def test_token_user_id_must_be_positive_integer(self):
        self.assertEqual(self.auth._token_user_id({"user_id": "7"}), 7)
        with self.assertRaises(_AccessDenied):
            self.auth._token_user_id({"user_id": "bad"})
        with self.assertRaises(_AccessDenied):
            self.auth._token_user_id({"user_id": 0})

    def test_session_user_id_must_be_positive_integer(self):
        self.assertEqual(self.auth._session_user_id("9"), 9)
        with self.assertRaises(_AccessDenied):
            self.auth._session_user_id("bad")
        with self.assertRaises(_AccessDenied):
            self.auth._session_user_id(0)

    def test_token_db_must_match_request_db_when_both_are_known(self):
        self.auth._ensure_token_db_matches_request("db_a")
        with self.assertRaises(_AccessDenied):
            self.auth._ensure_token_db_matches_request("db_b")

    def test_request_db_prefers_explicit_target_db(self):
        auth = _load_auth(_FakeRequest("default_db", header_db="target_from_header"))
        self.assertEqual(auth._request_db_name(), "target_from_header")

        auth = _load_auth(_FakeRequest("default_db", query_db="target_from_query"))
        self.assertEqual(auth._request_db_name(), "target_from_query")

        auth = _load_auth(_FakeRequest("default_db", session_db="target_from_session"))
        self.assertEqual(auth._request_db_name(), "target_from_session")


if __name__ == "__main__":
    unittest.main()
