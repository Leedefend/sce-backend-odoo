# -*- coding: utf-8 -*-
"""Replay SCBS55 user-acceptance surfaces from locked old-system row dumps.

Run through ``odoo shell``. The script refuses to write until the local old row
dumps match ``scbs55_user_acceptance_evidence_lock_v1.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
if not (ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json").exists():
    ROOT = Path.cwd()
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
EVIDENCE_LOCK = ROOT / "docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json"
OLD_ROWS_DIR = Path(
    os.getenv("MIGRATION_SCBS55_OLD_ROWS_DIR")
    or os.getenv("SCBS55_OLD_ROWS_DIR")
    or "/tmp/scbs55_old_pages_20260530"
)
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbs55_user_acceptance_replay_result_v1.json"


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def amount(value):
    text = clean(value).replace(",", "")
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def date_value(value):
    text = clean(value)
    return text[:10] if text else False


def datetime_value(value):
    text = clean(value)
    if not text:
        return False
    text = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def state_label(value, fallback=""):
    text = clean(fallback)
    if text:
        return text
    return {"2": "已审核", "1": "审核中", "0": "未审核", "-1": "已驳回"}.get(clean(value), clean(value))


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def load_locked_rows():
    manifest = load_json(MANIFEST)
    lock = load_json(EVIDENCE_LOCK)
    locked_by_key = {item["key"]: item for item in lock.get("surfaces", [])}
    out = {}
    errors = []
    for surface in manifest.get("surfaces", []):
        key = surface["key"]
        old = surface["old"]
        locked = locked_by_key.get(key)
        path = OLD_ROWS_DIR / old["row_dump_file"]
        if not locked:
            errors.append({"key": key, "error": "missing_evidence_lock_entry"})
            continue
        if not path.exists():
            errors.append({"key": key, "error": "missing_old_row_dump", "path": str(path)})
            continue
        actual_sha = sha256_file(path)
        if actual_sha != locked.get("old_row_dump_sha256"):
            errors.append({"key": key, "error": "old_row_dump_sha256_drift", "actual": actual_sha, "locked": locked.get("old_row_dump_sha256")})
            continue
        payload = load_json(path)
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            errors.append({"key": key, "error": "old_row_dump_missing_rows", "path": str(path)})
            continue
        if len(rows) != int(old["expected_count"]):
            errors.append({"key": key, "error": "old_row_count_mismatch", "actual": len(rows), "expected": old["expected_count"]})
        identity = old["identity_field"]
        identities = [clean(row.get(identity)) for row in rows if isinstance(row, dict)]
        if len(set(identities)) != len(rows) or any(not item for item in identities):
            errors.append({"key": key, "error": "old_identity_not_unique_or_blank", "identity_field": identity})
        out[key] = [row for row in rows if isinstance(row, dict)]
    if errors:
        raise RuntimeError({"locked_evidence_precheck_failed": errors})
    return manifest, out


def partner_id_for(legacy_id, name):
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    rec = Partner.browse()
    for field in ("legacy_partner_id", "sc_legacy_partner_id"):
        if legacy_id and field in Partner._fields:
            rec = Partner.search([(field, "=", legacy_id)], limit=1)
            if rec:
                return rec.id
    if name:
        rec = Partner.search([("name", "=", name)], limit=1)
    return rec.id if rec else False


def project_id_for(legacy_id, name, required=False):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    rec = Project.browse()
    if legacy_id and "legacy_project_id" in Project._fields:
        rec = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
    if not rec and name:
        rec = Project.search([("name", "=", name)], limit=1)
    if required and not rec:
        raise RuntimeError({"project_missing_for_locked_acceptance_row": {"legacy_project_id": legacy_id, "project_name": name}})
    return rec.id if rec else False


def precheck_replay_dependencies(rows_by_key):
    Fact = env["sc.legacy.receipt.income.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    rows = rows_by_key["engineering_progress_receipt"]
    ids = [clean(row.get("Id")) for row in rows if clean(row.get("Id"))]
    existing = {
        clean(row["legacy_record_id"])
        for row in Fact.search_read(
            [
                ("legacy_source_table", "=", "C_JFHKLR"),
                ("source_family", "=", "engineering_progress_receipt_visible"),
                ("operation_strategy", "=", "joint"),
                ("legacy_record_id", "in", ids),
            ],
            ["legacy_record_id"],
        )
    }
    project_cache = {}
    blockers = []
    for row in rows:
        legacy_id = clean(row.get("Id"))
        if not legacy_id or legacy_id in existing:
            continue
        project_legacy_id = clean(row.get("XMID"))
        project_name = clean(row.get("XMMC"))
        cache_key = (project_legacy_id, project_name)
        if cache_key not in project_cache:
            rec = Project.browse()
            if project_legacy_id and "legacy_project_id" in Project._fields:
                rec = Project.search([("legacy_project_id", "=", project_legacy_id)], limit=1)
            if not rec and project_name:
                rec = Project.search([("name", "=", project_name)], limit=1)
            project_cache[cache_key] = bool(rec)
        if not project_cache[cache_key]:
            blockers.append(
                {
                    "surface": "engineering_progress_receipt",
                    "legacy_record_id": legacy_id,
                    "document_no": clean(row.get("DJBH")),
                    "legacy_project_id": project_legacy_id,
                    "project_name": project_name,
                    "reason": "project_master_dependency_missing_for_new_engineering_receipt_fact",
                }
            )
            if len(blockers) >= 50:
                break
    return blockers


def self_funding_vals(line_type, source_table, row):
    if line_type == "income_visible":
        self_amount = amount(row.get("f_JE"))
        refund_amount = amount(row.get("THJE") or row.get("CZJE"))
        return {
            "source_table": source_table,
            "legacy_record_id": clean(row.get("Id")),
            "legacy_pid": clean(row.get("PID") or row.get("pid")),
            "line_type": line_type,
            "document_no": clean(row.get("DJBH")),
            "document_date": date_value(row.get("f_RQ")),
            "document_state": clean(row.get("DJZT")),
            "document_state_label": state_label(row.get("DJZT"), row.get("DJZTText")),
            "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
            "kingdee_document_no": clean(row.get("OTHER_SYSTEM_CODE")),
            "deleted_flag": clean(row.get("DEL")) or "0",
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("XMMC")),
            "project_id": project_id_for(clean(row.get("XMID")), clean(row.get("XMMC"))),
            "partner_legacy_id": clean(row.get("WLDWID")),
            "partner_name": clean(row.get("WLDWMC")),
            "partner_id": partner_id_for(clean(row.get("WLDWID")), clean(row.get("WLDWMC"))),
            "income_category": clean(row.get("f_SRLBName")),
            "receipt_type": clean(row.get("type")),
            "legacy_category": clean(row.get("LX") or "自筹垫付"),
            "title": clean(row.get("BT")),
            "need_refund": clean(row.get("SFTH") or row.get("SFXYTHID")),
            "self_funding_amount": self_amount,
            "refund_amount": refund_amount,
            "unreturned_amount": amount(row.get("WTJE") or row.get("YSJE")) - refund_amount if clean(row.get("YSJE")) else self_amount - refund_amount,
            "payment_method": clean(row.get("FKFSMC")),
            "account_name": clean(row.get("SKZH")),
            "attachment_text": clean(row.get("f_FJ") or row.get("FJ")),
            "entry_user": clean(row.get("LRR")),
            "entry_time": datetime_value(row.get("LRSJ")),
            "note": clean(row.get("f_BZ") or row.get("BZ")),
            "import_batch": "scbs55_user_acceptance_replay_v1",
            "active": True,
        }
    refund_amount = amount(row.get("THJE") or row.get("f_JE"))
    return {
        "source_table": source_table,
        "legacy_record_id": clean(row.get("Id")),
        "legacy_pid": clean(row.get("pid") or row.get("PID")),
        "line_type": line_type,
        "document_no": clean(row.get("DJBH")),
        "document_date": date_value(row.get("DJRQ") or row.get("f_RQ")),
        "document_state": clean(row.get("DJZT")),
        "document_state_label": state_label(row.get("DJZT"), row.get("DJZTText")),
        "push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "deleted_flag": clean(row.get("DEL")) or "0",
        "project_legacy_id": clean(row.get("XMID")),
        "project_name": clean(row.get("XMMC")),
        "project_id": project_id_for(clean(row.get("XMID")), clean(row.get("XMMC"))),
        "partner_legacy_id": clean(row.get("XMJLID") or row.get("WLDWID")),
        "partner_name": clean(row.get("WLDWFKDW") or row.get("XMJLMC") or row.get("WLDWMC")),
        "partner_id": partner_id_for(clean(row.get("XMJLID") or row.get("WLDWID")), clean(row.get("WLDWFKDW") or row.get("XMJLMC") or row.get("WLDWMC"))),
        "legacy_category": clean(row.get("SJBMC") or "自筹垫付退回"),
        "refund_amount": refund_amount,
        "unreturned_amount": 0 - refund_amount,
        "attachment_text": clean(row.get("f_FJ") or row.get("FJ")),
        "entry_user": clean(row.get("LRR")),
        "entry_time": datetime_value(row.get("LRSJ")),
        "note": clean(row.get("BZ") or row.get("f_BZ")),
        "import_batch": "scbs55_user_acceptance_replay_v1",
        "active": True,
    }


def replay_self_funding(rows_by_key):
    Model = env["sc.legacy.self.funding.fact"].sudo().with_context(active_test=False)  # noqa: F821
    specs = {
        "self_funding_income": ("income_visible", "online_old_scbs:C_JFHKLR:self_funding_income"),
        "self_funding_refund": ("refund_visible", "online_old_scbs:C_JFHKLR_TH_ZCDF:self_funding_refund"),
    }
    result = {}
    for key, (line_type, source_table) in specs.items():
        rows = rows_by_key[key]
        seen = set()
        created = 0
        updated = 0
        for row in rows:
            vals = self_funding_vals(line_type, source_table, row)
            legacy_id = vals["legacy_record_id"]
            if not legacy_id:
                continue
            seen.add(legacy_id)
            rec = Model.search([("source_table", "=", source_table), ("line_type", "=", line_type), ("legacy_record_id", "=", legacy_id)], limit=1)
            if rec:
                rec.write(vals)
                updated += 1
            else:
                Model.create(vals)
                created += 1
        stale = Model.search([("source_table", "=", source_table), ("line_type", "=", line_type), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
        stale.write({"active": False})
        actual = Model.search_count([("source_table", "=", source_table), ("line_type", "=", line_type), ("active", "=", True)])
        result[key] = {"created": created, "updated": updated, "stale_deactivated": len(stale), "actual_count": actual, "expected_count": len(rows)}
    return result


def replay_engineering_progress(rows_by_key):
    Model = env["sc.legacy.receipt.income.fact"].sudo().with_context(active_test=False)  # noqa: F821
    rows = rows_by_key["engineering_progress_receipt"]
    seen = set()
    created = 0
    updated = 0
    for row in rows:
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        seen.add(legacy_id)
        rec = Model.search([("legacy_source_table", "=", "C_JFHKLR"), ("source_family", "=", "engineering_progress_receipt_visible"), ("operation_strategy", "=", "joint"), ("legacy_record_id", "=", legacy_id)], limit=1)
        project_id = rec.project_id.id if rec and rec.project_id else project_id_for(clean(row.get("XMID")), clean(row.get("XMMC")), required=True)
        vals = {
            "legacy_source_table": "C_JFHKLR",
            "legacy_record_id": legacy_id,
            "legacy_pid": clean(row.get("PID") or row.get("pid")),
            "source_family": "engineering_progress_receipt_visible",
            "operation_strategy": "joint",
            "direction": "income",
            "document_no": clean(row.get("DJBH")),
            "document_date": date_value(row.get("f_RQ")),
            "legacy_state": clean(row.get("DJZT")),
            "receipt_type": clean(row.get("type")),
            "income_category": clean(row.get("f_SRLBName")),
            "project_id": project_id,
            "legacy_project_id": clean(row.get("XMID")),
            "legacy_project_name": clean(row.get("XMMC")),
            "partner_id": partner_id_for(clean(row.get("WLDWID")), clean(row.get("WLDWMC"))),
            "legacy_partner_id": clean(row.get("WLDWID")),
            "legacy_partner_name": clean(row.get("WLDWMC")),
            "source_amount": amount(row.get("f_JE")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": datetime_value(row.get("LRSJ")),
            "note": clean(row.get("f_BZ") or row.get("BZ")),
            "import_batch": "scbs55_user_acceptance_replay_v1",
        }
        if rec:
            rec.write(vals)
            updated += 1
        else:
            Model.create(vals)
            created += 1
    stale = Model.search([("legacy_source_table", "=", "C_JFHKLR"), ("source_family", "=", "engineering_progress_receipt_visible"), ("operation_strategy", "=", "joint"), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale.unlink()
    no_strategy_stale = Model.search([("legacy_source_table", "=", "C_JFHKLR"), ("source_family", "=", "engineering_progress_receipt_visible"), ("operation_strategy", "=", False)])
    no_strategy_stale.unlink()
    actual = env["sc.legacy.engineering.progress.receipt"].sudo().search_count([("operation_strategy", "=", "joint")])  # noqa: F821
    return {"created": created, "updated": updated, "stale_deleted": len(stale), "no_strategy_stale_deleted": len(no_strategy_stale), "actual_count": actual, "expected_count": len(rows)}


def replay_supplier_contract(rows_by_key):
    Model = env["sc.legacy.supplier.contract.pricing.fact"].sudo().with_context(active_test=False)  # noqa: F821
    rows = rows_by_key["supplier_contract"]
    seen = set()
    created = 0
    updated = 0
    for row in rows:
        legacy_id = clean(row.get("Id"))
        if not legacy_id:
            continue
        seen.add(legacy_id)
        vals = {
            "legacy_source_table": "T_GYSHT_INFO",
            "legacy_contract_id": legacy_id,
            "document_state": clean(row.get("DJZT")),
            "deleted_flag": clean(row.get("DEL")) or "0",
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("ProjectName") or row.get("XMMC")),
            "project_id": project_id_for(clean(row.get("XMID")), clean(row.get("ProjectName") or row.get("XMMC"))),
            "partner_legacy_id": clean(row.get("f_GYSID") or row.get("GYSID")),
            "partner_name": clean(row.get("f_GYSName") or row.get("GYSName")),
            "partner_id": partner_id_for(clean(row.get("f_GYSID") or row.get("GYSID")), clean(row.get("f_GYSName") or row.get("GYSName"))),
            "pricing_method_legacy_id": clean(row.get("JJFSID")),
            "pricing_method_text": clean(row.get("JJFSTEXT")),
            "amount_total": amount(row.get("ZJE")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("f_LRR") or row.get("LRR")),
            "created_time": datetime_value(row.get("f_LRRQ") or row.get("LRSJ")),
            "import_batch": "scbs55_user_acceptance_replay_v1",
            "active": True,
        }
        rec = Model.search([("legacy_contract_id", "=", legacy_id)], limit=1)
        if rec:
            rec.write(vals)
            updated += 1
        else:
            Model.create(vals)
            created += 1
    stale = Model.search([("legacy_source_table", "=", "T_GYSHT_INFO"), ("active", "=", True), ("legacy_contract_id", "not in", list(seen) or ["__none__"])])
    stale.write({"active": False})
    actual = Model.search_count([("legacy_source_table", "=", "T_GYSHT_INFO"), ("active", "=", True)])
    return {"created": created, "updated": updated, "stale_deactivated": len(stale), "actual_count": actual, "expected_count": len(rows)}


def post_counts():
    return {
        "self_guarantee": env["tender.guarantee"].sudo().search_count([("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Branch_SBZJDJ:list868")]),  # noqa: F821
        "self_guarantee_refund": env["tender.guarantee"].sudo().search_count([("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Branch_SBZJTH:list869")]),  # noqa: F821
        "self_funding_income": env["sc.legacy.self.funding.fact"].sudo().search_count([("line_type", "=", "income_visible")]),  # noqa: F821
        "self_funding_refund": env["sc.legacy.self.funding.fact"].sudo().search_count([("line_type", "=", "refund_visible")]),  # noqa: F821
        "engineering_progress_receipt": env["sc.legacy.engineering.progress.receipt"].sudo().search_count([("operation_strategy", "=", "joint")]),  # noqa: F821
        "supplier_contract": env["sc.legacy.supplier.contract.pricing.fact"].sudo().search_count([("legacy_source_table", "=", "T_GYSHT_INFO"), ("active", "=", True)]),  # noqa: F821
    }


ensure_allowed_db()
manifest, rows_by_key = load_locked_rows()
expected = {surface["key"]: int(surface["new"]["expected_count"]) for surface in manifest["surfaces"]}
dependency_blockers = precheck_replay_dependencies(rows_by_key)
if dependency_blockers:
    payload = {
        "status": "FAIL",
        "mode": "scbs55_user_acceptance_replay",
        "database": env.cr.dbname,  # noqa: F821
        "old_rows_dir": str(OLD_ROWS_DIR),
        "dependency_blockers": dependency_blockers,
        "errors": [{"error": "dependency_precheck_failed", "count": len(dependency_blockers)}],
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("SCBS55_USER_ACCEPTANCE_REPLAY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    raise RuntimeError(payload)
operations = {
    "self_funding": replay_self_funding(rows_by_key),
    "engineering_progress_receipt": replay_engineering_progress(rows_by_key),
    "supplier_contract": replay_supplier_contract(rows_by_key),
}
counts = post_counts()
errors = [{"key": key, "actual": counts.get(key), "expected": value} for key, value in expected.items() if counts.get(key) != value]
payload = {
    "status": "FAIL" if errors else "PASS",
    "mode": "scbs55_user_acceptance_replay",
    "database": env.cr.dbname,  # noqa: F821
    "old_rows_dir": str(OLD_ROWS_DIR),
    "operations": operations,
    "post_counts": counts,
    "expected_counts": expected,
    "errors": errors,
}
write_json(OUTPUT_JSON, payload)
if errors:
    env.cr.rollback()  # noqa: F821
    print("SCBS55_USER_ACCEPTANCE_REPLAY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    raise RuntimeError(payload)
env.cr.commit()  # noqa: F821
print("SCBS55_USER_ACCEPTANCE_REPLAY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
