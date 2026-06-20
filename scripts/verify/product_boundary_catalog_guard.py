#!/usr/bin/env python3
"""Ensure addon modules are covered by the formal product boundary catalog."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADDONS_ROOT = ROOT / "addons"
BOUNDARY_DOC = ROOT / "docs/product/formal_product_boundary_v1.md"
OUT_JSON = ROOT / "artifacts/docs/product_boundary_catalog_guard.json"

MODULE_CELL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")
MODULE_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")
PRODUCT_LAYER_RE = re.compile(r"^\|\s*(P[0-4])\s*\|")
PRODUCT_LAYER_ROW_RE = re.compile(r"^\|\s*(P[0-4])\s*\|\s*([^|]+?)\s*\|")
PRODUCT_LAYER_TOKEN_RE = re.compile(r"\bP[0-4]\b")

REQUIRED_SECTIONS = [
    "## 产品分层",
    "## 当前模块归属",
    "## 平台产品",
    "## 行业标准产品",
    "## 用户产品",
    "## 低代码配置产品",
    "## 运维交付工具",
    "## 归属判定规则",
    "## 配置沉淀规则",
    "## 交付验收",
    "## 当前结论",
]

REQUIRED_LAYERS = ["P0", "P1", "P2", "P3", "P4"]
REQUIRED_LAYER_NAMES = {
    "P0": "平台内核产品",
    "P1": "施工行业标准产品",
    "P2": "特定用户产品",
    "P3": "低代码配置产品",
    "P4": "运维交付工具",
}
REQUIRED_DELIVERY_TERMS = ["可重放", "可覆盖", "可审计", "可回滚", "业务端验证"]


def addon_modules() -> list[str]:
    return sorted(
        path.parent.name
        for path in ADDONS_ROOT.glob("*/__manifest__.py")
        if path.is_file()
    )


def documented_modules() -> list[str]:
    text = BOUNDARY_DOC.read_text(encoding="utf-8")
    modules: set[str] = set()
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 当前模块归属":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = MODULE_CELL_RE.match(line)
        if match:
            modules.add(match.group(1))
    return sorted(modules)


def documented_module_assignments() -> dict[str, str]:
    text = BOUNDARY_DOC.read_text(encoding="utf-8")
    assignments: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 当前模块归属":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = MODULE_ROW_RE.match(line)
        if match:
            assignments[match.group(1)] = match.group(2).strip()
    return dict(sorted(assignments.items()))


def documented_module_rows() -> list[dict[str, str]]:
    text = BOUNDARY_DOC.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 当前模块归属":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = MODULE_ROW_RE.match(line)
        if match:
            rows.append({"module": match.group(1), "assignment": match.group(2).strip()})
    return rows


def documented_layers(text: str) -> list[str]:
    layers: set[str] = set()
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 产品分层":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = PRODUCT_LAYER_RE.match(line)
        if match:
            layers.add(match.group(1))
    return sorted(layers)


def documented_layer_names(text: str) -> dict[str, str]:
    layer_names: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 产品分层":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = PRODUCT_LAYER_ROW_RE.match(line)
        if match:
            layer_names[match.group(1)] = match.group(2).strip()
    return dict(sorted(layer_names.items()))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    payload = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(OUT_JSON))
    missing = payload["missing"]
    extra = payload["extra"]
    duplicate_modules = payload["duplicate_modules"]
    missing_sections = payload["missing_sections"]
    missing_layers = payload["missing_layers"]
    invalid_layer_names = payload["invalid_layer_names"]
    missing_delivery_terms = payload["missing_delivery_terms"]
    invalid_module_assignments = payload["invalid_module_assignments"]
    if (
        missing
        or extra
        or duplicate_modules
        or missing_sections
        or missing_layers
        or invalid_layer_names
        or missing_delivery_terms
        or invalid_module_assignments
    ):
        if missing:
            print("[FAIL] modules missing from formal product boundary: " + ", ".join(missing))
        if extra:
            print("[FAIL] modules documented but not present under addons: " + ", ".join(extra))
        if duplicate_modules:
            print("[FAIL] duplicate module rows in formal product boundary: " + ", ".join(duplicate_modules))
        if invalid_module_assignments:
            details = ", ".join(
                f"{item['module']}={item['assignment']}" for item in invalid_module_assignments
            )
            print("[FAIL] modules with invalid product layer assignment: " + details)
        if missing_sections:
            print("[FAIL] required sections missing: " + ", ".join(missing_sections))
        if missing_layers:
            print("[FAIL] product layers missing: " + ", ".join(missing_layers))
        if invalid_layer_names:
            details = ", ".join(
                f"{item['layer']} expected={item['expected']} actual={item['actual']}"
                for item in invalid_layer_names
            )
            print("[FAIL] product layer names invalid: " + details)
        if missing_delivery_terms:
            print("[FAIL] delivery acceptance terms missing: " + ", ".join(missing_delivery_terms))
        return 2
    print(
        f"[OK] product boundary catalog covers "
        f"{payload['summary']['addon_module_count']} addon modules and "
        f"{payload['summary']['documented_layer_count']} product layers"
    )
    return 0


def build_report() -> dict:
    text = BOUNDARY_DOC.read_text(encoding="utf-8")
    addons = addon_modules()
    documented = documented_modules()
    module_assignments = documented_module_assignments()
    module_rows = documented_module_rows()
    layers = documented_layers(text)
    layer_names = documented_layer_names(text)
    missing = sorted(set(addons) - set(documented))
    extra = sorted(set(documented) - set(addons))
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in text]
    missing_layers = sorted(set(REQUIRED_LAYERS) - set(layers))
    invalid_layer_names = [
        {"layer": layer, "expected": expected, "actual": layer_names.get(layer, "")}
        for layer, expected in REQUIRED_LAYER_NAMES.items()
        if layer_names.get(layer) != expected
    ]
    missing_delivery_terms = [term for term in REQUIRED_DELIVERY_TERMS if term not in text]
    invalid_module_assignments = [
        {"module": module, "assignment": assignment}
        for module, assignment in module_assignments.items()
        if not PRODUCT_LAYER_TOKEN_RE.search(assignment)
    ]
    duplicate_modules = sorted(
        {
            row["module"]
            for row in module_rows
            if [item["module"] for item in module_rows].count(row["module"]) > 1
        }
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary_doc": display_path(BOUNDARY_DOC),
        "summary": {
            "addon_module_count": len(addons),
            "documented_module_count": len(documented),
            "documented_layer_count": len(layers),
            "missing_count": len(missing),
            "extra_count": len(extra),
            "missing_section_count": len(missing_sections),
            "missing_layer_count": len(missing_layers),
            "invalid_layer_name_count": len(invalid_layer_names),
            "missing_delivery_term_count": len(missing_delivery_terms),
            "invalid_module_assignment_count": len(invalid_module_assignments),
            "duplicate_module_count": len(duplicate_modules),
            "ok": (
                not missing
                and not extra
                and not duplicate_modules
                and not missing_sections
                and not missing_layers
                and not invalid_layer_names
                and not missing_delivery_terms
                and not invalid_module_assignments
            ),
        },
        "addon_modules": addons,
        "documented_modules": documented,
        "module_rows": module_rows,
        "module_assignments": module_assignments,
        "documented_layers": layers,
        "documented_layer_names": layer_names,
        "missing": missing,
        "extra": extra,
        "duplicate_modules": duplicate_modules,
        "missing_sections": missing_sections,
        "missing_layers": missing_layers,
        "invalid_layer_names": invalid_layer_names,
        "missing_delivery_terms": missing_delivery_terms,
        "invalid_module_assignments": invalid_module_assignments,
    }


if __name__ == "__main__":
    raise SystemExit(main())
