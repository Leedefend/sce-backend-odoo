# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_migration():
    root = Path(__file__).resolve().parents[1]
    odoo_mod = _install_module("odoo", SUPERUSER_ID=1, api=types.SimpleNamespace())
    del odoo_mod
    spec = importlib.util.spec_from_file_location(
        "smart_construction_core_migration_17_0_0_56",
        root / "migrations" / "17.0.0.56" / "post-migration.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeEnv:
    def __init__(self, context=None, user=None):
        self.context = context or {}
        self.user = user

    def __call__(self, user=None, context=None):
        return _FakeEnv(context=context or {}, user=user)


class BusinessConfigMigration170056Tests(unittest.TestCase):
    def setUp(self):
        self.migration = _load_migration()

    def test_system_env_marks_business_config_remediation_context(self):
        env = _FakeEnv(context={"lang": "zh_CN"})
        user = types.SimpleNamespace(login="sc_fx_config_admin")

        system_env = self.migration._system_env(env, user=user)

        self.assertEqual(system_env.user, user)
        self.assertTrue(system_env.context["business_config_system_remediation"])
        self.assertEqual(system_env.context["lang"], "zh_CN")

    def test_remediate_loops_until_runtime_gap_is_clear(self):
        calls = []

        class ScanHandler:
            def __init__(self, env=None, payload=None):
                self.payload = payload or {}

            def handle(self):
                calls.append(("scan", self.payload["params"]))
                remaining = 1 if len([item for item in calls if item[0] == "bootstrap"]) == 0 else 0
                return {"ok": True, "data": {"summary": {"runtime_missing_count": remaining}}}

        class BootstrapHandler:
            def __init__(self, env=None, payload=None):
                self.payload = payload or {}

            def handle(self):
                calls.append(("bootstrap", self.payload["params"]))
                return {"ok": True, "data": {"candidate_count": 1, "failed_count": 0, "results": []}}

        self.migration._remediate(
            _FakeEnv(),
            params={"limit": 1000},
            scan_handler=ScanHandler,
            bootstrap_handler=BootstrapHandler,
        )

        self.assertEqual([item[0] for item in calls], ["scan", "bootstrap", "scan"])

    def test_remediate_raises_when_bootstrap_fails(self):
        class ScanHandler:
            def __init__(self, env=None, payload=None):
                pass

            def handle(self):
                return {"ok": True, "data": {"summary": {"runtime_missing_count": 1}}}

        class BootstrapHandler:
            def __init__(self, env=None, payload=None):
                pass

            def handle(self):
                return {
                    "ok": False,
                    "data": {
                        "candidate_count": 1,
                        "failed_count": 1,
                        "results": [{"ok": False, "action_id": 11, "name": "客户"}],
                    },
                }

        with self.assertRaisesRegex(RuntimeError, "11:客户"):
            self.migration._remediate(
                _FakeEnv(),
                params={"limit": 1000},
                scan_handler=ScanHandler,
                bootstrap_handler=BootstrapHandler,
            )

    def test_remediate_ignores_system_config_wizard_bootstrap_failure(self):
        calls = []

        class ScanHandler:
            def __init__(self, env=None, payload=None):
                pass

            def handle(self):
                calls.append("scan")
                return {"ok": True, "data": {"summary": {"runtime_missing_count": 1}}}

        class BootstrapHandler:
            def __init__(self, env=None, payload=None):
                pass

            def handle(self):
                calls.append("bootstrap")
                return {
                    "ok": False,
                    "data": {
                        "candidate_count": 1,
                        "failed_count": 1,
                        "results": [
                            {
                                "ok": False,
                                "action_id": 734,
                                "name": "四川定额导入",
                                "model": "quota.import.wizard",
                            }
                        ],
                    },
                }

        self.migration._remediate(
            _FakeEnv(),
            params={"limit": 1000},
            scan_handler=ScanHandler,
            bootstrap_handler=BootstrapHandler,
        )

        self.assertEqual(calls, ["scan", "bootstrap"])

    def test_representative_logins_include_acceptance_and_role_accounts(self):
        self.assertIn("sc_fx_config_admin", self.migration.REPRESENTATIVE_LOGINS)
        self.assertTrue(
            all(
                login == "admin" or login.startswith(("demo_", "sc_fx_"))
                for login in self.migration.REPRESENTATIVE_LOGINS
            )
        )
        self.assertIn("demo_business_full", self.migration.REPRESENTATIVE_LOGINS)
        self.assertIn("sc_fx_finance", self.migration.REPRESENTATIVE_LOGINS)
        self.assertIn("sc_fx_pm", self.migration.REPRESENTATIVE_LOGINS)


if __name__ == "__main__":
    unittest.main()
