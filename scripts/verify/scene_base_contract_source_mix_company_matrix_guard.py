#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_base_contract_source_mix_company_matrix_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_base_contract_source_mix_company_matrix_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    companies = [_text(item) for item in _as_list(baseline.get("companies")) if _text(item)]
    if not companies:
        print("[scene_base_contract_source_mix_company_matrix_guard] FAIL")
        print(" - companies is empty")
        return 1

    state_files = _as_dict(baseline.get("state_files"))
    thresholds = _as_dict(baseline.get("thresholds"))
    min_scene_count = _safe_int(thresholds.get("min_scene_count"), 1)
    min_asset_ratio = _safe_float(thresholds.get("min_asset_ratio"), 0.0)
    max_runtime_minimal_ratio = _safe_float(thresholds.get("max_runtime_minimal_ratio"), 1.0)
    max_none_ratio = _safe_float(thresholds.get("max_none_ratio"), 1.0)
    min_companies_observed = _safe_int(thresholds.get("min_companies_observed"), 1)

    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_base_contract_source_mix_company_matrix_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_base_contract_source_mix_company_matrix_report.md"
    )

    errors: list[str] = []
    company_reports: dict[str, dict[str, Any]] = {}
    observed_company_ids: set[int] = set()

    for company_key in companies:
        state_rel = _text(state_files.get(company_key))
        if not state_rel:
            errors.append(f"missing state file mapping for company key: {company_key}")
            continue
        state_path = ROOT / state_rel
        state = _load_json(state_path)
        if not state:
            errors.append(f"missing or invalid state for company key {company_key}: {state_rel}")
            continue

        scene_count = _safe_int(state.get("scene_count"), 0)
        kind_ratios = _as_dict(state.get("source_kind_ratios"))
        if not kind_ratios:
            kind_counts = _as_dict(state.get("source_kind_counts"))
            denom = float(scene_count) if scene_count > 0 else 1.0
            kind_ratios = {key: float(_safe_int(value, 0)) / denom for key, value in kind_counts.items()}

        asset_ratio = _safe_float(kind_ratios.get("asset"), 0.0)
        runtime_minimal_ratio = _safe_float(kind_ratios.get("runtime_minimal"), 0.0)
        none_ratio = _safe_float(kind_ratios.get("none"), 0.0)
        company_id = _safe_int(state.get("company_id"), 0)
        if company_id > 0:
            observed_company_ids.add(company_id)

        company_errors: list[str] = []
        if scene_count < min_scene_count:
            company_errors.append(f"scene_count {scene_count} < {min_scene_count}")
        if asset_ratio < min_asset_ratio:
            company_errors.append(f"asset_ratio {asset_ratio:.4f} < {min_asset_ratio:.4f}")
        if runtime_minimal_ratio > max_runtime_minimal_ratio:
            company_errors.append(
                f"runtime_minimal_ratio {runtime_minimal_ratio:.4f} > {max_runtime_minimal_ratio:.4f}"
            )
        if none_ratio > max_none_ratio:
            company_errors.append(f"none_ratio {none_ratio:.4f} > {max_none_ratio:.4f}")

        if company_errors:
            errors.extend([f"{company_key}: {item}" for item in company_errors])

        company_reports[company_key] = {
            "state_file": state_rel,
            "company_id": company_id,
            "scene_count": scene_count,
            "asset_ratio": asset_ratio,
            "runtime_minimal_ratio": runtime_minimal_ratio,
            "none_ratio": none_ratio,
            "errors": company_errors,
        }

    if len(observed_company_ids) < min_companies_observed:
        errors.append(
            f"observed company count {len(observed_company_ids)} < {min_companies_observed}; "
            f"observed={sorted(observed_company_ids)}"
        )

    report = {
        "ok": len(errors) == 0,
        "companies": companies,
        "company_reports": company_reports,
        "observed_company_ids": sorted(observed_company_ids),
        "errors": errors,
        "sources": {"baseline": BASELINE_PATH.relative_to(ROOT).as_posix()},
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = ["# Scene Base Contract Source Mix Company Matrix Report", ""]
    for company_key in companies:
        item = _as_dict(company_reports.get(company_key))
        lines.append(
            f"- {company_key}: company_id=`{_safe_int(item.get('company_id'), 0)}` scene_count=`{_safe_int(item.get('scene_count'), 0)}`"
        )
        lines.append(f"  asset_ratio=`{_safe_float(item.get('asset_ratio'), 0.0):.4f}`")
        lines.append(
            f"  runtime_minimal_ratio=`{_safe_float(item.get('runtime_minimal_ratio'), 0.0):.4f}`"
        )
        lines.append(f"  none_ratio=`{_safe_float(item.get('none_ratio'), 0.0):.4f}`")
    lines.append("")
    lines.append(f"- observed_company_ids: `{sorted(observed_company_ids)}`")
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_base_contract_source_mix_company_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_base_contract_source_mix_company_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

