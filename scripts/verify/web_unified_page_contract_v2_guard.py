#!/usr/bin/env python3
"""Guard web contract API migration to Unified Page Contract v2."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_CONTRACT_API = ROOT / "frontend/apps/web/src/api/contract.ts"


def main() -> int:
    source = WEB_CONTRACT_API.read_text(encoding="utf-8") if WEB_CONTRACT_API.exists() else ""
    errors: list[str] = []
    if not source:
        errors.append("frontend web contract API is missing")
    if "intent: 'ui.contract.v2'" not in source and 'intent: "ui.contract.v2"' not in source:
        errors.append("web contract API must request ui.contract.v2")
    if "intent: 'ui.contract'," in source or 'intent: "ui.contract",' in source:
        errors.append("web contract API must not request legacy ui.contract directly")
    for token in (
        "adaptUnifiedPageContractV2Raw",
        "__unified_page_contract_v2",
        "resolveCompatSource",
        "delivery_profile: 'full'",
        "client_type: 'web_pc'",
    ):
        if token not in source:
            errors.append(f"web contract API missing v2 compatibility token: {token}")

    if errors:
        print("web unified page contract v2 guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("web unified page contract v2 guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
