#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAPPING_JSON = ROOT / "docs" / "contract" / "project_management_capability_mapping_v2.json"
SCENE_XML = ROOT / "addons" / "smart_construction_scene" / "data" / "project_management_scene.xml"
ORCHESTRATOR_PY = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"
BUILDERS_DIR = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"
CONTRACT_DOC = ROOT / "docs" / "contract" / "project_dashboard_contract_v1.md"
BLOCK_DOC = ROOT / "docs" / "contract" / "project_management_block_contract_v1.md"
ROUTE_DOC = ROOT / "docs" / "ops" / "project_management_scene_route_context_v1.md"

PRIMARY_PROTOCOL = "/s/project.management?project_id=<id>"


def _must(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def _load_mapping_rows():
    payload = json.loads(MAPPING_JSON.read_text(encoding="utf-8"))
    _must(payload.get("scene_key") == "project.management", "mapping scene_key mismatch")
    _must(payload.get("page_key") == "project.management.dashboard", "mapping page_key mismatch")
    rows = payload.get("mappings")
    _must(isinstance(rows, list) and len(rows) == 7, "mapping rows must be 7")
    return rows


def _load_scene_zone_blocks():
    tree = ET.parse(SCENE_XML)
    root = tree.getroot()
    eval_text = ""
    for rec in root.findall(".//record"):
        if rec.attrib.get("id") == "sc_scene_version_project_management_v2":
            node = rec.find("./field[@name='payload_json']")
            eval_text = (node.attrib.get("eval") if node is not None else "") or ""
            break
    _must(bool(eval_text), "scene payload_json(eval) missing")
    payload = ast.literal_eval(eval_text)
    _must(payload.get("code") == "project.management", "scene payload code mismatch")
    _must((payload.get("page") or {}).get("key") == "project.management.dashboard", "scene page key mismatch")
    zone_rows = []
    for zone in payload.get("zones") or []:
        blocks = zone.get("blocks") or []
        _must(len(blocks) == 1, "each scene zone must have exactly one block in v1")
        block = blocks[0]
        zone_rows.append(
            {
                "zone_key": str(zone.get("key") or "").strip(),
                "block_key": str(block.get("key") or "").strip(),
                "block_type": str(block.get("block_type") or "").strip(),
                "capability_key": str(block.get("capability_key") or "").strip(),
            }
        )
    _must(len(zone_rows) == 7, "scene zones must be 7")
    return zone_rows


def _load_orchestrator_zone_blocks():
    tree = ast.parse(ORCHESTRATOR_PY.read_text(encoding="utf-8"))
    tuple_rows = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProjectDashboardContractOrchestrator":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "ZONE_BLOCKS":
                            tuple_rows = ast.literal_eval(stmt.value)
    _must(isinstance(tuple_rows, tuple) and len(tuple_rows) == 7, "orchestrator ZONE_BLOCKS must be tuple with 7 rows")
    rows = []
    for row in tuple_rows:
        _must(isinstance(row, tuple) and len(row) == 5, "orchestrator ZONE_BLOCKS row shape invalid")
        zone_key, _title, _zone_type, _display_mode, block_key = row
        rows.append({"zone_key": f"zone.{zone_key}", "block_key": str(block_key)})
    return rows


def _load_builder_block_keys():
    keys = {}
    for py in BUILDERS_DIR.glob("project_*_builder.py"):
        text = py.read_text(encoding="utf-8")
        key_match = re.search(r'^\s*block_key\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
        type_match = re.search(r'^\s*block_type\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
        _must(key_match is not None, f"{py.name}: block_key missing")
        _must(type_match is not None, f"{py.name}: block_type missing")
        key = key_match.group(1).strip()
        _must(key not in keys, f"duplicate builder block_key: {key}")
        keys[key] = type_match.group(1).strip()
    _must(len(keys) >= 7, "builder files must expose at least 7 block keys")
    return keys


def _load_supported_block_types_from_doc() -> set[str]:
    text = BLOCK_DOC.read_text(encoding="utf-8")
    types = set(re.findall(r"- `([a-z_]+)`", text))
    _must(types, "block contract doc: no block types found")
    return types


def _guard_contract_doc_mentions_route_context():
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    _must('"route_context"' in text, "contract doc must include route_context")
    _must(PRIMARY_PROTOCOL in text, "contract doc missing primary route protocol")


def _guard_route_protocol_consistency():
    route_text = ROUTE_DOC.read_text(encoding="utf-8")
    _must(PRIMARY_PROTOCOL in route_text, "route doc missing primary protocol")
    orchestrator_text = ORCHESTRATOR_PY.read_text(encoding="utf-8")
    _must(PRIMARY_PROTOCOL in orchestrator_text, "orchestrator route_context missing primary protocol")
    _must("project_route_template" in orchestrator_text, "orchestrator route_context missing project_route_template")
    _must("query_key" in orchestrator_text and "project_id" in orchestrator_text, "orchestrator route_context missing query key semantics")


def _load_orchestrator_build_contract_keys() -> set[str]:
    tree = ast.parse(ORCHESTRATOR_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "ProjectDashboardContractOrchestrator":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.FunctionDef) or stmt.name != "build_contract":
                continue
            for line in stmt.body:
                if isinstance(line, ast.Return) and isinstance(line.value, ast.Dict):
                    out = set()
                    for key_node in line.value.keys:
                        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                            out.add(key_node.value)
                    return out
    raise SystemExit("unable to parse ProjectDashboardContractOrchestrator.build_contract return keys")


def main() -> None:
    mapping_rows = _load_mapping_rows()
    scene_rows = _load_scene_zone_blocks()
    service_rows = _load_orchestrator_zone_blocks()
    builder_keys = _load_builder_block_keys()
    supported_block_types = _load_supported_block_types_from_doc()
    _guard_contract_doc_mentions_route_context()
    _guard_route_protocol_consistency()
    service_contract_keys = _load_orchestrator_build_contract_keys()
    expected_contract_keys = {"scene", "page", "route_context", "project", "zones"}
    _must(
        expected_contract_keys.issubset(service_contract_keys),
        "orchestrator build return keys missing required contract fields",
    )

    mapping_by_zone = {r["zone_key"]: r for r in mapping_rows}
    scene_by_zone = {r["zone_key"]: r for r in scene_rows}
    service_by_zone = {r["zone_key"]: r for r in service_rows}

    _must(set(mapping_by_zone.keys()) == set(scene_by_zone.keys()) == set(service_by_zone.keys()), "zone key set drift detected")

    for zone_key in sorted(mapping_by_zone):
        m = mapping_by_zone[zone_key]
        s = scene_by_zone[zone_key]
        v = service_by_zone[zone_key]
        _must(m["block_key"] == s["block_key"], f"{zone_key}: mapping/scene block key mismatch")
        _must(m["block_key"] == v["block_key"], f"{zone_key}: mapping/orchestrator block key mismatch")
        _must(bool(m.get("capability_key")), f"{zone_key}: capability_key missing in mapping")
        _must(bool(s.get("capability_key")), f"{zone_key}: capability_key missing in scene payload")
        _must(m.get("capability_key") == s.get("capability_key"), f"{zone_key}: capability mismatch mapping vs scene payload")
        _must(m["block_key"] in builder_keys, f"{zone_key}: block key missing builder")
        _must(bool(s.get("block_type")), f"{zone_key}: block_type missing in scene payload")
        _must(
            s["block_type"] == builder_keys[m["block_key"]],
            f"{zone_key}: block_type mismatch scene vs builder",
        )
        _must(
            s["block_type"] in supported_block_types,
            f"{zone_key}: block_type not declared in block contract doc",
        )

    print("[verify.project.dashboard.assembly] PASS")


if __name__ == "__main__":
    main()
