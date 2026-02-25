#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
RECORD_VIEW = ROOT / "frontend/apps/web/src/views/RecordView.vue"
REPORT_JSON = ROOT / "artifacts/backend/frontend_scene_record_semantics_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_scene_record_semantics_report.md"

SCENE_TOKENS = [
    "status === 'forbidden'",
    "variant=\"forbidden_capability\"",
    "const forbiddenCopy = ref(",
    "const policy = evaluateCapabilityPolicy",
    "const meta = session.capabilityCatalog[key];",
]

RECORD_TOKENS = [
    "const readonlyHint = computed(() => {",
    "session.productFacts.license?.level",
    "const meta = session.capabilityCatalog[key];",
    "缺少能力：",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    scene_text = _read(SCENE_VIEW)
    record_text = _read(RECORD_VIEW)

    if not scene_text:
        errors.append(f"missing file: {SCENE_VIEW.relative_to(ROOT).as_posix()}")
    if not record_text:
        errors.append(f"missing file: {RECORD_VIEW.relative_to(ROOT).as_posix()}")

    for token in SCENE_TOKENS:
        if scene_text and token not in scene_text:
            errors.append(f"SceneView missing token: {token}")
    for token in RECORD_TOKENS:
        if record_text and token not in record_text:
            errors.append(f"RecordView missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_files": [
                SCENE_VIEW.relative_to(ROOT).as_posix(),
                RECORD_VIEW.relative_to(ROOT).as_posix(),
            ],
            "error_count": len(errors),
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Scene/Record Semantics Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- error_count: `{report['summary']['error_count']}`",
        "",
        "## Checked Files",
    ]
    for file in report["summary"]["checked_files"]:
        lines.append(f"- `{file}`")
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_scene_record_semantics_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[frontend_scene_record_semantics_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
