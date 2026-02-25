#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "frontend/apps/web/src/views/HomeView.vue"
REPORT_JSON = ROOT / "artifacts/backend/frontend_home_suggestion_semantics_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_home_suggestion_semantics_report.md"

TOKENS = [
    "function suggestionEntryScore(entry: CapabilityEntry)",
    "const groupScore = capabilityGroupScoreMap.value.get(entry.groupKey) || 0;",
    "const pendingCount = resolveSuggestionCount(entry.sceneKey) || 0;",
    "if (entry.capabilityState === 'readonly') stateBase += 0.5;",
    "if (entry.capabilityState === 'deny') stateBase -= 1;",
    ".sort((a, b) => suggestionEntryScore(b) - suggestionEntryScore(a)",
]


def main() -> int:
    errors: list[str] = []
    text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.is_file() else ""
    if not text:
        errors.append(f"missing file: {TARGET.relative_to(ROOT).as_posix()}")
    else:
        for token in TOKENS:
            if token not in text:
                errors.append(f"missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_file": TARGET.relative_to(ROOT).as_posix(),
            "error_count": len(errors),
            "signal_count": len(TOKENS),
        },
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Home Suggestion Semantics Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_file: `{report['summary']['checked_file']}`",
        f"- signal_count: `{report['summary']['signal_count']}`",
        f"- error_count: `{report['summary']['error_count']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_home_suggestion_semantics_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[frontend_home_suggestion_semantics_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
