#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _parse_ratio(value: object) -> float:
    if isinstance(value, str) and "/" in value:
        left, _, right = value.partition("/")
        try:
            numerator = float(left.strip())
            denominator = float(right.strip())
            if denominator > 0:
                return round(numerator / denominator, 6)
        except Exception:
            return 0.0
    return _safe_float(value, 0.0)


def main() -> int:
    artifacts_root = _resolve_artifacts_dir()
    backend_dir = artifacts_root / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    output_json = backend_dir / "backend_architecture_full_report.json"
    output_md = backend_dir / "backend_architecture_full_report.md"

    local_artifacts = ROOT / "artifacts"
    runtime_surface = _load_json(backend_dir / "runtime_surface_dashboard_report.json") or _load_json(
        local_artifacts / "backend" / "runtime_surface_dashboard_report.json"
    )
    semantic_smoke = _load_json(backend_dir / "contract_assembler_semantic_smoke.json") or _load_json(
        local_artifacts / "backend" / "contract_assembler_semantic_smoke.json"
    )
    role_floor = _load_json(backend_dir / "role_capability_floor_prod_like.json") or _load_json(
        local_artifacts / "backend" / "role_capability_floor_prod_like.json"
    )
    business_baseline = _load_json(local_artifacts / "business_capability_baseline_report.json")
    coverage = _load_json(local_artifacts / "contract_governance_coverage.json")
    boundary_report = _load_json(local_artifacts / "controller_boundary_guard_report.json")
    catalog_alignment = _load_json(local_artifacts / "scene_catalog_runtime_alignment_guard.json")

    checks: list[dict] = []

    checks.append(
        {
            "name": "role_capability_prod_like",
            "ok": bool(role_floor.get("ok") is True),
            "error_count": _safe_int((role_floor.get("summary") or {}).get("error_count"), 0),
            "source": "artifacts/backend/role_capability_floor_prod_like.json",
        }
    )
    checks.append(
        {
            "name": "contract_assembler_semantic_smoke",
            "ok": bool(semantic_smoke.get("ok") is True),
            "error_count": _safe_int((semantic_smoke.get("summary") or {}).get("error_count"), 0),
            "source": "artifacts/backend/contract_assembler_semantic_smoke.json",
        }
    )
    checks.append(
        {
            "name": "runtime_surface_dashboard",
            "ok": bool(runtime_surface.get("ok", True)),
            "warning_count": _safe_int((runtime_surface.get("summary") or {}).get("warning_count"), 0),
            "source": "artifacts/backend/runtime_surface_dashboard_report.json",
        }
    )
    checks.append(
        {
            "name": "business_capability_baseline",
            "ok": bool(business_baseline.get("ok") is True),
            "failed_check_count": _safe_int((business_baseline.get("summary") or {}).get("failed_check_count"), 0),
            "required_intent_count": _safe_int((business_baseline.get("summary") or {}).get("required_intent_count"), 0),
            "required_role_count": _safe_int((business_baseline.get("summary") or {}).get("required_role_count"), 0),
            "catalog_runtime_ratio": _safe_float((business_baseline.get("summary") or {}).get("catalog_runtime_ratio"), 0.0),
            "source": "artifacts/business_capability_baseline_report.json",
        }
    )
    checks.append(
        {
            "name": "contract_governance_coverage",
            "ok": bool(coverage.get("ok") is True),
            "coverage_ratio": _parse_ratio(coverage.get("coverage_ratio")),
            "source": "artifacts/contract_governance_coverage.json",
        }
    )
    checks.append(
        {
            "name": "controller_boundary_report",
            "ok": bool(boundary_report.get("ok", True)),
            "error_count": _safe_int((boundary_report.get("summary") or {}).get("error_count"), 0),
            "source": "artifacts/controller_boundary_guard_report.json",
        }
    )
    checks.append(
        {
            "name": "scene_catalog_runtime_alignment",
            "ok": bool(catalog_alignment.get("ok") is True),
            "catalog_runtime_ratio": _safe_float((catalog_alignment.get("summary") or {}).get("catalog_runtime_ratio"), 0.0),
            "source": "artifacts/scene_catalog_runtime_alignment_guard.json",
        }
    )

    checks = sorted(checks, key=lambda item: str(item.get("name") or ""))
    failed = sorted([item["name"] for item in checks if item.get("ok") is not True])
    warnings = sorted([item["name"] for item in checks if _safe_int(item.get("warning_count"), 0) > 0])
    business_row = next((item for item in checks if item.get("name") == "business_capability_baseline"), {})
    report = {
        "ok": not failed,
        "summary": {
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "warning_check_count": len(warnings),
            "business_required_intent_count": _safe_int(business_row.get("required_intent_count"), 0),
            "business_required_role_count": _safe_int(business_row.get("required_role_count"), 0),
            "business_catalog_runtime_ratio": _safe_float(business_row.get("catalog_runtime_ratio"), 0.0),
            "failed_checks": failed,
            "warning_checks": warnings,
            "artifacts_dir": str(backend_dir),
        },
        "checks": checks,
    }

    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Backend Architecture Full Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- check_count: {report['summary']['check_count']}",
        f"- failed_check_count: {report['summary']['failed_check_count']}",
        f"- warning_check_count: {report['summary']['warning_check_count']}",
        f"- business_required_intent_count: {report['summary']['business_required_intent_count']}",
        f"- business_required_role_count: {report['summary']['business_required_role_count']}",
        f"- business_catalog_runtime_ratio: {report['summary']['business_catalog_runtime_ratio']}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['name']}: {'PASS' if item.get('ok') else 'FAIL'} ({item['source']})")
    if failed:
        lines.extend(["", "## Failed Checks", ""])
        for name in failed:
            lines.append(f"- {name}")
    if warnings:
        lines.extend(["", "## Warning Checks", ""])
        for name in warnings:
            lines.append(f"- {name}")
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(output_json))
    print(str(output_md))
    if not report["ok"]:
        print("[backend_architecture_full_report] FAIL")
        return 1
    print("[backend_architecture_full_report] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
