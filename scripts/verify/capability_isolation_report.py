#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
OWNER_REGISTRY = ROOT / "addons" / "smart_owner_core" / "services" / "capability_registry_owner.py"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "capability_isolation_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "capability_isolation_report.json"


def _extract_capability_keys(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.is_file():
        return out
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return out
    cap_call_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_cap" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                text = arg.value.strip()
                if text:
                    cap_call_found = True
                    out.add(text)
    if cap_call_found:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "key":
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        text = v.value.strip()
                        if text:
                            out.add(text)
    return out


def _prefix_bucket(keys: set[str]) -> set[str]:
    out: set[str] = set()
    for key in keys:
        head = key.split(".", 1)[0].strip().lower()
        if head:
            out.add(head)
    return out


def main() -> int:
    construction = _extract_capability_keys(CONSTRUCTION_REGISTRY)
    owner = _extract_capability_keys(OWNER_REGISTRY)
    overlap = sorted(construction & owner)

    owner_prefixes = sorted(_prefix_bucket(owner))
    construction_prefixes = sorted(_prefix_bucket(construction))
    forbidden_owner_prefixes = sorted(set(owner_prefixes) & {"project", "finance", "cost", "contract", "analytics"})
    forbidden_construction_prefixes = sorted(set(construction_prefixes) & {"owner"})

    errors: list[str] = []
    if overlap:
        errors.append(f"capability key overlap detected: {len(overlap)}")
    if forbidden_owner_prefixes:
        errors.append(f"owner capability prefixes polluted: {', '.join(forbidden_owner_prefixes)}")
    if forbidden_construction_prefixes:
        errors.append(f"construction capability prefixes polluted: {', '.join(forbidden_construction_prefixes)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "construction_capability_count": len(construction),
            "owner_capability_count": len(owner),
            "overlap_count": len(overlap),
            "error_count": len(errors),
        },
        "construction_prefixes": construction_prefixes,
        "owner_prefixes": owner_prefixes,
        "overlap_capabilities": overlap,
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Capability Isolation Report",
        "",
        f"- construction_capability_count: {payload['summary']['construction_capability_count']}",
        f"- owner_capability_count: {payload['summary']['owner_capability_count']}",
        f"- overlap_count: {payload['summary']['overlap_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        "",
        "## Construction Prefixes",
        "",
        f"- {', '.join(construction_prefixes) if construction_prefixes else 'none'}",
        "",
        "## Owner Prefixes",
        "",
        f"- {', '.join(owner_prefixes) if owner_prefixes else 'none'}",
        "",
        "## Overlap Capabilities",
        "",
    ]
    if overlap:
        for key in overlap:
            lines.append(f"- `{key}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[capability_isolation_report] FAIL")
        return 2
    print("[capability_isolation_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
