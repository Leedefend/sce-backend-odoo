"""Project legacy bid/tender facts into tender.bid.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_TABLES = ("P_ZTB_GCXXGL", "WS_HTGL_ZBHT")
SOURCE_MODEL_PREFIX = "legacy.main."


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/tmp")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value) -> str:
    return str(value or "").strip()


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_date(value: str):
    return value[:10] if value else False


def raw_json(record) -> dict[str, object]:
    try:
        return json.loads(record.raw_payload or "{}")
    except json.JSONDecodeError:
        return {}


def project_by_fact(cache: dict[str, int | bool], legacy_id: str, name: str):
    """Prefer exact name for tender facts; some old tender rows reused generic XMID."""
    key = clean(name) or "__legacy__:" + clean(legacy_id)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    if not project and clean(legacy_id):
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def partner_by_name(cache: dict[str, int | bool], name: str):
    key = clean(name)
    if not key:
        return False
    if key in cache:
        return cache[key]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", key)], limit=1)
    if not partner:
        partner = Partner.create({"name": key, "customer_rank": 1})
    elif partner.customer_rank <= 0:
        partner.write({"customer_rank": 1})
    cache[key] = partner.id
    return cache[key]


def user_name(payload: dict[str, object]) -> str:
    return clean(payload.get("f_LRR")) or clean(payload.get("LRR")) or clean(payload.get("XGR"))


def p_ztb_values(record, payload: dict[str, object], project_id: int | bool, partner_cache: dict[str, int | bool]) -> dict[str, object]:
    owner_name = clean(payload.get("f_JSDW")) or clean(payload.get("JSDW")) or clean(payload.get("KHMC"))
    guarantee_amount = to_float(payload.get("BZJJE"))
    project_scale = to_float(payload.get("ZGXJ")) or to_float(payload.get("XMGM"))
    open_time = clean(payload.get("KBSJ"))
    deadline = clean(payload.get("EndBMSD")) or clean(payload.get("BJJZSJ"))
    lines = []
    if guarantee_amount:
        lines.append(
            (
                0,
                0,
                {
                    "type": "out",
                    "date": to_date(clean(payload.get("BZJJZSJ")) or clean(payload.get("f_DJRQ")) or str(record.document_date or "")),
                    "amount": guarantee_amount,
                    "remark": "历史投标保证金; source_table=P_ZTB_GCXXGL; legacy_record_id=%s; 保证金截止=%s"
                    % (record.legacy_record_id, clean(payload.get("BZJJZSJ"))),
                },
            )
        )
    return {
        "name": record.document_no or "P_ZTB-%s" % record.id,
        "tender_name": clean(payload.get("f_GCMC")) or record.project_name or record.document_no or "历史投标工程",
        "project_id": project_id,
        "owner_id": partner_by_name(partner_cache, owner_name),
        "legacy_owner_name": owner_name or "旧系统未填招标人/业主",
        "bid_amount": project_scale,
        "deadline": deadline[:19].replace("T", " ") if deadline else False,
        "open_date": open_time[:19].replace("T", " ") if open_time else False,
        "state": "submitted" if clean(payload.get("DJZT")) == "2" else "prepare",
        "legacy_fact_model": SOURCE_MODEL_PREFIX + "P_ZTB_GCXXGL",
        "legacy_fact_id": record.id,
        "legacy_fact_type": "project_tender_info",
        "legacy_note": "\n".join(
            [
                "旧系统工程信息/投标事实迁入。",
                "source_table=P_ZTB_GCXXGL",
                "legacy_record_id=%s" % clean(payload.get("ID")),
                "legacy_document_state=%s" % clean(payload.get("DJZT")),
                "legacy_project_id=%s" % clean(payload.get("XMID")),
                "legacy_project_name=%s" % (clean(payload.get("f_GCMC")) or record.project_name),
                "legacy_owner=%s" % owner_name,
                "legacy_BZJJE=%s" % clean(payload.get("BZJJE")),
                "legacy_ZGXJ=%s" % clean(payload.get("ZGXJ")),
                "legacy_XMGM=%s" % clean(payload.get("XMGM")),
                "legacy_bid_method=%s" % clean(payload.get("JSDWXZ")),
                "legacy_open_place=%s" % clean(payload.get("KBDD")),
                "legacy_creator=%s(%s)" % (user_name(payload), clean(payload.get("LRRID"))),
            ]
        ),
        "guarantee_ids": lines,
    }


def ws_zbht_values(record, payload: dict[str, object], project_id: int | bool, partner_cache: dict[str, int | bool]) -> dict[str, object]:
    owner_name = clean(payload.get("SGDW"))
    bid_amount = to_float(payload.get("ZBJE"))
    guarantee_amount = to_float(payload.get("BZJJE")) or to_float(payload.get("ZBJJE"))
    sign_date = clean(payload.get("QYRQ")) or str(record.document_date or "")
    lines = []
    if guarantee_amount:
        lines.append(
            (
                0,
                0,
                {
                    "type": "out",
                    "date": to_date(sign_date),
                    "amount": guarantee_amount,
                    "remark": "历史中标合同保证金; source_table=WS_HTGL_ZBHT; legacy_record_id=%s; 保证金比例=%s"
                    % (record.legacy_record_id, clean(payload.get("BZJBL"))),
                },
            )
        )
    return {
        "name": record.document_no or "WS-ZBHT-%s" % record.id,
        "tender_name": clean(payload.get("HTTM")) or clean(payload.get("WS_BDGL_BDXX_Name")) or record.project_name or "历史中标合同",
        "project_id": project_id,
        "owner_id": partner_by_name(partner_cache, owner_name),
        "legacy_owner_name": owner_name or "旧系统未填招标人/业主",
        "bid_amount": bid_amount,
        "deadline": False,
        "open_date": sign_date[:19].replace("T", " ") if sign_date else False,
        "state": "won",
        "legacy_fact_model": SOURCE_MODEL_PREFIX + "WS_HTGL_ZBHT",
        "legacy_fact_id": record.id,
        "legacy_fact_type": "winning_bid_contract",
        "legacy_note": "\n".join(
            [
                "旧系统中标合同事实迁入。",
                "source_table=WS_HTGL_ZBHT",
                "legacy_record_id=%s" % clean(payload.get("Id")),
                "legacy_contract_no=%s" % clean(payload.get("HTBH")),
                "legacy_contract_title=%s" % clean(payload.get("HTTM")),
                "legacy_project_id=%s" % clean(payload.get("XMID")),
                "legacy_project_name=%s" % record.project_name,
                "legacy_owner=%s" % owner_name,
                "legacy_ZBJE=%s" % clean(payload.get("ZBJE")),
                "legacy_BZJJE=%s" % clean(payload.get("BZJJE")),
                "legacy_ZBJJE=%s" % clean(payload.get("ZBJJE")),
                "legacy_bid_method=%s" % clean(payload.get("ZBFS")),
                "legacy_contract_type=%s" % clean(payload.get("WS_HTGL_HTLX_Name")),
                "legacy_attachment=%s" % clean(payload.get("FJ")),
                "legacy_creator=%s" % user_name(payload),
            ]
        ),
        "guarantee_ids": lines,
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_bid_tender_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_bid_tender_projection_residual_v1.csv"
    result_json = artifacts / "legacy_bid_tender_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Tender = env["tender.bid"].sudo().with_context(active_test=False)  # noqa: F821
    records = Residual.search([("source_table", "in", list(SOURCE_TABLES))], order="source_table, document_date, id")
    existing = Tender.search_read(
        [("legacy_fact_model", "in", [SOURCE_MODEL_PREFIX + table for table in SOURCE_TABLES])],
        ["legacy_fact_id"],
    )
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    partner_cache: dict[str, int | bool] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    planned = 0
    planned_amount = 0.0
    planned_guarantee_amount = 0.0
    created = 0
    skipped_existing = 0
    blocked = 0

    for record in records:
        payload = raw_json(record)
        project_id = project_by_fact(project_cache, record.project_legacy_id, record.project_name)
        reason = ""
        if not record.active:
            reason = "inactive_legacy_record"
        elif not project_id:
            reason = "missing_project_anchor"

        if record.id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
            values = {}
        elif reason:
            action = "blocked"
            blocked += 1
            values = {}
            residual_rows.append(
                {
                    "source_table": record.source_table,
                    "legacy_record_id": record.legacy_record_id,
                    "document_no": record.document_no,
                    "project_legacy_id": record.project_legacy_id,
                    "project_name": record.project_name,
                    "amount": record.amount_total,
                    "reason": reason,
                }
            )
        else:
            values = (
                p_ztb_values(record, payload, project_id, partner_cache)
                if record.source_table == "P_ZTB_GCXXGL"
                else ws_zbht_values(record, payload, project_id, partner_cache)
            )
            action = "create_tender_bid"
            planned += 1
            planned_amount += to_float(values.get("bid_amount"))
            planned_guarantee_amount += sum(command[2].get("amount") or 0 for command in values.get("guarantee_ids", []))
            if apply:
                tender = Tender.create(values)
                created += 1 if tender else 0

        plan_rows.append(
            {
                "source_table": record.source_table,
                "legacy_record_id": record.legacy_record_id,
                "legacy_fact_id": record.id,
                "document_no": record.document_no,
                "project_legacy_id": record.project_legacy_id,
                "project_name": record.project_name,
                "target_model": "tender.bid",
                "action": action,
                "reason": reason,
                "bid_amount": to_float(values.get("bid_amount")) if values else 0,
                "guarantee_amount": sum(command[2].get("amount") or 0 for command in values.get("guarantee_ids", [])) if values else 0,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fieldnames = [
        "source_table",
        "legacy_record_id",
        "legacy_fact_id",
        "document_no",
        "project_legacy_id",
        "project_name",
        "target_model",
        "action",
        "reason",
        "bid_amount",
        "guarantee_amount",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)
    write_csv(residual_csv, residual_rows, [key for key in fieldnames if key not in {"legacy_fact_id", "target_model", "action", "bid_amount", "guarantee_amount"}])
    result = {
        "status": "PASS",
        "mode": "legacy_bid_tender_projection",
        "apply": apply,
        "source_rows": len(records),
        "planned_rows": planned,
        "planned_bid_amount": round(planned_amount, 2),
        "planned_guarantee_amount": round(planned_guarantee_amount, 2),
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_rows": blocked,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_BID_TENDER_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
