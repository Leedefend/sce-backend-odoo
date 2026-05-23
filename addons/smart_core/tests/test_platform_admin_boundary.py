# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    module_name = "platform_admin_boundary_under_test"
    spec = importlib.util.spec_from_file_location(module_name, root / "security" / "platform_admin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeUser:
    def __init__(self, groups):
        self._groups = set(groups)

    def has_group(self, xmlid):
        return xmlid in self._groups


class TestPlatformAdminBoundary(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_platform_admin_default_excludes_legacy_industry_config_group(self):
        user = _FakeUser({self.module.LEGACY_PLATFORM_ADMIN_GROUP})

        self.assertFalse(self.module.user_is_platform_admin(user))
        self.assertTrue(self.module.user_is_platform_admin(user, include_legacy=True))

    def test_platform_admin_default_excludes_system_admin_group(self):
        user = _FakeUser({self.module.SYSTEM_ADMIN_GROUP})

        self.assertFalse(self.module.user_is_platform_admin(user))
        self.assertTrue(self.module.user_is_platform_admin(user, include_system=True))

    def test_platform_admin_group_xmlids_are_strict_by_default(self):
        self.assertEqual(self.module.platform_admin_group_xmlids(), [self.module.PLATFORM_ADMIN_GROUP])


if __name__ == "__main__":
    unittest.main()
