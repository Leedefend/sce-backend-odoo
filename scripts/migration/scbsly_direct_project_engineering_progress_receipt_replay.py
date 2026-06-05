# -*- coding: utf-8 -*-
"""Replay SCBSLY direct-project engineering-progress receipts.

Run through ``odoo shell``. The script writes only to an allowlisted database
and feeds the existing user-visible engineering-progress receipt SQL view via
``sc.legacy.receipt.income.fact``.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
if not (ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json").exists():
    ROOT = Path.cwd()
OLD_ROWS_DIR = Path(
    os.getenv("MIGRATION_SCBSLY_OLD_ROWS_DIR")
    or os.getenv("SCBSLY_OLD_ROWS_DIR")
    or "/tmp/scbsly_direct_project_old_pages_20260530"
)
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_direct_project_engineering_progress_receipt_replay_result_v1.json"

LABEL = "工程进度收款"
INPUT_FILE = "工程进度收款__e65e4a85bed946968daad69271e91ca2.json"
SOURCE_TABLE = "C_JFHKLR"
SOURCE_FAMILY = "engineering_progress_receipt_visible"
OPERATION_STRATEGY = "direct"
IMPORT_BATCH = "scbsly_direct_project_engineering_progress_receipt_replay_v1"
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
ATTACHMENT_FIELDS = ("FJ", "f_FJ")


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def amount(*values):
    for value in values:
        text = clean(value).replace(",", "")
        if not text:
            continue
        try:
            return float(text)
        except ValueError:
            continue
    return 0.0


def date_value(value):
    text = clean(value)
    return text[:10] if text else False


def datetime_value(value):
    text = clean(value).replace("T", " ")
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def attachment_ref_value(row):
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and ATTACHMENT_ID_RE.match(value):
            return value
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and not ATTACHMENT_LABEL_RE.match(value):
            return value
    return ""


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        target = Path("/tmp") / path.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["output_json"] = str(target)
    return target


def ensure_allowed_db():
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def partner_id_for(legacy_id, name, cache):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = False
    for field in ("legacy_partner_id", "sc_legacy_partner_id"):
        if clean(legacy_id) and field in Partner._fields:
            partner = Partner.search([(field, "=", clean(legacy_id))], limit=1)
            if partner:
                break
    if not partner and clean(name):
        partner = Partner.search([("name", "=", clean(name))], limit=1)
    cache[key] = partner.id if partner else False
    return cache[key]


def project_id_for(legacy_id, name, cache, created_projects):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(legacy_id) and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    if not project and clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    if not project:
        values = {
            "name": clean(name) or ("SCBSLY历史项目 " + clean(legacy_id)),
        }
        if "legacy_project_id" in Project._fields:
            values["legacy_project_id"] = clean(legacy_id) or False
        if "legacy_parent_id" in Project._fields:
            values["legacy_parent_id"] = clean(legacy_id) or False
        if "legacy_note" in Project._fields:
            values["legacy_note"] = "SCBSLY直营项目工程进度收款补锚；source=C_JFHKLR"
        project = Project.create(values)
        created_projects.append(
            {
                "legacy_project_id": clean(legacy_id),
                "project_id": project.id,
                "project_name": project.display_name,
            }
        )
    cache[key] = project.id if project else False
    return cache[key]


def values_for(row, project_cache, partner_cache, created_projects):
    return {
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": clean(row.get("Id")),
        "legacy_pid": clean(row.get("PID") or row.get("pid")),
        "source_family": SOURCE_FAMILY,
        "operation_strategy": OPERATION_STRATEGY,
        "direction": "income",
        "document_no": clean(row.get("DJBH")),
        "document_date": date_value(row.get("f_RQ")),
        "legacy_state": clean(row.get("DJZT")),
        "receipt_type": clean(row.get("type") or row.get("D_LYXM_SRLX")),
        "income_category": clean(row.get("f_SRLBName") or row.get("BT")),
        "project_id": project_id_for(row.get("XMID"), row.get("XMMC"), project_cache, created_projects),
        "legacy_project_id": clean(row.get("XMID")),
        "legacy_project_name": clean(row.get("XMMC")),
        "partner_id": partner_id_for(row.get("WLDWID"), row.get("WLDWMC"), partner_cache),
        "legacy_partner_id": clean(row.get("WLDWID")),
        "legacy_partner_name": clean(row.get("WLDWMC")),
        "legacy_company_name": clean(row.get("SSGS")),
        "legacy_contract_no": clean(row.get("SGHTBH")),
        "legacy_receiving_account": clean(row.get("SKZH")),
        "legacy_attachment_ref": attachment_ref_value(row),
        "source_amount": amount(row.get("f_JE"), row.get("D_LYXM_JENR3")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": datetime_value(row.get("LRSJ")),
        "note": clean(row.get("f_BZ") or row.get("BZ")),
        "import_batch": IMPORT_BATCH,
    }


def replay():
    path = OLD_ROWS_DIR / INPUT_FILE
    if not path.exists():
        raise RuntimeError({"missing_scbsly_engineering_progress_old_rows": str(path)})
    payload = load_json(path)
    rows = payload.get("rows") or []
    if len(rows) != int(payload.get("expected_count") or len(rows)):
        raise RuntimeError({"old_row_count_mismatch": {"actual": len(rows), "expected": payload.get("expected_count")}})
    Model = env["sc.legacy.receipt.income.fact"].sudo().with_context(active_test=False)  # noqa: F821
    project_cache = {}
    partner_cache = {}
    created_projects = []
    created = updated = skipped = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            skipped += 1
            continue
        values = values_for(row, project_cache, partner_cache, created_projects)
        seen.add(legacy_id)
        existing = Model.search(
            [
                ("legacy_source_table", "=", SOURCE_TABLE),
                ("source_family", "=", SOURCE_FAMILY),
                ("operation_strategy", "=", OPERATION_STRATEGY),
                ("legacy_record_id", "=", legacy_id),
            ],
            limit=1,
        )
        if existing:
            existing.write(values)
            updated += 1
        else:
            Model.create(values)
            created += 1
    stale = Model.search(
        [
            ("legacy_source_table", "=", SOURCE_TABLE),
            ("source_family", "=", SOURCE_FAMILY),
            ("operation_strategy", "=", OPERATION_STRATEGY),
            ("legacy_record_id", "not in", list(seen) or ["__none__"]),
        ]
    )
    stale_count = len(stale)
    if stale:
        stale.unlink()
    legacy_split_stale = Model.search(
        [
            ("legacy_source_table", "=", SOURCE_TABLE),
            ("source_family", "=", "scbsly_direct_engineering_progress_receipt_visible"),
        ]
    )
    legacy_split_stale_count = len(legacy_split_stale)
    if legacy_split_stale:
        legacy_split_stale.unlink()
    no_strategy_stale = Model.search(
        [
            ("legacy_source_table", "=", SOURCE_TABLE),
            ("source_family", "=", SOURCE_FAMILY),
            ("operation_strategy", "=", False),
        ]
    )
    no_strategy_stale_count = len(no_strategy_stale)
    if no_strategy_stale:
        no_strategy_stale.unlink()
    visible_count = env["sc.legacy.engineering.progress.receipt"].sudo().search_count([])  # noqa: F821
    direct_count = env["sc.legacy.engineering.progress.receipt"].sudo().search_count([("operation_strategy", "=", OPERATION_STRATEGY)])  # noqa: F821
    return {
        "label": LABEL,
        "input_path": str(path),
        "input_rows": len(rows),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "stale_deleted": stale_count,
        "legacy_split_stale_deleted": legacy_split_stale_count,
        "no_strategy_stale_deleted": no_strategy_stale_count,
        "created_project_anchor_count": len(created_projects),
        "created_project_anchors": created_projects,
        "visible_count": visible_count,
        "direct_visible_count": direct_count,
        "expected_count": len(rows),
    }


ensure_allowed_db()
result = replay()
output = {
    "status": "PASS" if result["direct_visible_count"] == result["expected_count"] else "FAIL",
    "db": env.cr.dbname,  # noqa: F821
    "old_rows_dir": str(OLD_ROWS_DIR),
    "result": result,
}
write_json(OUTPUT_JSON, output)
env.cr.commit()  # noqa: F821
print("SCBSLY_DIRECT_PROJECT_ENGINEERING_PROGRESS_RECEIPT_REPLAY=" + json.dumps(output, ensure_ascii=False, sort_keys=True))
