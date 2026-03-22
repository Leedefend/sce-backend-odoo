#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "five_layer_workspace_audit.json"

SERVICE_FILES = [
    "addons/smart_construction_core/services/project_dashboard_service.py",
    "addons/smart_construction_core/services/project_plan_bootstrap_service.py",
    "addons/smart_construction_core/services/project_execution_service.py",
]
FRONTEND_FILES = [
    "frontend/apps/web/src/views/ProjectManagementDashboardView.vue",
]
SHADOW_PATH_PATTERNS = [
    re.compile(r"^addons/smart_construction_core/(handlers|services)/project_(payment|contract|cost)"),
    re.compile(r"^scripts/verify/product_project_(payment|contract|cost)"),
]
SHADOW_TOKEN = re.compile(r"project\.(payment|contract|cost)\.")
FRONTEND_SCENE_BRANCH = re.compile(r"currentEntryIntent\.value === 'project\.[^']+\.enter'|intent === 'project\.[^']+\.enter'")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _line_of(text: str, match_start: int) -> int:
    return text[:match_start].count("\n") + 1


def _git_changed_paths() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    out: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            out.append(path)
    return out


def main() -> int:
    findings: list[dict] = []

    for rel in SERVICE_FILES:
        path = ROOT / rel
        text = _read(path)
        if not text:
            continue
        if "def build_entry(" in text and "runtime_fetch_hints" in text and '"blocks"' in text:
            findings.append(
                {
                    "rule": "scene_assembly_in_domain_service",
                    "severity": "high",
                    "path": rel,
                    "message": "service is assembling scene-entry payload inside domain addon service",
                }
            )

    for rel in FRONTEND_FILES:
        path = ROOT / rel
        text = _read(path)
        if not text:
            continue
        for match in FRONTEND_SCENE_BRANCH.finditer(text):
            findings.append(
                {
                    "rule": "frontend_scene_intent_branch",
                    "severity": "high",
                    "path": rel,
                    "line": _line_of(text, match.start()),
                    "message": f"frontend branches on concrete scene intent `{match.group(0)}`",
                }
            )

    changed_paths = _git_changed_paths()
    scan_paths = set(changed_paths)
    scan_paths.update(SERVICE_FILES)
    scan_paths.update(FRONTEND_FILES)

    for rel in sorted(scan_paths):
        path = ROOT / rel
        if not path.is_file():
            continue
        if not (
            rel.startswith("addons/")
            or rel.startswith("frontend/")
            or rel.startswith("scripts/verify/")
        ):
            continue
        if any(pattern.search(rel) for pattern in SHADOW_PATH_PATTERNS):
            findings.append(
                {
                    "rule": "shadow_project_domain_path",
                    "severity": "high",
                    "path": rel,
                    "message": "path indicates project-scoped shadow business scene implementation",
                }
            )
        text = _read(path)
        if not text:
            continue
        match = SHADOW_TOKEN.search(text)
        if match:
            findings.append(
                {
                    "rule": "shadow_project_domain_intent",
                    "severity": "high",
                    "path": rel,
                    "line": _line_of(text, match.start()),
                    "message": f"found shadow intent token `{match.group(0)}`",
                }
            )

    summary = {
        "finding_count": len(findings),
        "blocked": bool(findings),
        "focus": [
            "business_truth_reuse",
            "orchestration_layer_extraction",
            "frontend_contract_consumption",
        ],
    }
    report = {"status": "BLOCKED" if findings else "PASS", "summary": summary, "findings": findings}
    _write_json(OUT_JSON, report)

    if findings:
        print("[five_layer_workspace_audit] BLOCKED")
        for item in findings[:15]:
            path = item.get("path") or "-"
            line = item.get("line")
            suffix = f":{line}" if line else ""
            print(f" - {path}{suffix} {item.get('rule')}: {item.get('message')}")
        return 1

    print("[five_layer_workspace_audit] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
