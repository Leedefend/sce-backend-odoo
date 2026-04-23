#!/usr/bin/env python3
"""Screen BASE_SYSTEM_FILE linkage for receipt invoice line assets."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/receipt_invoice_attachment_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_receipt_invoice_attachment_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_receipt_invoice_attachment_screen_v1.md")
EXTERNAL_MANIFEST = Path("manifest/receipt_invoice_line_external_id_manifest_v1.json")
EXPECTED_FILE_ROWS = 126967

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), ID) AS ID,
  CONVERT(nvarchar(max), PID) AS PID,
  CONVERT(nvarchar(max), BILLID) AS BILLID,
  CONVERT(nvarchar(max), BUSINESSID) AS BUSINESSID,
  CONVERT(nvarchar(max), ATTR_NAME) AS ATTR_NAME,
  CONVERT(nvarchar(max), ATTR_PATH) AS ATTR_PATH,
  CONVERT(nvarchar(max), FILEMD5) AS FILEMD5,
  CONVERT(nvarchar(max), FILESIZE) AS FILESIZE,
  CONVERT(nvarchar(max), SOURCE) AS SOURCE,
  CONVERT(nvarchar(max), DEL) AS DEL
FROM dbo.BASE_SYSTEM_FILE
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(ID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(PID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BILLID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BUSINESSID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ATTR_NAME, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ATTR_PATH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FILEMD5, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FILESIZE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SOURCE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY ID;
"""

SQL_COLUMNS = ["ID", "PID", "BILLID", "BUSINESSID", "ATTR_NAME", "ATTR_PATH", "FILEMD5", "FILESIZE", "SOURCE", "DEL"]
SOURCE_FIELDS = ("BILLID", "BUSINESSID", "PID")
CANDIDATE_KEYS = ("Id", "ZBID", "FPID", "FP_CB_Id", "pid")


class ReceiptInvoiceAttachmentScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceAttachmentScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0",
    ]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sql_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != len(SQL_COLUMNS):
            continue
        rows.append(dict(zip(SQL_COLUMNS, parts)))
    require(len(rows) == EXPECTED_FILE_ROWS, f"file row count drifted: {len(rows)} != {EXPECTED_FILE_ROWS}")
    return rows


def load_candidate_index(asset_root: Path) -> dict[str, list[dict[str, str]]]:
    manifest = load_json(asset_root / EXTERNAL_MANIFEST)
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in manifest.get("records", []):
        external_id = clean(row.get("external_id"))
        keys = row.get("attachment_candidate_keys") or {}
        if not external_id or not isinstance(keys, dict):
            continue
        for key_name in CANDIDATE_KEYS:
            value = clean(keys.get(key_name))
            if value:
                index[value].append({"external_id": external_id, "candidate_key": key_name})
    require(index, "receipt invoice attachment candidate index is empty")
    return index


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def screen(asset_root: Path) -> dict[str, Any]:
    candidate_index = load_candidate_index(asset_root)
    file_rows = parse_sql_rows(run_sql())
    match_counter: Counter[str] = Counter()
    matched_file_ids: set[str] = set()
    matched_external_ids: set[str] = set()
    ambiguous_file_ids: set[str] = set()
    deleted_matches = 0
    samples: list[dict[str, Any]] = []

    for row in file_rows:
        file_id = clean(row.get("ID"))
        file_matches: list[dict[str, str]] = []
        for source_field in SOURCE_FIELDS:
            source_value = clean(row.get(source_field))
            if not source_value:
                continue
            for candidate in candidate_index.get(source_value, []):
                match_counter[f"{source_field}->{candidate['candidate_key']}"] += 1
                file_matches.append(
                    {
                        "source_field": source_field,
                        "source_value": source_value,
                        "candidate_key": candidate["candidate_key"],
                        "external_id": candidate["external_id"],
                    }
                )
        if not file_matches:
            continue

        matched_file_ids.add(file_id)
        matched_external_ids.update(match["external_id"] for match in file_matches)
        unique_targets = {match["external_id"] for match in file_matches}
        if len(unique_targets) > 1:
            ambiguous_file_ids.add(file_id)
        if is_deleted(row.get("DEL")):
            deleted_matches += 1
        if len(samples) < 50:
            samples.append(
                {
                    "file_id": file_id,
                    "attr_name": clean(row.get("ATTR_NAME")),
                    "file_size": clean(row.get("FILESIZE")),
                    "source": clean(row.get("SOURCE")),
                    "deleted": is_deleted(row.get("DEL")),
                    "matches": file_matches[:5],
                }
            )

    deterministic = bool(matched_file_ids) and not ambiguous_file_ids
    decision = "attachment_asset_lane_ready" if deterministic else "attachment_asset_lane_blocked_need_broader_mapping"
    return {
        "status": "PASS",
        "source_table": "BASE_SYSTEM_FILE",
        "file_rows": len(file_rows),
        "candidate_key_values": len(candidate_index),
        "matched_file_rows": len(matched_file_ids),
        "matched_receipt_invoice_lines": len(matched_external_ids),
        "ambiguous_file_rows": len(ambiguous_file_ids),
        "deleted_matched_file_rows": deleted_matches,
        "match_counts": dict(sorted(match_counter.items())),
        "decision": decision,
        "samples": samples,
        "db_writes": 0,
        "odoo_shell": False,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    match_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["match_counts"].items()) or "| none | 0 |"
    sample_rows = "\n".join(
        f"| {row['file_id']} | {row['attr_name']} | {row['file_size']} | {row['source']} | {row['deleted']} | {len(row['matches'])} |"
        for row in payload["samples"][:20]
    ) or "| none |  |  |  |  | 0 |"
    return f"""# Legacy Receipt Invoice Attachment Screen v1

Status: `{payload["status"]}`

This is a read-only screen for `BASE_SYSTEM_FILE` linkage against receipt
invoice line assets. It does not generate `ir.attachment` records and does not
copy file binaries.

## Result

- source table: `{payload["source_table"]}`
- file rows: `{payload["file_rows"]}`
- candidate key values: `{payload["candidate_key_values"]}`
- matched file rows: `{payload["matched_file_rows"]}`
- matched receipt invoice lines: `{payload["matched_receipt_invoice_lines"]}`
- ambiguous file rows: `{payload["ambiguous_file_rows"]}`
- deleted matched file rows: `{payload["deleted_matched_file_rows"]}`
- DB writes: `0`
- Odoo shell: `false`

## Match Distribution

| Source field -> candidate key | Matches |
|---|---:|
{match_rows}

## Sample Matches

| File ID | Name | Size | Source | Deleted | Match count |
|---|---|---:|---|---|---:|
{sample_rows}

## Decision

`{payload["decision"]}`

If the decision is blocked, the next step is a broader attachment mapping screen
against the parent receipt table and source module metadata before any
attachment XML asset is generated.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen receipt invoice attachment linkage.")
    parser.add_argument("--asset-root", default=str(ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ReceiptInvoiceAttachmentScreenError, json.JSONDecodeError, OSError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_ATTACHMENT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "RECEIPT_INVOICE_ATTACHMENT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "file_rows": payload["file_rows"],
                "matched_file_rows": payload["matched_file_rows"],
                "matched_receipt_invoice_lines": payload["matched_receipt_invoice_lines"],
                "ambiguous_file_rows": payload["ambiguous_file_rows"],
                "decision": payload["decision"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
