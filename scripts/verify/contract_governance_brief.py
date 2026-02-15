#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_COVERAGE = ROOT / "artifacts" / "contract_governance_coverage.json"
INPUT_SCENE_CAP = ROOT / "artifacts" / "scene_capability_contract_guard.json"
OUT_JSON = ROOT / "artifacts" / "contract_governance_brief.json"
OUT_MD = ROOT / "artifacts" / "contract_governance_brief.md"
OUT_PREV_JSON = ROOT / "artifacts" / "contract_governance_brief.prev.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _coverage_ratio_to_float(raw: Any) -> float | None:
    if not isinstance(raw, str) or "/" not in raw:
        return None
    left, right = raw.split("/", 1)
    left_i = _to_int(left)
    right_i = _to_int(right)
    if left_i is None or right_i in (None, 0):
        return None
    return float(left_i) / float(right_i)


def main() -> int:
    prev = _load_json(OUT_JSON)
    coverage = _load_json(INPUT_COVERAGE)
    scene_cap = _load_json(INPUT_SCENE_CAP)

    issues = []
    if not coverage:
        issues.append(f"missing_or_invalid: {INPUT_COVERAGE.as_posix()}")
    if not scene_cap:
        issues.append(f"missing_or_invalid: {INPUT_SCENE_CAP.as_posix()}")

    coverage_ok = bool(coverage.get("ok")) if coverage else False
    scene_cap_ok = bool(scene_cap.get("ok")) if scene_cap else False
    if coverage and not coverage_ok:
        issues.append("contract_governance_coverage_not_ok")
    if scene_cap and not scene_cap_ok:
        issues.append("scene_capability_contract_guard_not_ok")

    prev_metrics = prev.get("metrics") if isinstance(prev.get("metrics"), dict) else {}

    summary = {
        "ok": (len(issues) == 0),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "contract_governance_coverage": INPUT_COVERAGE.as_posix(),
            "scene_capability_contract_guard": INPUT_SCENE_CAP.as_posix(),
        },
        "checks": {
            "contract_governance_coverage_ok": coverage_ok,
            "scene_capability_contract_guard_ok": scene_cap_ok,
        },
        "metrics": {
            "coverage_ratio": coverage.get("coverage_ratio"),
            "scene_count": ((scene_cap.get("summary") or {}).get("scene_count")),
            "capability_count": ((scene_cap.get("summary") or {}).get("capability_count")),
            "missing_ref_count": ((scene_cap.get("summary") or {}).get("missing_ref_count")),
            "error_count": ((scene_cap.get("summary") or {}).get("error_count")),
        },
        "issues": issues,
    }

    delta = {}
    for key in ("scene_count", "capability_count", "missing_ref_count", "error_count"):
        cur_i = _to_int(summary["metrics"].get(key))
        prev_i = _to_int(prev_metrics.get(key))
        if cur_i is None or prev_i is None:
            delta[key] = None
        else:
            delta[key] = cur_i - prev_i

    cur_cov = _coverage_ratio_to_float(summary["metrics"].get("coverage_ratio"))
    prev_cov = _coverage_ratio_to_float(prev_metrics.get("coverage_ratio"))
    coverage_delta = None if (cur_cov is None or prev_cov is None) else (cur_cov - prev_cov)
    summary["trend"] = {
        "has_previous": bool(prev),
        "previous_generated_at": prev.get("generated_at") if isinstance(prev, dict) else None,
        "delta": {
            **delta,
            "coverage_ratio_delta": coverage_delta,
        },
    }

    if summary["trend"]["has_previous"]:
        if isinstance(coverage_delta, float) and coverage_delta < 0:
            issues.append("coverage_ratio_regressed")
        if isinstance(delta.get("missing_ref_count"), int) and delta["missing_ref_count"] > 0:
            issues.append("missing_ref_count_increased")
        if isinstance(delta.get("error_count"), int) and delta["error_count"] > 0:
            issues.append("error_count_increased")
        summary["ok"] = (len(issues) == 0)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    if prev:
        OUT_PREV_JSON.write_text(json.dumps(prev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Contract Governance Brief",
        "",
        f"- status: {'PASS' if summary['ok'] else 'FAIL'}",
        f"- generated_at: {summary['generated_at']}",
        f"- coverage_ratio: {summary['metrics']['coverage_ratio']}",
        f"- scene_count: {summary['metrics']['scene_count']}",
        f"- capability_count: {summary['metrics']['capability_count']}",
        f"- missing_ref_count: {summary['metrics']['missing_ref_count']}",
        f"- error_count: {summary['metrics']['error_count']}",
        f"- has_previous: {summary['trend']['has_previous']}",
        "",
        "## Check Status",
        "",
        f"- contract_governance_coverage_ok: {coverage_ok}",
        f"- scene_capability_contract_guard_ok: {scene_cap_ok}",
    ]
    if summary["trend"]["has_previous"]:
        d = summary["trend"]["delta"]
        lines.extend([
            "",
            "## Trend",
            "",
            f"- previous_generated_at: {summary['trend']['previous_generated_at']}",
            f"- delta.scene_count: {d.get('scene_count')}",
            f"- delta.capability_count: {d.get('capability_count')}",
            f"- delta.missing_ref_count: {d.get('missing_ref_count')}",
            f"- delta.error_count: {d.get('error_count')}",
            f"- delta.coverage_ratio: {d.get('coverage_ratio_delta')}",
        ])
    if issues:
        lines.extend(["", "## Issues", ""])
        lines.extend([f"- {item}" for item in issues])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if not summary["ok"]:
        print("[contract_governance_brief] FAIL")
        return 1
    print("[contract_governance_brief] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
