# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
import importlib.util
from types import SimpleNamespace
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "backend_contract_boundaries.py"
spec = importlib.util.spec_from_file_location("backend_contract_boundaries", MODULE_PATH)
boundaries = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(boundaries)

classify_view_orchestration_contract = boundaries.classify_view_orchestration_contract
ensure_view_orchestration_source = boundaries.ensure_view_orchestration_source
ensure_lowcode_contract_source_status = boundaries.ensure_lowcode_contract_source_status
is_business_config_runtime_model = boundaries.is_business_config_runtime_model
LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE = boundaries.LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE
LOWCODE_SOURCE_STATUS_TENANT_RUNTIME = boundaries.LOWCODE_SOURCE_STATUS_TENANT_RUNTIME
MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING = boundaries.MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING
APPROVAL_POLICY_RUNTIME_SOURCE = boundaries.APPROVAL_POLICY_RUNTIME_SOURCE
APPROVAL_POLICY_SOURCE_TENANT_LOWCODING = boundaries.APPROVAL_POLICY_SOURCE_TENANT_LOWCODING
view_orchestration_apply_order_key = boundaries.view_orchestration_apply_order_key


class _Ref:
    def __init__(self, record_id=0):
        self.id = record_id


def _contract(record_id, name, source="", *, action_id=0, priority=100, version_no=1):
    payload = {"view_orchestration": {"context": {"source": source}}} if source else {"view_orchestration": {}}
    return SimpleNamespace(
        id=record_id,
        name=name,
        contract_json=payload,
        action_id=_Ref(action_id),
        view_id=_Ref(0),
        role_key="",
        priority=priority,
        version_no=version_no,
    )


class BackendContractBoundaryTests(unittest.TestCase):
    def test_business_config_runtime_model_scope_is_shared(self):
        self.assertTrue(is_business_config_runtime_model("sc.approval.policy"))
        self.assertTrue(is_business_config_runtime_model("ui.business.config.contract"))
        self.assertFalse(is_business_config_runtime_model("project.project"))

    def test_view_orchestration_source_is_attached_without_overwriting_views(self):
        payload = {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}}
        result = ensure_view_orchestration_source(payload, "smart_core.lowcode.business_config")

        self.assertEqual(result["view_orchestration"]["context"]["source"], "smart_core.lowcode.business_config")
        self.assertEqual(result["view_orchestration"]["context"]["source_status"], LOWCODE_SOURCE_STATUS_TENANT_RUNTIME)
        self.assertEqual(result["view_orchestration"]["views"]["form"]["fields"][0]["name"], "name")

    def test_view_orchestration_product_release_source_status_is_default_for_product_payload(self):
        boundary = classify_view_orchestration_contract(
            "project_project_form_structure_v1",
            {"view_orchestration": {"context": {"source": "smart_construction_core.product_release"}}},
        )

        self.assertEqual(boundary["source_status"], LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE)

    def test_contract_source_status_backfill_marks_product_view_contracts(self):
        result = ensure_lowcode_contract_source_status({"view_orchestration": {"views": {"form": {}}}})

        self.assertEqual(
            result["view_orchestration"]["context"]["source_status"],
            LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE,
        )

    def test_contract_source_status_backfill_marks_tenant_menu_contracts(self):
        result = ensure_lowcode_contract_source_status({
            "menu_orchestration": {"source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING},
        })

        self.assertEqual(result["menu_orchestration"]["source_status"], LOWCODE_SOURCE_STATUS_TENANT_RUNTIME)

    def test_contract_source_status_backfill_does_not_override_explicit_status(self):
        result = ensure_lowcode_contract_source_status({
            "view_orchestration": {"context": {"source_status": LOWCODE_SOURCE_STATUS_TENANT_RUNTIME}},
        })

        self.assertEqual(
            result["view_orchestration"]["context"]["source_status"],
            LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
        )

    def test_menu_lowcode_source_constant_is_explicit(self):
        self.assertEqual(MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING, "smart_core.lowcode.menu_config")

    def test_approval_lowcode_source_constant_is_explicit(self):
        self.assertEqual(APPROVAL_POLICY_RUNTIME_SOURCE, "sc.approval.policy")
        self.assertEqual(APPROVAL_POLICY_SOURCE_TENANT_LOWCODING, "smart_core.lowcode.approval_policy")

    def test_user_preference_source_wins_over_view_orchestration_name(self):
        boundary = classify_view_orchestration_contract(
            "view_orchestration:res.partner:form:action:1:view:0",
            {"view_orchestration": {"context": {"source": "smart_construction_custom.partner_form_preference"}}},
        )

        self.assertEqual(boundary["kind"], "user_preference_projection")
        self.assertTrue(boundary["compatibility"])

    def test_contract_classification_keeps_user_preferences_below_product_and_lowcode(self):
        rows = [
            _contract(1, "project_project_form_structure_generated_v1", priority=77),
            _contract(2, "project_project_form_structure_v1", priority=90),
            _contract(
                3,
                "view_orchestration:project.project:form:action:506:view:0:custom_user_flat",
                "smart_construction_custom.user_form_preference",
                action_id=506,
                priority=600,
            ),
            _contract(
                4,
                "view_orchestration:project.project:form:action:506:view:0",
                "smart_core.lowcode.business_config",
                action_id=506,
                priority=100,
            ),
        ]

        ordered = sorted(rows, key=view_orchestration_apply_order_key)
        self.assertEqual([row.id for row in ordered], [1, 3, 2, 4])
        self.assertEqual(
            [classify_view_orchestration_contract(row.name, row.contract_json)["kind"] for row in ordered],
            [
                "generated_industry_baseline",
                "user_preference_projection",
                "industry_standard_configuration",
                "tenant_lowcode_configuration",
            ],
        )

    def test_runtime_view_snapshot_does_not_override_productized_entry_surface(self):
        rows = [
            _contract(
                1,
                "view_orchestration:purchase.order:form:action:581:view:0",
                "runtime_backend_form_view_contract",
                action_id=581,
                priority=100,
            ),
            _contract(
                2,
                "view_orchestration:purchase.order:form:action:581:view:0:custom_user_flat",
                "smart_construction_custom.user_form_preference",
                action_id=581,
                priority=600,
            ),
            _contract(
                3,
                "purchase_order_productized_form_v1",
                "smart_construction_core.product_release",
                action_id=581,
                priority=50,
            ),
        ]

        ordered = sorted(rows, key=view_orchestration_apply_order_key)
        self.assertEqual([row.id for row in ordered], [1, 2, 3])
        self.assertEqual(
            [classify_view_orchestration_contract(row.name, row.contract_json)["kind"] for row in ordered],
            [
                "generated_industry_baseline",
                "user_preference_projection",
                "industry_standard_configuration",
            ],
        )


if __name__ == "__main__":
    unittest.main()
