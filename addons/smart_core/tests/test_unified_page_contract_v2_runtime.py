# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

_load_module("odoo.addons.smart_core.core.source_authority", CORE_DIR / "source_authority.py")
runtime = _load_module(
    "odoo.addons.smart_core.core.unified_page_contract_v2_runtime",
    CORE_DIR / "unified_page_contract_v2_runtime.py",
)


class TestUnifiedPageContractV2Runtime(unittest.TestCase):
    def _contract(self):
        return {
            "formStructureContract": {
                "source": "ui.contract.v2.form_structure_contract",
                "viewType": "form",
                "slots": [
                    {
                        "slot": "overview",
                        "title": "办理总览",
                        "fieldRefs": ["name"],
                    },
                    {
                        "slot": "primary_facts",
                        "title": "主业务事实",
                        "groups": [
                            {"name": "identity", "fieldRefs": ["subject"]},
                        ],
                    },
                ],
                "fieldRoles": {
                    "name": {"role": "identity", "slot": "overview", "group": "overview"},
                    "subject": {"role": "identity", "slot": "primary_facts", "group": "identity"},
                },
                "sourceAuthority": {
                    "kind": "unified_page_contract_v2",
                    "runtime_carrier": "ui.contract.v2.form_structure_contract",
                    "projection_only": True,
                    "no_business_fact_authority": True,
                    "governed_form_structure": True,
                    "governance_source": {
                        "source": "business_view_orchestration",
                        "field_names": ["name", "subject"],
                    },
                },
            },
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "sheet",
                        "children": [
                            {"type": "field", "name": "name"},
                            {"type": "field", "name": "subject"},
                        ],
                    }
                ],
                "componentRegistry": {"sc.input": {}},
            },
            "dataContract": {
                "dataMeta": {
                    "fields": {
                        "name": {"type": "char"},
                        "subject": {"type": "char"},
                    }
                }
            },
        }

    def test_form_structure_contract_accepts_projected_known_fields(self):
        issues = runtime.find_form_structure_contract_issues(self._contract())
        self.assertEqual(issues, [])

    def test_data_source_authority_rejects_missing_source_authority(self):
        issues = runtime.find_data_source_authority_issues({
            "dataSource": {
                "primary": {
                    "query": "api.data",
                    "intent": "api.data",
                    "params": {"model": "project.project"},
                }
            },
        })

        self.assertIn("dataContract.dataSource.primary.sourceAuthority is required", issues)

    def test_data_source_authority_accepts_projected_sources(self):
        issues = runtime.find_data_source_authority_issues({
            "dataSource": {
                "primary": {
                    "query": "api.data",
                    "intent": "api.data",
                    "sourceAuthority": {
                        "projection_only": True,
                        "no_business_fact_authority": True,
                        "fact_authority": "odoo.model",
                    },
                }
            },
        })

        self.assertEqual(issues, [])

    def test_metadata_projection_rejects_legacy_projection_payloads(self):
        issues = runtime.find_metadata_projection_issues({
            "dataMeta": {
                "legacyContractProjection": {
                    "business_operation_profile": {"source": "legacy"},
                    "field_groups": [{"name": "core", "fields": ["name"]}],
                    "form_structure_contract": {"source": "legacy"},
                    "list_profile": {"columns": ["name"]},
                    "visible_fields": ["name"],
                }
            }
        })

        self.assertIn(
            "dataContract.dataMeta.legacyContractProjection must not be emitted in stable V2 contract",
            issues,
        )
        self.assertIn(
            "legacyContractProjection.business_operation_profile must not be emitted; use formal V2 metadata",
            issues,
        )
        self.assertIn(
            "legacyContractProjection.field_groups must not be emitted; use formal V2 metadata",
            issues,
        )
        self.assertIn(
            "legacyContractProjection.form_structure_contract must not be emitted; use formal V2 metadata",
            issues,
        )
        self.assertIn(
            "legacyContractProjection.list_profile must not be emitted; use formal V2 metadata",
            issues,
        )
        self.assertIn(
            "legacyContractProjection.visible_fields must not be emitted; use formal V2 metadata",
            issues,
        )

    def test_metadata_projection_rejects_legacy_projection_alias_presence(self):
        issues = runtime.find_metadata_projection_issues({
            "dataMeta": {
                "legacy_contract_projection": {},
            }
        })

        self.assertIn(
            "dataContract.dataMeta.legacyContractProjection must not be emitted in stable V2 contract",
            issues,
        )

    def test_metadata_projection_accepts_formal_v2_metadata(self):
        issues = runtime.find_metadata_projection_issues({
            "dataMeta": {
                "businessOperationProfile": {
                    "common_fields": ["name"],
                    "sourceAuthority": self._metadata_source("business_operation_profile"),
                },
                "visibleFields": {
                    "fields": ["name"],
                    "sourceAuthority": self._metadata_source("visible_fields"),
                },
                "fieldGroups": {
                    "groups": [{"name": "core", "fields": ["name"]}],
                    "sourceAuthority": self._metadata_source("field_groups"),
                },
            }
        })

        self.assertEqual(issues, [])

    def test_metadata_projection_rejects_snake_case_formal_aliases(self):
        issues = runtime.find_metadata_projection_issues({
            "dataMeta": {
                "business_operation_profile": {
                    "common_fields": ["name"],
                    "sourceAuthority": self._metadata_source("business_operation_profile"),
                },
                "visible_fields": {
                    "fields": ["name"],
                    "sourceAuthority": self._metadata_source("visible_fields"),
                },
                "field_groups": {
                    "groups": [{"name": "core", "fields": ["name"]}],
                    "sourceAuthority": self._metadata_source("field_groups"),
                },
            }
        })

        self.assertIn(
            "dataContract.dataMeta.business_operation_profile must not be emitted; use formal V2 camelCase metadata",
            issues,
        )
        self.assertIn(
            "dataContract.dataMeta.visible_fields must not be emitted; use formal V2 camelCase metadata",
            issues,
        )
        self.assertIn(
            "dataContract.dataMeta.field_groups must not be emitted; use formal V2 camelCase metadata",
            issues,
        )

    def test_policy_contract_rejects_root_compatibility_fields(self):
        contract = self._contract()
        contract["delete_policy"] = {"allow": True}
        contract["surface_policies"] = {"kind": "list"}
        contract["list_profile"] = {"batch_policy": {"enabled": True}}

        issues = runtime.find_policy_contract_issues(contract)

        self.assertIn("root compatibility field delete_policy must not be emitted by V2 contract", issues)
        self.assertIn("root compatibility field surface_policies must not be emitted by V2 contract", issues)
        self.assertIn("root compatibility field list_profile must not be emitted by V2 contract", issues)

    def test_policy_contract_rejects_nested_compatibility_fields(self):
        contract = self._contract()
        contract["actionContract"] = {
            "delete_policy": {"allow": True},
            "surface_policies": {"kind": "list"},
        }
        contract["layoutContract"]["list_profile"] = {"batch_policy": {"enabled": True}}

        issues = runtime.find_policy_contract_issues(contract)

        self.assertIn("actionContract compatibility field delete_policy must not be emitted by V2 contract", issues)
        self.assertIn("actionContract compatibility field surface_policies must not be emitted by V2 contract", issues)
        self.assertIn("layoutContract compatibility field list_profile must not be emitted by V2 contract", issues)

    def test_policy_contract_accepts_formal_v2_policy_projection(self):
        contract = self._contract()
        contract["actionContract"] = {
            "deletePolicy": {
                "allow": True,
                "sourceAuthority": self._policy_source("delete_policy"),
            },
            "surfacePolicies": {
                "kind": "list",
                "sourceAuthority": self._policy_source("surface_policies"),
            },
        }
        contract["layoutContract"]["listProfile"] = {
            "batch_policy": {"enabled": True},
            "sourceAuthority": self._policy_source("list_profile"),
        }

        issues = runtime.find_policy_contract_issues(contract)

        self.assertEqual(issues, [])

    def test_policy_contract_rejects_projection_without_authority(self):
        contract = self._contract()
        contract["layoutContract"]["listProfile"] = {
            "batch_policy": {"enabled": False},
        }

        issues = runtime.find_policy_contract_issues(contract)

        self.assertIn(
            "layoutContract.listProfile.sourceAuthority is required",
            issues,
        )

    def _policy_source(self, source_key):
        return {
            "projection_only": True,
            "no_business_fact_authority": True,
            "formal_projection": True,
            "source_key": source_key,
        }

    def _metadata_source(self, source_key):
        return {
            "projection_only": True,
            "no_business_fact_authority": True,
            "formal_projection": True,
            "source_key": source_key,
        }

    def test_form_structure_contract_rejects_unknown_duplicate_and_unprojected_fields(self):
        contract = self._contract()
        contract["formStructureContract"]["slots"][1]["groups"][0]["fieldRefs"].extend(["subject", "missing_field"])
        contract["formStructureContract"]["fieldRoles"]["missing_role"] = {"role": "identity", "slot": "missing_slot"}

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertIn("formStructureContract references field more than once: subject", issues)
        self.assertIn("formStructureContract references unknown field: missing_field", issues)
        self.assertIn("formStructureContract.fieldRoles.missing_role references unknown field", issues)
        self.assertIn("formStructureContract.fieldRoles.missing_role.slot references unknown slot missing_slot", issues)
        self.assertIn("formStructureContract field not projected to layout: missing_field", issues)

    def test_form_structure_contract_rejects_root_compatibility_alias(self):
        contract = self._contract()
        contract["form_structure_contract"] = contract["formStructureContract"]

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertIn("root compatibility field form_structure_contract must not be emitted by V2 contract", issues)

    def test_form_structure_contract_allows_overview_summary_references(self):
        contract = self._contract()
        contract["formStructureContract"]["slots"][1]["groups"][0]["fieldRefs"].append("name")

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertNotIn("formStructureContract references field more than once: name", issues)

    def test_form_structure_contract_rejects_internal_fields(self):
        contract = self._contract()
        contract["formStructureContract"]["slots"][1]["groups"][0]["fieldRefs"].extend([
            "access_token",
            "alias_id",
            "dashboard_graph_data",
            "is_favorite",
            "source_origin",
            "validation_status",
            "legacy_counterparty_text",
            "amount_source",
            "review_ids",
        ])
        contract["layoutContract"]["containerTree"][0]["children"].extend([
            {"type": "field", "name": "access_token"},
            {"type": "field", "name": "alias_id"},
            {"type": "field", "name": "dashboard_graph_data"},
            {"type": "field", "name": "is_favorite"},
            {"type": "field", "name": "source_origin"},
            {"type": "field", "name": "validation_status"},
            {"type": "field", "name": "legacy_counterparty_text"},
            {"type": "field", "name": "amount_source"},
            {"type": "field", "name": "review_ids"},
        ])
        contract["dataContract"]["dataMeta"]["fields"].update({
            "access_token": {"type": "char"},
            "alias_id": {"type": "many2one"},
            "dashboard_graph_data": {"type": "char"},
            "is_favorite": {"type": "boolean"},
            "source_origin": {"type": "char"},
            "validation_status": {"type": "char"},
            "legacy_counterparty_text": {"type": "char"},
            "amount_source": {"type": "char"},
            "review_ids": {"type": "one2many"},
        })

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertIn("formStructureContract references internal field: access_token", issues)
        self.assertIn("formStructureContract references internal field: alias_id", issues)
        self.assertIn("formStructureContract references internal field: dashboard_graph_data", issues)
        self.assertIn("formStructureContract references internal field: is_favorite", issues)
        self.assertIn("formStructureContract references internal field: source_origin", issues)
        self.assertIn("formStructureContract references internal field: validation_status", issues)
        self.assertIn("formStructureContract references internal field: legacy_counterparty_text", issues)
        self.assertIn("formStructureContract references internal field: amount_source", issues)
        self.assertIn("formStructureContract references internal field: review_ids", issues)

    def test_form_structure_contract_rejects_fields_outside_governance(self):
        contract = self._contract()
        contract["formStructureContract"]["slots"][1]["groups"][0]["fieldRefs"].append("company_id")
        contract["layoutContract"]["containerTree"][0]["children"].append({"type": "field", "name": "company_id"})
        contract["dataContract"]["dataMeta"]["fields"]["company_id"] = {"type": "many2one"}

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertIn("formStructureContract references field outside governance: company_id", issues)

    def test_form_structure_contract_rejects_layout_fields_outside_structure(self):
        contract = self._contract()
        contract["layoutContract"]["containerTree"][0]["children"].append({"type": "field", "name": "company_id"})
        contract["layoutContract"]["containerTree"][0]["children"].append({"type": "field", "name": "can_review"})
        contract["dataContract"]["dataMeta"]["fields"].update({
            "company_id": {"type": "many2one"},
            "can_review": {"type": "boolean"},
        })

        issues = runtime.find_form_structure_contract_issues(contract)

        self.assertIn("formStructureContract layout projects field outside structure: company_id", issues)
        self.assertNotIn("formStructureContract layout projects field outside structure: can_review", issues)


if __name__ == "__main__":
    unittest.main()
