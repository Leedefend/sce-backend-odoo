#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_source_fallback_burndown_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


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


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
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
        print("[scene_source_fallback_burndown_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    source_mix_report_path = ROOT / _text(
        baseline.get("source_mix_report_file") or "artifacts/backend/scene_base_contract_source_mix_report.json"
    )
    state_path = ROOT / _text(
        baseline.get("state_file") or "artifacts/backend/scene_source_fallback_burndown_state.json"
    )
    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_source_fallback_burndown_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_source_fallback_burndown_report.md"
    )

    source_report = _load_json(source_mix_report_path)
    if not source_report:
        print("[scene_source_fallback_burndown_guard] FAIL")
        print(f" - missing source mix report: {source_mix_report_path.relative_to(ROOT).as_posix()}")
        return 1

    summary = _as_dict(source_report.get("summary"))
    counts = _as_dict(summary.get("source_kind_counts"))
    ratios = _as_dict(summary.get("source_kind_ratios"))

    scene_count = _safe_int(summary.get("scene_count"), 0)
    runtime_fallback_count = _safe_int(counts.get("runtime_fallback"), 0)
    runtime_minimal_count = _safe_int(counts.get("runtime_minimal"), 0)
    runtime_fallback_ratio = _safe_float(summary.get("runtime_fallback_ratio"), _safe_float(ratios.get("runtime_fallback"), 0.0))
    runtime_minimal_ratio = _safe_float(summary.get("runtime_minimal_ratio"), _safe_float(ratios.get("runtime_minimal"), 0.0))

    max_runtime_fallback_ratio = _safe_float(baseline.get("max_runtime_fallback_ratio"), 1.0)
    max_runtime_minimal_ratio = _safe_float(baseline.get("max_runtime_minimal_ratio"), 1.0)
    max_fallback_scene_growth_per_run = _safe_int(baseline.get("max_fallback_scene_growth_per_run"), 0)
    max_minimal_scene_growth_per_run = _safe_int(baseline.get("max_minimal_scene_growth_per_run"), 0)
    enforce_non_increasing = _safe_bool(baseline.get("enforce_non_increasing"), True)

    previous = _load_json(state_path)
    prev_fallback = _safe_int(previous.get("runtime_fallback_count"), 0)
    prev_minimal = _safe_int(previous.get("runtime_minimal_count"), 0)
    fallback_growth = runtime_fallback_count - prev_fallback
    minimal_growth = runtime_minimal_count - prev_minimal

    errors: list[str] = []
    if runtime_fallback_ratio > max_runtime_fallback_ratio:
        errors.append(
            f"runtime_fallback_ratio {runtime_fallback_ratio:.4f} > {max_runtime_fallback_ratio:.4f}"
        )
    if runtime_minimal_ratio > max_runtime_minimal_ratio:
        errors.append(
            f"runtime_minimal_ratio {runtime_minimal_ratio:.4f} > {max_runtime_minimal_ratio:.4f}"
        )
    if enforce_non_increasing and previous:
        if fallback_growth > max_fallback_scene_growth_per_run:
            errors.append(
                f"runtime_fallback_count growth {fallback_growth} > {max_fallback_scene_growth_per_run}"
            )
        if minimal_growth > max_minimal_scene_growth_per_run:
            errors.append(
                f"runtime_minimal_count growth {minimal_growth} > {max_minimal_scene_growth_per_run}"
            )

    state_payload = {
        "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "scene_count": scene_count,
        "runtime_fallback_count": runtime_fallback_count,
        "runtime_minimal_count": runtime_minimal_count,
        "runtime_fallback_ratio": runtime_fallback_ratio,
        "runtime_minimal_ratio": runtime_minimal_ratio,
        "fallback_growth": fallback_growth,
        "minimal_growth": minimal_growth,
        "source_report": source_mix_report_path.relative_to(ROOT).as_posix(),
    }
    _write(state_path, json.dumps(state_payload, ensure_ascii=False, indent=2))

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "summary": state_payload,
        "thresholds": {
            "max_runtime_fallback_ratio": max_runtime_fallback_ratio,
            "max_runtime_minimal_ratio": max_runtime_minimal_ratio,
            "max_fallback_scene_growth_per_run": max_fallback_scene_growth_per_run,
            "max_minimal_scene_growth_per_run": max_minimal_scene_growth_per_run,
            "enforce_non_increasing": enforce_non_increasing,
        },
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "source_mix_report_file": source_mix_report_path.relative_to(ROOT).as_posix(),
            "state_file": state_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = [
        "# Scene Source Fallback Burn-down Report",
        "",
        f"- scene_count: `{scene_count}`",
        f"- runtime_fallback_count: `{runtime_fallback_count}` (growth `{fallback_growth}`)",
        f"- runtime_minimal_count: `{runtime_minimal_count}` (growth `{minimal_growth}`)",
        f"- runtime_fallback_ratio: `{runtime_fallback_ratio:.4f}`",
        f"- runtime_minimal_ratio: `{runtime_minimal_ratio:.4f}`",
    ]
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_source_fallback_burndown_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_source_fallback_burndown_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

