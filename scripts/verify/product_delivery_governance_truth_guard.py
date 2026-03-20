#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKLOG_MD = ROOT / "docs" / "product" / "capability_gap_backlog_v1.md"
SCOREBOARD_MD = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_readiness_scoreboard_v1.md"
CONTEXT_LOG_MD = ROOT / "docs" / "ops" / "iterations" / "delivery_context_switch_log_v1.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_governance_truth_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_governance_truth_guard_report.md"

REQUIRED_HARD_GAP_KEYS = {
    "gap.frontend.action_view_lint_strict",
    "gap.scene_contract_v1_strict_schema",
    "gap.backlog_empty_false_green",
    "gap.delivery_readiness_scoreboard",
}


def _norm(value: object) -> str:
    return str(value or "").strip()


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_md_table(md: str) -> list[dict[str, str]]:
    lines = [line.rstrip() for line in md.splitlines()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 3:
        return []
    header = [part.strip() for part in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        rows.append({header[index]: cells[index] for index in range(len(header))})
    return rows


def _extract_snapshot_value(md: str, key: str) -> str:
    pattern = rf"^-\s+{re.escape(key)}:\s+`?([^`\n]+)`?$"
    match = re.search(pattern, md, flags=re.MULTILINE)
    return _norm(match.group(1) if match else "")


def _parse_scoreboard_rows(md: str, section_name: str) -> int:
    marker = f"## {section_name}"
    start = md.find(marker)
    if start < 0:
        return 0
    section = md[start:].split("\n## ", 1)[0]
    lines = [line.strip() for line in section.splitlines()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 3:
        return 0
    return len(table_lines) - 2


def _commit_exists(commit_ref: str) -> bool:
    if not commit_ref:
        return False
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit_ref}^{{commit}}"],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return False
    return result.returncode == 0


def _parse_utc_timestamp(text: str) -> datetime | None:
    value = _norm(text)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    backlog_md = _read(BACKLOG_MD)
    scoreboard_md = _read(SCOREBOARD_MD)
    context_log_md = _read(CONTEXT_LOG_MD)

    if not backlog_md:
        errors.append("missing capability backlog doc")
    if not scoreboard_md:
        errors.append("missing readiness scoreboard doc")
    if not context_log_md:
        errors.append("missing delivery context-switch log")

    backlog_rows = _parse_md_table(backlog_md)
    if not backlog_rows:
        errors.append("backlog_table_empty_or_unparseable")

    priorities = {row.get("priority", "") for row in backlog_rows}
    for required_priority in ("Blocker", "Pilot Risk", "Post-GA"):
        if required_priority not in priorities:
            errors.append(f"backlog_missing_priority={required_priority}")

    item_keys = {row.get("item_key", "") for row in backlog_rows}
    missing_keys = sorted(key for key in REQUIRED_HARD_GAP_KEYS if key not in item_keys)
    if missing_keys:
        errors.append(f"backlog_missing_hard_gap_keys={','.join(missing_keys)}")

    evidence_empty_count = 0
    unresolved_count = 0
    for row in backlog_rows:
        if not _norm(row.get("evidence")):
            evidence_empty_count += 1
        status = _norm(row.get("status")).lower()
        if status and all(token not in status for token in ("done", "closed", "resolved")):
            unresolved_count += 1
    if evidence_empty_count:
        errors.append(f"backlog_empty_evidence_count={evidence_empty_count}")

    require_open = os.getenv("PRODUCT_DELIVERY_GOVERNANCE_REQUIRE_OPEN_GAPS", "1") == "1"
    if require_open and unresolved_count == 0:
        errors.append("backlog_no_unresolved_gap_in_seal_mode")

    snapshot_generated_at = _extract_snapshot_value(scoreboard_md, "generated_at_utc")
    snapshot_branch = _extract_snapshot_value(scoreboard_md, "branch")
    snapshot_commit = _extract_snapshot_value(scoreboard_md, "commit_ref")
    snapshot_gate_result = _extract_snapshot_value(scoreboard_md, "gate_result")

    if not snapshot_generated_at:
        errors.append("scoreboard_missing_snapshot.generated_at_utc")
    if not snapshot_branch:
        errors.append("scoreboard_missing_snapshot.branch")
    if not snapshot_commit:
        errors.append("scoreboard_missing_snapshot.commit_ref")
    if not snapshot_gate_result:
        errors.append("scoreboard_missing_snapshot.gate_result")

    if snapshot_commit and not _commit_exists(snapshot_commit):
        errors.append("scoreboard_commit_ref_not_found_in_repo")

    ts = _parse_utc_timestamp(snapshot_generated_at)
    if snapshot_generated_at and ts is None:
        errors.append("scoreboard_invalid_generated_at_utc")
    if ts is not None:
        max_age_hours = int(os.getenv("PRODUCT_DELIVERY_SCOREBOARD_MAX_AGE_HOURS", "168") or 168)
        age_hours = round((datetime.now(timezone.utc) - ts).total_seconds() / 3600.0, 2)
        if age_hours > max_age_hours:
            errors.append(f"scoreboard_snapshot_stale>{max_age_hours}h")
    else:
        age_hours = None
        max_age_hours = int(os.getenv("PRODUCT_DELIVERY_SCOREBOARD_MAX_AGE_HOURS", "168") or 168)

    module_rows = _parse_scoreboard_rows(scoreboard_md, "9-Module Readiness Board")
    journey_rows = _parse_scoreboard_rows(scoreboard_md, "4 Key Journey Status")
    if module_rows < 9:
        errors.append(f"scoreboard_module_rows<{9}")
    if journey_rows < 4:
        errors.append(f"scoreboard_journey_rows<{4}")

    pending_commit_count = context_log_md.count("active_commit: `pending`")
    if pending_commit_count > 0:
        errors.append(f"context_log_pending_commit_count={pending_commit_count}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "backlog_row_count": len(backlog_rows),
            "backlog_unresolved_count": unresolved_count,
            "scoreboard_module_rows": module_rows,
            "scoreboard_journey_rows": journey_rows,
            "scoreboard_snapshot_max_age_hours": max_age_hours,
            "scoreboard_snapshot_age_hours": age_hours,
            "context_log_pending_commit_count": pending_commit_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "snapshot": {
            "generated_at_utc": snapshot_generated_at,
            "branch": snapshot_branch,
            "commit_ref": snapshot_commit,
            "gate_result": snapshot_gate_result,
        },
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Governance Truth Guard",
        "",
        f"- backlog_row_count: {len(backlog_rows)}",
        f"- backlog_unresolved_count: {unresolved_count}",
        f"- scoreboard_module_rows: {module_rows}",
        f"- scoreboard_journey_rows: {journey_rows}",
        f"- scoreboard_snapshot_age_hours: {age_hours}",
        f"- context_log_pending_commit_count: {pending_commit_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_delivery_governance_truth_guard] FAIL")
        return 2
    print("[product_delivery_governance_truth_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

