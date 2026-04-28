#!/usr/bin/env python3
"""Replay legacy account master records into the neutral account carrier."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
        return
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifact_fallback"] = str(fallback)
        data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        fallback.write_text(data, encoding="utf-8")


def bulk_load(csv_path: Path, temp_table: str, columns: list[str]) -> None:
    env.cr.execute(f"DROP TABLE IF EXISTS {temp_table}")  # noqa: F821
    env.cr.execute(f"CREATE TEMP TABLE {temp_table} ({', '.join(f'{col} text' for col in columns)}) ON COMMIT DROP")  # noqa: F821
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        env.cr.copy_expert(  # noqa: F821
            f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER",
            handle,
        )


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json"
ACCOUNT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_account_master_replay_write_result_v1.json"

ACCOUNT_COLUMNS = [
    "legacy_account_id",
    "project_legacy_id",
    "project_name",
    "name",
    "account_no",
    "account_type",
    "opening_balance",
    "bank_name",
    "sort_no",
    "is_default",
    "fixed_account",
    "legacy_state",
    "source_table",
    "note",
    "active",
]

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
uid = env.uid  # noqa: F821

bulk_load(ACCOUNT_CSV, "tmp_legacy_account_master", ACCOUNT_COLUMNS)

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_account_master")  # noqa: F821
before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_legacy_account_master (
      legacy_account_id, project_legacy_id, project_name, project_id,
      name, account_no, account_type, opening_balance, bank_name, sort_no,
      is_default, fixed_account, legacy_state, source_table, note, active,
      create_uid, create_date, write_uid, write_date
    )
    SELECT
      t.legacy_account_id,
      NULLIF(t.project_legacy_id, ''),
      NULLIF(t.project_name, ''),
      p.id,
      COALESCE(NULLIF(t.name, ''), t.legacy_account_id),
      NULLIF(t.account_no, ''),
      NULLIF(t.account_type, ''),
      COALESCE(NULLIF(t.opening_balance, '')::numeric, 0),
      NULLIF(t.bank_name, ''),
      NULLIF(t.sort_no, ''),
      COALESCE(NULLIF(t.is_default, ''), '0') = '1',
      COALESCE(NULLIF(t.fixed_account, ''), '0') = '1',
      NULLIF(t.legacy_state, ''),
      COALESCE(NULLIF(t.source_table, ''), 'C_Base_ZHSZ'),
      NULLIF(t.note, ''),
      COALESCE(NULLIF(t.active, ''), '1') = '1',
      %s, NOW(), %s, NOW()
    FROM tmp_legacy_account_master t
    LEFT JOIN project_project p ON p.legacy_project_id = NULLIF(t.project_legacy_id, '')
    WHERE NULLIF(t.legacy_account_id, '') IS NOT NULL
    ON CONFLICT (legacy_account_id) DO UPDATE SET
      project_legacy_id = EXCLUDED.project_legacy_id,
      project_name = EXCLUDED.project_name,
      project_id = EXCLUDED.project_id,
      name = EXCLUDED.name,
      account_no = EXCLUDED.account_no,
      account_type = EXCLUDED.account_type,
      opening_balance = EXCLUDED.opening_balance,
      bank_name = EXCLUDED.bank_name,
      sort_no = EXCLUDED.sort_no,
      is_default = EXCLUDED.is_default,
      fixed_account = EXCLUDED.fixed_account,
      legacy_state = EXCLUDED.legacy_state,
      source_table = EXCLUDED.source_table,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = EXCLUDED.write_uid,
      write_date = NOW()
    """,
    [uid, uid],
)

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_legacy_account_master")  # noqa: F821
after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE active), COUNT(DISTINCT account_type), COUNT(DISTINCT account_no) FROM sc_legacy_account_master")  # noqa: F821
total, active_rows, account_types, account_nos = env.cr.fetchone()  # noqa: F821

payload = {
    "mode": "fresh_db_legacy_account_master_replay_write",
    "manifest_account_rows": int(manifest.get("account_rows") or 0),
    "before": before,
    "after": after,
    "total": total,
    "active_rows": active_rows,
    "account_types": account_types,
    "account_nos": account_nos,
    "decision": "legacy_account_master_replay_complete" if after >= int(manifest.get("account_rows") or 0) else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_ACCOUNT_MASTER_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
