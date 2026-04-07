#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


SEED_FILE = Path("addons/smart_construction_core/data/sc_capability_group_seed.xml")


def main() -> None:
    if not SEED_FILE.exists():
        raise SystemExit(
            f"[native_business_fact_install_order_guard_verify] FAIL missing file: {SEED_FILE}"
        )

    text = SEED_FILE.read_text(encoding="utf-8")
    failures: list[str] = []

    risky_required_group_ref = re.findall(
        r"required_group_ids[^\n]*ref\('smart_construction_core\.group_sc_cap_[^']+'\)",
        text,
        flags=re.IGNORECASE,
    )
    if risky_required_group_ref:
        failures.append(
            "seed contains required_group_ids referencing late-loaded smart_construction_core.group_sc_cap_* xmlids"
        )

    if failures:
        raise SystemExit(
            "[native_business_fact_install_order_guard_verify] FAIL " + "; ".join(failures)
        )

    print(
        "[native_business_fact_install_order_guard_verify] PASS "
        "no early required_group_ids dependency on smart_construction_core.group_sc_cap_*"
    )


if __name__ == "__main__":
    main()
