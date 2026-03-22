#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "tmp" / "project_management_productization_flow_report.json"
OUT_MD = ROOT / "tmp" / "project_management_productization_flow_report.md"


def _exists(path: Path) -> bool:
    return path.exists()


def _builder_count() -> int:
    path = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"
    return len(list(path.glob("project_*_builder.py")))


def _orchestrator_zone_count() -> int:
    service = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
    tree = ast.parse(service.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProjectDashboardContractOrchestrator":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "ZONE_BLOCKS":
                            rows = ast.literal_eval(stmt.value)
                            return len(rows)
    return 0


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    checks = []

    scene_xml = ROOT / "addons" / "smart_construction_scene" / "data" / "project_management_scene.xml"
    handler_py = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_dashboard.py"
    service_py = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_service.py"
    orchestrator_py = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
    mapping_json = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"
    route_doc = ROOT / "docs" / "ops" / "project_management_scene_route_context_v1.md"
    contract_doc = ROOT / "docs" / "contract" / "project_dashboard_contract_v1.md"
    block_doc = ROOT / "docs" / "contract" / "project_management_block_contract_v1.md"
    snapshot_json = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
    evidence_json = ROOT / "tmp" / "project_dashboard_verification_evidence_v1.json"

    checks.append(("scene_xml_exists", _exists(scene_xml), str(scene_xml)))
    checks.append(("handler_exists", _exists(handler_py), str(handler_py)))
    checks.append(("service_exists", _exists(service_py), str(service_py)))
    checks.append(("orchestrator_exists", _exists(orchestrator_py), str(orchestrator_py)))
    checks.append(("mapping_v2_exists", _exists(mapping_json), str(mapping_json)))
    checks.append(("route_doc_exists", _exists(route_doc), str(route_doc)))
    checks.append(("contract_doc_exists", _exists(contract_doc), str(contract_doc)))
    checks.append(("block_doc_exists", _exists(block_doc), str(block_doc)))
    checks.append(("snapshot_exists", _exists(snapshot_json), str(snapshot_json)))
    checks.append(("evidence_exists", _exists(evidence_json), str(evidence_json)))

    checks.append(("builder_count_gte_7", _builder_count() >= 7, f"count={_builder_count()}"))
    checks.append(("orchestrator_zone_count_is_7", _orchestrator_zone_count() == 7, f"count={_orchestrator_zone_count()}"))

    snapshot = _load_json(snapshot_json)
    snap_data = snapshot.get("data") if isinstance(snapshot, dict) else {}
    snap_meta = snapshot.get("meta") if isinstance(snapshot, dict) else {}
    checks.append(("snapshot_scene_key", (snap_data or {}).get("scene", {}).get("key") == "project.management", "scene.key"))
    checks.append(("snapshot_page_key", (snap_data or {}).get("page", {}).get("key") == "project.management.dashboard", "page.key"))
    checks.append(("snapshot_zone_count", len((snap_data or {}).get("zones") or {}) == 7, "zones==7"))
    checks.append(("snapshot_intent", (snap_meta or {}).get("intent") == "project.dashboard", "meta.intent"))
    checks.append(("snapshot_contract_version", (snap_meta or {}).get("contract_version") == "v1", "meta.contract_version"))

    evidence = _load_json(evidence_json)
    checks.append(("evidence_zone_count_snapshot", (evidence.get("zone_count_snapshot") == 7), "evidence.zone_count_snapshot"))
    checks.append(("evidence_zone_count_service", (evidence.get("zone_count_service") == 7), "evidence.zone_count_service"))
    checks.append(("evidence_mapping_rows", (evidence.get("mapping_rows") == 7), "evidence.mapping_rows"))
    checks.append(
        ("evidence_route_protocol", evidence.get("route_primary_protocol") == "/s/project.management?project_id=<id>", "evidence.route_primary_protocol")
    )

    passed = [c for c in checks if c[1]]
    failed = [c for c in checks if not c[1]]
    status = "pass" if not failed else "fail"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "total": len(checks),
            "passed": len(passed),
            "failed": len(failed),
        },
        "checks": [
            {"name": name, "ok": ok, "detail": detail}
            for name, ok, detail in checks
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# project.management productization flow report",
        "",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- status: **{status.upper()}**",
        f"- checks: {len(passed)}/{len(checks)} passed",
        "",
        "## Check Results",
    ]
    for item in report["checks"]:
        mark = "PASS" if item["ok"] else "FAIL"
        lines.append(f"- [{mark}] {item['name']} ({item['detail']})")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if failed:
        print(f"[verify.project.management.productization] FAIL ({len(failed)} checks)")
        raise SystemExit(1)

    print("[verify.project.management.productization] PASS")
    print(f"[verify.project.management.productization] report: {OUT_JSON}")


if __name__ == "__main__":
    main()
