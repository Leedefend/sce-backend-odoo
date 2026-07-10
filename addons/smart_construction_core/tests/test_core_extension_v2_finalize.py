# -*- coding: utf-8 -*-
from copy import deepcopy

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.smart_construction_core import core_extension


@tagged("core_extension_v2_finalize")
class TestCoreExtensionV2Finalize(TransactionCase):
    def _base_project_contract(self):
        return {
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "form",
                        "containerId": "root",
                        "children": [
                            {
                                "type": "group",
                                "containerId": "base",
                                "children": [
                                    {"type": "field", "name": "user_id", "widgetId": "field.user_id"},
                                    {"type": "field", "name": "partner_id", "widgetId": "field.partner_id"},
                                    {"type": "field", "name": "manager_id", "widgetId": "field.manager_id"},
                                ],
                            }
                        ],
                    }
                ],
                "componentRegistry": {},
            },
            "statusContract": {
                "globalStatus": {"pageAuth": "edit"},
                "widgetStatus": [
                    {"widgetId": "field.user_id", "visible": True},
                    {"widgetId": "field.partner_id", "visible": True},
                ],
            },
            "runtimeContract": {},
        }

    def _field_nodes(self, value, *, include_widget_list=True):
        nodes = []
        if isinstance(value, list):
            for item in value:
                nodes.extend(self._field_nodes(item, include_widget_list=include_widget_list))
            return nodes
        if not isinstance(value, dict):
            return nodes
        if value.get("type") == "field" or str(value.get("widgetId") or "").startswith("field."):
            nodes.append(value)
        keys = ["children", "tabs", "pages", "nodes", "items"]
        if include_widget_list:
            keys.append("widgetList")
        for key in keys:
            nodes.extend(self._field_nodes(value.get(key), include_widget_list=include_widget_list))
        return nodes

    def test_finalize_handles_non_dict_context_without_mutation(self):
        contract = self._base_project_contract()

        projected = core_extension.smart_core_finalize_unified_page_contract_v2(None, contract, None)

        self.assertIsNone(projected)
        self.assertIn("field.user_id", {row["widgetId"] for row in contract["statusContract"]["widgetStatus"]})

    def test_project_form_finalize_prunes_user_field_and_adds_responsibility_group_once(self):
        contract = self._base_project_contract()
        source = {"model": "project.project", "view_type": "form", "render_profile": "edit"}

        projected = core_extension.smart_core_finalize_unified_page_contract_v2(
            self.env,
            contract,
            {"source_contract": source, "view_type": "form"},
        )
        projected_again = core_extension.smart_core_finalize_unified_page_contract_v2(
            self.env,
            deepcopy(projected),
            {"source_contract": source, "view_type": "form"},
        ) or projected

        self.assertIsInstance(projected, dict)
        field_nodes = self._field_nodes(projected["layoutContract"]["containerTree"], include_widget_list=False)
        widget_nodes = self._field_nodes(projected["layoutContract"]["containerTree"], include_widget_list=True)
        field_names = [row.get("name") or str(row.get("widgetId") or "").replace("field.", "") for row in field_nodes]
        widget_names = [row.get("fieldCode") for row in widget_nodes if row.get("fieldCode")]
        widget_status_ids = {row["widgetId"] for row in projected["statusContract"]["widgetStatus"]}

        self.assertNotIn("user_id", field_names)
        self.assertNotIn("field.user_id", widget_status_ids)
        self.assertEqual(field_names.count("responsibility_ids"), 1)
        self.assertEqual(field_names.count("collaborator_ids"), 1)
        self.assertIn("responsibility_ids", widget_names)
        self.assertIn("collaborator_ids", widget_names)
        self.assertEqual(projected["layoutContract"]["componentRegistry"]["sc.table.data"]["componentKey"], "sc.table.data")

        second_field_nodes = self._field_nodes(projected_again["layoutContract"]["containerTree"], include_widget_list=False)
        second_field_names = [
            row.get("name") or str(row.get("widgetId") or "").replace("field.", "")
            for row in second_field_nodes
        ]
        second_status_ids = {row["widgetId"] for row in projected_again["statusContract"]["widgetStatus"]}
        self.assertNotIn("user_id", second_field_names)
        self.assertNotIn("field.user_id", second_status_ids)
        self.assertEqual(second_field_names.count("responsibility_ids"), 1)
        self.assertEqual(second_field_names.count("collaborator_ids"), 1)

    def test_project_create_profile_does_not_add_collaborators(self):
        projected = core_extension.smart_core_finalize_unified_page_contract_v2(
            self.env,
            self._base_project_contract(),
            {"source_contract": {"model": "project.project", "view_type": "form", "render_profile": "create"}},
        )

        field_names = [
            row.get("name") or str(row.get("widgetId") or "").replace("field.", "")
            for row in self._field_nodes(projected["layoutContract"]["containerTree"], include_widget_list=False)
        ]

        self.assertIn("responsibility_ids", field_names)
        self.assertNotIn("collaborator_ids", field_names)

    def test_non_project_contract_is_unchanged_without_workflow_record(self):
        contract = self._base_project_contract()

        projected = core_extension.smart_core_finalize_unified_page_contract_v2(
            self.env,
            contract,
            {"source_contract": {"model": "res.partner", "view_type": "tree"}, "view_type": "tree"},
        )

        self.assertIsNone(projected)

    def test_projected_data_finalize_locks_formal_action_over_business_list_config_columns(self):
        data = {
            "model": "project.material.plan",
            "view_type": "tree",
            "action_id": 525,
            "list_profile": {
                "columns": [
                    "legacy_visible_01",
                    "legacy_visible_02",
                    "source_created_by",
                    "source_created_at",
                ],
                "fact_columns": [
                    "legacy_visible_01",
                    "legacy_visible_02",
                    "source_created_by",
                    "source_created_at",
                ],
                "column_policy": {
                    "mode": "strict",
                    "reason": "business_list_config_contract_authoritative",
                },
            },
        }

        projected = core_extension.smart_core_finalize_projected_contract_data(self.env, data, {"view_type": "tree"})

        self.assertIsInstance(projected, dict)
        profile = projected.get("list_profile") or {}
        self.assertEqual(
            (profile.get("column_policy") or {}).get("reason"),
            "formal_product_action_bound_tree_authoritative",
        )
        self.assertNotEqual(profile.get("columns"), data["list_profile"]["columns"])
        self.assertFalse((profile.get("preference_policy") or {}).get("allow_visibility"))

    def test_projected_contract_action_id_accepts_v2_action_aliases(self):
        self.assertEqual(
            core_extension._projected_contract_action_id({"actionId": "967"}),
            967,
        )
        self.assertEqual(
            core_extension._projected_contract_action_id({"source_meta": {"action_id": "964"}}),
            964,
        )
        self.assertEqual(
            core_extension._projected_contract_action_id({"pageInfo": {"actionId": "758"}}),
            758,
        )
