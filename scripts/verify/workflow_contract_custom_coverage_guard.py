#!/usr/bin/env python3
"""Guard workflowContract coverage for custom business workflow forms."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs/ops/audit/workflow_state_inventory_sc_demo.md"
ALLOWED_STANDARD_UNCOVERED = {
    "account.move",
    "purchase.order",
    "stock.picking",
}


def main() -> int:
    text = INVENTORY.read_text(encoding="utf-8")
    section = text.split("- Uncovered models with workflow methods:", 1)
    if len(section) != 2:
        print("[workflow_contract_custom_coverage_guard] FAIL missing uncovered section", file=sys.stderr)
        return 1
    body = section[1].split("\n## Models", 1)[0]
    uncovered = set(re.findall(r"^\s+- `([^`]+)`:", body, flags=re.MULTILINE))
    unexpected = sorted(uncovered - ALLOWED_STANDARD_UNCOVERED)
    if unexpected:
        print(
            "[workflow_contract_custom_coverage_guard] FAIL unexpected uncovered custom models: %s"
            % ", ".join(unexpected),
            file=sys.stderr,
        )
        return 1
    print(
        "[workflow_contract_custom_coverage_guard] PASS allowed_standard_uncovered=%s"
        % ",".join(sorted(uncovered & ALLOWED_STANDARD_UNCOVERED))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
