# -*- coding: utf-8 -*-
"""Replay SCBSLY direct-project fuel-card lists into legacy fact carriers.

Run through ``odoo shell``. The script writes only to an allowlisted database
and uses the locked SCBSLY old row dump directory as input.
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
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_direct_project_fuel_card_replay_result_v1.json"

SPECS = {
    "油卡登记": {
        "file": "油卡登记__3c1aee58340b44f7a31bc986d9dbaf51.json",
        "model": "sc.legacy.fuel.card.fact",
        "source_model": "online_old_scbsly:D_LYXM_BG_BX_YKDJ:list",
        "identity_field": "DJBH",
    },
    "充值登记": {
        "file": "充值登记__63bc86f498964cdc97d8849effdc114d.json",
        "model": "sc.legacy.fuel.card.recharge.fact",
        "source_model": "online_old_scbsly:D_LYXM_BG_BX_CZDJ:list",
        "identity_field": "DJBH",
    },
    "加油登记": {
        "file": "加油登记__91bad12210e94979bdcaf2eb19eaa3fd.json",
        "model": "sc.legacy.fuel.card.refuel.fact",
        "source_model": "online_old_scbsly:D_LYXM_BG_BX_JYDJ:list",
        "identity_field": "DJBH",
    },
}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def amount(value):
    text = clean(value).replace(",", "")
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


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


def project_id(legacy_id, name, cache):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(legacy_id):
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    if not project and clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def base_values(row, spec, project_cache):
    return {
        "legacy_source_model": spec["source_model"],
        "legacy_record_id": clean(row.get(spec["identity_field"])),
        "legacy_parent_id": clean(row.get("PID") or row.get("Pid") or row.get("pid")),
        "document_no": clean(row.get("DJBH")),
        "document_date": datetime_value(row.get("DJRQ") or row.get("CZRQ") or row.get("JYRQ")),
        "document_state": clean(row.get("DJZT")),
        "project_legacy_id": clean(row.get("XMID")),
        "project_name": clean(row.get("XMMC")),
        "project_id": project_id(row.get("XMID"), row.get("XMMC"), project_cache),
        "creator_name": clean(row.get("LRR")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "created_time": datetime_value(row.get("LRSJ")),
        "attachment_ref": clean(row.get("FJ") or row.get("f_FJ")),
        "note": clean(row.get("BZ") or row.get("BZ$D_LYXM_BG_BX_CZDJCB")),
        "active": True,
    }


def values_for(label, row, spec, project_cache):
    values = base_values(row, spec, project_cache)
    if label == "油卡登记":
        values.update(
            {
                "card_no": clean(row.get("YKKH")),
                "initial_amount": amount(row.get("CSJE")),
                "balance_amount": amount(row.get("CSJE")),
                "manager_name": clean(row.get("ZYGLR")),
                "manager_legacy_id": clean(row.get("ZYGLRID")),
            }
        )
    elif label == "充值登记":
        values.update(
            {
                "card_no": clean(row.get("CZKH$D_LYXM_BG_BX_CZDJCB")),
                "recharge_amount": amount(row.get("CZJE$D_LYXM_BG_BX_CZDJCB") or row.get("CZZE")),
                "used_amount": amount(row.get("YSYJE$D_LYXM_BG_BX_CZDJCB")),
                "balance_amount": amount(row.get("SYJE$D_LYXM_BG_BX_CZDJCB")),
                "total_recharge_amount": amount(row.get("YCZJE$D_LYXM_BG_BX_CZDJCB") or row.get("CZZE")),
                "related_document_no": clean(row.get("GLBXD")),
                "handler_name": clean(row.get("CZR")),
            }
        )
    elif label == "加油登记":
        values.update(
            {
                "card_no": clean(row.get("JYKH")),
                "fuel_date": datetime_value(row.get("JYRQ")),
                "fuel_amount": amount(row.get("JYJE")),
                "initial_amount": amount(row.get("YKCSJE")),
                "total_recharge_amount": amount(row.get("LJCZJE")),
                "total_fuel_amount": amount(row.get("LJJYJE")),
                "balance_amount": amount(row.get("YKSYJE")),
                "related_document_no": clean(row.get("GLBXD")),
                "handler_name": clean(row.get("DJR")),
            }
        )
    return values


def replay_label(label, spec):
    path = OLD_ROWS_DIR / spec["file"]
    if not path.exists():
        raise RuntimeError({"missing_scbsly_fuel_old_rows": str(path), "label": label})
    payload = load_json(path)
    rows = payload.get("rows") or []
    Model = env[spec["model"]].sudo().with_context(active_test=False)  # noqa: F821
    project_cache = {}
    created = updated = skipped = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        key = clean(row.get(spec["identity_field"]))
        if not key:
            skipped += 1
            continue
        values = values_for(label, row, spec, project_cache)
        seen.add(key)
        existing = Model.search(
            [("legacy_source_model", "=", spec["source_model"]), ("legacy_record_id", "=", key)],
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
            ("legacy_source_model", "=", spec["source_model"]),
            ("legacy_record_id", "not in", list(seen) or ["__none__"]),
        ]
    )
    stale_count = len(stale)
    if stale:
        stale.write({"active": False})
    return {
        "label": label,
        "model": spec["model"],
        "source_model": spec["source_model"],
        "input_path": str(path),
        "input_rows": len(rows),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "stale_deactivated": stale_count,
        "final_count": Model.search_count([("legacy_source_model", "=", spec["source_model"]), ("active", "=", True)]),
    }


ensure_allowed_db()
results = [replay_label(label, spec) for label, spec in SPECS.items()]
output = {
    "status": "PASS" if all(item["final_count"] == item["input_rows"] for item in results) else "FAIL",
    "db": env.cr.dbname,  # noqa: F821
    "old_rows_dir": str(OLD_ROWS_DIR),
    "results": results,
}
write_json(OUTPUT_JSON, output)
env.cr.commit()  # noqa: F821
print("SCBSLY_DIRECT_PROJECT_FUEL_CARD_REPLAY=" + json.dumps(output, ensure_ascii=False, sort_keys=True))
