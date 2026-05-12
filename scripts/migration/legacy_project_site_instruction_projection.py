# -*- coding: utf-8 -*-
"""Project legacy project site instruction facts into contract events."""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


SOURCE_MODEL = "sc.legacy.business.fact.residual"
SOURCE_TABLE = "T_Project_GCQZD"


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
RESULT_JSON = ARTIFACT_DIR / "legacy_project_site_instruction_projection_result_v1.json"
PLAN_CSV = ARTIFACT_DIR / "legacy_project_site_instruction_projection_plan_v1.csv"
RESIDUAL_CSV = ARTIFACT_DIR / "legacy_project_site_instruction_projection_residual_v1.csv"
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


def raw_for(record):
    try:
        return json.loads(record.raw_payload or "{}")
    except Exception:
        return {}


def state_for(raw):
    state = clean(raw.get("DJZT"))
    if state == "2":
        return "approved"
    if state in {"-1", "作废", "已作废", "cancel"}:
        return "cancel"
    return "draft"


def partner_name_for(raw):
    for key in ("JSDW", "JLDW"):
        value = clean(raw.get(key))
        if value and not value.isdigit():
            return value
    return ""


Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
Event = env["sc.contract.event"].sudo()  # noqa: F821
Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821


def project_for(record, raw):
    legacy_id = clean(record.project_legacy_id) or clean(raw.get("XMID"))
    project_name = clean(record.project_name) or clean(raw.get("XMMC")) or "历史工程签证未归集项目"
    project = False
    if legacy_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
    if not project and project_name:
        project = Project.search([("name", "=", project_name)], limit=1)
    if project:
        return project
    return Project.create({"name": project_name, "legacy_project_id": legacy_id or False})


def partner_for(raw):
    name = partner_name_for(raw)
    if not name:
        return False
    partner = Partner.search([("name", "=", name)], limit=1)
    if partner:
        return partner.id
    return Partner.create({"name": name, "company_type": "company"}).id


def values_for(record, raw):
    project = project_for(record, raw)
    event_no = clean(record.document_no) or clean(raw.get("DJBH")) or "LEGACY-GCQZD-%s" % record.id
    event_type_text = clean(raw.get("QZLX")) or "工程签证"
    description_parts = [
        "旧库工程签证单",
        "签证类型：%s" % event_type_text,
        "签证描述：%s" % clean(raw.get("QZMS")),
        "风险名称：%s" % clean(raw.get("FXMC")),
        "建设单位：%s" % clean(raw.get("JSDW")),
        "监理单位：%s" % clean(raw.get("JLDW")),
        "录入人：%s" % (clean(raw.get("LRR")) or clean(record.creator_name)),
        "录入时间：%s" % (clean(raw.get("LRSJ")) or clean(record.document_date)),
    ]
    return {
        "name": "%s-%s" % (event_type_text, event_no),
        "event_type": "site_instruction",
        "project_id": project.id,
        "partner_id": partner_for(raw),
        "event_no": event_no,
        "source_channel": "import",
        "event_date": date_value(raw.get("SJ")) or date_value(record.document_date),
        "amount_impact": money(raw.get("SJJE")),
        "tax_excluded_amount": 0.0,
        "tax_amount": 0.0,
        "settlement_included": money(raw.get("SJJE")) != 0.0,
        "description": "\n".join(description_parts),
        "basis": clean(raw.get("FJ")),
        "state": state_for(raw),
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": record.id,
        "legacy_fact_key": "%s:%s" % (SOURCE_TABLE, clean(record.legacy_record_id)),
        "legacy_fact_type": event_type_text,
    }


records = Residual.search([("source_table", "=", SOURCE_TABLE)], order="document_date, id")
plan = []
residuals = []
created = 0
updated = 0
skipped = 0

for record in records:
    raw = raw_for(record)
    values = values_for(record, raw)
    existing = Event.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_key", "=", values["legacy_fact_key"])], limit=1)
    entry = {
        "legacy_fact_key": values["legacy_fact_key"],
        "event_no": values["event_no"],
        "project": Project.browse(values["project_id"]).display_name,
        "type": values["legacy_fact_type"],
        "state": values["state"],
        "amount": "%.2f" % values["amount_impact"],
        "action": "update" if existing else "create",
    }
    plan.append(entry)
    if not APPLY:
        skipped += 1
        continue
    if existing:
        existing.write(values)
        updated += 1
    else:
        Event.create(values)
        created += 1

if APPLY:
    env.cr.commit()  # noqa: F821

with PLAN_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["legacy_fact_key", "event_no", "project", "type", "state", "amount", "action"])
    writer.writeheader()
    writer.writerows(plan)

with RESIDUAL_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["legacy_fact_key", "reason", "amount"])
    writer.writeheader()
    writer.writerows(residuals)

domain = [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_key", "like", SOURCE_TABLE + ":%")]
events = Event.search(domain)
state_counts = {}
for group in Event.read_group(domain, ["state"], ["state"]):
    state_counts[group.get("state") or ""] = group.get("state_count", 0)
type_counts = {}
for group in Event.read_group(domain, ["legacy_fact_type"], ["legacy_fact_type"]):
    type_counts[group.get("legacy_fact_type") or ""] = group.get("legacy_fact_type_count", 0)

result = {
    "status": "PASS" if not residuals else "WARN",
    "mode": "legacy_project_site_instruction_projection",
    "target_model": "sc.contract.event",
    "source_model": SOURCE_MODEL,
    "source_table": SOURCE_TABLE,
    "apply": APPLY,
    "source_rows": len(records),
    "planned": len(plan),
    "created": created,
    "updated": updated,
    "skipped": skipped,
    "target_rows": len(events),
    "target_amount": round(sum(events.mapped("amount_impact")), 2),
    "state_counts": state_counts,
    "type_counts": type_counts,
    "residuals": residuals,
    "artifacts": {
        "plan_csv": str(PLAN_CSV),
        "residual_csv": str(RESIDUAL_CSV),
        "result_json": str(RESULT_JSON),
    },
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("LEGACY_PROJECT_SITE_INSTRUCTION_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
