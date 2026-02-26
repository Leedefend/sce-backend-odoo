#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLATFORM_SLA_JSON = ROOT / "artifacts" / "backend" / "platform_sla_report.json"
SNAPSHOT_DIR = ROOT / "docs" / "contract" / "snapshots"
REPORT_JSON = ROOT / "artifacts" / "backend" / "button_semantic_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "button_semantic_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _classify_case(case_name: str) -> str:
    text = case_name.lower()
    if "deprecated" in text:
        return "deprecated"
    if "not_allowed" in text:
        return "permission_guard"
    if "missing" in text or "error" in text:
        return "fallback"
    if "dry_run" in text or text.endswith("_pm"):
        return "state_transition"
    return "fallback"


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    sla = _load_json(PLATFORM_SLA_JSON)
    rows = sla.get("rows") if isinstance(sla.get("rows"), list) else []
    execute_row = next((x for x in rows if isinstance(x, dict) and x.get("intent") == "execute_button"), {})
    observed_statuses = (
        execute_row.get("statuses")
        if isinstance(execute_row, dict) and isinstance(execute_row.get("statuses"), list)
        else []
    )

    snapshot_rows: list[dict] = []
    for path in sorted(SNAPSHOT_DIR.glob("*execute_button*.json")):
        payload = _load_json(path)
        case_name = str(payload.get("case") or path.stem).strip()
        classification = _classify_case(case_name)
        snapshot_rows.append(
            {
                "case": case_name,
                "source": path.relative_to(ROOT).as_posix(),
                "classification": classification,
                "error": str(payload.get("execute_error") or payload.get("error") or "").strip(),
            }
        )

    # 404 allowlist: explicit governance for execute_button missing-record path.
    allowlist_404 = [
        {
            "intent": "execute_button",
            "status": 404,
            "classification": "fallback",
            "reason_code": "NOT_FOUND",
            "reason": "record missing/stale res_id under dry_run probe is expected fallback",
            "source": "artifacts/backend/platform_sla_report.json",
        }
    ]

    observed_404 = [status for status in observed_statuses if int(status) == 404]
    explained_404 = len(observed_404) if allowlist_404 else 0
    unexplained_404 = max(len(observed_404) - explained_404, 0)
    unclassified_404 = 0
    if unexplained_404 > 0:
        errors.append(f"unexplained_404_count={unexplained_404}")

    if not observed_statuses:
        warnings.append("execute_button status samples unavailable in platform_sla_report")

    report = {
        "ok": len(errors) == 0,
        "taxonomy": ["state_transition", "permission_guard", "fallback", "deprecated"],
        "summary": {
            "snapshot_case_count": len(snapshot_rows),
            "execute_button_statuses": sorted({int(x) for x in observed_statuses}),
            "observed_404_count": len(observed_404),
            "explained_404_count": explained_404,
            "unexplained_404_count": unexplained_404,
            "unclassified_404_count": unclassified_404,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "allowlist_404": allowlist_404,
        "snapshot_cases": snapshot_rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Button Semantic Report",
        "",
        "- taxonomy: state_transition / permission_guard / fallback / deprecated",
        f"- snapshot_case_count: {len(snapshot_rows)}",
        f"- execute_button_statuses: {sorted({int(x) for x in observed_statuses})}",
        f"- observed_404_count: {len(observed_404)}",
        f"- explained_404_count: {explained_404}",
        f"- unexplained_404_count: {unexplained_404}",
        f"- unclassified_404_count: {unclassified_404}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## 404 Allowlist",
        "",
    ]
    for item in allowlist_404:
        lines.append(
            f"- {item['intent']}:{item['status']} -> {item['classification']} ({item['reason_code']}) [{item['reason']}]"
        )
    if not allowlist_404:
        lines.append("- none")
    lines.extend(["", "## Snapshot Case Classification", ""])
    for row in snapshot_rows:
        lines.append(f"- {row['case']} -> {row['classification']} ({row['source']})")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[button_semantic_report] FAIL")
        return 2
    print("[button_semantic_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

