#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs"
PRIMARY_DOC = ROOT / "docs/architecture/scene_orchestration_v0_1.md"
COMMON = ROOT / "scripts/common/scene_legacy_contract.py"
LEGACY_ENDPOINT = "/api/scenes/my"


def _extract_constant(text: str, name: str) -> str:
    m = re.search(rf"{re.escape(name)}\s*=\s*\"([^\"]+)\"", text)
    return str(m.group(1) or "").strip() if m else ""


def main() -> int:
    if not PRIMARY_DOC.is_file():
        print("[scene_legacy_docs_guard] FAIL")
        print(f"missing doc: {PRIMARY_DOC.as_posix()}")
        return 1
    if not COMMON.is_file():
        print("[scene_legacy_docs_guard] FAIL")
        print(f"missing common contract: {COMMON.as_posix()}")
        return 1

    doc_text = PRIMARY_DOC.read_text(encoding="utf-8", errors="ignore")
    common_text = COMMON.read_text(encoding="utf-8", errors="ignore")

    successor = _extract_constant(common_text, "LEGACY_SCENES_SUCCESSOR")
    sunset_date = _extract_constant(common_text, "LEGACY_SCENES_SUNSET_DATE")

    violations: list[str] = []
    if not successor:
        violations.append("missing LEGACY_SCENES_SUCCESSOR in common contract")
    if not sunset_date:
        violations.append("missing LEGACY_SCENES_SUNSET_DATE in common contract")
    if successor and successor not in doc_text:
        violations.append(f"doc missing successor endpoint: {successor}")
    if successor and "intent=app.init" not in doc_text:
        violations.append("doc missing migration hint: intent=app.init")
    if "/api/v1/intent" not in doc_text or "intent=app.init" not in doc_text:
        violations.append("doc orchestration flow must use /api/v1/intent with intent=app.init")
    if sunset_date and sunset_date not in doc_text:
        violations.append(f"doc missing sunset date: {sunset_date}")

    for required in ("Deprecation", "Sunset", "Link", "X-Legacy-Endpoint"):
        if required not in doc_text:
            violations.append(f"doc missing header keyword: {required}")

    # Guard future docs from reintroducing legacy endpoint as primary path.
    if DOCS_ROOT.is_dir():
        for path in DOCS_ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if LEGACY_ENDPOINT not in text:
                continue
            rel = path.relative_to(ROOT).as_posix()
            lowered = text.lower()
            if "deprecated" not in lowered:
                violations.append(f"{rel}: missing deprecated marker for {LEGACY_ENDPOINT}")
            if successor and successor not in text:
                violations.append(f"{rel}: missing successor endpoint {successor}")
            if "intent=app.init" not in text:
                violations.append(f"{rel}: missing migration hint intent=app.init")
            if sunset_date and sunset_date not in text:
                violations.append(f"{rel}: missing sunset date {sunset_date}")

    if violations:
        print("[scene_legacy_docs_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_legacy_docs_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
