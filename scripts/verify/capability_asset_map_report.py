#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_REGISTRY_PY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
INTENT_CATALOG_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
RELEASE_CAPABILITY_JSON = ROOT / "artifacts" / "backend" / "release_capability_report.json"
SCENE_CAPABILITY_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
REPORT_MD = ROOT / "docs" / "product" / "capability_asset_map_v1.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _ast_literal(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return None


def _parse_capabilities() -> list[dict]:
    if not CAPABILITY_REGISTRY_PY.is_file():
        return []
    text = CAPABILITY_REGISTRY_PY.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(CAPABILITY_REGISTRY_PY))
    out: list[dict] = []
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "_CAPABILITIES" in target_names and isinstance(node.value, ast.List):
                nodes.append(node.value)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "_CAPABILITIES" and isinstance(node.value, ast.List):
                nodes.append(node.value)

    for value in nodes:
        for item in value.elts:
            if not isinstance(item, ast.Call):
                continue
            fn_name = item.func.id if isinstance(item.func, ast.Name) else ""
            if fn_name != "_cap":
                continue
            args = list(item.args)
            if len(args) < 5:
                continue
            key = _ast_literal(args[0]) or ""
            label = _ast_literal(args[1]) or ""
            group_key = _ast_literal(args[3]) or ""
            scene_key = _ast_literal(args[4]) or ""
            if not key:
                continue
            kwargs = {kw.arg: kw.value for kw in item.keywords if kw.arg}
            required_roles = _ast_literal(kwargs.get("required_roles")) or []
            required_groups = _ast_literal(kwargs.get("required_groups")) or []
            intent = _ast_literal(kwargs.get("intent")) or "ui.contract"
            out.append(
                {
                    "capability_key": str(key).strip(),
                    "label": str(label).strip(),
                    "group_key": str(group_key).strip(),
                    "scene_key": str(scene_key).strip(),
                    "intent": str(intent).strip(),
                    "required_roles": sorted({str(x).strip() for x in required_roles if str(x).strip()}),
                    "required_groups": sorted({str(x).strip() for x in required_groups if str(x).strip()}),
                }
            )
    return sorted(out, key=lambda x: x["capability_key"])


