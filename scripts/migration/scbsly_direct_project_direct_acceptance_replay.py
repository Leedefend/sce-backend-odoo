# -*- coding: utf-8 -*-
"""Replay locked SCBSLY direct-project old lists into a user-acceptance carrier.

Run through ``odoo shell``. This deliberately targets the acceptance surface:
each configured menu label receives exactly the old-system rows locked by the
online dump, while the original row JSON remains available for later formal
business replay.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
if not (ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json").exists():
    ROOT = Path.cwd()

IDENTITY_LOCK = Path(
    os.getenv("MIGRATION_SCBSLY_IDENTITY_LOCK")
    or ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
)
OLD_ROWS_DIR = Path(
    os.getenv("MIGRATION_SCBSLY_OLD_ROWS_DIR")
    or os.getenv("SCBSLY_OLD_ROWS_DIR")
    or ROOT / "artifacts/migration/scbsly_direct_project_old_pages_20260530"
)
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_direct_project_direct_acceptance_replay_result_v1.json"
SOURCE_SYSTEM = "online_old_scbsly"

ACCEPTANCE_LABELS = {
    "施工合同",
    "分包合同",
    "租赁合同",
    "供货合同",
    "劳务合同",
    "机械合同（合同）",
    "材料计划",
    "报价单",
    "入库",
    "材料结算单",
    "方单",
    "零星用工",
    "劳务结算",
    "分包方单",
    "分包结算单",
    "机械台班记录",
    "机械结算单",
    "租入",
    "还租",
    "租赁结算单",
    "项目费用报销单",
    "管理人员工资表",
    "油卡登记",
    "充值登记",
    "加油登记",
    "支付申请",
    "工程进度收款",
    "往来单位付款",
    "工程结算单",
    "进项上报",
    "总包进项上报",
    "施工日志（新）",
}
DOCUMENT_NO_FIELDS = ("DJBH", "HTBH", "WBHTBH", "BH", "DJH", "JSDH")
TITLE_FIELDS = (
    "HTBT",
    "BT",
    "ZJHMC",
    "BXZL",
    "SXSM",
    "f_CLMC$T_JH_XMZJH",
    "SGBW",
    "RZMC",
    "GCMC",
    "CLMC",
    "MC",
)
DATE_FIELDS = (
    "DJRQ",
    "RQ",
    "BZSJ",
    "LRSJ",
    "f_LRSJ",
    "HTDLRQ",
    "f_HTDLRQ",
    "JYRQ",
    "CZRQ",
    "ZBSJ",
    "SGRQ",
    "JSRQ",
)
PROJECT_ID_FIELDS = ("XMID", "f_XMID$T_JH_XMZJH", "SJBXXMID")
PROJECT_NAME_FIELDS = ("ProjectName", "XMMC", "f_XMMC", "BM", "SJBXXM")
PARTNER_FIELDS = ("CBF", "FBF", "BXDW", "SKR", "GYS", "DWMC", "SGDW", "LWRY", "JBR", "BXR", "ZRR")
AMOUNT_FIELDS = (
    "GCYSZJ",
    "HTJE",
    "SQBXJE",
    "SJBXJE",
    "HJ",
    "JE",
    "JYJE",
    "CZJE",
    "YSJE",
    "JSJE",
    "FKJE",
    "SKJE",
    "SE",
    "f_YSCBHJ$T_JH_XMZJH",
    "SJJFJE",
    "BCFKJE",
)
QUANTITY_FIELDS = ("SL", "f_YSCBSL$T_JH_XMZJH", "GCSL", "TS", "JXTS", "JXSL")
STATE_FIELDS = ("DJZT", "ZT", "f_ZT$T_JH_XMZJH")
CREATOR_FIELDS = ("LRR", "f_LRR", "BZR", "DJR", "CJR")
CREATOR_ID_FIELDS = ("LRRID", "BXRID", "DJRID", "CJRID")
CREATED_TIME_FIELDS = ("LRSJ", "f_LRSJ", "XGSJ", "CJSJ")
ATTACHMENT_FIELDS = ("FJ", "f_FJ")
NOTE_FIELDS = ("BZ", "f_BZ", "SXSM", "SM", "NR")
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def first_text(row, fields):
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def attachment_ref_value(row, acceptance_label=""):
    if acceptance_label == "分包方单" and not ATTACHMENT_LABEL_RE.match(clean(row.get("f_FJ"))):
        return ""
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and ATTACHMENT_ID_RE.match(value):
            return value
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and not ATTACHMENT_LABEL_RE.match(value):
            return value
    return ""


def numeric(value):
    text = clean(value).replace(",", "")
    if not text:
        return 0.0
    text = text.replace("￥", "").replace("¥", "")
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group(0)) if match else 0.0


def first_numeric(row, fields):
    for field in fields:
        value = numeric(row.get(field))
        if value:
            return value
    return 0.0


def datetime_value(value):
    text = clean(value).replace("T", " ").replace("/", "-")
    if not text:
        return False
    text = re.sub(r"\.\d+$", "", text)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            length = 19 if "%S" in fmt else 16 if "%M" in fmt else 10
            parsed = datetime.strptime(text[:length], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return False


def first_datetime(row, fields):
    for field in fields:
        value = datetime_value(row.get(field))
        if value:
            return value
    return False


def int_value(value):
    try:
        return int(float(clean(value)))
    except ValueError:
        return 0


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
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_odoo,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def project_id(legacy_id, name, cache):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(legacy_id) and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    if not project and clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def row_hash(row):
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def identity_value(row, identity_field):
    value = clean(row.get(identity_field))
    if value:
        return value
    for field in ("Id", "id", "DJBH", "PID", "Pid", "pid", "RowIndex"):
        value = clean(row.get(field))
        if value:
            return value
    return "hash:" + row_hash(row)


def values_for(row, spec, project_cache):
    project_legacy_id = first_text(row, PROJECT_ID_FIELDS)
    project_name = first_text(row, PROJECT_NAME_FIELDS)
    raw_payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return {
        "source_system": SOURCE_SYSTEM,
        "acceptance_label": spec["label"],
        "category": spec.get("category") or "",
        "legacy_config_id": spec.get("config_id") or "",
        "legacy_record_id": identity_value(row, spec.get("identity_field")),
        "legacy_parent_id": first_text(row, ("PID", "Pid", "pid")),
        "row_index": int_value(row.get("RowIndex")),
        "document_no": first_text(row, DOCUMENT_NO_FIELDS),
        "document_title": first_text(row, TITLE_FIELDS),
        "document_date": first_datetime(row, DATE_FIELDS),
        "document_state": first_text(row, STATE_FIELDS),
        "project_id": project_id(project_legacy_id, project_name, project_cache),
        "project_legacy_id": project_legacy_id,
        "project_name": project_name,
        "partner_name": first_text(row, PARTNER_FIELDS),
        "amount_total": first_numeric(row, AMOUNT_FIELDS),
        "quantity": first_numeric(row, QUANTITY_FIELDS),
        "creator_name": first_text(row, CREATOR_FIELDS),
        "creator_legacy_user_id": first_text(row, CREATOR_ID_FIELDS),
        "created_time": first_datetime(row, CREATED_TIME_FIELDS),
        "attachment_ref": attachment_ref_value(row, spec.get("label") or ""),
        "note": first_text(row, NOTE_FIELDS),
        "raw_payload": raw_payload,
        "active": True,
    }


def specs_from_identity_lock():
    payload = load_json(IDENTITY_LOCK)
    specs = []
    for row in payload.get("rows") or []:
        label = row.get("label")
        if label not in ACCEPTANCE_LABELS:
            continue
        specs.append(
            {
                "label": label,
                "category": row.get("category"),
                "config_id": row.get("config_id"),
                "dump_path": row.get("dump_path"),
                "identity_field": row.get("identity_field"),
                "expected_total": row.get("total"),
            }
        )
    missing = sorted(ACCEPTANCE_LABELS.difference({spec["label"] for spec in specs}))
    if missing:
        raise RuntimeError({"missing_labels_in_identity_lock": missing, "identity_lock": str(IDENTITY_LOCK)})
    return specs


def replay_label(spec):
    path = Path(spec["dump_path"])
    if not path.exists():
        path = OLD_ROWS_DIR / Path(spec["dump_path"]).name
    if not path.exists():
        raise RuntimeError({"missing_scbsly_direct_old_rows": str(path), "label": spec["label"]})
    payload = load_json(path)
    rows = payload.get("rows") or []
    Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Model.search([("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", spec["label"])]).write(
        {"active": False}
    )
    project_cache = {}
    created = updated = skipped = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        values = values_for(row, spec, project_cache)
        key = values["legacy_record_id"]
        if not key or key in seen:
            skipped += 1
            continue
        seen.add(key)
        existing = Model.search(
            [
                ("source_system", "=", SOURCE_SYSTEM),
                ("acceptance_label", "=", spec["label"]),
                ("legacy_record_id", "=", key),
            ],
            limit=1,
        )
        if existing:
            existing.write(values)
            updated += 1
        else:
            Model.create(values)
            created += 1
    active_count = Model.search_count(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", spec["label"]), ("active", "=", True)]
    )
    return {
        "label": spec["label"],
        "category": spec.get("category"),
        "config_id": spec.get("config_id"),
        "input_path": str(path),
        "input_rows": len(rows),
        "expected_total": spec.get("expected_total"),
        "active_count": active_count,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "status": "PASS" if active_count == len(rows) == spec.get("expected_total") else "FAIL",
    }


def main():
    ensure_allowed_db()
    specs = specs_from_identity_lock()
    results = [replay_label(spec) for spec in specs]
    env.cr.commit()  # noqa: F821
    summary = {
        "status": "PASS" if not any(item["status"] != "PASS" for item in results) else "FAIL",
        "db_name": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "identity_lock": str(IDENTITY_LOCK),
        "label_count": len(results),
        "failure_count": sum(1 for item in results if item["status"] != "PASS"),
        "results": results,
    }
    output = write_json(OUTPUT_JSON, summary)
    print(json.dumps({"output_json": str(output), **summary}, ensure_ascii=False, indent=2, sort_keys=True))
    if summary["failure_count"]:
        raise RuntimeError(summary)


main()
