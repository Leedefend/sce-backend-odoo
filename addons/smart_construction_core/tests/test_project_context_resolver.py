# -*- coding: utf-8 -*-
import importlib.util
import pathlib
import unittest

try:
    from odoo.tests.common import TransactionCase, tagged
    from odoo.addons.smart_construction_core.handlers.project_context_resolver import (
        coerce_positive_id,
        resolve_company_id,
        resolve_operation_strategy,
        resolve_project_id,
    )
    BaseCase = TransactionCase
except ModuleNotFoundError:
    module_path = pathlib.Path(__file__).resolve().parents[1] / "handlers" / "project_context_resolver.py"
    spec = importlib.util.spec_from_file_location("project_context_resolver", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    coerce_positive_id = module.coerce_positive_id
    resolve_company_id = module.resolve_company_id
    resolve_operation_strategy = module.resolve_operation_strategy
    resolve_project_id = module.resolve_project_id
    BaseCase = unittest.TestCase

    def tagged(*_args, **_kwargs):
        def decorator(cls):
            return cls

        return decorator


@tagged("sc_gate", "project_context_resolver")
class TestProjectContextResolver(BaseCase):
    def test_coerce_positive_id_rejects_invalid_values(self):
        self.assertEqual(coerce_positive_id("18"), 18)
        self.assertEqual(coerce_positive_id(0), 0)
        self.assertEqual(coerce_positive_id(-2), 0)
        self.assertEqual(coerce_positive_id("abc"), 0)

    def test_resolve_project_id_uses_stable_priority(self):
        project_id = resolve_project_id(
            {"project_id": "", "record_id": 22, "project_context": {"project_id": 33}},
            {"project_id": 44, "record_id": 55},
        )

        self.assertEqual(project_id, 22)

    def test_resolve_project_id_can_disable_param_record_id(self):
        project_id = resolve_project_id(
            {"record_id": 22, "project_context": {"project_id": 33}},
            {"project_id": 44, "record_id": 55},
            include_param_record_id=False,
        )

        self.assertEqual(project_id, 33)

    def test_resolve_project_id_can_gate_context_record_by_model(self):
        self.assertEqual(
            resolve_project_id(
                {},
                {"model": "res.partner", "record_id": 55},
                include_project_context=False,
                include_ctx_record_id=True,
                ctx_record_model_only="project.project",
            ),
            0,
        )
        self.assertEqual(
            resolve_project_id(
                {},
                {"model": "project.project", "record_id": 55},
                include_project_context=False,
                include_ctx_record_id=True,
                ctx_record_model_only="project.project",
            ),
            55,
        )

    def test_resolve_company_and_strategy(self):
        self.assertEqual(resolve_company_id({"current_company_id": "7"}, {}), 7)
        self.assertEqual(resolve_company_id({"company_id": "bad"}, {"company_id": 9}), 9)
        self.assertEqual(resolve_operation_strategy({"operationStrategy": "joint"}, {}), "joint")
        self.assertEqual(resolve_operation_strategy({"operation_strategy": "other"}, {"operation_strategy": "direct"}), "direct")


if __name__ == "__main__":
    unittest.main()