def _build_scene_usage_index(matrix_payload: dict) -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    matrix = matrix_payload.get("matrix") if isinstance(matrix_payload.get("matrix"), list) else []
    for row in matrix:
        if not isinstance(row, dict):
            continue
        scene_key = str(row.get("scene_key") or "").strip()
        all_caps = row.get("all_capabilities") if isinstance(row.get("all_capabilities"), list) else []
        if not scene_key:
            continue
        for cap in all_caps:
            key = str(cap or "").strip()
            if not key:
                continue
            usage.setdefault(key, set()).add(scene_key)
    return usage


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    intent_catalog = _load_json(INTENT_CATALOG_JSON)
    release_report = _load_json(RELEASE_CAPABILITY_JSON)
    scene_matrix = _load_json(SCENE_CAPABILITY_MATRIX_JSON)

    catalog_intents = {
        str(item.get("intent_type") or "").strip()
        for item in (intent_catalog.get("intents") if isinstance(intent_catalog.get("intents"), list) else [])
        if isinstance(item, dict)
    }
    catalog_intents = {x for x in catalog_intents if x}
    if not catalog_intents:
        errors.append("intent catalog is empty")

    runtime_rows = (
        ((release_report.get("runtime_capability_matrix") or {}).get("rows"))
        if isinstance((release_report.get("runtime_capability_matrix") or {}).get("rows"), list)
        else []
    )
    runtime_role_by_cap: dict[str, dict] = {}
    for row in runtime_rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("capability_key") or "").strip()
        roles = row.get("roles") if isinstance(row.get("roles"), dict) else {}
        if key:
            runtime_role_by_cap[key] = roles

    scene_usage_index = _build_scene_usage_index(scene_matrix)
    missing_capability_ref_count = int(((scene_matrix.get("summary") or {}).get("missing_capability_ref_count")) or 0)

    capabilities = _parse_capabilities()
    if not capabilities:
        errors.append("failed to parse capability_registry definitions")

    rows: list[dict] = []
    unresolved_intents: list[str] = []
    structural_only: list[str] = []
    isolated: list[str] = []
    active_used: list[str] = []

    for cap in capabilities:
        key = cap["capability_key"]
        intent = cap["intent"]
        role_state = runtime_role_by_cap.get(key, {})
        role_ready = sorted(
            role
            for role, state in role_state.items()
            if isinstance(state, dict) and str(state.get("state") or "").strip().upper() == "READY"
        )
        scene_refs = sorted(scene_usage_index.get(key, set()))

        if key not in runtime_role_by_cap:
            usage_status = "structural_only"
            structural_only.append(key)
        elif role_ready:
            usage_status = "active_used"
            active_used.append(key)
        else:
            usage_status = "isolated"
            isolated.append(key)

        if intent and intent not in catalog_intents:
            unresolved_intents.append(f"{key}:{intent}")

        rows.append(
            {
                "capability_key": key,
                "label": cap["label"],
                "group_key": cap["group_key"],
                "intent": intent,
                "scene_entry": cap["scene_key"],
                "scene_refs": scene_refs,
                "required_roles": cap["required_roles"],
                "required_groups": cap["required_groups"],
                "runtime_ready_roles": role_ready,
                "usage_status": usage_status,
            }
        )

    if unresolved_intents:
        errors.append(f"unresolved_intent_count={len(unresolved_intents)}")
    if missing_capability_ref_count != 0:
        errors.append(f"missing_capability_ref_count={missing_capability_ref_count}")
    if structural_only:
        warnings.append(f"structural_only_count={len(structural_only)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "capability_count": len(rows),
            "active_used_count": len(active_used),
            "structural_only_count": len(structural_only),
            "isolated_count": len(isolated),
            "unresolved_intent_count": len(unresolved_intents),
            "missing_capability_ref_count": missing_capability_ref_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "acceptance": {
            "zero_unresolved_intent": len(unresolved_intents) == 0,
            "zero_missing_capability_ref": missing_capability_ref_count == 0,
            "zero_structural_only": len(structural_only) == 0,
        },
        "unresolved_intents": unresolved_intents,
        "structural_only_capabilities": structural_only,
        "isolated_capabilities": isolated,
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Capability Asset Map v1",
        "",
        "- source: capability_registry + release_capability_report + scene_capability_matrix_report",
        f"- capability_count: {len(rows)}",
        f"- active_used_count: {len(active_used)}",
        f"- structural_only_count: {len(structural_only)}",
        f"- isolated_count: {len(isolated)}",
        f"- unresolved_intent_count: {len(unresolved_intents)}",
        f"- missing_capability_ref_count: {missing_capability_ref_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Acceptance",
        "",
        f"- zero_unresolved_intent: {'PASS' if len(unresolved_intents) == 0 else 'FAIL'}",
        f"- zero_missing_capability_ref: {'PASS' if missing_capability_ref_count == 0 else 'FAIL'}",
        f"- zero_structural_only: {'PASS' if len(structural_only) == 0 else 'FAIL'}",
        "",
        "## Capability -> Scene -> Role -> Intent",
        "",
        "| capability | scene_entry | scene_refs | runtime_ready_roles | intent | usage_status |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {cap} | {entry} | {refs} | {roles} | {intent} | {status} |".format(
                cap=row["capability_key"],
                entry=row["scene_entry"] or "-",
                refs=",".join(row["scene_refs"]) if row["scene_refs"] else "-",
                roles=",".join(row["runtime_ready_roles"]) if row["runtime_ready_roles"] else "-",
                intent=row["intent"] or "-",
                status=row["usage_status"],
            )
        )
    lines.extend(["", "## Isolated Capabilities", ""])
    if isolated:
        for key in isolated:
            lines.append(f"- {key}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[capability_asset_map_report] FAIL")
        return 2
    print("[capability_asset_map_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
