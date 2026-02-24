# -*- coding: utf-8 -*-
from __future__ import annotations

CRITICAL_SCENES = {
    "projects.list",
    "projects.ledger",
}


def scene_severity(scene_key: str | None) -> str:
    if scene_key and scene_key in CRITICAL_SCENES:
        return "critical"
    return "non_critical"


def is_critical_drift_warn(entry: dict) -> bool:
    if not isinstance(entry, dict):
        return False
    if str(entry.get("severity") or "").strip().lower() != "warn":
        return False
    scene_key = entry.get("scene_key")
    return scene_key in CRITICAL_SCENES


def append_resolve_error(resolve_errors, *, scene_key, kind, code, ref=None, message=None, severity=None, field=None):
    entry = {
        "scene_key": scene_key or "",
        "kind": kind,
        "code": code,
        "severity": severity or scene_severity(scene_key),
        "message": message or "",
    }
    if ref:
        entry["ref"] = ref
    if field:
        entry["field"] = field
    resolve_errors.append(entry)


class SceneDriftEngine:
    def evaluate(self, scenes, diagnostics):
        if not isinstance(diagnostics, dict):
            return diagnostics
        diagnostics["drift"] = diagnostics.get("drift") if isinstance(diagnostics.get("drift"), list) else []
        diagnostics["resolve_errors"] = (
            diagnostics.get("resolve_errors") if isinstance(diagnostics.get("resolve_errors"), list) else []
        )
        return diagnostics
