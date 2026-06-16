# -*- coding: utf-8 -*-
"""Replay SCBSLY direct-project rental return documents into rental orders."""

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
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_direct_project_rental_return_replay_result_v1.json"

LABEL = "还租"
INPUT_FILE = "还租__fa1a970eae754b78a7f095606d906b87.json"
SOURCE_MODEL = "online_old_scbsly:T_ZL_HZD:list"
LEGACY_TYPE = "scbsly_lease_return"


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
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return text


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
        vals = {"name": clean(name) or ("SCBSLY历史项目 " + clean(legacy_id))}
        if "legacy_project_id" in Project._fields:
            vals["legacy_project_id"] = clean(legacy_id) or False
        if "legacy_parent_id" in Project._fields:
            vals["legacy_parent_id"] = clean(legacy_id) or False
        if "legacy_note" in Project._fields:
            vals["legacy_note"] = "SCBSLY直营项目还租补锚；source=T_ZL_HZD"
        project = Project.create(vals)
        created_projects.append({"legacy_project_id": clean(legacy_id), "project_id": project.id, "project_name": project.display_name})
    cache[key] = project.id
    return cache[key]


def partner_id_for(legacy_id, name, cache, created_partners):
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
    if not partner:
        vals = {"name": clean(name) or ("SCBSLY历史供应商 " + clean(legacy_id)), "supplier_rank": 1}
        if "legacy_partner_id" in Partner._fields and clean(legacy_id):
            vals["legacy_partner_id"] = clean(legacy_id)
        partner = Partner.create(vals)
        created_partners.append({"legacy_partner_id": clean(legacy_id), "partner_id": partner.id, "partner_name": partner.display_name})
    cache[key] = partner.id
    return cache[key]


def state_for(row):
    if clean(row.get("DEL")) not in ("", "0", "False", "false"):
        return "cancel"
    return "returned" if clean(row.get("DJZT")) == "2" else "draft"


def values_for(row, project_cache, partner_cache, created_projects, created_partners):
    total = amount(row.get("D_LYXM_HZJEHJ"), row.get("f_JSJE"))
    fee_total = amount(row.get("D_LYXM_FYXJEHJ"), row.get("f_PCF"), row.get("f_WXF"), row.get("f_JCCF"))
    supplier_name = clean(row.get("f_SupplierName") or row.get("f_LldwName"))
    supplier_legacy_id = clean(row.get("f_Supplier_ID") or row.get("f_Lldw_ID"))
    name = clean(row.get("DJBH") or row.get("f_HZDH") or row.get("ID"))
    return {
        "name": name,
        "project_id": project_id_for(row.get("f_XMID"), row.get("XMMC"), project_cache, created_projects),
        "supplier_id": partner_id_for(supplier_legacy_id, supplier_name, partner_cache, created_partners),
        "rental_date": date_value(row.get("f_DJRQ") or row.get("f_LRSJ")),
        "planned_return_date": date_value(row.get("f_DJRQ") or row.get("f_LRSJ")),
        "owner_id": env.uid,  # noqa: F821
        "currency_id": env.ref("base.CNY", raise_if_not_found=False).id,  # noqa: F821
        "state": state_for(row),
        "note": "\n".join(
            item
            for item in [
                "SCBSLY直营项目还租回放",
                "旧系统ID：%s" % clean(row.get("ID")),
                "旧系统Pid：%s" % clean(row.get("Pid")),
                "旧系统合同：%s" % clean(row.get("f_HTBH")),
                "旧系统状态：%s" % clean(row.get("DJZT")),
                "还租金额：%s" % total,
                "费用合计：%s" % fee_total,
                "录入人：%s" % clean(row.get("f_LRR") or row.get("XGR")),
                "录入时间：%s" % datetime_value(row.get("f_LRSJ")),
                clean(row.get("f_BZ")),
            ]
            if item
        ),
        "legacy_fact_model": SOURCE_MODEL,
        "legacy_fact_id": 0,
        "legacy_fact_type": LEGACY_TYPE,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "material_name": clean(row.get("BT")) or name or "历史还租明细",
                    "qty": 1.0,
                    "rental_days": 1.0,
                    "daily_price": total,
                    "returned_qty": 1.0,
                    "note": clean(row.get("f_BZ")),
                },
            ),
        ],
    }


def replay():
    path = OLD_ROWS_DIR / INPUT_FILE
    if not path.exists():
        raise RuntimeError({"missing_scbsly_rental_return_old_rows": str(path)})
    payload = load_json(path)
    rows = payload.get("rows") or []
    expected = int(payload.get("expected_count") or len(rows))
    if len(rows) != expected:
        raise RuntimeError({"old_row_count_mismatch": {"actual": len(rows), "expected": expected}})
    Model = env["sc.material.rental.order"].sudo().with_context(active_test=False)  # noqa: F821
    project_cache = {}
    partner_cache = {}
    created_projects = []
    created_partners = []
    created = updated = skipped = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        legacy_id = clean(row.get("ID"))
        name = clean(row.get("DJBH") or row.get("f_HZDH") or legacy_id)
        if not legacy_id or not name:
            skipped += 1
            continue
        seen.add(name)
        vals = values_for(row, project_cache, partner_cache, created_projects, created_partners)
        existing = Model.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", LEGACY_TYPE), ("name", "=", name)], limit=1)
        if existing:
            existing.write(vals)
            updated += 1
        else:
            Model.create(vals)
            created += 1
    stale = Model.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", LEGACY_TYPE), ("name", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.unlink()
    final_count = Model.search_count([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", LEGACY_TYPE)])
    lease_in_count = Model.search_count([("legacy_fact_type", "=", "scbsly_lease_in")])
    return {
        "label": LABEL,
        "input_path": str(path),
        "input_rows": len(rows),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "stale_deleted": stale_count,
        "created_project_anchor_count": len(created_projects),
        "created_project_anchors": created_projects,
        "created_partner_anchor_count": len(created_partners),
        "created_partner_anchors": created_partners,
        "final_count": final_count,
        "lease_in_count": lease_in_count,
        "expected_count": len(rows),
    }


ensure_allowed_db()
result = replay()
output = {
    "status": "PASS" if result["final_count"] == result["expected_count"] and result["lease_in_count"] == 0 else "FAIL",
    "db": env.cr.dbname,  # noqa: F821
    "old_rows_dir": str(OLD_ROWS_DIR),
    "result": result,
}
write_json(OUTPUT_JSON, output)
env.cr.commit()  # noqa: F821
print("SCBSLY_DIRECT_PROJECT_RENTAL_RETURN_REPLAY=" + json.dumps(output, ensure_ascii=False, sort_keys=True))
