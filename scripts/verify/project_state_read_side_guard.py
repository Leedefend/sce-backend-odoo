#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard project read-side consumers from treating stage_id as truth."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "project_state_read_side_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "backend" / "project_state_read_side_guard.md"

PROJECT_SERVICE_FILES = [
    ROOT / "addons/smart_construction_core/services/project_state_explain_service.py",
    ROOT / "addons/smart_construction_core/services/project_dashboard_service.py",
    ROOT / "addons/smart_construction_core/services/project_dashboard_builders/project_header_builder.py",
    ROOT / "addons/smart_construction_core/services/project_dashboard_builders/base.py",
    ROOT / "addons/smart_construction_core/services/project_context_contract.py",
    ROOT / "addons/smart_construction_core/services/insight/project_insight_service.py",
    ROOT / "addons/smart_construction_core/services/project_execution_service.py",
    ROOT / "addons/smart_construction_core/services/cost_tracking_service.py",
    ROOT / "addons/smart_construction_core/services/project_plan_bootstrap_service.py",
]

READ_SIDE_FORBIDDEN_PATTERNS = [
    re.compile(r"getattr\s*\(\s*getattr\s*\(\s*project\s*,\s*[\"']stage_id[\"']"),
    re.compile(r"_safe_rel_name\s*\(\s*project\s*,\s*[\"']stage_id[\"']\s*\)"),
    re.compile(r"\bproject\.stage_id\b"),
]

REQUIRED_PROJECT_SERVICE_TOKENS = {
    "project_state_explain_service.py": ["def lifecycle_state_label", "LIFECYCLE_STATE_LABELS"],
    "project_dashboard_service.py": ["lifecycle_state_label(project)"],
    "project_header_builder.py": ["lifecycle_state_label(project)"],
    "base.py": ["lifecycle_state_label(project"],
    "project_context_contract.py": ["lifecycle_state_label(stage"],
    "project_insight_service.py": ["lifecycle_state_label(project"],
    "project_execution_service.py": ["lifecycle_state_label(project)"],
    "cost_tracking_service.py": ["lifecycle_state_label(project)"],
    "project_plan_bootstrap_service.py": ["lifecycle_state_label(project)"],
}

ALLOWED_STAGE_ID_CONSUMERS = [
    {
        "path": "addons/smart_construction_core/models/core/project_core.py",
        "reason": "write-side lifecycle projection and advisory diagnostics",
    },
    {
        "path": "addons/smart_construction_core/views/core/project_views.xml",
        "reason": "replaces native header stage_id with lifecycle_state and shows legacy_stage fields",
    },
    {
        "path": "addons/smart_construction_core/services/project_execution_builders/project_execution_tasks_builder.py",
        "reason": "project.task stage display, not project.project business state",
    },
    {
        "path": "addons/smart_construction_core/services/project_plan_bootstrap_builders/project_plan_tasks_builder.py",
        "reason": "project.task stage display, not project.project business state",
    },
    {
        "path": "addons/smart_construction_core/handlers/app_catalog.py",
        "reason": "project.task todo badge uses project.task.stage_id.fold",
    },
]


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _line_hits(path: Path, patterns: list[re.Pattern[str]]) -> list[dict[str, object]]:
    hits = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            if pattern.search(line):
                hits.append(
                    {
                        "path": _relative(path),
                        "line": lineno,
                        "pattern": pattern.pattern,
                        "text": line.strip(),
                    }
                )
    return hits


def main() -> int:
    failures: list[str] = []
    forbidden_hits: list[dict[str, object]] = []
    token_results: dict[str, dict[str, bool]] = {}

    for path in PROJECT_SERVICE_FILES:
        if not path.exists():
            failures.append(f"missing file: {_relative(path)}")
            continue
        forbidden_hits.extend(_line_hits(path, READ_SIDE_FORBIDDEN_PATTERNS))
        tokens = REQUIRED_PROJECT_SERVICE_TOKENS.get(path.name, [])
        text = path.read_text(encoding="utf-8")
        token_results[_relative(path)] = {token: token in text for token in tokens}

    for path, results in token_results.items():
        missing = [token for token, present in results.items() if not present]
        if missing:
            failures.append(f"{path} missing lifecycle-state token(s): {', '.join(missing)}")

    for hit in forbidden_hits:
        failures.append(
            "{path}:{line} forbidden project.stage_id read-side consumer: {text}".format(**hit)
        )

    artifact = {
        "guard": "project_state_read_side_guard",
        "passed": not failures,
        "forbidden_hits": forbidden_hits,
        "token_results": token_results,
        "allowed_stage_id_consumers": ALLOWED_STAGE_ID_CONSUMERS,
        "failures": failures,
    }

    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    ARTIFACT_MD.write_text(
        "# project_state_read_side_guard\n\n"
        + ("PASS\n" if not failures else "FAIL\n")
        + "\n## Allowed stage_id consumers\n"
        + "\n".join(f"- `{row['path']}`: {row['reason']}" for row in ALLOWED_STAGE_ID_CONSUMERS)
        + "\n\n## Failures\n"
        + ("\n".join(f"- {failure}" for failure in failures) if failures else "- none")
        + "\n",
        encoding="utf-8",
    )

    if failures:
        print("[project_state_read_side_guard] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("[project_state_read_side_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
