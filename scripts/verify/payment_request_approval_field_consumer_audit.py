#!/usr/bin/env python3
"""Audit deprecated payment approval summary field consumers.

Checks repository references of:
- preferred key: live_no_executable_actions
- deprecated key: live_no_allowed_actions

Outputs:
- artifacts/backend/payment_request_approval_field_consumer_audit.json
- artifacts/backend/payment_request_approval_field_consumer_audit.md
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "payment_request_approval_field_consumer_audit.json"
OUT_MD = ROOT / "artifacts" / "backend" / "payment_request_approval_field_consumer_audit.md"

NEW_KEY = "live_no_executable_actions"
OLD_KEY = "live_no_allowed_actions"

SCAN_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".vue",
    ".md",
    ".yml",
    ".yaml",
    ".json",
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "artifacts",
    ".pnpm-store",
    ".cache",
    "tmp",
    "out",
}

SCAN_ROOT_DIRS = (
    ROOT / "scripts",
    ROOT / "docs",
    ROOT / "frontend",
    ROOT / "addons",
)

ALLOWED_OLD_KEY_FILES = {
    "scripts/verify/payment_request_approval_smoke.py",
    "scripts/verify/payment_request_approval_field_consumer_audit.py",
    "docs/releases/delivery_readiness_execution_evidence_2026-03-19.md",
    "docs/releases/delivery_readiness_execution_evidence_2026-03-19.en.md",
    "docs/ops/verify/README.md",
    "docs/ops/releases/current/phase_12_stage4_payment_handoff_actor_match.md",
}


def _iter_files():
    for base in SCAN_ROOT_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            yield path


def _scan_file(path: Path, needle: str) -> list[int]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    return [idx for idx, line in enumerate(lines, start=1) if needle in line]


def _format_rows(rows: list[dict]) -> str:
    if not rows:
        return "-"
    return "\n".join(f"- `{row['path']}:{row['line']}`" for row in rows)


def main() -> int:
    old_rows: list[dict] = []
    new_rows: list[dict] = []

    for path in _iter_files():
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        for line in _scan_file(path, OLD_KEY):
            old_rows.append({"path": rel, "line": int(line)})
        for line in _scan_file(path, NEW_KEY):
            new_rows.append({"path": rel, "line": int(line)})

    unexpected_old = [
        row for row in old_rows if str(row.get("path") or "") not in ALLOWED_OLD_KEY_FILES
    ]

    ok = len(unexpected_old) == 0

    report = {
        "ok": ok,
        "preferred_key": NEW_KEY,
        "deprecated_key": OLD_KEY,
        "deprecated_key_allowed_files": sorted(ALLOWED_OLD_KEY_FILES),
        "deprecated_key_refs": old_rows,
        "preferred_key_refs": new_rows,
        "unexpected_deprecated_key_refs": unexpected_old,
        "summary": {
            "deprecated_key_ref_count": len(old_rows),
            "preferred_key_ref_count": len(new_rows),
            "unexpected_deprecated_key_ref_count": len(unexpected_old),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# Payment Approval Field Consumer Audit",
        "",
        f"- `ok`: `{str(ok).lower()}`",
        f"- preferred key: `{NEW_KEY}`",
        f"- deprecated key: `{OLD_KEY}`",
        f"- deprecated key refs: `{len(old_rows)}`",
        f"- preferred key refs: `{len(new_rows)}`",
        f"- unexpected deprecated refs: `{len(unexpected_old)}`",
        "",
        "## Unexpected Deprecated Refs",
        _format_rows(unexpected_old),
        "",
        "## Deprecated Refs (All)",
        _format_rows(old_rows),
        "",
        "## Preferred Refs (All)",
        _format_rows(new_rows),
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("[payment_request_approval_field_consumer_audit]", "PASS" if ok else "FAIL")
    print(f"- json: {OUT_JSON.relative_to(ROOT)}")
    print(f"- md: {OUT_MD.relative_to(ROOT)}")
    print(f"- unexpected_deprecated_refs: {len(unexpected_old)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
