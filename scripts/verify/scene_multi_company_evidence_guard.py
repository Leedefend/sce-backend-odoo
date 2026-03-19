#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_multi_company_evidence_guard.json"


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
        print("[scene_multi_company_evidence_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    company_matrix_report_path = ROOT / _text(
        baseline.get("company_matrix_report_file")
        or "artifacts/backend/scene_base_contract_source_mix_company_matrix_report.json"
    )
    state_path = ROOT / _text(
        baseline.get("state_file") or "artifacts/backend/scene_multi_company_evidence_state.json"
    )
    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_multi_company_evidence_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_multi_company_evidence_report.md"
    )

    min_companies_block = _safe_int(baseline.get("min_companies_block"), 1)
    min_companies_target = _safe_int(baseline.get("min_companies_target"), 2)
    strict_target = str(os.getenv("SC_MULTI_COMPANY_EVIDENCE_STRICT") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    matrix_report = _load_json(company_matrix_report_path)
    if not matrix_report:
        print("[scene_multi_company_evidence_guard] FAIL")
        print(
            " - missing company matrix report: "
            f"{company_matrix_report_path.relative_to(ROOT).as_posix()}"
        )
        return 1

    observed_now = sorted(
        {
            _safe_int(item)
            for item in _as_list(matrix_report.get("observed_company_ids"))
            if _safe_int(item) > 0
        }
    )
    company_reports = _as_dict(matrix_report.get("company_reports"))
    mapped_ids = sorted(
        {
            _safe_int(_as_dict(item).get("company_id"))
            for item in company_reports.values()
            if _safe_int(_as_dict(item).get("company_id")) > 0
        }
    )

    previous = _load_json(state_path)
    historical_ids = {
        _safe_int(item)
        for item in _as_list(previous.get("historical_observed_company_ids"))
        if _safe_int(item) > 0
    }
    historical_ids.update(observed_now)
    historical_sorted = sorted(historical_ids)

    errors: list[str] = []
    warnings: list[str] = []

    if len(observed_now) < min_companies_block:
        errors.append(
            f"current observed company count {len(observed_now)} < block threshold {min_companies_block}; observed={observed_now}"
        )
    if len(observed_now) < min_companies_target:
        warnings.append(
            f"current observed company count {len(observed_now)} < target {min_companies_target}; observed={observed_now}"
        )
    if len(historical_sorted) < min_companies_target:
        warnings.append(
            "historical observed company count "
            f"{len(historical_sorted)} < target {min_companies_target}; historical={historical_sorted}"
        )
    if len(mapped_ids) <= 1:
        warnings.append(f"company matrix mapped ids are not diversified yet: mapped={mapped_ids}")
    if strict_target and len(historical_sorted) < min_companies_target:
        errors.append(
            "strict target enabled but historical observed company count "
            f"{len(historical_sorted)} < {min_companies_target}"
        )

    state_payload = {
        "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "current_observed_company_ids": observed_now,
        "historical_observed_company_ids": historical_sorted,
        "mapped_company_ids": mapped_ids,
        "strict_target": strict_target,
    }
    _write(state_path, json.dumps(state_payload, ensure_ascii=False, indent=2))

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": state_payload,
        "thresholds": {
            "min_companies_block": min_companies_block,
            "min_companies_target": min_companies_target,
            "strict_target": strict_target,
        },
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "company_matrix_report_file": company_matrix_report_path.relative_to(ROOT).as_posix(),
            "state_file": state_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = [
        "# Scene Multi-Company Evidence Report",
        "",
        f"- current_observed_company_ids: `{observed_now}`",
        f"- historical_observed_company_ids: `{historical_sorted}`",
        f"- mapped_company_ids: `{mapped_ids}`",
        f"- strict_target: `{strict_target}`",
    ]
    if warnings:
        lines.extend(["", "## Warnings"] + [f"- {item}" for item in warnings])
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_multi_company_evidence_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    if warnings:
        print("[scene_multi_company_evidence_guard] PASS_WITH_WARNINGS")
        for item in warnings:
            print(f" - {item}")
    else:
        print("[scene_multi_company_evidence_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

