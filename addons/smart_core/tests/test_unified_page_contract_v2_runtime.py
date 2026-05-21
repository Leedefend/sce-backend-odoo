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
