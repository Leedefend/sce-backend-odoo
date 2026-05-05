"""Export target partner candidates for SCBS partner mapping decisions."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fact_stats_by_partner_map() -> dict[int, dict[str, object]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    groups = Staging.read_group(
        [("partner_map_id", "!=", False), ("import_batch", "=", "scbs_fact_staging_v1")],
        ["partner_map_id", "amount_total:sum", "__count"],
        ["partner_map_id"],
        lazy=False,
    )
    stats: dict[int, dict[str, object]] = {}
    for row in groups:
        value = row.get("partner_map_id")
        if not value:
            continue
        stats[value[0]] = {
            "fact_rows": row.get("__count", 0),
            "fact_amount": round(float(row.get("amount_total", 0.0) or 0.0), 2),
        }
    return stats


def looks_like_non_counterparty_label(name: str) -> bool:
    normalized = (name or "").strip()
    if not normalized:
        return False
    keywords = ["工资", "库房", "食堂", "备用金", "押金", "保证金", "代付", "暂估", "内部"]
    return any(keyword in normalized for keyword in keywords)


def suggested_action(mapping) -> str:
    name = mapping.legacy_partner_name or ""
    if "测试" in name:
        return "ignore_or_conflict_test_value"
    if looks_like_non_counterparty_label(name):
        return "review_non_counterparty_label"
    if mapping.suggested_state == "tax_code_conflict":
        return "manual_partner_required"
    if mapping.match_method == "multiple":
        return "choose_target_partner"
    return "confirm_or_ignore_partner"


def partner_identity(partner) -> dict[str, object]:
    return {
        "candidate_partner_id": partner.id,
        "candidate_name": partner.display_name,
        "candidate_vat": partner.vat or "",
        "candidate_legacy_tax_no": getattr(partner, "legacy_tax_no", "") or "",
        "candidate_active": partner.active,
        "candidate_company": partner.company_id.display_name if partner.company_id else "",
        "candidate_is_company": getattr(partner, "is_company", False),
    }


def candidate_rows_for_mapping(mapping, fact_stat: dict[str, object]) -> list[dict[str, object]]:
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    name = (mapping.legacy_partner_name or "").strip()
    tax_code = (mapping.legacy_tax_code or "").strip()
    candidates: dict[int, dict[str, object]] = {}

    def add(partners, reason: str, rank: int, confidence: float) -> None:
        for partner in partners:
            row = candidates.setdefault(partner.id, partner_identity(partner))
            existing_rank = int(row.get("candidate_rank", 999))
            if rank < existing_rank:
                row.update({"match_reason": reason, "candidate_rank": rank, "confidence": confidence})
            else:
                row["match_reason"] = f"{row.get('match_reason', '')};{reason}".strip(";")

    if mapping.partner_id:
        add(mapping.partner_id, "current_mapping_target", 0, 1.0)
    if tax_code:
        add(Partner.search(["|", ("vat", "=", tax_code), ("legacy_tax_no", "=", tax_code)], limit=20), "tax_or_legacy_tax_exact", 1, 0.9)
    if name:
        add(Partner.search([("name", "=", name)], limit=20), "name_exact", 2, 0.7)
        if len(candidates) < 3:
            add(Partner.search([("name", "ilike", name)], limit=20), "name_ilike", 4, 0.35)

    rows = []
    for candidate in sorted(candidates.values(), key=lambda row: (int(row.get("candidate_rank", 999)), str(row.get("candidate_name", "")))):
        rows.append(
            {
                "map_id": mapping.id,
                "legacy_key": mapping.legacy_key,
                "legacy_partner_name": name,
                "legacy_tax_code": tax_code,
                "suggested_state": mapping.suggested_state,
                "mapping_state": mapping.mapping_state,
                "map_match_method": mapping.match_method,
                "suggested_action": suggested_action(mapping),
                "fact_rows": fact_stat.get("fact_rows", mapping.active_rows or mapping.legacy_rows or 0),
                "fact_amount": fact_stat.get("fact_amount", 0.0),
                "target_partner_count": mapping.target_partner_count,
                **candidate,
            }
        )
    if not rows:
        rows.append(
            {
                "map_id": mapping.id,
                "legacy_key": mapping.legacy_key,
                "legacy_partner_name": name,
                "legacy_tax_code": tax_code,
                "suggested_state": mapping.suggested_state,
                "mapping_state": mapping.mapping_state,
                "map_match_method": mapping.match_method,
                "suggested_action": suggested_action(mapping),
                "fact_rows": fact_stat.get("fact_rows", mapping.active_rows or mapping.legacy_rows or 0),
                "fact_amount": fact_stat.get("fact_amount", 0.0),
                "target_partner_count": mapping.target_partner_count,
                "candidate_rank": "",
                "match_reason": "no_target_candidate_found",
                "confidence": 0.0,
                "candidate_partner_id": "",
                "candidate_name": "",
                "candidate_vat": "",
                "candidate_legacy_tax_no": "",
                "candidate_active": "",
                "candidate_company": "",
                "candidate_is_company": "",
            }
        )
    return rows


def main() -> None:
    artifacts = artifact_root()
    result_json = artifacts / "scbs_partner_target_candidate_report_result_v1.json"
    report_csv = artifacts / "scbs_partner_target_candidate_report_v1.csv"
    Mapping = env["sc.legacy.partner.map"].sudo().with_context(active_test=False)  # noqa: F821
    fact_stats = fact_stats_by_partner_map()
    mappings = Mapping.search(
        [
            ("id", "in", list(fact_stats)),
            ("source_domain", "=", "SCBS"),
            ("mapping_state", "!=", "confirmed"),
        ]
    )

    rows: list[dict[str, object]] = []
    for mapping in mappings:
        action = suggested_action(mapping)
        if action not in {"manual_partner_required", "choose_target_partner", "review_non_counterparty_label", "confirm_or_ignore_partner"}:
            continue
        rows.extend(candidate_rows_for_mapping(mapping, fact_stats.get(mapping.id, {})))

    fieldnames = [
        "map_id",
        "legacy_key",
        "legacy_partner_name",
        "legacy_tax_code",
        "suggested_state",
        "mapping_state",
        "map_match_method",
        "suggested_action",
        "fact_rows",
        "fact_amount",
        "target_partner_count",
        "candidate_rank",
        "match_reason",
        "confidence",
        "candidate_partner_id",
        "candidate_name",
        "candidate_vat",
        "candidate_legacy_tax_no",
        "candidate_active",
        "candidate_company",
        "candidate_is_company",
    ]
    rows.sort(key=lambda row: (str(row["suggested_action"]), -float(row["fact_amount"] or 0.0), int(row["map_id"]), int(row["candidate_rank"] or 999)))
    write_csv(report_csv, fieldnames, rows)

    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        action = str(row["suggested_action"])
        bucket = summary.setdefault(action, {"candidate_rows": 0, "mapping_rows": 0, "with_candidate": 0, "fact_rows": 0, "fact_amount": 0.0})
        bucket["candidate_rows"] += 1
        if row.get("candidate_partner_id"):
            bucket["with_candidate"] += 1
    for action, bucket in summary.items():
        action_map_ids = {row["map_id"] for row in rows if row["suggested_action"] == action}
        bucket["mapping_rows"] = len(action_map_ids)
        bucket["fact_rows"] = sum(int(fact_stats.get(int(map_id), {}).get("fact_rows", 0) or 0) for map_id in action_map_ids)
        bucket["fact_amount"] = round(sum(float(fact_stats.get(int(map_id), {}).get("fact_amount", 0.0) or 0.0) for map_id in action_map_ids), 2)

    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "report_csv": str(report_csv),
        "candidate_rows": len(rows),
        "mapping_rows": len({row["map_id"] for row in rows}),
        "summary": summary,
    }
    write_json(result_json, payload)
    print("SCBS_PARTNER_TARGET_CANDIDATE_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
