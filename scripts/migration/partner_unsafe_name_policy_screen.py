#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining_unsafe_name_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_unsafe_name_policy_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_unsafe_name_policy_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_unsafe_name_policy_screen_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 1111

ENTERPRISE_MARKERS = (
    "公司", "集团", "厂", "店", "合作社", "经营部", "门市", "商行", "超市",
    "酒店", "宾馆", "餐厅", "饭店", "银行", "建材", "工程", "运输",
)
PUBLIC_ORG_MARKERS = ("政府", "委员会", "局", "医院", "学校", "院", "所", "中心", "站")
GENERIC_INVALID_NAMES = {"公司", "劳务", "租赁", "租租赁", "单位", "个人", "客户", "供应商"}
GARBAGE_MARKERS = (
    "报销", "业务费", "交通费", "住宿费", "餐饮", "发票", "定额", "工资", "油票",
    "加油票", "材料票", "材料款", "差旅", "项目员工", "员工", "零星", "请选择",
    "测试", "费用", "水电费", "办公费", "招待费", "票",
)
WRAPPER_CHARS = " \t\r\n【】[]（）(){}<>《》“”\"'`·、，,。.;；:："


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def normalize_name(value: object) -> str:
    text = clean(value).strip(WRAPPER_CHARS)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[（(](供应商|客户|材料|租赁|装载机|挖掘机|塔机)[）)]$", "", text)
    text = re.sub(r"[\-—_]+$", "", text)
    return text.strip(WRAPPER_CHARS)


def has_enterprise_marker(name: str) -> bool:
    return any(marker in name for marker in ENTERPRISE_MARKERS)


def has_public_org_marker(name: str) -> bool:
    return any(marker in name for marker in PUBLIC_ORG_MARKERS)


def has_garbage_marker(name: str) -> bool:
    return any(marker in name for marker in GARBAGE_MARKERS)


def likely_person_name(name: str) -> bool:
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,3}", name)) and not has_enterprise_marker(name)


def classify(original_name: str) -> tuple[str, str, str]:
    normalized = normalize_name(original_name)
    if not normalized or re.fullmatch(r"\d+", normalized):
        return ("discard_non_enterprise_garbage", normalized, "blank_or_numeric")
    if normalized in GENERIC_INVALID_NAMES:
        return ("discard_non_enterprise_garbage", normalized, "generic_non_entity_name")
    if has_garbage_marker(normalized):
        return ("discard_non_enterprise_garbage", normalized, "expense_or_invoice_marker")
    if likely_person_name(normalized):
        return ("discard_non_enterprise_garbage", normalized, "likely_person_name")
    if has_public_org_marker(normalized):
        return ("manual_review_public_org", normalized, "public_org_not_enterprise")
    if has_enterprise_marker(normalized) and normalized != clean(original_name):
        return ("auto_normalize_enterprise_candidate", normalized, "enterprise_marker_with_normalization")
    if has_enterprise_marker(normalized):
        return ("enterprise_candidate_as_is", normalized, "enterprise_marker")
    return ("manual_review_uncertain_name", normalized, "no_enterprise_marker")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {"row_no", "subroute", "blockers", "legacy_partner_source", "legacy_partner_id", "partner_name", "tax_number", "sources", "source_row_count"}
    missing_columns = sorted(required_columns - set(columns))
    policy_rows = []
    decision_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        decision, normalized, reason = classify(clean(row.get("partner_name")))
        decision_counts[decision] += 1
        reason_counts[reason] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "policy_decision": decision,
            "policy_reason": reason,
            "normalized_partner_name": normalized,
            "original_partner_name": clean(row.get("partner_name")),
            "subroute": clean(row.get("subroute")),
            "blockers": clean(row.get("blockers")),
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "recommended_next_task": decision,
        }
        policy_rows.append(output_row)
        if len(samples[decision]) < 20:
            samples[decision].append(output_row)

    fieldnames = [
        "row_no", "policy_decision", "policy_reason", "normalized_partner_name",
        "original_partner_name", "subroute", "blockers", "legacy_partner_source",
        "legacy_partner_id", "tax_number", "sources", "source_row_count",
        "recommended_next_task",
    ]
    write_csv(OUTPUT_CSV, fieldnames, policy_rows)
    write_csv(SAMPLE_CSV, fieldnames, [sample for decision in sorted(samples) for sample in samples[decision]])
    result = {
        "status": "PASS" if not missing_columns and len(policy_rows) == EXPECTED_ROUTE_ROWS else "FAIL",
        "mode": "partner_l4_unsafe_name_policy_screen",
        "input": str(INPUT_CSV),
        "policy": {
            "normalize_fixable_enterprise_names": True,
            "discard_non_enterprise_garbage": True,
            "tax_number_can_remain_blank": True,
        },
        "route_rows": len(policy_rows),
        "missing_columns": missing_columns,
        "decision_counts": dict(sorted(decision_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "outputs": {"policy_rows": str(OUTPUT_CSV), "sample_rows": str(SAMPLE_CSV)},
        "next_gate": "Only enterprise_candidate_as_is and auto_normalize_enterprise_candidate may enter no-DB write design; discard rows require no DB write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_UNSAFE_NAME_POLICY_SCREEN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "decision_counts": result["decision_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
