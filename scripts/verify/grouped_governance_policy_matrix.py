#!/usr/bin/env python3
"""Export grouped governance policy matrix for audit readability."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASE_GGB = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_brief_baseline_guard.json"
BASE_GDS = ROOT / "scripts" / "verify" / "baselines" / "grouped_drift_summary_baseline_guard.json"
BASE_EVID = ROOT / "scripts" / "verify" / "baselines" / "contract_evidence_guard_baseline.json"
OUT_JSON = ROOT / "artifacts" / "grouped_governance_policy_matrix.json"
OUT_MD = ROOT / "artifacts" / "grouped_governance_policy_matrix.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []

    ggb = _load_json(BASE_GGB)
    gds = _load_json(BASE_GDS)
    evid = _load_json(BASE_EVID)

    if not ggb:
        errors.append(f"missing or invalid baseline: {BASE_GGB.relative_to(ROOT).as_posix()}")
    if not gds:
        errors.append(f"missing or invalid baseline: {BASE_GDS.relative_to(ROOT).as_posix()}")
    if not evid:
        errors.append(f"missing or invalid baseline: {BASE_EVID.relative_to(ROOT).as_posix()}")

    evidence_keys = sorted([k for k in evid.keys() if str(k).startswith("require_grouped_governance_")])
    policy_matrix = {
        "ok": len(errors) == 0,
        "sources": {
            "grouped_governance_brief_baseline_guard": BASE_GGB.relative_to(ROOT).as_posix(),
            "grouped_drift_summary_baseline_guard": BASE_GDS.relative_to(ROOT).as_posix(),
            "contract_evidence_guard_baseline": BASE_EVID.relative_to(ROOT).as_posix(),
        },
        "policy_groups": {
            "grouped_governance_brief": ggb,
            "grouped_drift_summary": gds,
            "contract_evidence_grouped_governance": {key: evid.get(key) for key in evidence_keys},
        },
        "summary": {
            "grouped_governance_brief_policy_count": len(ggb),
            "grouped_drift_summary_policy_count": len(gds),
            "contract_evidence_grouped_governance_policy_count": len(evidence_keys),
            "report_json": OUT_JSON.relative_to(ROOT).as_posix(),
            "report_md": OUT_MD.relative_to(ROOT).as_posix(),
        },
        "errors": errors,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(policy_matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Grouped Governance Policy Matrix",
        "",
        f"- ok: {policy_matrix['ok']}",
        f"- grouped_governance_brief_policy_count: {policy_matrix['summary']['grouped_governance_brief_policy_count']}",
        f"- grouped_drift_summary_policy_count: {policy_matrix['summary']['grouped_drift_summary_policy_count']}",
        (
            "- contract_evidence_grouped_governance_policy_count: "
            f"{policy_matrix['summary']['contract_evidence_grouped_governance_policy_count']}"
        ),
        f"- report_json: `{policy_matrix['summary']['report_json']}`",
        f"- report_md: `{policy_matrix['summary']['report_md']}`",
        "",
        "## Sources",
        "",
        f"- grouped_governance_brief_baseline_guard: `{policy_matrix['sources']['grouped_governance_brief_baseline_guard']}`",
        f"- grouped_drift_summary_baseline_guard: `{policy_matrix['sources']['grouped_drift_summary_baseline_guard']}`",
        f"- contract_evidence_guard_baseline: `{policy_matrix['sources']['contract_evidence_guard_baseline']}`",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend([f"- {line}" for line in errors])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON.relative_to(ROOT)))
    print(str(OUT_MD.relative_to(ROOT)))
    if errors:
        print("[grouped_governance_policy_matrix] FAIL")
        return 1
    print("[grouped_governance_policy_matrix] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
