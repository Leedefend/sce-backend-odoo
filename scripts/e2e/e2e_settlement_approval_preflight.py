#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


CHECKS = [
    {
        "id": "settlement_payment_runtime_flow",
        "path": "scripts/verify/core_document_processing_gate.py",
        "needles": [
            "def _run_settlement_payment",
            "def _approve_settlement",
            "sc.settlement.order",
            "settlement.action_submit()",
            "settlement.action_on_tier_approved()",
            "settlement.action_done()",
            "_assert_amount",
        ],
    },
    {
        "id": "settlement_model_flow_tests",
        "path": "addons/smart_construction_core/tests/test_p0_state_closure.py",
        "needles": [
            "P0 Settlement Order Flow",
            "P0 Project Settlement Closure",
            "action_submit",
            "action_on_tier_approved",
            "action_done",
        ],
    },
    {
        "id": "settlement_views_and_actions_loaded",
        "path": "addons/smart_construction_core/__manifest__.py",
        "needles": [
            "data/settlement_order_tier_actions.xml",
            "views/core/settlement_views.xml",
        ],
    },
    {
        "id": "settlement_model_surface",
        "path": "addons/smart_construction_core/models/core/settlement_order.py",
        "needles": [
            '_name = "sc.settlement.order"',
            "def action_submit",
            "def action_on_tier_approved",
            "def action_done",
            "amount_total",
            "contract_id",
            "project_id",
        ],
    },
]


def run_check(check: dict[str, object]) -> dict[str, object]:
    path = ROOT / str(check["path"])
    if not path.exists():
        return {"id": check["id"], "path": str(check["path"]), "ok": False, "missing": ["file"]}
    text = path.read_text(encoding="utf-8")
    missing = [str(needle) for needle in check["needles"] if str(needle) not in text]
    return {"id": check["id"], "path": str(check["path"]), "ok": not missing, "missing": missing}


def main() -> int:
    results = [run_check(check) for check in CHECKS]
    failed = [item for item in results if not item["ok"]]
    report = {
        "journey": "E2E-08 settlement creation and approval",
        "status": "preflight_passed" if not failed else "preflight_failed",
        "acceptance_points": [
            "Settlement order model exposes submit, approval, and done transitions.",
            "Runtime gate creates settlement, approves it, links payment, and verifies amount.",
            "P0 state closure tests include settlement lifecycle and blocking cases.",
            "Views and tier actions are loaded for user-facing approval operation.",
        ],
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if failed:
        return 1
    print("[e2e_settlement_approval_preflight] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
