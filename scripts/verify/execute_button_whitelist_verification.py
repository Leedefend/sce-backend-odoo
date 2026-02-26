#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUTTON_SEM_JSON = ROOT / "artifacts" / "backend" / "button_semantic_report.json"
PLATFORM_SLA_JSON = ROOT / "artifacts" / "backend" / "platform_sla_report.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "execute_button_whitelist_verification.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "execute_button_whitelist_verification.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    button_sem = _load(BUTTON_SEM_JSON)
    platform_sla = _load(PLATFORM_SLA_JSON)

    allowlist = button_sem.get("allowlist_404") if isinstance(button_sem.get("allowlist_404"), list) else []
    allowlist_exec = [
        row
        for row in allowlist
        if isinstance(row, dict) and _norm(row.get("intent")) == "execute_button"
    ]
    allowlist_statuses = {
        int(row.get("status"))
        for row in allowlist_exec
        if str(row.get("status") or "").isdigit()
    }

    sem_summary = button_sem.get("summary") if isinstance(button_sem.get("summary"), dict) else {}
    unclassified_404_count = int(sem_summary.get("unclassified_404_count") or 0)
    unexplained_404_count = int(sem_summary.get("unexplained_404_count") or 0)

    rows = platform_sla.get("rows") if isinstance(platform_sla.get("rows"), list) else []
    exec_row = next(
        (r for r in rows if isinstance(r, dict) and _norm(r.get("intent")) == "execute_button"),
        {},
    )
    observed_statuses = sorted(
        {
            int(s)
            for s in (exec_row.get("statuses") if isinstance(exec_row.get("statuses"), list) else [])
            if str(s).isdigit()
        }
    )
    status_classification = _norm(exec_row.get("status_classification"))

    non2xx_statuses = [s for s in observed_statuses if s < 200 or s >= 300]
    non_allowlisted_statuses = [s for s in non2xx_statuses if s not in allowlist_statuses]

    if not allowlist_exec:
        errors.append("missing execute_button allowlist entry")
    if unclassified_404_count > 0:
        errors.append(f"unclassified_404_count={unclassified_404_count}")
    if unexplained_404_count > 0:
        errors.append(f"unexplained_404_count={unexplained_404_count}")
    if non_allowlisted_statuses:
        errors.append(f"non_allowlisted_status_count={len(non_allowlisted_statuses)}")
    if non2xx_statuses and status_classification != "fallback":
        errors.append("execute_button non2xx must be classified as fallback")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "allowlist_entry_count": len(allowlist_exec),
            "observed_status_count": len(observed_statuses),
            "observed_non2xx_count": len(non2xx_statuses),
            "non_allowlisted_status_count": len(non_allowlisted_statuses),
            "unclassified_404_count": unclassified_404_count,
            "unexplained_404_count": unexplained_404_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "allowlist_execute_button": allowlist_exec,
        "observed_statuses": observed_statuses,
        "observed_non2xx_statuses": non2xx_statuses,
        "non_allowlisted_statuses": non_allowlisted_statuses,
        "platform_status_classification": status_classification,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Execute Button Whitelist Verification",
        "",
        f"- allowlist_entry_count: {payload['summary']['allowlist_entry_count']}",
        f"- observed_statuses: {payload['observed_statuses']}",
        f"- observed_non2xx_statuses: {payload['observed_non2xx_statuses']}",
        f"- non_allowlisted_status_count: {payload['summary']['non_allowlisted_status_count']}",
        f"- unclassified_404_count: {payload['summary']['unclassified_404_count']}",
        f"- unexplained_404_count: {payload['summary']['unexplained_404_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[execute_button_whitelist_verification] FAIL")
        return 2
    print("[execute_button_whitelist_verification] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
