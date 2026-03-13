#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
REPORT_JSON = ROOT / "artifacts/backend/frontend_actionview_scene_specialcase_guard_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_actionview_scene_specialcase_guard_report.md"


def main() -> int:
    errors: list[str] = []
    text = ACTION_VIEW.read_text(encoding="utf-8", errors="ignore") if ACTION_VIEW.is_file() else ""
    if not text:
        errors.append("missing file: frontend/apps/web/src/views/ActionView.vue")

    forbidden = [
        "sceneKey.value === 'projects.list'",
        "sceneKey.value === 'projects.ledger'",
        "sceneKey.value === 'task.center'",
        "sceneKey.value === 'risk.center'",
        "sceneKey.value === 'cost.project_boq'",
        "MODEL_LIST_PROFILE_PRESETS",
        "effectiveListModel",
        "resolvedModel === 'project.project'",
        "targetModel !== 'project.project'",
    ]
    required = [
        "const listSemanticKind = computed(() =>",
        "const hasLedgerOverviewStrip = computed(() =>",
        "const listProfile = computed<SceneListProfile | null>(() =>",
    ]

    for token in forbidden:
        if token in text:
            errors.append(f"forbidden special-case token present: {token}")
    for token in required:
        if token not in text:
            errors.append(f"missing required token: {token}")

    payload = {
        "ok": not errors,
        "check": "verify.frontend.actionview.scene_specialcase.guard",
        "file": "frontend/apps/web/src/views/ActionView.vue",
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Frontend ActionView Scene Specialcase Guard Report",
        "",
        f"- ok: {str(payload['ok']).lower()}",
        f"- check: {payload['check']}",
        f"- file: {payload['file']}",
    ]
    if errors:
        lines.append("- errors:")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("- errors: []")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if errors:
        print("[verify.frontend.actionview.scene_specialcase.guard] FAIL")
        for err in errors:
            print(f" - {err}")
        return 2
    print("[verify.frontend.actionview.scene_specialcase.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
