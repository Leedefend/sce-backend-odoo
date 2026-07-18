#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRODUCT_MODULES = (
    "smart_core",
    "smart_scene",
    "smart_license_core",
    "smart_construction_core",
    "smart_construction_portal",
    "smart_construction_scene",
    "smart_construction_bundle",
    "sc_norm_engine",
)
FORBIDDEN_TOKENS = (
    "smart_construction_custom",
)


def main() -> int:
    findings: list[str] = []
    for module in PRODUCT_MODULES:
        root = ROOT / "addons" / module
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            tokens = sorted(token for token in FORBIDDEN_TOKENS if token in text)
            if tokens:
                findings.append(f"{path.relative_to(ROOT)} tokens={','.join(tokens)}")
    if findings:
        print("[product_to_customer_dependency_guard] FAIL", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"[product_to_customer_dependency_guard] PASS modules={len(PRODUCT_MODULES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
