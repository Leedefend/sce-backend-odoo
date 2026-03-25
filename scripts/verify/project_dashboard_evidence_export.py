#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
MAPPING = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"
ORCHESTRATOR = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
HANDLER = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_dashboard.py"
OUT = ROOT / "tmp" / "project_dashboard_verification_evidence_v1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_zone_blocks_from_orchestrator():
    tree = ast.parse(ORCHESTRATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProjectDashboardContractOrchestrator":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "ZONE_BLOCKS":
                            rows = ast.literal_eval(stmt.value)
                            return [
                                {
                                    "zone": r[0],
                                    "zone_title": r[1],
                                    "zone_type": r[2],
                                    "display_mode": r[3],
                                    "block_key": r[4],
                                }
                                for r in rows
                            ]
    raise SystemExit("unable to parse ZONE_BLOCKS from orchestrator")


def main():
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    zones = _load_zone_blocks_from_orchestrator()
    data = snapshot.get("data") or {}
    route_ctx = data.get("route_context") or {}
    project_context = data.get("project_context") or {}

    evidence = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scene_key": (data.get("scene") or {}).get("key"),
        "page_key": (data.get("page") or {}).get("key"),
        "intent": (snapshot.get("meta") or {}).get("intent"),
        "contract_version": (snapshot.get("meta") or {}).get("contract_version"),
        "route_primary_protocol": route_ctx.get("primary_protocol"),
        "route_context_transport": route_ctx.get("context_transport"),
        "zone_count_snapshot": len(data.get("zones") or {}),
        "zone_count_service": len(zones),
        "zone_service_matrix": zones,
        "mapping_rows": len(mapping.get("mappings") or []),
        "project_context_keys": sorted(str(key) for key in project_context.keys()),
        "checksums": {
            "snapshot_sha256": _sha256(SNAPSHOT),
            "mapping_sha256": _sha256(MAPPING),
            "orchestrator_sha256": _sha256(ORCHESTRATOR),
            "handler_sha256": _sha256(HANDLER),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[verify.project.dashboard.evidence] exported: {OUT}")


if __name__ == "__main__":
    main()
