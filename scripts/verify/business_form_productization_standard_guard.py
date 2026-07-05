#!/usr/bin/env python3
"""Guard the formal business form productization standard wiring."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "docs/product/formal_business_form_productization_standard_v1.md"
AUDIT = ROOT / "scripts/verify/business_form_productization_audit.py"
MAKEFILE = ROOT / "Makefile"
VERIFY_README = ROOT / "docs/ops/verify/README.md"

STANDARD_TOKENS = (
    "Formal Business Form Productization Standard v1",
    "Product Layer Responsibilities",
    "P0 platform",
    "P1 industry product",
    "P2 customer product",
    "P3 low-code runtime",
    "P4 ops/migration",
    "Core Design Logic",
    "Standard Form Anatomy",
    "Density Rules",
    "Entry Semantics",
    "Field Classification",
    "State and Actions",
    "Attachments and Evidence",
    "List/Form/Search Alignment",
    "Role and Complexity",
    "Machine Verification",
    "make verify.business_form.productization.audit",
    "First Batch Rule",
)

AUDIT_TOKENS = (
    "STANDARD_PATH = ROOT / \"docs/product/formal_business_form_productization_standard_v1.md\"",
    "\"standard_path\": str(STANDARD_PATH.relative_to(ROOT))",
    "HIGH_DENSITY_THRESHOLD = 70",
    "MEDIUM_DENSITY_THRESHOLD = 50",
)

MAKEFILE_TOKENS = (
    ".PHONY: verify.form_structure.contract.guard",
    "verify.business_form.productization.audit: guard.prod.forbid",
    "python3 -m py_compile scripts/verify/business_form_productization_audit.py",
    "python3 scripts/verify/business_form_productization_audit.py",
)

VERIFY_README_TOKENS = (
    "`make verify.business_form.productization.audit`",
    "business_form_productization_audit.json",
    "business_form_productization_audit.md",
)


def _read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def _require(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{label}: missing token: {token}")


def main() -> int:
    errors: list[str] = []
    standard = _read(STANDARD, errors)
    audit = _read(AUDIT, errors)
    makefile = _read(MAKEFILE, errors)
    verify_readme = _read(VERIFY_README, errors)

    _require("standard", standard, STANDARD_TOKENS, errors)
    _require("audit", audit, AUDIT_TOKENS, errors)
    _require("makefile", makefile, MAKEFILE_TOKENS, errors)
    _require("verify_readme", verify_readme, VERIFY_README_TOKENS, errors)

    if errors:
        print("[business_form_productization_standard_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[business_form_productization_standard_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
