#!/usr/bin/env python3
"""Read-only probe for financing loan runtime coverage."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count(model_name: str, domain=None, active_test=False) -> int:
    if model_name not in env:  # noqa: F821
        return 0
    return env[model_name].sudo().with_context(active_test=active_test).search_count(domain or [])  # noqa: F821


artifact_root = resolve_artifact_root()
output_json = artifact_root / "history_financing_loan_runtime_probe_result_v1.json"

counts = {
    "legacy_financing_loan_facts": count("sc.legacy.financing.loan.fact", [], active_test=False),
    "legacy_financing_loan_project_amount": count(
        "sc.legacy.financing.loan.fact",
        [("project_id", "!=", False), ("source_amount", ">", 0)],
        active_test=False,
    ),
    "financing_loan_runtime_records": count("sc.financing.loan", [], active_test=False),
    "financing_loan_legacy_records": count(
        "sc.financing.loan", [("source_origin", "=", "legacy")], active_test=False
    ),
    "financing_loan_legacy_with_project": count(
        "sc.financing.loan",
        [("source_origin", "=", "legacy"), ("project_id", "!=", False)],
        active_test=False,
    ),
    "financing_loan_legacy_confirmed": count(
        "sc.financing.loan",
        [("source_origin", "=", "legacy"), ("state", "=", "legacy_confirmed")],
        active_test=False,
    ),
    "financing_loan_manual_records": count(
        "sc.financing.loan", [("source_origin", "=", "manual")], active_test=False
    ),
}
gaps = {
    "runtime_model_missing": "sc.financing.loan" not in env,  # noqa: F821
    "legacy_projection_gap": (
        counts["legacy_financing_loan_project_amount"] > 0 and counts["financing_loan_legacy_with_project"] == 0
    ),
}
failing_gaps = [key for key, value in gaps.items() if value]
payload = {
    "status": "PASS",
    "mode": "history_financing_loan_runtime_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "gaps": gaps,
    "gap_count": len(failing_gaps),
    "decision": "history_financing_loan_runtime_ready" if not failing_gaps else "history_financing_loan_runtime_gap",
}
write_json(output_json, payload)
print("HISTORY_FINANCING_LOAN_RUNTIME_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
