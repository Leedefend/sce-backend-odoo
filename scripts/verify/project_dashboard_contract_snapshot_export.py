#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
BUILDERS_DIR = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"
OUT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"


def _load_zone_blocks():
    tree = ast.parse(ORCHESTRATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProjectDashboardContractOrchestrator":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "ZONE_BLOCKS":
                            rows = ast.literal_eval(stmt.value)
                            out = []
                            for key, title, zone_type, display_mode, block_key in rows:
                                out.append(
                                    {
                                        "zone_key": f"zone.{key}",
                                        "title": title,
                                        "zone_type": zone_type,
                                        "display_mode": display_mode,
                                        "block_key": block_key,
                                    }
                                )
                            return out
    raise SystemExit("ZONE_BLOCKS not found")


def _load_builder_types():
    out = {}
    for py in BUILDERS_DIR.glob("project_*_builder.py"):
        text = py.read_text(encoding="utf-8")
        key = ""
        btype = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("block_key = "):
                key = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("block_type = "):
                btype = line.split("=", 1)[1].strip().strip('"')
        if key and btype:
            out[key] = btype
    required = {
        "block.project.header",
        "block.project.metrics",
        "block.project.progress",
        "block.project.contract",
        "block.project.cost",
        "block.project.finance",
        "block.project.risk",
    }
    if not required.issubset(set(out.keys())):
        raise SystemExit("required dashboard builder set incomplete for snapshot")
    return out


def main():
    zones = _load_zone_blocks()
    block_types = _load_builder_types()

    contract = {
        "ok": True,
        "data": {
            "scene": {"key": "project.management", "page": "project.management.dashboard"},
            "page": {"key": "project.management.dashboard", "title": "项目管理控制台", "route": "/s/project.management"},
            "route_context": {
                "primary_protocol": "/s/project.management",
                "scene_route": "/s/project.management",
                "context_transport": "scene_payload.project_context",
                "project_route_template": "/s/project.management",
                "project_route": "/s/project.management",
            },
            "project_context": {
                "project_id": 123,
                "project_name": "DEMO PROJECT",
                "stage": "executing",
                "stage_label": "执行中",
                "milestone": "execution_started",
                "milestone_label": "已开工",
                "status": "healthy",
            },
            "project": {
                "id": 123,
                "name": "DEMO PROJECT",
                "project_code": "DEMO-001",
                "partner_name": "",
                "manager_name": "",
                "stage_name": "",
                "state": "ready",
                "date": "2026-03-10",
            },
            "zones": {},
        },
        "meta": {
            "intent": "project.dashboard",
            "trace_id": "snapshot",
            "contract_version": "v1",
        },
    }

    for z in zones:
        block_key = z["block_key"]
        contract["data"]["zones"][z["zone_key"].split(".", 1)[1]] = {
            "zone_key": z["zone_key"],
            "title": z["title"],
            "zone_type": z["zone_type"],
            "display_mode": z["display_mode"],
            "blocks": [
                {
                    "block_key": block_key,
                    "block_type": block_types.get(block_key, "unknown"),
                    "title": z["title"],
                    "state": "ready",
                    "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
                    "data": {},
                    "error": {"code": "", "message": ""},
                }
            ],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[verify.project.dashboard.snapshot] exported: {OUT}")


if __name__ == "__main__":
    main()
