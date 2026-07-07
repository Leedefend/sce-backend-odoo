#!/usr/bin/env python3
"""Guard attachment supplement policy for confirmed legacy handling records."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "addons/smart_construction_core/models/core/expense_claim.py": [
        'def _history_surface_allowed_write_fields(self):',
        'return {"attachment_ids"}',
    ],
    "addons/smart_construction_core/models/core/payment_execution.py": [
        'def _history_surface_allowed_write_fields(self):',
        'return {"attachment_ids"}',
    ],
    "addons/smart_construction_core/models/core/receipt_income.py": [
        'def _history_surface_allowed_write_fields(self):',
        'return {"attachment_ids"}',
    ],
    "addons/smart_construction_core/models/core/general_contract.py": [
        '"attachment_ids"',
        "历史迁移综合合同已确认",
    ],
}


def main() -> int:
    errors = []
    for rel, needles in REQUIRED.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel}: missing {needle!r}")
    if errors:
        for error in errors:
            print(error)
        return 1
    print("[history_confirmed_attachment_write_policy_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
