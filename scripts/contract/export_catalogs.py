#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


HANDLER_DIRS = [
    Path("addons/smart_core/handlers"),
    Path("addons/smart_construction_core/handlers"),
]

TEST_DIRS = [
    Path("addons/smart_core/tests"),
    Path("addons/smart_construction_core/tests"),
]


@dataclass
class IntentRow:
    intent: str
    module: str
    cls: str
    aliases: list[str]
    has_idempotency_window: bool
    inferred_request_keys: list[str]
    test_refs: int


def _literal_list(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            value = elt.value.strip()
            if value:
                out.append(value)
    return out


def _class_assign_map(node: ast.ClassDef) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for item in node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
            out[item.targets[0].id] = item.value
    return out


def collect_intent_rows(repo_root: Path) -> list[IntentRow]:
    rows: list[IntentRow] = []
    for rel_dir in HANDLER_DIRS:
        abs_dir = repo_root / rel_dir
        if not abs_dir.exists():
            continue
        for py_file in sorted(abs_dir.glob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(py_file))
            module = str(py_file.relative_to(repo_root))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                assigns = _class_assign_map(node)
                intent_node = assigns.get("INTENT_TYPE")
                if not (isinstance(intent_node, ast.Constant) and isinstance(intent_node.value, str)):
                    continue
                intent = intent_node.value.strip()
                if not intent:
                    continue
                rows.append(
                    IntentRow(
                        intent=intent,
                        module=module,
                        cls=node.name,
                        aliases=_literal_list(assigns.get("ALIASES", ast.List(elts=[]))),
                        has_idempotency_window="IDEMPOTENCY_WINDOW_SECONDS" in assigns,
                        inferred_request_keys=collect_inferred_request_keys(src, node),
                        test_refs=0,
                    )
                )
    return rows


def collect_inferred_request_keys(src: str, node: ast.ClassDef) -> list[str]:
    segment = ast.get_source_segment(src, node) or ""
    keys: set[str] = set()
    patterns = (
        r'params\.get\(\s*["\']([A-Za-z0-9_.-]+)["\']',
        r'params\[\s*["\']([A-Za-z0-9_.-]+)["\']\s*\]',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, segment):
            key = str(match.group(1) or "").strip()
            if key:
                keys.add(key)
    return sorted(keys)


def count_test_refs(repo_root: Path, rows: list[IntentRow]) -> None:
    test_blobs: list[str] = []
    for rel_dir in TEST_DIRS:
        abs_dir = repo_root / rel_dir
        if not abs_dir.exists():
            continue
        for py_file in sorted(abs_dir.rglob("test_*.py")):
            try:
                test_blobs.append(py_file.read_text(encoding="utf-8"))
            except OSError:
                continue
    combined = "\n".join(test_blobs)
    for row in rows:
        row.test_refs = len(re.findall(re.escape(row.intent), combined))


def dotted_paths(value: object, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            key = str(k)
            current = f"{prefix}.{key}" if prefix else key
            paths.add(current)
            paths.update(dotted_paths(v, current))
        return paths
    if isinstance(value, list):
        marker = f"{prefix}[]" if prefix else "[]"
        paths.add(marker)
        for item in value[:3]:
            paths.update(dotted_paths(item, marker))
        return paths
    if prefix:
        paths.add(prefix)
    return paths


def collect_reason_codes(value: object) -> set[str]:
    out: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "reason_code" and isinstance(v, str) and v.strip():
                out.add(v.strip())
            out.update(collect_reason_codes(v))
    elif isinstance(value, list):
        for item in value:
            out.update(collect_reason_codes(item))
    return out


def load_cases(cases_file: Path) -> list[dict]:
    raw = cases_file.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"{cases_file} must be a JSON array")
    return [item for item in data if isinstance(item, dict)]


def build_intent_catalog(repo_root: Path, rows: list[IntentRow], cases_file: Path, snapshots_dir: Path) -> dict:
    cases = load_cases(cases_file)
    cases_by_name = {str(case.get("case")): case for case in cases if case.get("case")}
    intent_case_map: dict[str, list[dict]] = defaultdict(list)

    for case in cases:
        if case.get("op") != "intent.invoke":
            continue
        intent = str(case.get("intent") or "").strip()
        if not intent:
            continue
        intent_case_map[intent].append(case)

    snapshot_payloads: dict[str, dict] = {}
    for snap in sorted(snapshots_dir.glob("*.json")):
        try:
            payload = json.loads(snap.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        case_name = str(payload.get("case") or "").strip()
        if case_name:
            snapshot_payloads[case_name] = payload

    by_intent: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: (r.intent, r.module, r.cls)):
        if row.intent not in by_intent:
            by_intent[row.intent] = {
                "intent": row.intent,
                "owner": {"module": row.module, "class": row.cls},
                "aliases": sorted(set(row.aliases)),
                "stability": "stable",
                "has_idempotency_window": row.has_idempotency_window,
                "test_refs": row.test_refs,
                "request_schema_hint": [],
                "response_data_schema_hint": [],
                "error_schema_hint": [],
                "observed_reason_codes": [],
                "examples": [],
                "inferred_example": None,
            }
        else:
            by_intent[row.intent]["aliases"] = sorted(set(by_intent[row.intent]["aliases"] + row.aliases))
            by_intent[row.intent]["test_refs"] += row.test_refs
            if row.has_idempotency_window:
                by_intent[row.intent]["has_idempotency_window"] = True
        if row.inferred_request_keys:
            req_hint = set(by_intent[row.intent]["request_schema_hint"])
            req_hint.update(row.inferred_request_keys)
            by_intent[row.intent]["request_schema_hint"] = sorted(req_hint)

    for intent, cases_for_intent in sorted(intent_case_map.items(), key=lambda kv: kv[0]):
        entry = by_intent.setdefault(
            intent,
            {
                "intent": intent,
                "owner": {"module": "", "class": ""},
                "aliases": [],
                "stability": "stable",
                "has_idempotency_window": False,
                "test_refs": 0,
                "request_schema_hint": [],
                "response_data_schema_hint": [],
                "error_schema_hint": [],
                "observed_reason_codes": [],
                "examples": [],
                "inferred_example": None,
            },
        )
        request_paths: set[str] = set()
        response_paths: set[str] = set()
        error_paths: set[str] = set()
        reason_codes: set[str] = set()
        for case in cases_for_intent:
            case_name = str(case.get("case", "")).strip()
            intent_params = case.get("intent_params") if isinstance(case.get("intent_params"), dict) else {}
            request_paths.update(dotted_paths(intent_params))
            snapshot = snapshot_payloads.get(case_name) or {}
            response_data = snapshot.get("ui_contract_raw")
            response_error = snapshot.get("error")
            if response_data is not None:
                response_paths.update(dotted_paths(response_data))
                reason_codes.update(collect_reason_codes(response_data))
            if response_error is not None:
                error_paths.update(dotted_paths(response_error))
                reason_codes.update(collect_reason_codes(response_error))
            entry["examples"].append(
                {
                    "case": case_name,
                    "snapshot_file": f"docs/contract/snapshots/{case_name}.json" if case_name else "",
                    "request_keys": sorted(dotted_paths(intent_params)),
                    "response_data_keys": sorted(dotted_paths(response_data if response_data is not None else {})),
                    "response_error_keys": sorted(dotted_paths(response_error if response_error is not None else {})),
                }
            )
        entry["request_schema_hint"] = sorted(set(entry["request_schema_hint"]) | request_paths)
        entry["response_data_schema_hint"] = sorted(set(entry["response_data_schema_hint"]) | response_paths)
        entry["error_schema_hint"] = sorted(set(entry["error_schema_hint"]) | error_paths)
        entry["observed_reason_codes"] = sorted(set(entry["observed_reason_codes"]) | reason_codes)

    for intent, entry in sorted(by_intent.items(), key=lambda kv: kv[0]):
        examples = entry.get("examples") or []
        if examples:
            continue
        request_keys = sorted(set(entry.get("request_schema_hint") or []))
        inferred_example = {
            "case": "__inferred__",
            "snapshot_file": "",
            "request_keys": request_keys,
            "response_data_keys": [],
            "response_error_keys": [],
            "inferred": True,
            "source": "handler_params_scan",
        }
        entry["examples"] = [inferred_example]
        entry["inferred_example"] = inferred_example

    return {
        "source": {
            "handlers": [str(p) for p in HANDLER_DIRS],
            "tests": [str(p) for p in TEST_DIRS],
            "cases_file": str(cases_file.relative_to(repo_root)),
            "snapshots_dir": str(snapshots_dir.relative_to(repo_root)),
        },
        "intents": [by_intent[k] for k in sorted(by_intent.keys())],
    }


def infer_target_type(target: dict) -> str:
    if not isinstance(target, dict):
        return "unknown"
    if "route" in target:
        return "spa_route"
    if "action_id" in target:
        return "odoo_action"
    return "unknown"


def to_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return sorted(set(out))


def to_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return default
    return bool(value)


def build_scene_catalog(repo_root: Path, scene_contract_file: Path) -> dict:
    payload = json.loads(scene_contract_file.read_text(encoding="utf-8"))
    scenes = payload.get("scenes") if isinstance(payload, dict) else []
    if not isinstance(scenes, list):
        scenes = []
    layout_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    renderability = {
        "renderable_scene_count": 0,
        "interaction_ready_scene_count": 0,
    }
    out_scenes: list[dict] = []

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_key = str(scene.get("code") or "")
        name = str(scene.get("name") or "")
        layout = scene.get("layout") if isinstance(scene.get("layout"), dict) else {}
        list_profile = scene.get("list_profile") if isinstance(scene.get("list_profile"), dict) else {}
        tiles = scene.get("tiles") if isinstance(scene.get("tiles"), list) else []
        filters = scene.get("filters") if isinstance(scene.get("filters"), list) else []
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        access = scene.get("access") if isinstance(scene.get("access"), dict) else {}
        tile_caps = []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            caps = tile.get("required_capabilities")
            tile_caps.extend(to_string_list(caps))

        required_capabilities = sorted(set(
            to_string_list(scene.get("required_capabilities"))
            + to_string_list(access.get("required_capabilities"))
            + tile_caps
        ))
        required_caps = len(required_capabilities)
        visible = to_bool(access.get("visible"), True)
        allowed = to_bool(access.get("allowed"), visible)
        reason_code = str(access.get("reason_code") or ("OK" if allowed else "PERMISSION_DENIED"))
        suggested_action = str(access.get("suggested_action") or "")
        has_access_clause = bool(access.get("has_access_clause")) or required_caps > 0

        layout_kind = str(layout.get("kind") or "")
        target_type = infer_target_type(target)
        is_renderable = bool(layout_kind) and target_type != "unknown" and len(target.keys()) > 0
        # interaction-ready means scene can be rendered and access does not explicitly deny.
        is_interaction_ready = is_renderable and bool(allowed)
        if is_renderable:
            renderability["renderable_scene_count"] += 1
        if is_interaction_ready:
            renderability["interaction_ready_scene_count"] += 1
        layout_counts[layout_kind or "unknown"] += 1
        target_counts[target_type] += 1
        out_scenes.append(
            {
                "scene_key": scene_key,
                "name": name,
                "identity": {
                    "scene_key": scene_key,
                    "label": name,
                },
                "access": {
                    "visible": visible,
                    "allowed": allowed,
                    "reason_code": reason_code,
                    "suggested_action": suggested_action,
                    "required_capabilities": required_capabilities,
                    "required_capabilities_count": required_caps,
                    "has_access_clause": has_access_clause,
                },
                "layout": {
                    "kind": layout_kind,
                    "keys": sorted(layout.keys()),
                },
                "components": {
                    "tiles_count": len(tiles),
                    "has_tiles": len(tiles) > 0,
                    "has_list_profile": bool(list_profile),
                    "list_profile_keys": sorted(list_profile.keys()),
                    "filters_count": len(filters),
                },
                "target": {
                    "type": target_type,
                    "keys": sorted(target.keys()),
                },
                "renderability": {
                    "is_renderable": is_renderable,
                    "is_interaction_ready": is_interaction_ready,
                },
            }
        )

    total = len(out_scenes)
    if total <= 0:
        renderability["renderable_ratio"] = 0.0
        renderability["interaction_ready_ratio"] = 0.0
    else:
        renderability["renderable_ratio"] = round(renderability["renderable_scene_count"] / total, 4)
        renderability["interaction_ready_ratio"] = round(renderability["interaction_ready_scene_count"] / total, 4)

    return {
        "source": {
            "scene_contract_file": str(scene_contract_file.relative_to(repo_root)),
        },
        "schema_version": payload.get("schema_version", ""),
        "scene_version": payload.get("scene_version", ""),
        "profiles_version": payload.get("profiles_version", ""),
        "scene_count": len(out_scenes),
        "layout_kind_counts": dict(sorted(layout_counts.items())),
        "target_type_counts": dict(sorted(target_counts.items())),
        "renderability": renderability,
        "scenes": sorted(out_scenes, key=lambda x: x["scene_key"]),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export contract catalogs (intent/scene).")
    parser.add_argument("--cases-file", default="docs/contract/cases.yml")
    parser.add_argument("--snapshots-dir", default="docs/contract/snapshots")
    parser.add_argument("--scene-contract-file", default="docs/contract/exports/scenes/stable/LATEST.json")
    parser.add_argument("--intent-out", default="docs/contract/exports/intent_catalog.json")
    parser.add_argument("--scene-out", default="docs/contract/exports/scene_catalog.json")
    parser.add_argument("--include-generated-at", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    cases_file = repo_root / args.cases_file
    snapshots_dir = repo_root / args.snapshots_dir
    scene_contract_file = repo_root / args.scene_contract_file
    intent_out = repo_root / args.intent_out
    scene_out = repo_root / args.scene_out

    if not cases_file.exists():
        raise SystemExit(f"Missing cases file: {cases_file}")
    if not snapshots_dir.exists():
        raise SystemExit(f"Missing snapshots dir: {snapshots_dir}")
    if not scene_contract_file.exists():
        raise SystemExit(f"Missing scene contract file: {scene_contract_file}")

    rows = collect_intent_rows(repo_root)
    count_test_refs(repo_root, rows)
    intent_catalog = build_intent_catalog(repo_root, rows, cases_file, snapshots_dir)
    scene_catalog = build_scene_catalog(repo_root, scene_contract_file)
    if args.include_generated_at:
        stamp = datetime.now(tz=timezone.utc).isoformat()
        intent_catalog["generated_at"] = stamp
        scene_catalog["generated_at"] = stamp

    write_json(intent_out, intent_catalog)
    write_json(scene_out, scene_catalog)
    print(str(intent_out))
    print(str(scene_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
