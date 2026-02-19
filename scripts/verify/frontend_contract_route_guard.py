#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "frontend/apps/web/src/router/index.ts"


def fail(msg: str) -> int:
    print("[frontend_contract_route_guard] FAIL")
    print(msg)
    return 1


def main() -> int:
    if not ROUTER.is_file():
        return fail("router file missing: frontend/apps/web/src/router/index.ts")

    text = ROUTER.read_text(encoding="utf-8", errors="ignore")

    required_tokens = [
        "path: '/f/:model/:id'",
        "name: 'model-form'",
        "component: ContractFormPage",
        "path: '/r/:model/:id'",
        "name: 'record'",
        "component: RecordView",
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        return fail("missing required router tokens: " + ", ".join(missing))

    forbidden_tokens = [
        "component: ModelFormPage",
        "component: ModelListPage",
    ]
    found_forbidden = [token for token in forbidden_tokens if token in text]
    if found_forbidden:
        return fail("forbidden legacy route component found: " + ", ".join(found_forbidden))

    print("[frontend_contract_route_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
