#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_product_delivery_readiness_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_path(raw: Any, fallback: str) -> Path:
    path_text = _text(raw)
    if not path_text:
        return ROOT / fallback
    return ROOT / path_text


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_product_delivery_readiness_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    snapshot_path = _resolve_path(
        baseline.get("scene_registry_asset_snapshot_state"),
        "artifacts/backend/scene_registry_asset_snapshot_state.json",
    )
    diff_report_path = _resolve_path(
        baseline.get("scene_sample_registry_diff_report"),
        "artifacts/backend/scene_sample_registry_diff_report.json",
    )
    governance_report_path = _resolve_path(
        baseline.get("scene_governance_history_report"),
        "artifacts/backend/scene_governance_history_report.json",
    )
    report_json_path = _resolve_path(
        baseline.get("report_json"),
        "artifacts/backend/scene_product_delivery_readiness_report.json",
    )
    report_md_path = _resolve_path(
        baseline.get("report_md"),
        "artifacts/backend/scene_product_delivery_readiness_report.md",
    )

    snapshot = _load_json(snapshot_path)
    diff_report = _load_json(diff_report_path)
    governance_report = _load_json(governance_report_path)

    snapshot_scene_count = _safe_int(snapshot.get("scene_count"), 0)
    base_contract_bound_scene_count = _safe_int(snapshot.get("base_contract_bound_scene_count"), 0)
    compile_issue_scene_count = _safe_int(snapshot.get("compile_issue_scene_count"), 0)

    diff_summary = _as_dict(diff_report.get("summary"))
    missing_required_scene_count = _safe_int(diff_summary.get("missing_required_scene_count"), 0)
    unbound_matched_scene_count = _safe_int(diff_summary.get("unbound_matched_scene_count"), 0)

    governance_summary = _as_dict(governance_report.get("summary"))
    consumption_enabled = _safe_bool(governance_summary.get("consumption_enabled"), False)
    scene_type_count = _safe_int(governance_summary.get("scene_type_count"), 0)

    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)
    min_base_contract_bound_scene_count = _safe_int(baseline.get("min_base_contract_bound_scene_count"), 1)
    max_compile_issue_scene_count = _safe_int(baseline.get("max_compile_issue_scene_count"), 0)
    max_missing_required_scene_count = _safe_int(baseline.get("max_missing_required_scene_count"), 0)
    max_unbound_matched_scene_count = _safe_int(baseline.get("max_unbound_matched_scene_count"), 0)
    min_scene_type_count = _safe_int(baseline.get("min_scene_type_count"), 1)
    require_consumption_enabled = _safe_bool(baseline.get("require_consumption_enabled"), False)

    errors: list[str] = []
    if snapshot_scene_count < min_scene_count:
        errors.append(f"scene_count below threshold: {snapshot_scene_count} < {min_scene_count}")
    if base_contract_bound_scene_count < min_base_contract_bound_scene_count:
        errors.append(
            "base_contract_bound_scene_count below threshold: "
            f"{base_contract_bound_scene_count} < {min_base_contract_bound_scene_count}"
        )
    if compile_issue_scene_count > max_compile_issue_scene_count:
        errors.append(
            "compile_issue_scene_count above threshold: "
            f"{compile_issue_scene_count} > {max_compile_issue_scene_count}"
        )
    if missing_required_scene_count > max_missing_required_scene_count:
        errors.append(
            "missing_required_scene_count above threshold: "
            f"{missing_required_scene_count} > {max_missing_required_scene_count}"
        )
    if unbound_matched_scene_count > max_unbound_matched_scene_count:
        errors.append(
            "unbound_matched_scene_count above threshold: "
            f"{unbound_matched_scene_count} > {max_unbound_matched_scene_count}"
        )
    if scene_type_count < min_scene_type_count:
        errors.append(f"scene_type_count below threshold: {scene_type_count} < {min_scene_type_count}")
    if require_consumption_enabled and not consumption_enabled:
        errors.append("scene_ready consumption is not enabled")

    observed = {
        "scene_count": snapshot_scene_count,
        "base_contract_bound_scene_count": base_contract_bound_scene_count,
        "compile_issue_scene_count": compile_issue_scene_count,
        "missing_required_scene_count": missing_required_scene_count,
        "unbound_matched_scene_count": unbound_matched_scene_count,
        "scene_type_count": scene_type_count,
        "consumption_enabled": consumption_enabled,
    }
    thresholds = {
        "min_scene_count": min_scene_count,
        "min_base_contract_bound_scene_count": min_base_contract_bound_scene_count,
        "max_compile_issue_scene_count": max_compile_issue_scene_count,
        "max_missing_required_scene_count": max_missing_required_scene_count,
        "max_unbound_matched_scene_count": max_unbound_matched_scene_count,
        "min_scene_type_count": min_scene_type_count,
        "require_consumption_enabled": require_consumption_enabled,
    }

    report = {
        "ok": len(errors) == 0,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "observed": observed,
        "thresholds": thresholds,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "scene_registry_asset_snapshot_state": snapshot_path.relative_to(ROOT).as_posix(),
            "scene_sample_registry_diff_report": diff_report_path.relative_to(ROOT).as_posix(),
            "scene_governance_history_report": governance_report_path.relative_to(ROOT).as_posix(),
        },
        "errors": errors,
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = [
        "# Scene Product Delivery Readiness Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- scene_count: `{snapshot_scene_count}` / min `{min_scene_count}`",
        (
            "- base_contract_bound_scene_count: "
            f"`{base_contract_bound_scene_count}` / min `{min_base_contract_bound_scene_count}`"
        ),
        f"- compile_issue_scene_count: `{compile_issue_scene_count}` / max `{max_compile_issue_scene_count}`",
        f"- missing_required_scene_count: `{missing_required_scene_count}` / max `{max_missing_required_scene_count}`",
        f"- unbound_matched_scene_count: `{unbound_matched_scene_count}` / max `{max_unbound_matched_scene_count}`",
        f"- scene_type_count: `{scene_type_count}` / min `{min_scene_type_count}`",
        f"- consumption_enabled: `{consumption_enabled}` (required `{require_consumption_enabled}`)",
    ]
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_product_delivery_readiness_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_product_delivery_readiness_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

