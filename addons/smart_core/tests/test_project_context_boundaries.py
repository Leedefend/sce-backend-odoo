# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, request=None, params=None, context=None):
        self.env = env
        self.request = request
        self.params = params or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)

    captured = {}

    def _build_project_context_contract(env, params, *, search="", limit=20):
        captured["search"] = search
        captured["limit"] = limit
        return {"selector": {"limit": limit}, "options": []}

    _install_module(
        "odoo.addons.smart_core.core.project_context",
        build_project_context_contract=_build_project_context_contract,
        source_authority_contract=lambda: {"kind": "record_context_projection"},
    )

    for module_name, rel_path in (
        ("odoo.addons.smart_core.core.intent_execution_result", "core/intent_execution_result.py"),
        ("odoo.addons.smart_core.core.request_params", "core/request_params.py"),
    ):
        sys.modules.pop(module_name, None)
        spec = importlib.util.spec_from_file_location(module_name, root / rel_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    module_name = "odoo.addons.smart_core.handlers.project_context"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "project_context.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    module._captured = captured
    return module


def _load_project_context_core():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.exceptions", AccessError=type("AccessError", (Exception,), {}))
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    utils_mod.__path__ = [str(root / "utils")]
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda *args, **kwargs: None,
    )

    module_name = "odoo.addons.smart_core.core.project_context"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "project_context.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestProjectContextBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_search_rejects_invalid_limit(self):
        handler = self.module.ProjectContextSearchHandler(env=object())

        result = handler.handle(payload={"params": {"limit": "bad"}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "limit 无效")

    def test_search_rejects_zero_limit(self):
        handler = self.module.ProjectContextSearchHandler(env=object())

        result = handler.handle(payload={"params": {"limit": 0}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "limit 无效")

    def test_search_passes_parsed_limit(self):
        handler = self.module.ProjectContextSearchHandler(env=object())

        result = handler.handle(payload={"params": {"search": "abc", "limit": "7"}})

        self.assertTrue(result.ok)
        self.assertEqual(result.data["selector"]["limit"], 7)
        self.assertEqual(self.module._captured["search"], "abc")
        self.assertEqual(self.module._captured["limit"], 7)

    def test_record_context_domain_excludes_unsearchable_display_name(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, *, store=False, search=None):
                self.store = store
                self.search = search

        class Model:
            _fields = {
                "name": Field(store=True),
                "display_name": Field(store=False),
                "code": Field(store=True),
                "project_code": Field(store=True),
            }

        domain = core._record_context_domain(Model, "五洲")

        self.assertEqual(
            domain,
            [
                "|",
                "|",
                ("name", "ilike", "五洲"),
                ("code", "ilike", "五洲"),
                ("project_code", "ilike", "五洲"),
            ],
        )

    def test_business_scope_domain_applies_company_project_and_operation_strategy(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "payment.request"
            _fields = {
                "company_id": Field("res.company"),
                "project_id": Field("project.project"),
                "operation_strategy": Field(),
            }

        domain, meta = core.apply_business_scope_domain(
            Model,
            [("state", "=", "draft")],
            {
                "company_id": 3,
                "current_project_id": 9,
                "operation_strategy": "joint",
            },
            {},
        )

        self.assertEqual(
            domain,
            [
                ("company_id", "=", 3),
                ("project_id", "=", 9),
                "|",
                "&",
                ("project_id", "!=", False),
                ("project_id.operation_strategy", "=", "joint"),
                "&",
                ("project_id", "=", False),
                ("operation_strategy", "=", "joint"),
                ("state", "=", "draft"),
            ],
        )
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["company_id"], 3)
        self.assertEqual(meta["project_id"], 9)
        self.assertEqual(meta["operation_strategy"], "joint")

    def test_business_scope_operation_strategy_prefers_project_field(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "sc.general.contract"
            _fields = {
                "project_id": Field("project.project"),
                "operation_strategy": Field(),
            }

        self.assertEqual(
            core.business_scope_domain(Model, {"operation_strategy": "joint"}),
            [
                "|",
                "&",
                ("project_id", "!=", False),
                ("project_id.operation_strategy", "=", "joint"),
                "&",
                ("project_id", "=", False),
                ("operation_strategy", "=", "joint"),
            ],
        )

    def test_business_scope_domain_uses_project_fields_when_direct_fields_missing(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "project.boq.line"
            _fields = {
                "project_id": Field("project.project"),
            }

        domain, meta = core.apply_business_scope_domain(
            Model,
            [],
            {"company_id": 5, "operation_strategy": "direct"},
            {},
        )

        self.assertEqual(
            domain,
            [
                ("project_id.company_id", "=", 5),
                ("project_id.operation_strategy", "=", "direct"),
            ],
        )
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["company_id"], 5)
        self.assertEqual(meta["operation_strategy"], "direct")

    def test_partner_master_data_is_not_filtered_by_business_scope(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "res.partner"
            _fields = {
                "project_ids": Field("project.project"),
                "company_id": Field("res.company"),
            }

        domain, meta = core.apply_business_scope_domain(
            Model,
            [("customer_rank", ">", 0)],
            {
                "company_id": 3,
                "current_project_id": 9,
                "operation_strategy": "direct",
            },
            {},
        )

        self.assertEqual(domain, [("customer_rank", ">", 0)])
        self.assertFalse(meta["applied"])
        self.assertEqual(meta["model"], "res.partner")


if __name__ == "__main__":
    unittest.main()
