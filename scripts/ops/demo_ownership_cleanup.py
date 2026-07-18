#!/usr/bin/env python3
"""Fingerprint-bound, report-only boundary for demo ownership cleanup.

The automatic module migration never calls this tool.  No cleanup executor is
implemented until a separately reviewed model whitelist and reference proof
exist.  Even an apply request with approvals therefore fails closed.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ACTION = os.getenv("DEMO_OWNERSHIP_ACTION", "report").strip().lower()
REPORT_PATH = Path(
    os.getenv(
        "DEMO_OWNERSHIP_REPORT_PATH",
        "/mnt/artifacts/backend/demo-ownership-cleanup-report.json",
    )
)
DEMO_MODULE = "smart_construction_demo"


def _canonical_hash(payload):
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _inventory():
    rows = env["ir.model.data"].sudo().search(  # noqa: F821
        [("module", "=", DEMO_MODULE)], order="model,name,id"
    )
    model_counts = Counter()
    existing_record_count = 0
    missing_record_count = 0
    scalar_rows = []
    for row in rows:
        model = str(row.model or "")
        scalar_rows.append((DEMO_MODULE, str(row.name or ""), model, int(row.res_id or 0)))
        model_counts[model] += 1
        if model not in env:  # noqa: F821
            missing_record_count += 1
            continue
        record = env[model].sudo().with_context(active_test=False).browse(row.res_id).exists()  # noqa: F821
        if record:
            existing_record_count += 1
        else:
            missing_record_count += 1
    ownership_facts = {
        "module": DEMO_MODULE,
        "xmlid_count": len(rows),
        "model_counts": dict(sorted(model_counts.items())),
        "existing_record_count": existing_record_count,
        "missing_record_count": missing_record_count,
        "xmlid_scalar_sha256": _canonical_hash({"rows": scalar_rows}),
    }
    return ownership_facts, _canonical_hash(ownership_facts)


facts, source_fingerprint = _inventory()
payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "action": ACTION,
    "mode": "dry_run_report_only",
    "source_database_fingerprint": source_fingerprint,
    "ownership": facts,
    "database_writes": 0,
    "cleanup_executor_implemented": False,
    "required_apply_approvals": [
        "SC_DEMO_OWNERSHIP_CLEANUP_APPROVED=1",
        "SOURCE_DATABASE_FINGERPRINT=<exact report fingerprint>",
        "APPROVED_BY=<responsible role>",
    ],
}

if ACTION == "apply":
    if os.getenv("SC_DEMO_OWNERSHIP_CLEANUP_APPROVED") != "1":
        raise RuntimeError("SC_DEMO_OWNERSHIP_CLEANUP_APPROVED=1 is required")
    if os.getenv("SOURCE_DATABASE_FINGERPRINT") != source_fingerprint:
        raise RuntimeError("SOURCE_DATABASE_FINGERPRINT does not match current ownership facts")
    if not os.getenv("APPROVED_BY", "").strip():
        raise RuntimeError("APPROVED_BY responsible role is required")
    raise RuntimeError("cleanup executor is intentionally not implemented; reviewed whitelist required")
if ACTION != "report":
    raise RuntimeError("DEMO_OWNERSHIP_ACTION must be report or apply")

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
env.cr.rollback()  # noqa: F821
print("DEMO_OWNERSHIP_CLEANUP=" + json.dumps(payload, sort_keys=True))
