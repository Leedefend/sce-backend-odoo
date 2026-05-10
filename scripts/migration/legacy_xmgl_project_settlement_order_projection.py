"""Project legacy XMGL project settlement applications into sc.settlement.order.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "legacy.main.XMGL_HTGL_XMJSSQ"
SOURCE_TABLE = "XMGL_HTGL_XMJSSQ"


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


def project_by_legacy_id(cache: dict[str, int | bool], legacy_id: str, name: str):
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


def customer_by_name(cache: dict[str, int | bool], name: str):
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


def user_by_legacy_or_name(cache: dict[str, int | bool], legacy_id: str, name: str):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    user = False
    if clean(legacy_id):
        profile = env["sc.legacy.user.profile"].sudo().search([("legacy_user_id", "=", clean(legacy_id))], limit=1)  # noqa: F821
        if profile and profile.user_id:
            user = profile.user_id
    if not user and clean(name):
        user = Users.search([("name", "=", clean(name))], limit=1)
    cache[key] = user.id if user else False
    return cache[key]


def settlement_stage(value: str) -> str:
    value = clean(value)
    return {
        "一审": "first_review",
        "二审": "second_review",
        "定案": "final",
        "终审": "final",
    }.get(value, "declared")


def state_from_legacy(value) -> str:
    value = clean(value)
    if value == "-1":
        return "cancel"
    if value == "2":
        return "approve"
    return "draft"


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_xmgl_project_settlement_order_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_xmgl_project_settlement_order_projection_residual_v1.csv"
    result_json = artifacts / "legacy_xmgl_project_settlement_order_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.settlement.order"].sudo().with_context(  # noqa: F821
        active_test=False,
        legacy_migration_allow_missing_contract=True,
    )
    records = Residual.search([("source_table", "=", SOURCE_TABLE)], order="document_date, id")
    existing = Settlement.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    customer_cache: dict[str, int | bool] = {}
    user_cache: dict[str, int | bool] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    planned = 0
    planned_amount = 0.0
    created = 0
    skipped_existing = 0
    blocked = 0

    for record in records:
        payload = raw_json(record)
        legacy_id = clean(payload.get("Id")) or record.legacy_record_id.split("#", 1)[0]
        project_id = project_by_legacy_id(project_cache, record.project_legacy_id, record.project_name)
        counterparty_name = clean(payload.get("JFDW"))
        approved_amount = to_float(payload.get("JSJE"))
        settlement_date = to_date(clean(payload.get("JSRQ")) or str(record.document_date or ""))
        reason = ""
        if not record.active:
            reason = "inactive_legacy_record"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not counterparty_name:
            reason = "missing_counterparty_name"
        elif approved_amount <= 0:
            reason = "non_positive_approved_amount"
        elif not settlement_date:
            reason = "missing_settlement_date"

        if record.id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif reason:
            action = "blocked"
            blocked += 1
            residual_rows.append(
                {
                    "legacy_record_id": record.legacy_record_id,
                    "document_no": record.document_no,
                    "project_legacy_id": record.project_legacy_id,
                    "project_name": record.project_name,
                    "counterparty_name": counterparty_name,
                    "approved_amount": approved_amount,
                    "reason": reason,
                }
            )
        else:
            action = "create_settlement_order"
            planned += 1
            planned_amount += approved_amount
            if apply:
                customer_id = customer_by_name(customer_cache, counterparty_name)
                entry_user_id = user_by_legacy_or_name(user_cache, payload.get("LRRID"), payload.get("LRR"))
                settlement = Settlement.create(
                    {
                        "name": record.document_no or "XMGL项目结算-%s" % legacy_id,
                        "project_id": project_id,
                        "partner_id": customer_id,
                        "settlement_unit_id": customer_id,
                        "title": clean(payload.get("BT")) or record.document_no or "历史项目结算申请",
                        "document_date": settlement_date,
                        "settlement_type": "in",
                        "settlement_stage": settlement_stage(payload.get("JSJD")),
                        "date_settlement": settlement_date,
                        "approved_date": settlement_date,
                        "approved_amount": approved_amount,
                        "state": state_from_legacy(payload.get("DJZT")),
                        "entry_user_id": entry_user_id or env.user.id,  # noqa: F821
                        "entry_data": "legacy:%s:%s" % (SOURCE_TABLE, legacy_id),
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": record.id,
                        "legacy_fact_type": "project_settlement_application",
                        "settlement_description": clean(payload.get("JSSM")),
                        "note": "\n".join(
                            [
                                "旧系统项目结算申请单迁入。",
                                "source_table=%s" % SOURCE_TABLE,
                                "legacy_record_id=%s" % legacy_id,
                                "legacy_document_state=%s" % clean(payload.get("DJZT")),
                                "legacy_project_id=%s" % clean(payload.get("XMID")),
                                "legacy_counterparty=%s" % counterparty_name,
                                "legacy_contract_id=%s" % clean(payload.get("ZBHTID")),
                                "legacy_contract_no=%s" % clean(payload.get("ZBHTBH")),
                                "legacy_stage=%s" % clean(payload.get("JSJD")),
                                "legacy_HTZE=%s" % clean(payload.get("HTZE")),
                                "legacy_YSKJE=%s" % clean(payload.get("YSKJE")),
                                "legacy_JSJE=%s" % clean(payload.get("JSJE")),
                                "legacy_HTJE=%s" % clean(payload.get("HTJE")),
                                "legacy_attachment=%s" % clean(payload.get("FJ")),
                                "legacy_creator=%s(%s)" % (clean(payload.get("LRR")), clean(payload.get("LRRID"))),
                            ]
                        ),
                        "line_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": "历史项目结算审定金额",
                                    "qty": 1.0,
                                    "price_unit": approved_amount,
                                    "contract_id": False,
                                },
                            )
                        ],
                    }
                )
                created += 1 if settlement else 0

        plan_rows.append(
            {
                "legacy_record_id": record.legacy_record_id,
                "legacy_fact_id": record.id,
                "document_no": record.document_no,
                "project_legacy_id": record.project_legacy_id,
                "project_name": record.project_name,
                "counterparty_name": counterparty_name,
                "approved_amount": approved_amount,
                "target_model": "sc.settlement.order",
                "action": action,
                "reason": reason,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fieldnames = [
        "legacy_record_id",
        "legacy_fact_id",
        "document_no",
        "project_legacy_id",
        "project_name",
        "counterparty_name",
        "approved_amount",
        "target_model",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)
    write_csv(residual_csv, residual_rows, [key for key in fieldnames if key not in {"legacy_fact_id", "target_model", "action"}])
    result = {
        "status": "PASS",
        "mode": "legacy_xmgl_project_settlement_order_projection",
        "apply": apply,
        "source_rows": len(records),
        "planned_rows": planned,
        "planned_amount": round(planned_amount, 2),
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_rows": blocked,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_XMGL_PROJECT_SETTLEMENT_ORDER_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
