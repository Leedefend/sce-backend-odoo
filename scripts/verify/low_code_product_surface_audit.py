#!/usr/bin/env python3
"""Generate the static denominator for LC-AUDIT-01.

This is a read-only source audit.  It deliberately does not call Odoo, mutate a
configuration contract, or claim that source presence proves runtime usability.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "frontend/apps/web/src"
SURFACE_FILES = [
    WEB / "views/BusinessConfigSurfaceView.vue",
    WEB / "views/MenuConfigView.vue",
    *sorted((WEB / "views/businessConfigSurface").glob("*")),
    WEB / "pages/ContractFormPage.vue",
    *sorted((WEB / "pages/contractForm").glob("*FormDesigner*")),
    WEB / "api/businessConfig.ts",
    WEB / "api/menuConfig.ts",
    WEB / "app/businessConfigBoundaries.ts",
]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def file_metrics(path: Path) -> dict[str, object]:
    source = text(path)
    return {
        "path": str(path.relative_to(ROOT)),
        "lines": len(source.splitlines()),
        "sha256": sha256(path),
        "raw_button_count": len(re.findall(r"<button\b", source)),
        "raw_input_count": len(re.findall(r"<input\b", source)),
        "raw_select_count": len(re.findall(r"<select\b", source)),
        "raw_textarea_count": len(re.findall(r"<textarea\b", source)),
        "design_system_component_count": len(re.findall(r"<Sc[A-Z][A-Za-z0-9]*\b", source)),
        "inline_style_count": len(re.findall(r"\bstyle\s*=", source)),
        "hard_color_count": len(re.findall(r"#[0-9a-fA-F]{3,8}\b|(?:rgb|hsl)a?\(", source)),
    }


def route_inventory() -> list[dict[str, object]]:
    source = text(WEB / "router/index.ts")
    rows = []
    pattern = re.compile(
        r"\{\s*path:\s*'(?P<path>[^']+)',\s*name:\s*'(?P<name>[^']+)',"
        r"\s*component:\s*\(\)\s*=>\s*import\('(?P<component>[^']+)'\),"
        r"\s*meta:\s*\{(?P<meta>[^}]+)\}\s*\}"
    )
    for match in pattern.finditer(source):
        path = match.group("path")
        component = match.group("component")
        if "config" not in path and "ContractForm" not in component:
            continue
        rows.append(
            {
                "path": path,
                "name": match.group("name"),
                "component": component,
                "admin_only_meta": "adminOnly: true" in match.group("meta"),
            }
        )
    return rows


def api_inventory() -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for relative in ("api/businessConfig.ts", "api/menuConfig.ts"):
        source = text(WEB / relative)
        output[relative] = re.findall(r"export async function\s+([A-Za-z0-9_]+)\s*\(", source)
    return output


def intent_inventory() -> list[str]:
    source = text(WEB / "app/businessConfigBoundaries.ts")
    return sorted(set(re.findall(r"'((?:ui|sc)\.[a-zA-Z0-9_.]+)'", source)))


def technical_exposure_inventory() -> list[dict[str, object]]:
    path = WEB / "views/BusinessConfigSurfaceView.vue"
    source = text(path)
    terms = ("业务对象", "action_id", "view_id", "role_key", "boundary", "runtime", "snapshot")
    rows = []
    for line_no, line in enumerate(source.splitlines(), 1):
        matched = [term for term in terms if term in line]
        if matched:
            rows.append({"line": line_no, "terms": matched, "text": line.strip()[:240]})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="artifacts/frontend-professional/lc-audit-01/static-inventory.json",
    )
    args = parser.parse_args()
    output = ROOT / args.output
    files = [path for path in SURFACE_FILES if path.is_file()]
    metrics = [file_metrics(path) for path in files]
    payload = {
        "schema_version": "lc_audit_01_static_inventory.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git": {
            "sha": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
        },
        "scope": {
            "product_code_modified": False,
            "database_read": False,
            "database_write": False,
            "surface_file_count": len(metrics),
        },
        "administrator_authorities": [
            "smart_construction_core.group_sc_role_business_admin",
            "smart_construction_core.group_sc_cap_business_config_admin",
            "smart_construction_core.group_sc_cap_config_admin (historical XMLID)",
            "smart_core.group_smart_core_business_config_admin",
            "smart_core.group_smart_core_admin",
        ],
        "formal_routes": route_inventory(),
        "frontend_api_functions": api_inventory(),
        "intent_names": intent_inventory(),
        "surface_files": metrics,
        "totals": {
            key: sum(int(row[key]) for row in metrics)
            for key in (
                "lines",
                "raw_button_count",
                "raw_input_count",
                "raw_select_count",
                "raw_textarea_count",
                "design_system_component_count",
                "inline_style_count",
                "hard_color_count",
            )
        },
        "technical_exposure_source_rows": technical_exposure_inventory(),
        "frozen_editor_denominator": [
            "form_fields_and_layout",
            "list_columns",
            "search_filters_and_grouping",
            "analysis_pivot_and_graph",
            "menu_orchestration",
            "approval_policy_and_steps",
        ],
        "governance_denominator": [
            "coverage_scan_and_bootstrap",
            "contract_versions_and_rollback",
            "snapshot_export_compare_and_remediation",
            "delivery_readiness",
            "runtime_preview",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "totals": payload["totals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
