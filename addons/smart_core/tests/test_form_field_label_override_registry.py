# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_form_field_configuration():
    _install_module("odoo")
    _install_module("odoo.exceptions", ValidationError=type("ValidationError", (Exception,), {}))
    _install_module("odoo.addons")
    smart_core_pkg = _install_module("odoo.addons.smart_core")
    smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
    _install_module("odoo.addons.smart_core.handlers").__path__ = [str(SMART_CORE_DIR / "handlers")]
    _install_module("odoo.addons.smart_core.core").__path__ = [str(SMART_CORE_DIR / "core")]
    _install_module("odoo.addons.smart_core.utils").__path__ = [str(SMART_CORE_DIR / "utils")]
    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=object)
    request_params_spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.request_params",
        SMART_CORE_DIR / "core" / "request_params.py",
    )
    request_params = importlib.util.module_from_spec(request_params_spec)
    assert request_params_spec and request_params_spec.loader
    sys.modules["odoo.addons.smart_core.core.request_params"] = request_params
    request_params_spec.loader.exec_module(request_params)
    backend_spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.utils.backend_contract_boundaries",
        SMART_CORE_DIR / "utils" / "backend_contract_boundaries.py",
    )
    backend = importlib.util.module_from_spec(backend_spec)
    assert backend_spec and backend_spec.loader
    sys.modules["odoo.addons.smart_core.utils.backend_contract_boundaries"] = backend
    backend_spec.loader.exec_module(backend)
    reason_spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.utils.reason_codes",
        SMART_CORE_DIR / "utils" / "reason_codes.py",
    )
    reason = importlib.util.module_from_spec(reason_spec)
    assert reason_spec and reason_spec.loader
    sys.modules["odoo.addons.smart_core.utils.reason_codes"] = reason
    reason_spec.loader.exec_module(reason)
    module_name = "odoo.addons.smart_core.handlers.form_field_configuration"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SMART_CORE_DIR / "handlers" / "form_field_configuration.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FormFieldLabelOverrideRegistryTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_form_field_configuration()

    def test_core_has_no_default_business_field_label_overrides(self):
        self.assertEqual(self.module._FORM_FIELD_LABEL_OVERRIDES, {})

    def test_business_field_label_override_must_be_registered_explicitly(self):
        self.module.register_form_field_label_override("project.project", "manager_id", "项目经理")

        self.assertEqual(self.module._form_field_label_override("project.project", "manager_id"), "项目经理")


if __name__ == "__main__":
    unittest.main()
