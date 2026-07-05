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


def _load_project_context_core(record_context_hook=None):
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
        call_extension_hook_first=record_context_hook or (lambda *args, **kwargs: None),
    )

    module_name = "odoo.addons.smart_core.core.project_context"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "project_context.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _register_construction_project_scope(core):
    core.register_legacy_project_scope_model("project.project")
    core.register_operation_strategy("direct")
    core.register_operation_strategy("joint")


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
        _register_construction_project_scope(core)

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
                "|",
                ("company_id", "=", 3),
                ("project_id.company_id", "=", 3),
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
        _register_construction_project_scope(core)

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
        _register_construction_project_scope(core)

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
        _register_construction_project_scope(core)
        core.register_business_scope_exempt_model("res.partner")

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

    def test_project_scope_model_is_not_active_until_registered(self):
        core = _load_project_context_core()

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "payment.request"
            _fields = {
                "project_id": Field("project.project"),
            }

        self.assertEqual(core._registered_legacy_project_scope_models(), ())
        self.assertEqual(core.project_scope_domain(Model, 9), [])

        core.register_legacy_project_scope_model("project.project")

        self.assertEqual(core._registered_legacy_project_scope_models(), ("project.project",))
        self.assertEqual(core.project_scope_domain(Model, 9), [("project_id", "=", 9)])

    def test_operation_strategy_is_not_active_until_registered(self):
        core = _load_project_context_core()
        core.register_legacy_project_scope_model("project.project")

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "payment.request"
            _fields = {
                "project_id": Field("project.project"),
                "operation_strategy": Field(),
            }

        self.assertEqual(core.business_scope_domain(Model, {"operation_strategy": "joint"}), [])

        core.register_operation_strategy("joint")

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

    def test_business_scope_exempt_model_is_not_active_until_registered(self):
        core = _load_project_context_core()
        _register_construction_project_scope(core)

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "res.partner"
            _fields = {
                "project_ids": Field("project.project"),
                "company_id": Field("res.company"),
            }

        self.assertTrue(core.business_scope_domain(Model, {"company_id": 3, "operation_strategy": "direct"}))

        core.register_business_scope_exempt_model("res.partner")

        self.assertEqual(core.business_scope_domain(Model, {"company_id": 3, "operation_strategy": "direct"}), [])

    def test_legacy_direct_acceptance_scope_model_is_not_active_until_registered(self):
        core = _load_project_context_core()
        _register_construction_project_scope(core)

        class Field:
            def __init__(self, comodel_name=""):
                self.comodel_name = comodel_name

        class Model:
            _name = "sc.legacy.direct.acceptance.fact"
            _fields = {
                "project_id": Field("project.project"),
            }

        self.assertEqual(
            core.business_scope_domain(Model, {"company_id": 3, "operation_strategy": "direct"}),
            [
                ("project_id.company_id", "=", 3),
                ("project_id.operation_strategy", "=", "direct"),
            ],
        )

        core.register_legacy_direct_acceptance_scope_model("sc.legacy.direct.acceptance.fact", direct_strategy="direct")

        self.assertEqual(
            core.business_scope_domain(Model, {"company_id": 3, "operation_strategy": "direct"}),
            ["|", ("project_id", "=", False), ("project_id.operation_strategy", "=", "direct")],
        )

    def test_record_context_core_default_config_is_empty_legacy_project_is_fallback(self):
        core = _load_project_context_core()

        source = core.source_authority_contract()

        self.assertEqual(core.DEFAULT_RECORD_CONTEXT_CONFIG, {})
        self.assertEqual(source.get("default_record_context_model"), "")
        self.assertEqual(source.get("legacy_default_model"), "project.project")
        self.assertEqual(source.get("registered_legacy_scope_models"), [])
        self.assertEqual(source.get("registered_operation_strategies"), [])
        self.assertEqual(source.get("business_scope_exempt_models"), [])

    def test_record_context_config_can_be_supplied_by_extension_hook(self):
        def hook(env, name, *args):
            if name == "smart_core_resolve_record_context_config":
                return {
                    "model": "project.project",
                    "label": "当前项目",
                    "placeholder": "搜索项目名称",
                    "selected_id_param": "selected_id",
                }
            return None

        core = _load_project_context_core(record_context_hook=hook)

        config = core._resolve_record_context_config(object(), {})

        self.assertEqual(config["model"], "project.project")
        self.assertEqual(config["source"], "extension_hook")
        self.assertEqual(config["label"], "当前项目")
        self.assertEqual(config["placeholder"], "搜索项目名称")


if __name__ == "__main__":
    unittest.main()
