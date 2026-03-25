#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
ORCHESTRATOR = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
BUILDERS_DIR = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"
MAPPING = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _load_zone_blocks():
    tree = ast.parse(ORCHESTRATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProjectDashboardContractOrchestrator":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "ZONE_BLOCKS":
                            rows = ast.literal_eval(stmt.value)
                            return list(rows)
    raise SystemExit("ZONE_BLOCKS not found in orchestrator")


def _load_builder_types():
    out = {}
    for py in BUILDERS_DIR.glob("project_*_builder.py"):
        text = py.read_text(encoding="utf-8")
        block_key = ""
        block_type = ""
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("block_key = "):
                block_key = s.split("=", 1)[1].strip().strip('"')
            if s.startswith("block_type = "):
                block_type = s.split("=", 1)[1].strip().strip('"')
        if block_key and block_type:
            out[block_key] = block_type
    required = {
        "block.project.header",
        "block.project.metrics",
        "block.project.progress",
        "block.project.contract",
        "block.project.cost",
        "block.project.finance",
        "block.project.risk",
    }
    _must(required.issubset(set(out.keys())), "required dashboard builder block_type entries missing")
    return out


def main():
    _must(SNAPSHOT.exists(), "snapshot file missing; run make verify.project.dashboard.snapshot first")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    rows = _load_zone_blocks()
    builder_types = _load_builder_types()
    map_by_zone = {str(r.get("zone_key") or "").split(".", 1)[1]: r for r in (mapping.get("mappings") or [])}

    zones = ((snap.get("data") or {}).get("zones") or {})
    _must(len(zones) == 7, "snapshot zones count must be 7")

    for item in rows:
        zone_name, zone_title, zone_type, display_mode, block_key = item
        _must(zone_name in zones, f"snapshot missing zone: {zone_name}")
        zone = zones[zone_name] or {}
        _must(zone.get("title") == zone_title, f"{zone_name}: title drift in snapshot")
        _must(zone.get("zone_type") == zone_type, f"{zone_name}: zone_type drift in snapshot")
        _must(zone.get("display_mode") == display_mode, f"{zone_name}: display_mode drift in snapshot")
        blocks = zone.get("blocks") or []
        _must(isinstance(blocks, list) and len(blocks) == 1, f"{zone_name}: snapshot blocks shape invalid")
        block = blocks[0] or {}
        _must(block.get("block_key") == block_key, f"{zone_name}: block_key drift in snapshot")
        expected_type = builder_types.get(block_key) or "unknown"
        _must(block.get("block_type") == expected_type, f"{zone_name}: block_type drift in snapshot")
        mapped = map_by_zone.get(zone_name) or {}
        _must(mapped.get("block_key") == block_key, f"{zone_name}: mapping/service block mismatch")

    print("[verify.project.dashboard.snapshot_freshness] PASS")


if __name__ == "__main__":
    main()
