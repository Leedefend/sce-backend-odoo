#!/usr/bin/env python3
"""Project legacy self-funding facts into formal handling records."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ensure_allowed_db()
result = env["sc.self.funding.registration"].sudo().project_legacy_self_funding_facts(  # noqa: F821
    limit=int(os.getenv("SELF_FUNDING_PROJECTION_LIMIT", "0") or "0")
)
env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS",
    "mode": "fresh_db_self_funding_registration_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    **result,
}
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
write_json(artifact_root / "fresh_db_self_funding_registration_projection_write_result_v1.json", payload)
print("FRESH_DB_SELF_FUNDING_REGISTRATION_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
