#!/usr/bin/env python3
"""Audit missing output invoice documents across runtime, assets, and legacy source."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
ARTIFACT_ROOT = Path(
    os.getenv(
        "OUTPUT_INVOICE_SOURCE_GAP_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/output_invoice_source_gap_audit"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "output_invoice_source_gap_audit_v1.json"
OUTPUT_MD = ARTIFACT_ROOT / "output_invoice_source_gap_audit_v1.md"

DB_CONTAINER = os.getenv("ODOO_DB_CONTAINER", "sc-backend-odoo-dev-db-1")
DB_USER = os.getenv("DB_USER", "odoo")
DB_NAME = os.getenv("DB_NAME", "sc_demo")

LEGACY_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
LEGACY_SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
LEGACY_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
LEGACY_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_document_nos() -> list[str]:
    raw = os.getenv("OUTPUT_INVOICE_DOCUMENT_NOS", "XXKPDJ-20260511-001")
    docs = [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]
    if not docs:
        raise RuntimeError("OUTPUT_INVOICE_DOCUMENT_NOS is empty")
    expanded: list[str] = []
    for doc in docs:
        expanded.append(doc)
        if doc.startswith("XKPDJ-"):
            expanded.append("X" + doc)
        elif doc.startswith("XXKPDJ-"):
            expanded.append(doc[1:])
    return sorted(set(expanded))


def sql_literal(value: object) -> str:
    return "'" + clean(value).replace("'", "''") + "'"


def mssql_literal(value: object) -> str:
    return "N'" + clean(value).replace("'", "''") + "'"


def run(
    command: list[str],
    *,
    input_text: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, input=input_text, text=True, capture_output=True, check=False, cwd=cwd)


def psql_json(query: str) -> list[dict[str, Any]]:
    command = [
        "docker",
        "exec",
        "-i",
        DB_CONTAINER,
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-t",
        "-A",
        "-v",
        "ON_ERROR_STOP=1",
    ]
    completed = run(command, input_text=query)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "psql_failed": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    text = completed.stdout.strip()
    return json.loads(text or "[]")


def psql_one(query: str) -> dict[str, Any]:
    rows = psql_json(query)
    return rows[0] if rows else {}


def sqlcmd_rows(query: str, expected_columns: int) -> list[list[str]]:
    command = [
        "docker",
        "exec",
        "-i",
        LEGACY_CONTAINER,
        "bash",
        "-lc",
        (
            f"{LEGACY_SQLCMD} -S localhost -U sa -P {sql_literal(LEGACY_PASSWORD)} -C "
            f"-d {sql_literal(LEGACY_DATABASE)} -h -1 -s '|'"
        ),
    ]
    completed = run(command, input_text=query)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "stdout": completed.stdout[-1000:],
                "stderr": completed.stderr[-1000:],
            }
        )
    rows: list[list[str]] = []
    for raw in completed.stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("(") or line.startswith("-"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == expected_columns:
            rows.append(parts)
    return rows


def rg_hits(document_nos: list[str]) -> list[dict[str, str]]:
    paths = ["migration_assets", "artifacts/migration"]
    pattern = "|".join(document_nos)
    command = ["rg", "-n", "-S", pattern, *paths]
    completed = run(command, cwd=REPO_ROOT)
    hits = []
    if completed.returncode not in {0, 1}:
        hits.append({"path": "__ERROR__", "line": "", "text": completed.stderr[-1000:]})
        return hits
    for raw in completed.stdout.splitlines()[:200]:
        path, line, text = (raw.split(":", 2) + ["", ""])[:3]
        hits.append({"path": path, "line": line, "text": text[:500]})
    return hits


def runtime_audit(document_nos: list[str], project_name: str) -> dict[str, Any]:
    docs_sql = ", ".join(sql_literal(doc) for doc in document_nos)

    invoice_registration = psql_json(
        f"""
        SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
        FROM (
          SELECT ir.id, ir.document_no, ir.project_id, pp.name::text AS project_name,
                 ir.invoice_no, ir.invoice_date, ir.amount_total, ir.amount_no_tax,
                 ir.tax_amount, ir.surcharge_amount, ir.legacy_source_table,
                 ir.legacy_record_id
          FROM sc_invoice_registration ir
          LEFT JOIN project_project pp ON pp.id = ir.project_id
          WHERE ir.document_no IN ({docs_sql})
          ORDER BY ir.invoice_date DESC NULLS LAST, ir.document_no
        ) t;
        """
    )
    legacy_fact = psql_json(
        f"""
        SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
        FROM (
          SELECT f.id, f.document_no, f.project_id, pp.name::text AS project_name,
                 f.document_date, f.legacy_project_name, f.legacy_partner_name,
                 f.source_amount, f.source_tax_amount, f.legacy_source_table,
                 f.legacy_record_id
          FROM sc_legacy_invoice_tax_fact f
          LEFT JOIN project_project pp ON pp.id = f.project_id
          WHERE f.document_no IN ({docs_sql})
          ORDER BY f.document_date DESC NULLS LAST, f.document_no
        ) t;
        """
    )
    ledger = psql_json(
        f"""
        SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
        FROM (
          SELECT l.id, l.source_model, l.source_record_id, l.invoice_document_no,
                 l.source_document_no, l.invoice_no, l.invoice_date, l.project_id,
                 pp.name::text AS project_name, l.invoice_amount, l.amount_no_tax,
                 l.tax_amount, l.surcharge_amount, l.amount_source
          FROM sc_output_invoice_ledger l
          LEFT JOIN project_project pp ON pp.id = l.project_id
          WHERE l.invoice_document_no IN ({docs_sql})
             OR l.source_document_no IN ({docs_sql})
          ORDER BY l.invoice_date DESC NULLS LAST, l.source_document_no
        ) t;
        """
    )
    project_context_ledger: list[dict[str, Any]] = []
    if project_name:
        project_context_ledger = psql_json(
            f"""
            SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
            FROM (
              SELECT l.id, l.source_model, l.source_record_id, l.invoice_document_no,
                     l.source_document_no, l.invoice_no, l.invoice_date, l.project_id,
                     pp.name::text AS project_name, l.invoice_amount, l.amount_no_tax,
                     l.tax_amount, l.surcharge_amount, l.amount_source
              FROM sc_output_invoice_ledger l
              LEFT JOIN project_project pp ON pp.id = l.project_id
              WHERE COALESCE(pp.name::text, '') ILIKE {sql_literal('%' + project_name + '%')}
              ORDER BY l.invoice_date DESC NULLS LAST, l.source_document_no
            ) t;
            """
        )
    boundary = psql_one(
        """
        SELECT json_build_array(row_to_json(t))
        FROM (
          SELECT COUNT(*) AS runtime_rows, MIN(document_date) AS min_date, MAX(document_date) AS max_date
          FROM sc_legacy_invoice_tax_fact
          WHERE legacy_source_table = 'C_JXXP_XXKPDJ'
        ) t;
        """
    )
    return {
        "invoice_registration": invoice_registration,
        "legacy_invoice_tax_fact": legacy_fact,
        "output_invoice_ledger": ledger,
        "project_context_output_invoice_ledger": project_context_ledger,
        "runtime_source_boundary": boundary,
    }


def legacy_source_audit(document_nos: list[str], project_name: str) -> dict[str, Any]:
    docs_sql = ", ".join(mssql_literal(doc) for doc in document_nos)
    header_sql = f"""
