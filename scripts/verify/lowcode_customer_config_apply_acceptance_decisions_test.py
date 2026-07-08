#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verify.lowcode_customer_config_apply_acceptance_decisions import build_asset  # noqa: E402


def _draft(source_status: str = "tenant_runtime"):
    return {
        "schema_version": "lowcode_customer_config_module_asset_draft.v1",
        "target_module": "smart_construction_custom",
        "module_asset_records": [
            {
                "contract_key": "model|form|1|0||contract",
                "surface": "form_preferences",
                "name": "contract",
                "model": "x.model",
                "view_type": "form",
                "action_id": 1,
                "view_id": 0,
                "source_status": source_status,
                "payload_hash": "hash-1",
                "contract_json": {"view_orchestration": {"views": {"form": {"fields": []}}}},
            }
        ],
    }


def _decisions(**overrides):
    row = {
        "contract_key": "model|form|1|0||contract",
        "decision": "accepted",
        "reviewer": "reviewer",
        "review_note": "confirmed by customer",
        "payload_hash": "hash-1",
    }
    row.update(overrides)
    return {
        "schema_version": "lowcode_customer_config_acceptance_decisions.v1",
        "source_draft_schema": "lowcode_customer_config_module_asset_draft.v1",
        "target_module": "smart_construction_custom",
        "decisions": [row],
    }


class LowcodeCustomerConfigApplyAcceptanceDecisionsTest(unittest.TestCase):
    def test_accepts_reviewed_matching_tenant_runtime_record(self):
        asset = build_asset(_draft(), _decisions())

        self.assertEqual(asset["schema_version"], "lowcode_customer_config_contracts.v1")
        self.assertEqual(asset["summary"]["accepted_count"], 1)
        self.assertEqual(asset["summary"]["pending_count"], 0)
        self.assertEqual(asset["accepted_contracts"][0]["accepted_by"], "reviewer")
        self.assertEqual(asset["accepted_contracts"][0]["acceptance_note"], "confirmed by customer")

    def test_pending_decision_does_not_enter_asset(self):
        asset = build_asset(_draft(), _decisions(decision="pending", reviewer="", review_note=""))

        self.assertEqual(asset["summary"]["accepted_count"], 0)
        self.assertEqual(asset["summary"]["pending_count"], 1)
        self.assertEqual(asset["accepted_contracts"], [])

    def test_rejects_accepted_without_reviewer(self):
        with self.assertRaisesRegex(SystemExit, "reviewer and review_note"):
            build_asset(_draft(), _decisions(reviewer=""))

    def test_rejects_accepted_without_review_note(self):
        with self.assertRaisesRegex(SystemExit, "reviewer and review_note"):
            build_asset(_draft(), _decisions(review_note=""))

    def test_rejects_payload_hash_mismatch(self):
        with self.assertRaisesRegex(SystemExit, "payload_hash"):
            build_asset(_draft(), _decisions(payload_hash="wrong"))

    def test_rejects_non_tenant_runtime_record(self):
        with self.assertRaisesRegex(SystemExit, "tenant_runtime"):
            build_asset(_draft(source_status="product_release"), _decisions())

    def test_rejects_unknown_decision(self):
        with self.assertRaisesRegex(SystemExit, "invalid decision"):
            build_asset(_draft(), _decisions(decision="approved"))

    def test_rejects_duplicate_decisions(self):
        decisions = _decisions()
        decisions["decisions"].append(copy.deepcopy(decisions["decisions"][0]))

        with self.assertRaisesRegex(SystemExit, "duplicate decision"):
            build_asset(_draft(), decisions)


if __name__ == "__main__":
    unittest.main()
