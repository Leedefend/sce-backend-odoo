#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "tmp" / "project_dashboard_contract_snapshot_v1.json"
MAPPING = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _load_json(path: Path):
    _must(path.exists(), f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    snap = _load_json(SNAPSHOT)
    mapping = _load_json(MAPPING)

    _must(snap.get("ok") is True, "snapshot ok must be true")
    data = snap.get("data") or {}
    meta = snap.get("meta") or {}
    _must((data.get("scene") or {}).get("key") == "project.management", "snapshot scene.key mismatch")
    _must((data.get("scene") or {}).get("page") == "project.management.dashboard", "snapshot scene.page mismatch")
    _must((data.get("page") or {}).get("key") == "project.management.dashboard", "snapshot page.key mismatch")
    _must((meta.get("intent") or "") == "project.dashboard", "snapshot meta.intent mismatch")
    _must((meta.get("contract_version") or "") == "v1", "snapshot meta.contract_version mismatch")

    route_context = data.get("route_context") or {}
    _must(
        route_context.get("primary_protocol") == "/s/project.management",
        "snapshot route_context.primary_protocol mismatch",
    )
    _must(route_context.get("scene_route") == "/s/project.management", "snapshot route_context.scene_route mismatch")
    _must(route_context.get("context_transport") == "scene_payload.project_context", "snapshot route_context.context_transport mismatch")

    project_context = data.get("project_context") or {}
    _must(isinstance(project_context, dict), "snapshot project_context must be object")
    for key in ("project_id", "project_name", "stage", "milestone", "status"):
        _must(key in project_context, f"snapshot project_context missing key: {key}")

    zones = data.get("zones") or {}
    _must(isinstance(zones, dict), "snapshot zones must be object")
    _must(len(zones) == 7, "snapshot zones count must be 7")

    rows = mapping.get("mappings") or []
    _must(len(rows) == 7, "mapping rows count must be 7")
    by_zone = {str(r.get("zone_key") or "").split(".", 1)[1]: r for r in rows}
    _must(len(by_zone) == 7, "mapping zone uniqueness mismatch")

    for zone_name in ("header", "metrics", "progress", "contract", "cost", "finance", "risk"):
        _must(zone_name in zones, f"snapshot zone missing: {zone_name}")
        zone = zones[zone_name] or {}
        _must(zone.get("zone_key") == f"zone.{zone_name}", f"{zone_name}: zone_key mismatch")
        blocks = zone.get("blocks")
        _must(isinstance(blocks, list) and len(blocks) == 1, f"{zone_name}: blocks must be single-item list")
        blk = blocks[0] or {}
        expected_block_key = (by_zone.get(zone_name) or {}).get("block_key")
        _must(blk.get("block_key") == expected_block_key, f"{zone_name}: block_key mismatch vs mapping")
        _must(str(blk.get("block_type") or ""), f"{zone_name}: block_type empty")
        _must(blk.get("state") in {"ready", "empty", "forbidden", "error"}, f"{zone_name}: invalid state")
        vis = blk.get("visibility") or {}
        _must("allowed" in vis and "reason_code" in vis and "reason" in vis, f"{zone_name}: visibility shape invalid")
        _must(isinstance(blk.get("data"), dict), f"{zone_name}: data must be object")
        err = blk.get("error") or {}
        _must("code" in err and "message" in err, f"{zone_name}: error shape invalid")

    print("[verify.project.dashboard.snapshot_schema] PASS")


if __name__ == "__main__":
    main()