SET NOCOUNT ON;
SELECT Id, DJBH, CONVERT(varchar(19), SQRQ, 120), XMMC, SPFMC, KPZJE, ZSE, DJZT, DEL
FROM dbo.C_JXXP_XXKPDJ
WHERE DJBH IN ({docs_sql})
ORDER BY SQRQ DESC, DJBH DESC;
"""
    child_sql = f"""
SET NOCOUNT ON;
SELECT c.Id, c.ZBID, h.DJBH, CONVERT(varchar(19), h.SQRQ, 120), h.XMMC, c.FPH,
       CONVERT(varchar(19), c.KPRQ, 120), c.JE, c.JE_NO, c.SE, c.D_SCBSJS_FJS
FROM dbo.C_JXXP_XXKPDJ_CB c
LEFT JOIN dbo.C_JXXP_XXKPDJ h ON h.Id = c.ZBID
WHERE h.DJBH IN ({docs_sql})
ORDER BY h.SQRQ DESC, h.DJBH DESC;
"""
    project_context_header_sql = ""
    if project_name:
        project_context_header_sql = f"""
SET NOCOUNT ON;
SELECT Id, DJBH, CONVERT(varchar(19), SQRQ, 120), XMMC, SPFMC, KPZJE, ZSE, DJZT, DEL
FROM dbo.C_JXXP_XXKPDJ
WHERE XMMC LIKE {mssql_literal('%' + project_name + '%')}
ORDER BY SQRQ DESC, DJBH DESC;
"""
    boundary_sql = """
