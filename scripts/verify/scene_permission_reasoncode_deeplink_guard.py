#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_CAPABILITY_REPORT = ROOT / "artifacts" / "backend" / "release_capability_report.json"
SCENE_SHAPE_GUARD = ROOT / "artifacts" / "scene_contract_shape_guard.json"
DELIVERY_POLICY = ROOT / "docs" / "product" / "delivery" / "v1" / "construction_pm_v1_scene_surface_policy.json"
SNAPSHOT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "scene_permission_reasoncode_deeplink_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "scene_permission_reasoncode_deeplink_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    summary: dict = {
        "acl_runtime_probe_count": 0,
        "permission_denied_count": 0,
        "scene_shape_ok": False,
        "deeplink_contains_project_management": False,
        "route_context_equivalent": False,
    }

    report = _load_json(RELEASE_CAPABILITY_REPORT)
    probes = report.get("acl_runtime_probe") if isinstance(report.get("acl_runtime_probe"), list) else []
    denied = [
        row
        for row in probes
        if isinstance(row, dict)
        and str(row.get("error_code") or "").strip() == "PERMISSION_DENIED"
        and int(row.get("status") or 0) == 403
    ]
    summary["acl_runtime_probe_count"] = len(probes)
    summary["permission_denied_count"] = len(denied)
    if len(denied) <= 0:
        errors.append("release capability report has no runtime PERMISSION_DENIED samples")

    shape = _load_json(SCENE_SHAPE_GUARD)
    shape_ok = bool(shape.get("ok") is True)
    summary["scene_shape_ok"] = shape_ok
    if not shape_ok:
        errors.append("scene contract shape guard is not PASS")

    policy = _load_json(DELIVERY_POLICY)
    scene_links: list[str] = []
    nav_links: list[str] = []
    surfaces = policy.get("surfaces") if isinstance(policy.get("surfaces"), dict) else {}
    current = surfaces.get("construction_pm_v1") if isinstance(surfaces.get("construction_pm_v1"), dict) else {}
    if isinstance(current.get("deep_link_allowlist"), list):
        scene_links = [str(x).strip() for x in current.get("deep_link_allowlist") if str(x).strip()]
    if isinstance(current.get("nav_allowlist"), list):
        nav_links = [str(x).strip() for x in current.get("nav_allowlist") if str(x).strip()]
    required_link = "/s/project.management?project_id=<id>"
    summary["deeplink_contains_project_management"] = (
        "project.management" in scene_links or "project.management" in nav_links
    )
    if "project.management" not in scene_links and "project.management" not in nav_links:
        errors.append("delivery policy missing project.management in deep-link/nav allowlist")

    snapshot = _load_json(SNAPSHOT)
    route_context = (
        ((snapshot.get("data") or {}).get("route_context"))
        if isinstance(snapshot.get("data"), dict)
        else {}
    )
    route_equivalent = (
        str(route_context.get("primary_protocol") or "").strip() == required_link
        and str(route_context.get("scene_route") or "").strip() == "/s/project.management"
    )
    summary["route_context_equivalent"] = bool(route_equivalent)
    if not route_equivalent:
        errors.append("project dashboard route_context does not match deep-link policy")

    output = {
        "ok": len(errors) == 0,
        "summary": summary,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Scene Permission ReasonCode + DeepLink Guard",
        "",
        f"- status: {'PASS' if output['ok'] else 'FAIL'}",
        f"- acl_runtime_probe_count: {summary['acl_runtime_probe_count']}",
        f"- permission_denied_count: {summary['permission_denied_count']}",
        f"- scene_shape_ok: {summary['scene_shape_ok']}",
        f"- deeplink_contains_project_management: {summary['deeplink_contains_project_management']}",
        f"- route_context_equivalent: {summary['route_context_equivalent']}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[scene_permission_reasoncode_deeplink_guard] FAIL")
        return 1
    print("[scene_permission_reasoncode_deeplink_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
