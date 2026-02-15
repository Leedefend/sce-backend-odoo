#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MENU_DIR = ROOT / "artifacts" / "codex" / "portal-menu-scene-resolve"
DEFAULT_OUT_JSON = ROOT / "artifacts" / "audit" / "nav_alignment_report.latest.json"
DEFAULT_OUT_MD = ROOT / "artifacts" / "audit" / "nav_alignment_report.latest.md"
DEFAULT_ACTION_MISSING = ROOT / "docs" / "audit" / "action_groups_missing_db.csv"
DEFAULT_ACTION_VIS = ROOT / "docs" / "audit" / "action_visibility_by_role.csv"
DEFAULT_ACTION_VERDICTS = ROOT / "docs" / "audit" / "action_verdict_candidates.csv"
DEFAULT_OBJECT_VERDICTS = ROOT / "docs" / "audit" / "object_verdict_candidates.csv"
DEFAULT_ENFORCE_PREFIXES = (
    "smart_construction_core.",
    "smart_construction_demo.",
    "smart_construction_portal.",
)


@dataclass
class MenuResolveResult:
    summary: dict[str, Any]
    failures: list[dict[str, Any]]
    latest_json: str


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _latest_menu_json(menu_dir: Path) -> Path | None:
    if not menu_dir.exists():
        return None
    candidates: list[Path] = []
    for child in menu_dir.iterdir():
        if child.is_dir():
            payload = child / "menu_scene_resolve.json"
            if payload.exists():
                candidates.append(payload)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.parent.name)
    return candidates[-1]


def _load_menu_resolve(menu_dir: Path) -> MenuResolveResult:
    latest = _latest_menu_json(menu_dir)
    if not latest:
        return MenuResolveResult(summary={}, failures=[], latest_json="")
    data = json.loads(latest.read_text(encoding="utf-8"))
    return MenuResolveResult(
        summary=data.get("summary") or {},
        failures=data.get("failures") or [],
        latest_json=str(latest.relative_to(ROOT)),
    )


def _top_rows(rows: list[dict[str, str]], limit: int = 12) -> list[dict[str, str]]:
    return rows[:limit]


def _truthy(v: str | None) -> bool:
    return str(v or "").strip() in {"1", "true", "True", "yes", "YES"}


def _enforce_prefixes() -> tuple[str, ...]:
    raw = (os.getenv("NAV_ALIGNMENT_ENFORCE_PREFIXES") or "").strip()
    if not raw:
        return DEFAULT_ENFORCE_PREFIXES
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return tuple(items) if items else DEFAULT_ENFORCE_PREFIXES


def _in_scope(xmlid: str, prefixes: tuple[str, ...]) -> bool:
    if not xmlid:
        return False
    return any(xmlid.startswith(p) for p in prefixes)


def build_report() -> dict[str, Any]:
    prefixes = _enforce_prefixes()
    menu = _load_menu_resolve(DEFAULT_MENU_DIR)
    action_missing_all = _read_csv(DEFAULT_ACTION_MISSING)
    action_vis = _read_csv(DEFAULT_ACTION_VIS)
    action_verdicts = _read_csv(DEFAULT_ACTION_VERDICTS)
    object_verdicts = _read_csv(DEFAULT_OBJECT_VERDICTS)
    action_missing = [
        r
        for r in action_missing_all
        if _in_scope((r.get("xmlid") or "").strip(), prefixes)
    ]

    unguarded_visible_by_role: dict[str, int] = {}
    unguarded_visible_total = 0
    for row in action_vis:
        xmlid = (row.get("action_xmlid") or "").strip()
        if not _in_scope(xmlid, prefixes):
            continue
        role = (row.get("role") or "").strip() or "unknown"
        if _truthy(row.get("visible")) and not _truthy(row.get("has_groups")):
            unguarded_visible_by_role[role] = unguarded_visible_by_role.get(role, 0) + 1
            unguarded_visible_total += 1

    blockers: list[str] = []
    if int(menu.summary.get("failures", 0) or 0) > 0:
        blockers.append("menu_scene_unresolved")
    if len(action_missing) > 0:
        blockers.append("actions_missing_groups")

    warnings: list[str] = []
    if unguarded_visible_total > 0:
        warnings.append("unguarded_actions_visible")

    return {
        "status": "block" if blockers else "pass",
        "blockers": blockers,
        "warnings": warnings,
        "menu_scene_resolve": {
            "latest_json": menu.latest_json,
            "summary": menu.summary,
            "failure_samples": _top_rows(menu.failures, limit=10),
        },
        "actions": {
            "enforce_prefixes": list(prefixes),
            "missing_groups_count_all": len(action_missing_all),
            "missing_groups_count": len(action_missing),
            "missing_groups_samples": _top_rows(action_missing, limit=10),
            "unguarded_visible_total": unguarded_visible_total,
            "unguarded_visible_by_role": unguarded_visible_by_role,
        },
        "recommendations": {
            "action_verdict_count": len(action_verdicts),
            "action_verdict_samples": _top_rows(action_verdicts, limit=15),
            "object_verdict_count": len(object_verdicts),
            "object_verdict_samples": _top_rows(object_verdicts, limit=15),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    menu = report["menu_scene_resolve"]
    actions = report["actions"]
    rec = report["recommendations"]
    lines = [
        "# Navigation Alignment Report",
        "",
        f"- status: `{report['status']}`",
        f"- blockers: `{', '.join(report['blockers']) or '-'}`",
        f"- warnings: `{', '.join(report['warnings']) or '-'}`",
        "",
        "## Menu -> Scene",
        f"- source: `{menu.get('latest_json') or 'missing'}`",
        f"- failures: `{(menu.get('summary') or {}).get('failures', 'n/a')}`",
        f"- coverage: `{(menu.get('summary') or {}).get('coverage', 'n/a')}`",
        f"- effective_total: `{(menu.get('summary') or {}).get('effective_total', 'n/a')}`",
        "",
        "## Action Guarding",
        f"- enforce_prefixes: `{','.join(actions.get('enforce_prefixes') or [])}`",
        f"- actions_missing_groups_all: `{actions.get('missing_groups_count_all', 0)}`",
        f"- actions_missing_groups: `{actions.get('missing_groups_count', 0)}`",
        f"- unguarded_visible_total: `{actions.get('unguarded_visible_total', 0)}`",
        f"- unguarded_visible_by_role: `{json.dumps(actions.get('unguarded_visible_by_role') or {}, ensure_ascii=False)}`",
        "",
        "## Suggestions",
        f"- action_verdict_candidates: `{rec.get('action_verdict_count', 0)}`",
        f"- object_verdict_candidates: `{rec.get('object_verdict_count', 0)}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report()
    DEFAULT_OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    DEFAULT_OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(str(DEFAULT_OUT_JSON.relative_to(ROOT)))
    print(str(DEFAULT_OUT_MD.relative_to(ROOT)))
    print(f"[nav.alignment] status={report['status']} blockers={len(report['blockers'])} warnings={len(report['warnings'])}")


if __name__ == "__main__":
    main()
