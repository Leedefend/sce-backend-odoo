"""Create target partners from SCBS counterparty business facts.

Policy:

- SCBS partner labels used by facts are preserved as historical counterparty
  facts when no safe merge decision exists.
- Existing partners are not merged by fuzzy/multiple/tax-conflict signals.
- Created partners store the source identity in legacy fields; ``vat`` is not
  written to avoid polluting or colliding with formal partner tax identities.

Run through Odoo shell. Dry-run by default:

    odoo shell -c /path/to/odoo.conf -d DB < scripts/migration/scbs_partner_fact_bootstrap.py

Set ``SCBS_PARTNER_FACT_BOOTSTRAP_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from odoo import fields


BATCH = "scbs_partner_fact_bootstrap_v1"
SOURCE_DOMAIN = "SCBS"
ELIGIBLE_ACTIONS = {
    "confirm_or_ignore_partner",
    "choose_target_partner",
    "manual_partner_required",
    "review_non_counterparty_label",
    "ignore_or_conflict_test_value",
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


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


def looks_company(name: str) -> bool:
    markers = ("公司", "集团", "厂", "经营部", "商行", "中心", "合作社", "分公司", "项目部")
    return any(marker in (name or "") for marker in markers)


def partner_business_key(rec) -> str:
    return f"SCBS:{rec.source_table}:{rec.legacy_key}"


def partner_values(rec, action: str, fact_rows: int, fact_amount: float) -> dict[str, object]:
    values = {
        "name": rec.legacy_partner_name,
        "company_id": rec.company_id.id,
        "supplier_rank": 1,
        "customer_rank": 0,
        "is_company": looks_company(rec.legacy_partner_name),
        "comment": "\n".join(
            [
                "SCBS历史往来事实承接。",
                f"source_domain={SOURCE_DOMAIN}",
                f"source_table={rec.source_table}",
                f"legacy_key={rec.legacy_key}",
                f"legacy_partner_name={rec.legacy_partner_name}",
                f"legacy_tax_code={rec.legacy_tax_code or ''}",
                f"suggested_state={rec.suggested_state}",
                f"match_method={rec.match_method}",
                f"suggested_action={action}",
                f"fact_rows={fact_rows}",
                f"fact_amount={fact_amount}",
                f"batch={BATCH}",
            ]
        ),
    }
    if "legacy_partner_source" in rec.env["res.partner"]._fields:
        values["legacy_partner_source"] = partner_business_key(rec)
    if "legacy_partner_name" in rec.env["res.partner"]._fields:
        values["legacy_partner_name"] = rec.legacy_partner_name
    if "legacy_tax_no" in rec.env["res.partner"]._fields:
        values["legacy_tax_no"] = rec.legacy_tax_code or ""
    if "legacy_credit_code" in rec.env["res.partner"]._fields:
        values["legacy_credit_code"] = rec.legacy_tax_code or ""
    if "legacy_source_evidence" in rec.env["res.partner"]._fields:
        values["legacy_source_evidence"] = values["comment"]
    return values


def fact_stats_by_partner_map() -> dict[int, dict[str, object]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)
    groups = Staging.read_group(
        [("partner_map_id", "!=", False), ("import_batch", "=", "scbs_fact_staging_v1")],
        ["partner_map_id", "amount_total:sum", "__count"],
        ["partner_map_id"],
        lazy=False,
    )
    result: dict[int, dict[str, object]] = {}
    for row in groups:
        value = row.get("partner_map_id")
        if value:
            result[value[0]] = {
                "fact_rows": int(row.get("__count") or 0),
                "fact_amount": round(float(row.get("amount_total") or 0.0), 2),
            }
    return result


def suggested_action(rec) -> str:
    if rec.mapping_state == "confirmed":
        return "noop"
    if "测试" in (rec.legacy_partner_name or ""):
        return "ignore_or_conflict_test_value"
    if rec.suggested_state == "tax_code_conflict":
        return "manual_partner_required"
    if rec.match_method == "multiple":
        return "choose_target_partner"
    labels = ["工资", "库房", "食堂", "备用金", "押金", "保证金", "代付", "暂估", "内部"]
    if any(label in (rec.legacy_partner_name or "") for label in labels):
        return "review_non_counterparty_label"
    return "confirm_or_ignore_partner"


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_PARTNER_FACT_BOOTSTRAP_APPLY") == "1"
    plan_csv = artifacts / "scbs_partner_fact_bootstrap_plan_v1.csv"
    rollback_csv = artifacts / "scbs_partner_fact_bootstrap_rollback_targets_v1.csv"
    result_json = artifacts / "scbs_partner_fact_bootstrap_result_v1.json"

    PartnerMap = env["sc.legacy.partner.map"].sudo().with_context(active_test=False)
    Partner = env["res.partner"].sudo().with_context(active_test=False)
    stats = fact_stats_by_partner_map()

    maps = PartnerMap.search(
        [
            ("source_domain", "=", SOURCE_DOMAIN),
            ("mapping_state", "in", ["candidate", "conflict"]),
            ("partner_id", "=", False),
        ],
        order="legacy_rows desc, legacy_partner_name",
    )

    plan_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created = 0
    linked_existing = 0
    skipped_no_fact = 0
    skipped_no_name = 0

    for rec in maps:
        stat = stats.get(rec.id)
        if not stat:
            skipped_no_fact += 1
            continue
        if not rec.legacy_partner_name:
            skipped_no_name += 1
            continue
        action = suggested_action(rec)
        if action not in ELIGIBLE_ACTIONS:
            continue
        business_key = partner_business_key(rec)
        target = Partner.search([("legacy_partner_source", "=", business_key)], limit=1) if "legacy_partner_source" in Partner._fields else False
        proposal = "link_existing_by_business_key" if target else "create_partner_from_scbs_fact"
        fact_rows = int(stat["fact_rows"])
        fact_amount = float(stat["fact_amount"])

        plan_rows.append(
            {
                "map_id": rec.id,
                "legacy_key": rec.legacy_key,
                "legacy_partner_name": rec.legacy_partner_name,
                "legacy_tax_code": rec.legacy_tax_code,
                "mapping_state": rec.mapping_state,
                "suggested_state": rec.suggested_state,
                "match_method": rec.match_method,
                "suggested_action": action,
                "fact_rows": fact_rows,
                "fact_amount": fact_amount,
                "company": rec.company_id.display_name,
                "proposal": proposal,
                "target_partner_id": target.id if target else "",
                "target_partner_name": target.display_name if target else "",
            }
        )

        if not apply:
            continue

        if not target:
            target = Partner.create(partner_values(rec, action, fact_rows, fact_amount))
            created += 1
            rollback_rows.append(
                {
                    "partner_id": target.id,
                    "name": target.name,
                    "company": target.company_id.display_name,
                    "legacy_partner_source": getattr(target, "legacy_partner_source", ""),
                }
            )
        else:
            linked_existing += 1

        rec.write(
            {
                "partner_id": target.id,
                "mapping_state": "confirmed",
                "match_method": "manual",
                "reviewer_id": env.user.id,
                "reviewed_at": fields.Datetime.now(),
                "note": ((rec.note or "") + f"\n{BATCH}: {proposal}").strip(),
            }
        )

    result = {
        "mode": "apply" if apply else "dry_run",
        "planned_rows": len(plan_rows),
        "created_partners": created,
        "linked_existing_by_business_key": linked_existing,
        "skipped_no_fact": skipped_no_fact,
        "skipped_no_name": skipped_no_name,
        "remaining_candidate_partner_maps": PartnerMap.search_count([("source_domain", "=", SOURCE_DOMAIN), ("mapping_state", "=", "candidate")]),
        "remaining_conflict_partner_maps": PartnerMap.search_count([("source_domain", "=", SOURCE_DOMAIN), ("mapping_state", "=", "conflict")]),
        "plan_csv": str(plan_csv),
        "rollback_csv": str(rollback_csv),
        "result_json": str(result_json),
    }
    write_csv(
        plan_csv,
        plan_rows,
        [
            "map_id",
            "legacy_key",
            "legacy_partner_name",
            "legacy_tax_code",
            "mapping_state",
            "suggested_state",
            "match_method",
            "suggested_action",
            "fact_rows",
            "fact_amount",
            "company",
            "proposal",
            "target_partner_id",
            "target_partner_name",
        ],
    )
    write_csv(
        rollback_csv,
        rollback_rows,
        ["partner_id", "name", "company", "legacy_partner_source"],
    )
    write_json(result_json, result)

    if apply:
        env.cr.commit()

    print("SCBS_PARTNER_FACT_BOOTSTRAP=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
