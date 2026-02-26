#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_CAPABILITY_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
REPORT_MD = ROOT / "docs" / "product" / "scene_compression_model_v1.md"

PKG_SUFFIX_RE = re.compile(r"__pkg\d+$")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_scene(scene_key: str) -> str:
    return PKG_SUFFIX_RE.sub("", scene_key)


def _resolve_domain(scene_key: str) -> str:
    key = scene_key.lower()
    if key.startswith("projects."):
        return "project_execution"
    if key.startswith("finance."):
        return "finance_operations"
    if key.startswith("cost."):
        return "cost_control"
    if key.startswith("portal."):
        return "portal_governance"
    if key.startswith("default"):
        return "workspace_shell"
    if key.startswith("data."):
        return "data_foundation"
    return "misc_domain"


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    payload = _load_json(SCENE_CAPABILITY_MATRIX_JSON)
    scene_keys = payload.get("scene_keys") if isinstance(payload.get("scene_keys"), list) else []
    scene_keys = sorted({str(x or "").strip() for x in scene_keys if str(x or "").strip()})
    if not scene_keys:
        errors.append("scene_keys is empty")

    rows: list[dict] = []
    domain_to_scenes: dict[str, list[str]] = {}
    canonical_to_runtime: dict[str, list[str]] = {}

    for scene_key in scene_keys:
        canonical = _normalize_scene(scene_key)
        domain = _resolve_domain(canonical)
        rows.append(
            {
                "runtime_scene": scene_key,
                "canonical_scene": canonical,
                "domain": domain,
                "source_type": "derived_pkg" if canonical != scene_key else "catalog_or_system",
            }
        )
        domain_to_scenes.setdefault(domain, []).append(scene_key)
        canonical_to_runtime.setdefault(canonical, []).append(scene_key)

    domain_rows = []
    for domain, scenes in sorted(domain_to_scenes.items()):
        domain_rows.append(
            {
                "domain": domain,
                "runtime_scene_count": len(scenes),
                "canonical_scene_count": len({_normalize_scene(x) for x in scenes}),
                "sample_scenes": sorted(scenes)[:8],
            }
        )

    unassigned = [row["runtime_scene"] for row in rows if not row["domain"]]
    if unassigned:
        errors.append(f"unassigned_scene_count={len(unassigned)}")

    if len(domain_rows) > 25:
        errors.append(f"domain_count_exceeds_target={len(domain_rows)}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "runtime_scene_count": len(scene_keys),
            "canonical_scene_count": len(canonical_to_runtime),
            "domain_count": len(domain_rows),
            "unassigned_scene_count": len(unassigned),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "acceptance": {
            "all_scene_assigned": len(unassigned) == 0,
            "domain_count_le_25": len(domain_rows) <= 25,
        },
        "domains": domain_rows,
        "scene_to_domain": rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Compression Model v1",
        "",
        "- objective: compress runtime scenes into product-facing domains (<=25)",
        f"- runtime_scene_count: {len(scene_keys)}",
        f"- canonical_scene_count: {len(canonical_to_runtime)}",
        f"- domain_count: {len(domain_rows)}",
        f"- unassigned_scene_count: {len(unassigned)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Acceptance",
        "",
        f"- all_scene_assigned: {'PASS' if len(unassigned) == 0 else 'FAIL'}",
        f"- domain_count_le_25: {'PASS' if len(domain_rows) <= 25 else 'FAIL'}",
        "",
        "## Domain Mapping",
        "",
        "| domain | runtime_scene_count | canonical_scene_count | sample_scenes |",
        "|---|---:|---:|---|",
    ]
    for row in domain_rows:
        lines.append(
            f"| {row['domain']} | {row['runtime_scene_count']} | {row['canonical_scene_count']} | "
            f"{','.join(row['sample_scenes']) if row['sample_scenes'] else '-'} |"
        )
    lines.extend(["", "## Scene -> Domain", ""])
    for row in rows:
        lines.append(f"- {row['runtime_scene']} -> {row['domain']} (canonical={row['canonical_scene']})")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[scene_compression_model_report] FAIL")
        return 2
    print("[scene_compression_model_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

