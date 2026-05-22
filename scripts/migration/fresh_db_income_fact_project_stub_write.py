#!/usr/bin/env python3
"""Create visible income-contract stubs for projects that only have income flow facts."""

from __future__ import annotations

import json
import os
import re
from decimal import Decimal
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path("/mnt/extra-addons"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists() or (candidate / "tmp").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or str(REPO_ROOT / "artifacts/migration"))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_income_fact_project_stub_write_result_v1.json"
LINE_NOTE = "legacy_contract_amount:income_fact_project_stub"


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())


def as_float(value: object) -> float:
    return float(Decimal(str(value or "0")).quantize(Decimal("0.01")))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
ContractLine = env["construction.contract.line"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821


def residual_income_fact_projects() -> list[dict[str, object]]:
    env.cr.execute(  # noqa: F821
        """
        WITH income_contract_projects AS (
            SELECT DISTINCT cc.project_id
              FROM construction_contract_income ci
              JOIN construction_contract cc ON cc.id = ci.contract_id
             WHERE cc.active IS TRUE
               AND cc.project_id IS NOT NULL
               AND (COALESCE(cc.legacy_contract_id, '') = '' OR cc.legacy_income_surface_visible)
        ),
        inv_projects AS (
            SELECT project_id,
                   SUM(COALESCE(amount_total, 0)) AS amount,
                   COUNT(*)::integer AS cnt,
                   MIN(invoice_date) AS min_date,
                   MAX(invoice_date) AS max_date
              FROM sc_invoice_registration
             WHERE active IS TRUE
               AND project_id IS NOT NULL
               AND direction = 'output'
             GROUP BY project_id
        ),
        rec_projects AS (
            SELECT project_id,
                   SUM(COALESCE(amount, 0)) AS amount,
                   COUNT(*)::integer AS cnt,
                   MIN(date_receipt) AS min_date,
                   MAX(date_receipt) AS max_date,
                   STRING_AGG(DISTINCT NULLIF(income_category, ''), ', ' ORDER BY NULLIF(income_category, '')) AS income_categories
              FROM sc_receipt_income
             WHERE active IS TRUE
               AND project_id IS NOT NULL
             GROUP BY project_id
        ),
        fact_projects AS (
            SELECT COALESCE(i.project_id, r.project_id) AS project_id,
                   COALESCE(i.amount, 0) AS invoice_amount,
                   COALESCE(i.cnt, 0) AS invoice_count,
                   i.min_date AS invoice_min_date,
                   i.max_date AS invoice_max_date,
                   COALESCE(r.amount, 0) AS receipt_amount,
                   COALESCE(r.cnt, 0) AS receipt_count,
                   r.min_date AS receipt_min_date,
                   r.max_date AS receipt_max_date,
                   r.income_categories
              FROM inv_projects i
              FULL JOIN rec_projects r ON r.project_id = i.project_id
        )
        SELECT pp.id AS project_id,
               pp.name AS project_name,
               pp.legacy_project_id,
               fp.invoice_amount,
               fp.invoice_count,
               fp.invoice_min_date,
               fp.invoice_max_date,
               fp.receipt_amount,
               fp.receipt_count,
               fp.receipt_min_date,
               fp.receipt_max_date,
               fp.income_categories
          FROM fact_projects fp
          JOIN project_project pp ON pp.id = fp.project_id
          LEFT JOIN income_contract_projects icp ON icp.project_id = fp.project_id
         WHERE icp.project_id IS NULL
         ORDER BY fp.invoice_amount DESC NULLS LAST, fp.receipt_amount DESC NULLS LAST
        """
    )
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def project_display_name(project) -> str:
    name = project.display_name or ""
    return clean(name)


def stub_identity(project) -> str:
    legacy_project_id = clean(project.legacy_project_id)
    key = legacy_project_id or str(project.id)
    return f"income_fact_project_stub:{key}"


def resolve_partner(row: dict[str, object]):
    name = "待确认收入合同方"
    matches = Partner.search([("name", "=", name)], order="id", limit=1)
    if matches:
        return matches[0]
    vals = {
        "name": name,
        "company_type": "company",
        "legacy_partner_id": "income_fact_project_stub:unknown_counterparty",
        "legacy_partner_source": "income_fact_project_stub",
        "legacy_partner_name": name,
    }
    if "is_company" in Partner._fields:
        vals["is_company"] = True
    if "customer_rank" in Partner._fields:
        vals["customer_rank"] = 1
    return Partner.create(vals)


def stub_amount(row: dict[str, object]) -> float:
    invoice_amount = as_float(row.get("invoice_amount"))
    receipt_amount = as_float(row.get("receipt_amount"))
    return max(invoice_amount, receipt_amount)


def source_note(row: dict[str, object]) -> str:
    parts = [
        "收入流水兜底生成，用户可删除或补正。",
        f"销项开票={as_float(row.get('invoice_amount'))}，笔数={int(row.get('invoice_count') or 0)}，日期={clean(row.get('invoice_min_date'))}~{clean(row.get('invoice_max_date'))}。",
        f"收款={as_float(row.get('receipt_amount'))}，笔数={int(row.get('receipt_count') or 0)}，日期={clean(row.get('receipt_min_date'))}~{clean(row.get('receipt_max_date'))}。",
    ]
    categories = clean(row.get("income_categories"))
    if categories:
        parts.append(f"收款类别={categories}。")
    return "\n".join(parts)


def sync_amount_line(contract, amount: float) -> str:
    if not amount:
        return ""
    vals = {
        "contract_id": contract.id,
        "sequence": 1,
        "qty_contract": 1.0,
        "price_contract": amount,
        "note": LINE_NOTE,
    }
    lines = contract.line_ids.filtered(lambda line: (line.note or "") == LINE_NOTE)
    if lines:
        lines[:1].write(vals)
        return "line_updated"
    if not contract.line_ids:
        ContractLine.create(vals)
        return "line_created"
    return ""


rows = residual_income_fact_projects()
created = updated = line_created = line_updated = 0
created_ids: list[int] = []
for row in rows:
    project = Project.browse(row["project_id"]).exists()
    if not project:
        continue
    identity = stub_identity(project)
    partner = resolve_partner(row)
    amount = stub_amount(row)
    invoice_amount = as_float(row.get("invoice_amount"))
    receipt_amount = as_float(row.get("receipt_amount"))
    unreceived_amount = max(amount - receipt_amount, 0.0)
    vals = {
        "legacy_contract_id": identity,
        "legacy_project_id": clean(project.legacy_project_id),
        "legacy_document_no": identity,
        "legacy_contract_no": identity,
        "legacy_status": "用户待确认",
        "legacy_deleted_flag": "0",
        "legacy_counterparty_text": partner.name,
        "legacy_income_surface_visible": True,
        "subject": f"{project_display_name(project)} - 收入流水待确认合同",
        "type": "out",
        "state": "draft",
        "project_id": project.id,
        "partner_id": partner.id,
        "note": source_note(row),
        "legacy_contract_amount": amount,
        "legacy_contract_amount_source": "income_fact_project_stub.max(invoice_amount,receipt_amount)",
        "visible_invoice_amount": invoice_amount,
        "visible_invoice_amount_source": "income_fact_project_stub.invoice_amount",
        "visible_received_amount": receipt_amount,
        "visible_received_amount_source": "income_fact_project_stub.receipt_amount",
        "visible_unreceived_amount": unreceived_amount,
        "visible_unreceived_amount_source": "income_fact_project_stub.amount_minus_receipt",
    }
    if amount:
        vals["visible_unreceived_rate"] = f"{unreceived_amount / amount * 100:.2f}%"
    tax = Contract._get_default_tax("out")
    if tax:
        vals["tax_id"] = tax.id
    existing = Contract.search([("legacy_contract_id", "=", identity)], limit=1)
    if existing:
        existing.with_context(skip_validation_check=True).write(vals)
        contract = existing
        updated += 1
    else:
        contract = Contract.create(vals)
        created += 1
        created_ids.append(contract.id)
    line_action = sync_amount_line(contract, amount)
    if line_action == "line_created":
        line_created += 1
    elif line_action == "line_updated":
        line_updated += 1

env.cr.commit()  # noqa: F821
remaining = residual_income_fact_projects()
result = {
    "status": "PASS" if not remaining else "FAIL",
    "mode": "fresh_db_income_fact_project_stub_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_residual_projects": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "amount_line_created_rows": line_created,
    "amount_line_updated_rows": line_updated,
    "remaining_residual_projects": len(remaining),
    "created_contract_ids": created_ids[:100],
}
write_json(OUTPUT_JSON, result)
print("FRESH_DB_INCOME_FACT_PROJECT_STUB_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
if result["status"] != "PASS":
    raise RuntimeError({"income_fact_project_stub_failed": result})
