#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "ops" / "audits" / "native_view_ecosystem_sample_registry_v1.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "native_view_ecosystem_readiness_report.json"
OUT_MD = ROOT / "artifacts" / "backend" / "native_view_ecosystem_readiness_report.md"


def main() -> int:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}
    cases = payload.get("cases") if isinstance(payload.get("cases"), list) else []

    total = len(cases)
    ready = sum(1 for c in cases if isinstance(c, dict) and bool(c.get("ready")))
    by_view = Counter()
    by_domain = Counter()
    for case in cases:
        if not isinstance(case, dict):
            continue
        by_view[str(case.get("view_type") or "unknown")] += 1
        by_domain[str(case.get("domain") or "unknown")] += 1

    report = {
        "ok": total > 0,
        "summary": {
            "target_total": int(payload.get("target_total") or total),
            "total_case_count": total,
            "ready_case_count": ready,
            "gap_case_count": total - ready,
            "ready_ratio": round(ready / total, 4) if total else 0.0,
            "by_view_type": dict(by_view),
            "by_domain": dict(by_domain),
        },
        "cases": cases,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Native View Ecosystem Readiness Report",
        "",
        f"- target_total: {report['summary']['target_total']}",
        f"- total_case_count: {report['summary']['total_case_count']}",
        f"- ready_case_count: {report['summary']['ready_case_count']}",
        f"- gap_case_count: {report['summary']['gap_case_count']}",
        f"- ready_ratio: {report['summary']['ready_ratio']}",
        f"- by_view_type: {json.dumps(report['summary']['by_view_type'], ensure_ascii=False)}",
        f"- by_domain: {json.dumps(report['summary']['by_domain'], ensure_ascii=False)}",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    print("[native_view_ecosystem_readiness_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

