#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"
SCOPE_ZH = ROOT / "docs/releases/release_scope_v1.md"
SCOPE_EN = ROOT / "docs/releases/release_scope_v1.en.md"
BOARD_ZH = ROOT / "docs/releases/construction_system_v1_execution_board.md"
BOARD_EN = ROOT / "docs/releases/construction_system_v1_execution_board.en.md"
SCENE_XML = ROOT / "addons/smart_construction_scene/data/sc_scene_orchestration.xml"
PROJECT_SCENE_XML = ROOT / "addons/smart_construction_scene/data/project_management_scene.xml"
OUT_MD = ROOT / "artifacts/release/phase1_navigation_convergence.md"

PRIMARY_NAV_SCENES = [
    "my_work.workspace",
    "projects.ledger",
    "project.management",
    "contracts.workspace",
    "cost.analysis",
    "finance.workspace",
    "risk.center",
]
COMPAT_NAV_SCENES = {"workspace.home", "projects.list", "projects.intake"}
HIDDEN_PREFIXES = ("config.", "data.", "internal.")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(errors: list[str]) -> int:
    print("[release_phase1_navigation_convergence_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _contains_all(text: str, tokens: list[str], *, label: str, errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing tokens: {', '.join(missing)}")


def _validate_policy(errors: list[str]) -> dict[str, Any]:
    payload = _load_json(POLICY)
    if payload.get("default_surface") != "construction_pm_v1":
        errors.append("delivery policy default_surface must be construction_pm_v1")
    surfaces = payload.get("surfaces") if isinstance(payload.get("surfaces"), dict) else {}
    surface = surfaces.get("construction_pm_v1") if isinstance(surfaces.get("construction_pm_v1"), dict) else {}
    nav = surface.get("nav_allowlist") if isinstance(surface.get("nav_allowlist"), list) else []
    nav_keys = [str(item) for item in nav]
    if not nav_keys:
        errors.append("construction_pm_v1.nav_allowlist must be present")

    missing_primary = [key for key in PRIMARY_NAV_SCENES if key not in nav_keys]
    if missing_primary:
        errors.append(f"primary navigation scenes missing from policy: {', '.join(missing_primary)}")
    extra = sorted(set(nav_keys) - set(PRIMARY_NAV_SCENES))
    invalid_extra = [key for key in extra if key not in COMPAT_NAV_SCENES]
    if invalid_extra:
        errors.append(f"nav_allowlist has non-primary, non-compat entries: {', '.join(invalid_extra)}")
    hidden = [key for key in nav_keys if key.startswith(HIDDEN_PREFIXES)]
    if hidden:
        errors.append(f"hidden-prefix scenes must not be in primary nav policy: {', '.join(hidden)}")
    if len(PRIMARY_NAV_SCENES) != 7:
        errors.append("primary navigation baseline must contain exactly 7 scenes")
    if "project.management" not in nav_keys:
        errors.append("project.management must be directly reachable from navigation policy")
    return {"nav_keys": nav_keys, "extra": extra}


def _validate_docs(errors: list[str]) -> None:
    scope_zh = _read_text(SCOPE_ZH)
    scope_en = _read_text(SCOPE_EN)
    board_zh = _read_text(BOARD_ZH)
    board_en = _read_text(BOARD_EN)

    for text, label in ((scope_zh, "release_scope_v1.md"), (scope_en, "release_scope_v1.en.md")):
        _contains_all(text, PRIMARY_NAV_SCENES, label=label, errors=errors)
        _contains_all(text, ["construction_pm_v1", "config.*", "data.*", "internal.*"], label=label, errors=errors)
    if "| Phase 1 | 导航收口 | DONE |" not in board_zh:
        errors.append("Chinese execution board must mark Phase 1 navigation convergence DONE")
    if "| Phase 1 | Navigation convergence | DONE |" not in board_en:
        errors.append("English execution board must mark Phase 1 navigation convergence DONE")
    for task in ("W1-01", "W1-02"):
        if not any(task in line and "| P1 | DONE |" in line for line in board_zh.splitlines()):
            errors.append(f"Chinese execution board missing DONE evidence for {task}")
        if not any(task in line and "| P1 | DONE |" in line for line in board_en.splitlines()):
            errors.append(f"English execution board missing DONE evidence for {task}")


def _validate_scene_sources(errors: list[str]) -> None:
    scene_text = _read_text(SCENE_XML)
    project_text = _read_text(PROJECT_SCENE_XML)
    _contains_all(scene_text, PRIMARY_NAV_SCENES, label="sc_scene_orchestration.xml", errors=errors)
    _contains_all(project_text, ["project.management", "/s/project.management"], label="project_management_scene.xml", errors=errors)


def _write_report(policy_summary: dict[str, Any]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 1 Navigation Convergence Evidence",
        "",
        "- status: PASS",
        "- default_surface: `construction_pm_v1`",
        f"- primary_nav_scene_count: `{len(PRIMARY_NAV_SCENES)}`",
        "- primary_nav_scenes:",
        *[f"  - `{key}`" for key in PRIMARY_NAV_SCENES],
        "- compatible_nav_entries:",
        *[f"  - `{key}`" for key in policy_summary.get("extra", [])],
        "- hidden_prefixes_excluded_from_primary_nav: `config.*`, `data.*`, `internal.*`",
        "- direct_project_management_route: `/s/project.management`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    for path in (POLICY, SCOPE_ZH, SCOPE_EN, BOARD_ZH, BOARD_EN, SCENE_XML, PROJECT_SCENE_XML):
        if not path.is_file():
            errors.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    try:
        policy_summary = _validate_policy(errors)
        _validate_docs(errors)
        _validate_scene_sources(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report(policy_summary)
    print("[release_phase1_navigation_convergence_guard] PASS")
    print(f"[release_phase1_navigation_convergence_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
