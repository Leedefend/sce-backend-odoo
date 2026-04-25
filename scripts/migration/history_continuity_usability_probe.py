#!/usr/bin/env python3
"""Read-only business continuity probe for historical replay targets."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "history_continuity_usability_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_continuity_usability_probe_report_v1.md"
REQUIRED_MODELS = [
    "res.users",
    "res.partner",
    "project.project",
    "sc.project.member.staging",
    "construction.contract",
    "payment.request",
]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# History Continuity Usability Probe v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Scope",
        "",
        "Read-only continuity probe after historical replay or rehearsal.",
        "This probe does not mutate business data.",
        "",
        "## Current Counts",
        "",
        "```json",
        json.dumps(payload["counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Notes",
        "",
        "- This probe only verifies replayed historical facts are present in runtime/carrier models.",
        "- Promotion from carrier rows into runtime business ownership remains a later batch.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


missing_models = [model_name for model_name in REQUIRED_MODELS if model_name not in env]  # noqa: F821
counts = {
    "legacy_users": env["res.users"].sudo().with_context(active_test=False).search_count([("login", "like", "legacy_%")]) if "res.users" in env else None,  # noqa: F821
    "partner_l4_anchors": env["res.partner"].sudo().search_count([("legacy_partner_id", "!=", False)]) if "res.partner" in env else None,  # noqa: F821
    "contract_counterparty_partners": env["res.partner"].sudo().search_count([("legacy_partner_source", "=", "contract_counterparty")]) if "res.partner" in env else None,  # noqa: F821
    "receipt_counterparty_partners": env["res.partner"].sudo().search_count([("legacy_partner_source", "=", "receipt_counterparty")]) if "res.partner" in env else None,  # noqa: F821
    "project_anchors": env["project.project"].sudo().search_count([("legacy_project_id", "!=", False)]) if "project.project" in env else None,  # noqa: F821
    "project_member_carrier": env["sc.project.member.staging"].sudo().search_count([]) if "sc.project.member.staging" in env else None,  # noqa: F821
    "contract_headers": env["construction.contract"].sudo().search_count([("legacy_contract_id", "!=", False)]) if "construction.contract" in env else None,  # noqa: F821
    "contract_summary_lines": env["construction.contract.line"].sudo().search_count([("note", "ilike", "summary line from legacy contract header amount")]) if "construction.contract.line" in env else None,  # noqa: F821
    "supplier_contract_headers": env["construction.contract"].sudo().search_count([("type", "=", "in"), ("note", "ilike", "[migration:supplier_contract_header]")]) if "construction.contract" in env else None,  # noqa: F821
    "supplier_contract_lines": env["construction.contract.line"].sudo().search_count([("note", "ilike", "[migration:supplier_contract_summary_line]")]) if "construction.contract.line" in env else None,  # noqa: F821
    "receipt_core_requests": env["payment.request"].sudo().search_count([("note", "ilike", "[migration:receipt_core]")]) if "payment.request" in env else None,  # noqa: F821
}

zero_critical_counts = [
    key
    for key in ["partner_l4_anchors", "project_anchors", "project_member_carrier", "contract_headers"]
    if counts.get(key) in (None, 0)
]

status = "PASS" if not missing_models else "FAIL"
decision = "history_continuity_runtime_surface_detected"
if missing_models:
    decision = "STOP_REVIEW_REQUIRED"
elif zero_critical_counts:
    decision = "history_continuity_conditional_missing_runtime_facts"

payload = {
    "status": status,
    "mode": "history_continuity_usability_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "missing_models": missing_models,
    "zero_critical_counts": zero_critical_counts,
    "decision": decision,
}
write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print(
    "HISTORY_CONTINUITY_USABILITY_PROBE="
    + json.dumps(
        {
            "status": status,
            "database": env.cr.dbname,  # noqa: F821
            "missing_models": len(missing_models),
            "zero_critical_counts": len(zero_critical_counts),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
