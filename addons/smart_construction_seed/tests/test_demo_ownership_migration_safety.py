# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATABASE_NAMES = (
    "sc_demo",
    "sc_user_data_rehearsal",
    "sc_pilot_history_rehearsal",
    "random_7c341f_history",
)


def _load_migration(version):
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(Environment=None)
    sys.modules["odoo"] = odoo
    path = ROOT / "migrations" / version / "post-migration.py"
    spec = importlib.util.spec_from_file_location(f"seed_migration_{version.replace('.', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


class _ForbiddenMutationMixin:
    def write(self, values):
        raise AssertionError(f"business mutation forbidden: {values}")

    def unlink(self):
        raise AssertionError("record or XML-ID deletion forbidden")


class _Record(_ForbiddenMutationMixin):
    def __init__(self, exists=True):
        self._exists = exists

    def exists(self):
        return self if self._exists else False

    def __bool__(self):
        return self._exists


class _BusinessModel:
    def __init__(self, existing_ids):
        self.existing_ids = set(existing_ids)

    def sudo(self):
        return self

    def with_context(self, **kwargs):
        return self

    def browse(self, record_id):
        return _Record(record_id in self.existing_ids)


class _XmlIdRow(_ForbiddenMutationMixin):
    def __init__(self, model, res_id):
        self.model = model
        self.res_id = res_id


class _XmlIdModel(_ForbiddenMutationMixin):
    def __init__(self, rows):
        self.rows = rows

    def sudo(self):
        return self

    def search(self, domain):
        if domain != [("module", "=", "smart_construction_demo")]:
            raise AssertionError(f"unexpected domain: {domain}")
        return list(self.rows)


class _ConfigParameters:
    def __init__(self):
        self.values = {}

    def sudo(self):
        return self

    def set_param(self, key, value):
        self.values[key] = value


class _Cursor:
    def __init__(self, dbname):
        self.dbname = dbname


class _Environment:
    def __init__(self, dbname):
        self.cr = _Cursor(dbname)
        self.relationships = {
            "create_uid_write_uid": [(41, 7), (42, 7)],
            "project_managers": [(91, 7)],
            "followers": [(501, 7001)],
            "approvers": [(601, 7)],
            "business_users": [(701, 7)],
            "company_users": [(1, 7)],
        }
        self.icp = _ConfigParameters()
        self.models = {
            "ir.model.data": _XmlIdModel(
                [
                    _XmlIdRow("res.users", 7),
                    _XmlIdRow("project.project", 91),
                    _XmlIdRow("res.partner", 7001),
                    _XmlIdRow("missing.model", 2),
                ]
            ),
            "ir.config_parameter": self.icp,
            "res.users": _BusinessModel({7}),
            "project.project": _BusinessModel({91}),
            "res.partner": _BusinessModel({7001}),
        }

    def __contains__(self, model):
        return model in self.models

    def __getitem__(self, model):
        return self.models[model]


class DemoOwnershipMigrationSafetyTests(unittest.TestCase):
    def _run(self, version, dbname):
        migration, _path = _load_migration(version)
        env = _Environment(dbname)
        before = deepcopy(env.relationships)
        migration.api.Environment = lambda cr, uid, context: env
        migration.migrate(env.cr, "17.0.0.1.0")
        self.assertEqual(env.relationships, before)
        return dict(env.icp.values)

    def test_mig_s01_database_rename_does_not_change_semantics(self):
        for version in ("17.0.0.2.0", "17.0.0.2.1"):
            results = [self._run(version, name) for name in DATABASE_NAMES]
            self.assertTrue(all(result == results[0] for result in results[1:]))
            self.assertEqual(next(value for key, value in results[0].items() if key.endswith(".xmlid_count")), "4")

    def test_mig_s02_demo_history_relationships_are_unchanged(self):
        result = self._run("17.0.0.2.1", "sc_user_data_rehearsal")
        self.assertEqual(next(value for key, value in result.items() if key.endswith(".existing_record_count")), "3")
        self.assertEqual(next(value for key, value in result.items() if key.endswith(".missing_record_count")), "1")

    def test_mig_s03_repeated_execution_is_idempotent(self):
        migration, _path = _load_migration("17.0.0.2.1")
        env = _Environment("arbitrary_name")
        migration.api.Environment = lambda cr, uid, context: env
        migration.migrate(env.cr, "17.0.0.2.0")
        first = dict(env.icp.values)
        migration.migrate(env.cr, "17.0.0.2.0")
        self.assertEqual(env.icp.values, first)

    def test_mig_s04_and_missing_error_regression_have_no_delete_path(self):
        for version in ("17.0.0.2.0", "17.0.0.2.1"):
            _migration, path = _load_migration(version)
            source = path.read_text(encoding="utf-8")
            for forbidden in ("_is_demo_db", ".dbname", ".unlink(", ".write(", "_safe_archive"):
                self.assertNotIn(forbidden, source)
            self._run(version, "renamed_after_restore")


if __name__ == "__main__":
    unittest.main()
