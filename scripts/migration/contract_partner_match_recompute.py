#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
PARTNER_BASELINE_JSON = Path("artifacts/migration/contract_partner_baseline_v1.json")
PROJECT_SAMPLE_30_CSV = Path("data/migration_samples/project_sample_v1.csv")
PROJECT_SAMPLE_100_CSV = Path("artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/contract_partner_match_recompute_v1.json")

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限公司", "有限责任公司", "股份有限公司", "集团有限公司", "公司")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = clean_text(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def written_project_ids() -> set[str]:
    ids: set[str] = set()
    for path in (PROJECT_SAMPLE_30_CSV, PROJECT_SAMPLE_100_CSV):
        if not path.exists():
            continue
        for row in read_csv(path):
            value = clean_text(row.get("legacy_project_id"))
            if value:
                ids.add(value)
    return ids


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean_text(row.get("FBF"))
    cbf = clean_text(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def partner_index():
    data = json.loads(PARTNER_BASELINE_JSON.read_text(encoding="utf-8"))
    partners = data.get("partners") or []
    exact = {}
    normalized = {}
    for partner in partners:
        for key in (partner.get("display_name"), partner.get("name")):
            name = clean_text(key)
            if not name:
                continue
            exact.setdefault(name, []).append(partner)
            n = norm_name(name)
            if n:
                normalized.setdefault(n, []).append(partner)
    return partners, exact, normalized


def fuzzy_candidates(name: str, partners: list[dict[str, object]]) -> list[dict[str, object]]:
    needle = norm_name(name)
    scored = []
    if not needle:
        return []
    for partner in partners:
        p_name = clean_text(partner.get("display_name") or partner.get("name"))
        p_norm = norm_name(p_name)
        if not p_norm:
            continue
        score = SequenceMatcher(None, needle, p_norm).ratio()
        if needle in p_norm or p_norm in needle:
            score = max(score, 0.92)
        if score >= 0.82:
            scored.append({"id": partner.get("id"), "display_name": p_name, "confidence": round(score, 4)})
    return sorted(scored, key=lambda row: (-row["confidence"], str(row["display_name"])))[:5]


def main() -> int:
    rows = read_csv(CONTRACT_CSV)
    project_ids = written_project_ids()
    partners, exact, normalized = partner_index()
    counterparty_counts: Counter[str] = Counter()
    match_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    sample_matches = []
    safe_candidates = 0
    project_scope_counts: Counter[str] = Counter()
    deleted_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()

    for row in rows:
        direction, counterparty = infer_direction(row)
        direction_counts[direction] += 1
        if counterparty:
            counterparty_counts[counterparty] += 1
        exact_matches = exact.get(counterparty, []) if counterparty else []
        norm_matches = normalized.get(norm_name(counterparty), []) if counterparty else []
        fuzzy = [] if exact_matches or norm_matches else fuzzy_candidates(counterparty, partners)
        match_type = "exact" if exact_matches else "normalized" if norm_matches else "fuzzy_candidate" if fuzzy else "defer"
        match_counts[match_type] += 1

        xmid = clean_text(row.get("XMID"))
        deleted = clean_text(row.get("DEL")) == "1"
        subject = clean_text(row.get("HTBT")) or clean_text(row.get("DJBH")) or clean_text(row.get("HTBH"))
        partner_ok = len(exact_matches) == 1 or len(norm_matches) == 1
        project_in_scope = xmid in project_ids
        direction_ok = direction in {"out", "in"}
        subject_ok = bool(subject)
        project_scope_counts["written_project_match" if project_in_scope else "project_not_written_scope"] += 1
        deleted_counts["deleted" if deleted else "active_or_blank"] += 1
        if not project_in_scope:
            blocker_counts["project_not_written_scope"] += 1
        if not direction_ok:
            blocker_counts["direction_defer"] += 1
        if not partner_ok:
            blocker_counts["partner_unresolved"] += 1
        if not subject_ok:
            blocker_counts["missing_subject"] += 1
        if deleted:
            blocker_counts["deleted_flag"] += 1
        if project_in_scope and direction_ok and partner_ok and subject_ok and not deleted:
            safe_candidates += 1

        if len(sample_matches) < 80 and counterparty:
            candidates = exact_matches or norm_matches or fuzzy
            sample_matches.append(
                {
                    "counterparty_text": counterparty,
                    "row_count_for_text": counterparty_counts[counterparty],
                    "match_type": match_type,
                    "candidates": [
                        {
                            "id": item.get("id"),
                            "display_name": item.get("display_name") or item.get("name"),
                            "confidence": item.get("confidence", 1.0),
                        }
                        for item in candidates[:3]
                    ],
                }
            )

    distinct_counterparties = len(counterparty_counts)
    result = {
        "status": "PASS",
        "mode": "contract_partner_match_recompute_no_db_write",
        "row_count": len(rows),
        "partner_baseline_count": len(partners),
        "direction_counts": dict(sorted(direction_counts.items())),
        "counterparty": {
            "distinct_count": distinct_counterparties,
            "top_unmatched_texts": [
                {"text": text, "rows": count}
                for text, count in counterparty_counts.most_common(30)
            ],
        },
        "match_counts": dict(sorted(match_counts.items())),
        "project_scope_counts": dict(sorted(project_scope_counts.items())),
        "deleted_counts": dict(sorted(deleted_counts.items())),
        "safe_candidate_blockers": dict(sorted(blocker_counts.items())),
        "safe_candidate_recompute": {
            "candidate_rows": safe_candidates,
            "decision": "NO-GO for contract write" if safe_candidates == 0 else "candidate review required",
        },
        "sample_matches": sample_matches,
        "next_step": "partner master-data preparation is required before contract write",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "CONTRACT_PARTNER_MATCH_RECOMPUTE="
        + json.dumps(
            {
                "status": result["status"],
                "rows": result["row_count"],
                "distinct_counterparties": distinct_counterparties,
                "match_counts": result["match_counts"],
                "safe_candidates": safe_candidates,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
