#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLOW_REPORT = ROOT / "tmp" / "project_management_productization_flow_report.json"
SNAPSHOT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
EVIDENCE = ROOT / "tmp" / "project_dashboard_verification_evidence_v1.json"
OUT_JSON = ROOT / "tmp" / "project_management_scene_v0_1_acceptance_report.json"
OUT_MD = ROOT / "tmp" / "project_management_scene_v0_1_acceptance_report.md"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    flow = _load(FLOW_REPORT)
    snapshot = _load(SNAPSHOT)
    evidence = _load(EVIDENCE)

    flow_ok = (flow.get("status") or "").lower() == "pass"
    data = snapshot.get("data") or {}
    meta = snapshot.get("meta") or {}
    zones = data.get("zones") or {}

    checks = [
        ("flow_report_pass", flow_ok, "productization flow status"),
        ("snapshot_scene_key", (data.get("scene") or {}).get("key") == "project.management", "scene.key"),
        ("snapshot_page_key", (data.get("page") or {}).get("key") == "project.management.dashboard", "page.key"),
        ("snapshot_zone_count_7", len(zones) == 7, "zones count"),
        ("snapshot_intent", (meta.get("intent") or "") == "project.dashboard", "meta.intent"),
        ("snapshot_contract_version", (meta.get("contract_version") or "") == "v1", "meta.contract_version"),
        ("snapshot_project_context_present", isinstance(data.get("project_context"), dict), "data.project_context"),
        (
            "route_protocol_fixed",
            ((data.get("route_context") or {}).get("primary_protocol") == "/s/project.management"),
            "route_context.primary_protocol",
        ),
        (
            "route_context_transport_fixed",
            ((data.get("route_context") or {}).get("context_transport") == "scene_payload.project_context"),
            "route_context.context_transport",
        ),
        ("evidence_mapping_rows_7", evidence.get("mapping_rows") == 7, "evidence.mapping_rows"),
        ("evidence_zone_count_service_7", evidence.get("zone_count_service") == 7, "evidence.zone_count_service"),
    ]

    failed = [c for c in checks if not c[1]]
    status = "pass" if not failed else "fail"

    report = {
        "scene_key": "project.management",
        "version": "v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
        "inputs": {
            "flow_report": str(FLOW_REPORT),
            "snapshot": str(SNAPSHOT),
            "evidence": str(EVIDENCE),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# project.management scene v0.1 acceptance report",
        "",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- status: **{status.upper()}**",
        f"- checks: {report['summary']['passed']}/{report['summary']['total']} passed",
        "",
        "## Checks",
    ]
    for item in report["checks"]:
        lines.append(f"- [{'PASS' if item['ok'] else 'FAIL'}] {item['name']} ({item['detail']})")
    lines.extend(
        [
            "",
            "## Inputs",
            f"- {FLOW_REPORT}",
            f"- {SNAPSHOT}",
            f"- {EVIDENCE}",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if status != "pass":
        print("[verify.project.management.acceptance] FAIL")
        raise SystemExit(1)

    print("[verify.project.management.acceptance] PASS")
    print(f"[verify.project.management.acceptance] report: {OUT_JSON}")


if __name__ == "__main__":
    main()
