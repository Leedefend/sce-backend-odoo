# -*- coding: utf-8 -*-
import importlib.util
import unittest
from dataclasses import dataclass
from pathlib import Path


def _load_presence_module():
    path = Path(__file__).resolve().parents[1] / "core" / "view_contract_presence.py"
    spec = importlib.util.spec_from_file_location("smart_core_view_contract_presence_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRESENCE = _load_presence_module()


@dataclass
class ContractShape:
    view_type: str = ""
    contract_json: object = None
    status: str = "published"
    active: bool = True
    source_kind: str = "published"


def payload(**views):
    return {"view_orchestration": {"views": views}}


class TestViewContractPresence(unittest.TestCase):
    def assertViews(self, contract, expected):
        actual = {
            view_type: PRESENCE.contract_contributes_view(contract, view_type)
            for view_type in ("form", "tree", "search", "pivot", "graph")
        }
        self.assertEqual(actual, expected)

    def test_fixed_contract_shape_matrix(self):
        false = {"form": False, "tree": False, "search": False, "pivot": False, "graph": False}
        cases = {
            "dedicated_nonempty": (
                ContractShape("tree", payload(tree={"columns": [{"name": "name"}]})),
                {**false, "tree": True},
            ),
            "dedicated_empty": (
                ContractShape("tree", payload(tree={"columns": []})),
                {**false, "tree": True},
            ),
            "generic_multi_view": (
                ContractShape("", payload(form={}, tree={"columns": []}, search={"filters": []})),
                {**false, "form": True, "tree": True, "search": True},
            ),
            "generic_form_only": (ContractShape("", payload(form={})), {**false, "form": True}),
            "generic_tree_only": (ContractShape("", payload(tree={})), {**false, "tree": True}),
            "generic_search_only": (ContractShape("", payload(search={})), {**false, "search": True}),
            "generic_pivot_only": (ContractShape("", payload(pivot={})), {**false, "pivot": True}),
            "generic_graph_only": (ContractShape("", payload(graph={})), {**false, "graph": True}),
            "generic_empty_target": (ContractShape("", payload(tree={"columns": []})), {**false, "tree": True}),
            "no_target_view": (ContractShape("", payload(form={})), {**false, "form": True}),
            "damaged_target_view": (ContractShape("", payload(tree=[])), false),
            "draft": (ContractShape("tree", payload(tree={}), status="draft"), false),
            "inactive": (ContractShape("tree", payload(tree={}), active=False), false),
            "superseded": (ContractShape("tree", payload(tree={}), status="superseded"), false),
        }
        for name, (contract, expected) in cases.items():
            with self.subTest(name=name):
                self.assertViews(contract, expected)

    def test_list_alias_normalizes_to_tree_without_cross_view_leakage(self):
        dedicated = ContractShape("list", payload(list={"columns": []}))
        self.assertTrue(PRESENCE.contract_contributes_view(dedicated, "tree"))
        self.assertTrue(PRESENCE.contract_contributes_view(dedicated, "list"))
        self.assertFalse(PRESENCE.contract_contributes_view(dedicated, "search"))

    def test_preview_projection_contributes_but_draft_does_not(self):
        preview = ContractShape("pivot", payload(pivot={"measures": []}), status="preview", source_kind="change_set_preview")
        draft = ContractShape("pivot", payload(pivot={"measures": []}), status="draft")
        self.assertTrue(PRESENCE.contract_contributes_view(preview, "pivot"))
        self.assertFalse(PRESENCE.contract_contributes_view(draft, "pivot"))

    def test_bool_contracts_regression_cannot_pass_form_only_as_tree(self):
        contracts = [ContractShape("", payload(form={}))]
        self.assertTrue(bool(contracts))
        self.assertFalse(any(PRESENCE.contract_contributes_view(item, "tree") for item in contracts))

    def test_negative_mutants_are_rejected_by_behavior_matrix(self):
        scenarios = [
            (ContractShape("", payload(form={})), "tree", False),
            (ContractShape("tree", payload(tree={})), "search", False),
            (ContractShape("", payload(tree={"columns": []})), "tree", True),
            (ContractShape("", payload(pivot={})), "graph", False),
            (ContractShape("", payload(graph={})), "pivot", False),
        ]

        def bool_contracts(_contract, _requested):
            return True

        def declared_or_any_payload(contract, requested):
            declared = PRESENCE.normalize_contract_view_type(contract.view_type)
            return not declared or declared == PRESENCE.normalize_contract_view_type(requested)

        def payload_truthiness(contract, requested):
            views = contract.contract_json["view_orchestration"]["views"]
            normalized = PRESENCE.normalize_contract_view_type(requested)
            spec = views.get(normalized) or {}
            keys = {
                "form": ("fields", "layout"),
                "tree": ("columns",),
                "search": ("filters", "group_by"),
                "pivot": ("measures", "dimensions"),
                "graph": ("measures", "dimensions"),
            }.get(normalized, ())
            return any(bool(spec.get(key)) for key in keys)

        def analysis_any(contract, requested):
            views = contract.contract_json["view_orchestration"]["views"]
            normalized = PRESENCE.normalize_contract_view_type(requested)
            if normalized in {"pivot", "graph"}:
                return "pivot" in views or "graph" in views
            return normalized in views

        for name, mutant in {
            "bool_contracts": bool_contracts,
            "declared_or_any_payload": declared_or_any_payload,
            "payload_truthiness": payload_truthiness,
            "pivot_graph_cross_presence": analysis_any,
        }.items():
            with self.subTest(mutant=name):
                self.assertTrue(any(mutant(contract, requested) != expected for contract, requested, expected in scenarios))


if __name__ == "__main__":
    unittest.main()
