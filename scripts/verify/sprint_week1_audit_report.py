#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAP_USAGE_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
SCENE_DOMAIN_JSON = ROOT / "artifacts" / "backend" / "scene_domain_map.json"
BUTTON_SEM_JSON = ROOT / "artifacts" / "backend" / "button_semantic_report.json"
ROLE_DIFF_JSON = ROOT / "artifacts" / "backend" / "role_capability_diff_report.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "sprint_week1_audit_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "sprint_week1_audit_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    cap_usage = _load(CAP_USAGE_JSON)
    scene_domain = _load(SCENE_DOMAIN_JSON)
    button_sem = _load(BUTTON_SEM_JSON)
    role_diff = _load(ROLE_DIFF_JSON)

    dormant_count = int(((cap_usage.get("summary") or {}).get("isolated_count")) or 0)
    structural_only = int(((cap_usage.get("summary") or {}).get("structural_only_count")) or 0)
    unresolved_intent = int(((cap_usage.get("summary") or {}).get("unresolved_intent_count")) or 0)
    missing_cap_ref = int(((cap_usage.get("summary") or {}).get("missing_capability_ref_count")) or 0)
    orphan_count = structural_only + unresolved_intent + missing_cap_ref
    unclassified_404 = int(((button_sem.get("summary") or {}).get("unclassified_404_count")) or 0)
    unassigned_scene = int(((scene_domain.get("summary") or {}).get("unassigned_scene_count")) or 0)
    role_samples = int(((role_diff.get("summary") or {}).get("role_sample_count")) or ((role_diff.get("summary") or {}).get("profile_count")) or 0)

    checks = {
        "orphan_capability_eq_0": orphan_count == 0,
        "unclassified_404_eq_0": unclassified_404 == 0,
        "all_scene_assigned": unassigned_scene == 0,
        "role_sample_ge_8": role_samples >= 8,
    }
    if not checks["orphan_capability_eq_0"]:
        errors.append(f"orphan_capability_count={orphan_count}")
    if not checks["unclassified_404_eq_0"]:
        errors.append(f"unclassified_404_count={unclassified_404}")
    if not checks["all_scene_assigned"]:
        errors.append(f"unassigned_scene_count={unassigned_scene}")
    if not checks["role_sample_ge_8"]:
        errors.append(f"role_sample_count={role_samples} (<8)")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "orphan_capability_count": orphan_count,
            "dormant_capability_count": dormant_count,
            "unclassified_404_count": unclassified_404,
            "unassigned_scene_count": unassigned_scene,
            "role_sample_count": role_samples,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Sprint Week1 Audit Report",
        "",
        f"- orphan_capability_count: {orphan_count}",
        f"- dormant_capability_count: {dormant_count}",
        f"- unclassified_404_count: {unclassified_404}",
        f"- unassigned_scene_count: {unassigned_scene}",
        f"- role_sample_count: {role_samples}",
        f"- error_count: {len(errors)}",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[sprint_week1_audit_report] FAIL")
        return 2
    print("[sprint_week1_audit_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