SET NOCOUNT ON;
SELECT COUNT(*), CONVERT(varchar(19), MIN(SQRQ), 120), CONVERT(varchar(19), MAX(SQRQ), 120)
FROM dbo.C_JXXP_XXKPDJ;
"""
    header_cols = [
        "id",
        "document_no",
        "document_date",
        "project_name",
        "partner_name",
        "amount",
        "tax_amount",
        "state",
        "deleted",
    ]
    child_cols = [
        "id",
        "header_id",
        "document_no",
        "document_date",
        "project_name",
        "invoice_no",
        "invoice_date",
        "amount",
        "amount_no_tax",
        "tax_amount",
        "surcharge_amount",
    ]
    boundary_cols = ["legacy_rows", "min_date", "max_date"]
    return {
        "header": [dict(zip(header_cols, row)) for row in sqlcmd_rows(header_sql, len(header_cols))],
        "child": [dict(zip(child_cols, row)) for row in sqlcmd_rows(child_sql, len(child_cols))],
        "project_context_header": (
            [dict(zip(header_cols, row)) for row in sqlcmd_rows(project_context_header_sql, len(header_cols))]
            if project_context_header_sql
            else []
        ),
        "source_boundary": [dict(zip(boundary_cols, row)) for row in sqlcmd_rows(boundary_sql, len(boundary_cols))],
    }


def decision(payload: dict[str, Any]) -> str:
    runtime_has_document = any(payload["runtime"][key] for key in ("invoice_registration", "legacy_invoice_tax_fact", "output_invoice_ledger"))
    legacy_has_document = bool(payload["legacy_source"]["header"] or payload["legacy_source"]["child"])
    asset_has_document = bool(payload["asset_hits"])
    if runtime_has_document:
        return "runtime_contains_requested_output_invoice"
    if asset_has_document:
        return "asset_contains_requested_output_invoice_but_runtime_missing"
    if legacy_has_document:
        return "legacy_source_contains_requested_output_invoice_but_asset_missing"
    return "source_increment_required_for_requested_output_invoice"


def write_report(payload: dict[str, Any]) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    runtime_boundary = payload["runtime"].get("runtime_source_boundary") or {}
    legacy_boundary = (payload["legacy_source"].get("source_boundary") or [{}])[0]
    lines = [
        "# Output Invoice Source Gap Audit",
        "",
        f"- decision: `{payload['decision']}`",
        f"- document_nos: `{', '.join(payload['document_nos'])}`",
        f"- project_name: `{payload['project_name'] or ''}`",
        f"- runtime invoice registration rows: `{len(payload['runtime']['invoice_registration'])}`",
        f"- runtime legacy invoice fact rows: `{len(payload['runtime']['legacy_invoice_tax_fact'])}`",
        f"- runtime output ledger rows: `{len(payload['runtime']['output_invoice_ledger'])}`",
        f"- runtime project-context output ledger rows: `{len(payload['runtime']['project_context_output_invoice_ledger'])}`",
        f"- migration asset hits: `{len(payload['asset_hits'])}`",
        f"- legacy header rows: `{len(payload['legacy_source']['header'])}`",
        f"- legacy child rows: `{len(payload['legacy_source']['child'])}`",
        f"- legacy project-context header rows: `{len(payload['legacy_source']['project_context_header'])}`",
        f"- runtime C_JXXP_XXKPDJ boundary: `{runtime_boundary}`",
        f"- legacy C_JXXP_XXKPDJ boundary: `{legacy_boundary}`",
        "",
        "## Next Action",
        "",
    ]
    if payload["decision"] == "source_increment_required_for_requested_output_invoice":
        lines.append("Provide or restore an incremental legacy source after the current legacy boundary, then rerun the invoice-tax replay.")
    elif payload["decision"] == "legacy_source_contains_requested_output_invoice_but_asset_missing":
        lines.append("Regenerate the invoice-tax migration asset from the legacy source and replay it into the runtime database.")
    elif payload["decision"] == "asset_contains_requested_output_invoice_but_runtime_missing":
        lines.append("Replay the existing migration asset into the runtime database and rerun the ledger verification.")
    else:
        lines.append("Runtime already contains the requested output invoice; inspect visible surface filters or action context.")
    lines.append("")
    lines.append(f"Full JSON: `{OUTPUT_JSON}`")
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    document_nos = parse_document_nos()
    project_name = os.getenv("OUTPUT_INVOICE_PROJECT_NAME", "").strip()
    payload = {
        "mode": "output_invoice_source_gap_audit",
        "document_nos": document_nos,
        "project_name": project_name,
        "runtime": runtime_audit(document_nos, project_name),
        "asset_hits": rg_hits(document_nos),
        "legacy_source": legacy_source_audit(document_nos, project_name),
    }
    payload["decision"] = decision(payload)
    payload["artifacts"] = {"json": str(OUTPUT_JSON), "markdown": str(OUTPUT_MD)}
    write_report(payload)
    print(json.dumps({"decision": payload["decision"], "artifacts": payload["artifacts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
