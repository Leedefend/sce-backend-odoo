#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "frontend_zero_business_semantics_guard.json"
FRONTEND_ROOT = ROOT / "frontend" / "apps" / "web" / "src"
ALLOWED_FILES = {
    "frontend/apps/web/src/app/projectCreationBaseline.ts",
}
FORBIDDEN_PATTERNS = [
    re.compile(r"projects\.intake"),
    re.compile(r"project\.[a-z_]+\.enter"),
]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _line_of(text: str, match_start: int) -> int:
    return text[:match_start].count("\n") + 1


def main() -> int:
    findings: list[dict] = []
    for path in FRONTEND_ROOT.rglob("*"):
        if path.suffix not in {".ts", ".vue"}:
            continue
        rel = str(path.relative_to(ROOT))
        if rel in ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "path": rel,
                        "line": _line_of(text, match.start()),
                        "message": f"raw business semantic token `{match.group(0)}` remains in frontend source",
                    }
                )

    report = {
        "status": "PASS" if not findings else "BLOCKED",
        "finding_count": len(findings),
        "findings": findings,
    }
    _write_json(OUT_JSON, report)
    if findings:
        print("[frontend_zero_business_semantics_guard] BLOCKED")
        for item in findings[:20]:
            print(f" - {item['path']}:{item['line']} {item['message']}")
        return 1
    print("[frontend_zero_business_semantics_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
