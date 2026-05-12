# -*- coding: utf-8 -*-
"""Project legacy outbound project-contract deposit facts into expense claims."""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


SOURCE_MODEL = "legacy.main.T_ProjectContract_Out_CB_BZJ"
SOURCE_TABLE = "T_ProjectContract_Out_CB_BZJ"


def artifact_root():
    root = os.getenv("MIGRATION_ARTIFACT_ROOT") or "/mnt/artifacts/migration"
    path = Path(root)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        path = Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname)  # noqa: F821
        path.mkdir(parents=True, exist_ok=True)
    return path


ARTIFACT_DIR = artifact_root()
INPUT_CSV = Path(os.getenv("LEGACY_PROJECT_CONTRACT_DEPOSIT_CSV") or ARTIFACT_DIR / "legacy_project_contract_deposit_lines_v1.csv")
RESULT_JSON = ARTIFACT_DIR / "legacy_project_contract_deposit_projection_result_v1.json"
PLAN_CSV = ARTIFACT_DIR / "legacy_project_contract_deposit_projection_plan_v1.csv"
RESIDUAL_CSV = ARTIFACT_DIR / "legacy_project_contract_deposit_projection_residual_v1.csv"
APPLY = os.getenv("MIGRATION_APPLY") == "1"


def clean(value):
    text = str(value or "").strip()
    if text.lower() in {"none", "null", "false"}:
        return ""
    return text


def money(value):
    try:
        return float(clean(value) or 0.0)
    except Exception:
        return 0.0


def date_value(value):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt).date().isoformat()
        except ValueError:
            continue
    return False


def is_deleted(row):
    return clean(row.get("deleted_flag")) in {"1", "True", "true"}


def state_for(row):
    if is_deleted(row):
        return "cancel"
    if clean(row.get("document_state")) in {"2", "已通过", "已完成", "审核通过"}:
        return "legacy_confirmed"
    return "draft"


Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821


def project_for(row):
    legacy_id = clean(row.get("project_legacy_id"))
    project_name = clean(row.get("project_name")) or "历史外部合同保证金未归集项目"
    project = False
    if legacy_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
    if not project and project_name:
        project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name, "legacy_project_id": legacy_id or False})


def partner_for(row):
    partner_name = (
        clean(row.get("employer_name"))
        or clean(row.get("construction_unit_name"))
        or clean(row.get("contractor_name"))
    )
    if not partner_name:
        return False
    partner = Partner.search([("name", "=", partner_name)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": partner_name, "company_type": "company"}).id


def source_key(row):
    base = clean(row.get("legacy_line_id")) or clean(row.get("legacy_pid")) or clean(row.get("legacy_rownum"))
    rownum = clean(row.get("legacy_rownum"))
    return "%s#%s" % (base, rownum) if rownum and "#" not in base else base


def note_for(row):
    parts = [
        "旧库外部合同保证金从表",
        "主表ID：%s" % clean(row.get("legacy_header_id")),
        "承包方：%s" % clean(row.get("contractor_name")),
        "发包方：%s" % clean(row.get("employer_name")),
    ]
    if clean(row.get("payment_method")):
        parts.append("缴纳形式：%s" % clean(row.get("payment_method")))
    if clean(row.get("return_deadline")):
        parts.append("退还时限：%s" % clean(row.get("return_deadline")))
    if is_deleted(row):
        parts.append("旧库删除标记：%s" % clean(row.get("deleted_flag")))
    return "\n".join(parts)


def claim_values(row):
    project = project_for(row)
    claim_amount = money(row.get("line_amount"))
    deposit_type = clean(row.get("line_deposit_type")) or "合同保证金"
    date_claim = date_value(row.get("created_at"))
    document_no = clean(row.get("document_no"))
    legacy_key = source_key(row)
    return {
        "name": document_no and "%s-%s" % (document_no, clean(row.get("legacy_rownum")) or legacy_key) or "历史外部合同保证金-%s" % legacy_key,
        "source_origin": "legacy",
        "claim_type": "deposit_pay",
        "state": state_for(row),
        "project_id": project.id,
        "partner_id": partner_for(row),
        "applicant_name": clean(row.get("creator_name")),
        "guarantee_project_name": clean(row.get("contract_title")) or clean(row.get("project_name")) or project.display_name,
        "guarantee_type": "contract",
        "payment_method": clean(row.get("payment_method")),
        "clearing_method": clean(row.get("payment_method")),
        "date_claim": date_claim,
        "fill_date": date_claim,
        "expense_type": deposit_type,
        "summary": "外部合同%s" % deposit_type,
        "amount": claim_amount,
        "approved_amount": claim_amount,
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": legacy_key,
        "legacy_document_no": document_no,
        "legacy_document_state": clean(row.get("document_state")),
        "note": note_for(row),
        "active": not is_deleted(row),
    }


def read_rows():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = read_rows()
plan = []
residuals = []
created = 0
updated = 0
skipped = 0

for row in rows:
    values = claim_values(row)
    existing = Claim.search(
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_record_id", "=", values["legacy_record_id"])],
        limit=1,
    )
    entry = {
        "legacy_record_id": values["legacy_record_id"],
        "document_no": values["legacy_document_no"],
        "project": Project.browse(values["project_id"]).display_name,
        "partner": Partner.browse(values["partner_id"]).display_name if values["partner_id"] else "",
        "state": values["state"],
        "active": values["active"],
        "amount": "%.2f" % values["amount"],
        "action": "update" if existing else "create",
    }
    plan.append(entry)
    if not APPLY:
        skipped += 1
        continue
    if existing:
        existing.with_context(active_test=False).write(
            {
                "partner_id": values["partner_id"],
                "note": values["note"],
                "active": values["active"],
            }
        )
        updated += 1
    else:
        Claim.create(values)
        created += 1

if APPLY:
    env.cr.commit()  # noqa: F821

with PLAN_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["legacy_record_id", "document_no", "project", "partner", "state", "active", "amount", "action"])
    writer.writeheader()
    writer.writerows(plan)

with RESIDUAL_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["legacy_record_id", "reason", "amount"])
    writer.writeheader()
    writer.writerows(residuals)

domain = [("legacy_source_model", "=", SOURCE_MODEL)]
active_domain = domain + [("active", "=", True)]
all_claims = Claim.with_context(active_test=False).search(domain)
active_claims = Claim.search(active_domain)
state_counts = {}
for group in Claim.with_context(active_test=False).read_group(domain, ["state"], ["state"]):
    state = group.get("state")
    state_counts[state or ""] = group.get("state_count", 0)

result = {
    "status": "PASS" if not residuals else "WARN",
    "mode": "legacy_project_contract_deposit_projection",
    "target_model": "sc.expense.claim",
    "source_model": SOURCE_MODEL,
    "apply": APPLY,
    "source_rows": len(rows),
    "planned": len(plan),
    "created": created,
    "updated": updated,
    "skipped": skipped,
    "target_rows_all": len(all_claims),
    "target_amount_all": round(sum(all_claims.mapped("amount")), 2),
    "target_rows_active": len(active_claims),
    "target_amount_active": round(sum(active_claims.mapped("amount")), 2),
    "state_counts": state_counts,
    "residuals": residuals,
    "artifacts": {
        "plan_csv": str(PLAN_CSV),
        "residual_csv": str(RESIDUAL_CSV),
        "result_json": str(RESULT_JSON),
    },
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("LEGACY_PROJECT_CONTRACT_DEPOSIT_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
