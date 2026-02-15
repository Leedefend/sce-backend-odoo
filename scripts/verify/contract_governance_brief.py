#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
INPUT_COVERAGE = ROOT / "artifacts" / "contract_governance_coverage.json"
INPUT_SCENE_CAP = ROOT / "artifacts" / "scene_capability_contract_guard.json"
OUT_JSON = ROOT / "artifacts" / "contract_governance_brief.json"
OUT_MD = ROOT / "artifacts" / "contract_governance_brief.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
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

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
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
        "",
        "## Check Status",
        "",
        f"- contract_governance_coverage_ok: {coverage_ok}",
        f"- scene_capability_contract_guard_ok: {scene_cap_ok}",
    ]
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
