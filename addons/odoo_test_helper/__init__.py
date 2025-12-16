# -*- coding: utf-8 -*-
"""
Minimal stub to satisfy external test imports (e.g., base_tier_validation).
Placed directly under addons path so Python can resolve `import odoo_test_helper`
before any Odoo module is loaded.
"""

class FakeModelLoader:
    def __init__(self, env=None, module=None):
        self.env = env
        self.module = module

    def backup_registry(self):
        return None

    def update_registry(self, models=None):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
