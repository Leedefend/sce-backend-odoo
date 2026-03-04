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
OUT_PREV_JSON = ROOT / "artifacts" / "grouped_governance_policy_matrix.prev.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def main() -> int:
    errors: list[str] = []
    prev = _load_json(OUT_JSON)

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

    prev_summary = prev.get("summary") if isinstance(prev.get("summary"), dict) else {}
    cur_summary = policy_matrix["summary"]
    delta: dict[str, int | None] = {}
    for key in (
        "grouped_governance_brief_policy_count",
        "grouped_drift_summary_policy_count",
        "contract_evidence_grouped_governance_policy_count",
    ):
        cur_i = _to_int(cur_summary.get(key))
        prev_i = _to_int(prev_summary.get(key))
        if cur_i is None or prev_i is None:
            delta[key] = None
        else:
            delta[key] = cur_i - prev_i
    policy_matrix["trend"] = {
        "has_previous": bool(prev),
        "previous_report_json": prev_summary.get("report_json") if isinstance(prev_summary, dict) else None,
        "delta": delta,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    if prev:
        OUT_PREV_JSON.write_text(json.dumps(prev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
        f"- has_previous: {policy_matrix['trend']['has_previous']}",
        "",
        "## Sources",
        "",
        f"- grouped_governance_brief_baseline_guard: `{policy_matrix['sources']['grouped_governance_brief_baseline_guard']}`",
        f"- grouped_drift_summary_baseline_guard: `{policy_matrix['sources']['grouped_drift_summary_baseline_guard']}`",
        f"- contract_evidence_guard_baseline: `{policy_matrix['sources']['contract_evidence_guard_baseline']}`",
    ]
    if policy_matrix["trend"]["has_previous"]:
        d = policy_matrix["trend"]["delta"]
        lines.extend(
            [
                "",
                "## Trend",
                "",
                f"- delta.grouped_governance_brief_policy_count: {d.get('grouped_governance_brief_policy_count')}",
                f"- delta.grouped_drift_summary_policy_count: {d.get('grouped_drift_summary_policy_count')}",
                (
                    "- delta.contract_evidence_grouped_governance_policy_count: "
                    f"{d.get('contract_evidence_grouped_governance_policy_count')}"
                ),
            ]
        )
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
