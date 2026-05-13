# -*- coding: utf-8 -*-
"""Build a reviewed project-name reconciliation package.

Run through Odoo shell, for example:
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_contract_fact_alias_reconciliation.py

This script is intentionally read-only for business tables. It produces
machine-readable artifacts under artifacts/migration.
"""

import csv
import json
import os
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


REPO_ROOT = Path("/mnt/extra-addons")
if not REPO_ROOT.exists():
    REPO_ROOT = Path.cwd()

EXCEL_PATH = Path(os.getenv("PROJECT_POSITIVE_MIGRATION_EXCEL_PATH", "/mnt/tmp/001/672施工合同项目名称去重统计.xlsx"))
RAW_CONTRACT_CSV = Path(os.getenv("PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV", "/mnt/tmp/raw/contract/contract.csv"))
OUTPUT_DIR = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts" / "migration")))
OUTPUT_CSV = OUTPUT_DIR / "project_contract_fact_alias_reconciliation_v1.csv"
OUTPUT_JSON = OUTPUT_DIR / "project_contract_fact_alias_reconciliation_v1.json"
FALLBACK_OUTPUT_DIRS = (
    Path("/mnt/tmp") / "migration" / "project_contract_fact_alias_reconciliation",
    Path("/tmp") / "project_contract_fact_alias_reconciliation",
)

USER_KEEP_REVIEW = {
    "周超工程（德阳二重工程项目）": "用户确认该名称有大量业务事实，名称可能发生演变，保留复核",
}

USER_MANUAL_CANONICAL_PROJECT = {
    "周超工程（德阳二重工程项目）": {
        "name": "易静工程（德阳二重工程项目）",
        "reason": "用户确认需保留；追溯到当前 canonical 项目名称，且该项目存在大量合同、付款、收款事实",
    },
}

USER_DISCARD = {
    "2024年大邑县S216水晶(平武)-邛崃  K433+900-K434+300段道路水毁抢险救灾工程": "用户确认无实质性业务数据",
    "2026年春季乔木补植项目劳务分包合同": "用户确认无实质性业务数据",
    "旌兴·和悦雲岸1#-11#楼项目采购室外园林景观工程": "用户确认无实质性业务数据",
}

RAW_NAME_FIELDS = ("f_XMMC", "HTBT", "XMBM", "f_XMJC", "GCCBFW", "GCDZ")
FACT_MODELS = ("construction.contract", "sc.general.contract", "sc.payment.execution", "sc.receipt.income")
NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def clean(value):
    return str(value or "").strip()


def norm(value):
    text = re.sub(r"\s+", "", clean(value))
    return text.replace("（", "(").replace("）", ")").replace("，", ",").replace("。", ".")


def raw_visible(row):
    return (
        clean(row.get("DEL")) != "1"
        and clean(row.get("DJZT")) in {"2", "1", ""}
        and bool(clean(row.get("HTBT")))
        and bool(clean(row.get("FBF")))
    )


def read_excel_names(path):
    with ZipFile(path) as archive:
        shared = []
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for item in root.findall("a:si", NS):
            shared.append("".join(node.text or "" for node in item.findall(".//a:t", NS)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet = workbook.find("a:sheets/a:sheet", NS)
        sheet_ref = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        sheet_path = "xl/" + relmap[sheet_ref].lstrip("/")
        sheet_root = ET.fromstring(archive.read(sheet_path))

        names = []
        for row in sheet_root.findall(".//a:sheetData/a:row", NS):
            values = []
            for cell in row.findall("a:c", NS):
                value = cell.find("a:v", NS)
                text = "" if value is None else (value.text or "")
                if cell.attrib.get("t") == "s" and text:
                    text = shared[int(text)]
                values.append(text)
            if len(values) >= 2 and values[0].isdigit() and clean(values[1]):
                names.append(clean(values[1]))
        return names


def read_raw_contracts(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if raw_visible(row)]


def project_payload(project):
    if not project:
        return {"project_id": "", "canonical_project_name": "", "canonical_legacy_project_id": ""}
    return {
        "project_id": project.id,
        "canonical_project_name": clean(project.name),
        "canonical_legacy_project_id": clean(getattr(project, "legacy_project_id", "")),
    }


def fact_counts_for_project(project):
    if not project:
        return {model_name: 0 for model_name in FACT_MODELS}
    counts = {}
    for model_name in FACT_MODELS:
        model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        counts[model_name] = model.search_count([("project_id", "=", project.id)]) if "project_id" in model._fields else 0
    return counts


def main():
    excel_names = read_excel_names(EXCEL_PATH)
    excel_by_norm = {norm(name): name for name in excel_names}
    raw_rows = read_raw_contracts(RAW_CONTRACT_CSV)

    raw_by_name = {}
    for row in raw_rows:
        for field_name in RAW_NAME_FIELDS:
            value = norm(row.get(field_name))
            if value:
                raw_by_name.setdefault(value, []).append((field_name, row))

    project_model = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    contract_model = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    contract_groups = contract_model.read_group(
        [("project_id", "!=", False), ("legacy_contract_id", "!=", False), ("type", "=", "out")],
        ["project_id"],
        ["project_id"],
        lazy=False,
    )
    contract_project_ids = [int(group["project_id"][0]) for group in contract_groups if group.get("project_id")]
    contract_projects = project_model.browse(contract_project_ids).exists()
    db_contract_project_names = {
        norm(project.name)
        for project in contract_projects
        if clean(project.name) and clean(getattr(project, "operation_strategy", "")) != "direct"
    }

    missing_names = sorted(set(excel_by_norm) - db_contract_project_names)
    project_by_legacy = {
        clean(project.legacy_project_id): project
        for project in project_model.search([("legacy_project_id", "!=", False)])
    }
    contract_by_legacy = {
        clean(contract.legacy_contract_id): contract
        for contract in contract_model.search([("legacy_contract_id", "!=", False), ("type", "=", "out")])
    }

    rows = []
    for key in missing_names:
        source_name = excel_by_norm[key]
        source_name_key = norm(source_name)
        raw_matches = raw_by_name.get(source_name_key, [])
        raw_contract_ids = sorted({clean(row.get("Id")) for _field, row in raw_matches if clean(row.get("Id"))})
        raw_xmids = sorted({clean(row.get("XMID")) for _field, row in raw_matches if clean(row.get("XMID"))})
        raw_fields = sorted({field for field, _row in raw_matches})

        target_project = None
        target_contracts = []
        for contract_id in raw_contract_ids:
            contract = contract_by_legacy.get(contract_id)
            if contract:
                target_contracts.append(contract)
                if not target_project:
                    target_project = contract.project_id
        if not target_project:
            for xmid in raw_xmids:
                target_project = project_by_legacy.get(xmid)
                if target_project:
                    break

        same_name_project = project_model.search([("name", "=", source_name)], limit=1)
        same_name_counts = fact_counts_for_project(same_name_project)
        same_name_has_fact = any(same_name_counts.values())
        manual_target = USER_MANUAL_CANONICAL_PROJECT.get(source_name)
        manual_project = project_model.browse()
        if manual_target:
            manual_project = project_model.search([("name", "=", manual_target["name"])], limit=1)

        if target_project:
            decision = "alias_to_canonical_project"
            confidence = "high"
            review_state = "resolved"
            match_reason = "raw_visible_construction_contract_name_to_legacy_contract_or_xmid"
            project = target_project
            fact_counts = fact_counts_for_project(project)
        elif manual_project:
            decision = "manual_alias_to_canonical_project"
            confidence = "user_confirmed"
            review_state = "resolved"
            match_reason = manual_target["reason"]
            project = manual_project
            fact_counts = fact_counts_for_project(project)
        elif source_name in USER_KEEP_REVIEW:
            decision = "keep_for_manual_review"
            confidence = "manual_review"
            review_state = "review"
            match_reason = USER_KEEP_REVIEW[source_name]
            project = same_name_project
            fact_counts = same_name_counts
        elif source_name in USER_DISCARD:
            decision = "ignore_no_substantive_business_data"
            confidence = "user_confirmed"
            review_state = "ignored"
            match_reason = USER_DISCARD[source_name]
            project = same_name_project
            fact_counts = same_name_counts
        elif same_name_project and same_name_has_fact:
            decision = "project_fact_alias"
            confidence = "medium"
            review_state = "resolved"
            match_reason = "same_project_name_exists_with_runtime_project_facts_but_not_visible_out_contract_xmid"
            project = same_name_project
            fact_counts = same_name_counts
        else:
            decision = "review_required"
            confidence = "low"
            review_state = "review"
            match_reason = "no_raw_visible_contract_or_runtime_project_fact_anchor"
            project = same_name_project
            fact_counts = same_name_counts

        payload = project_payload(project)
        rows.append(
            {
                "source_name": source_name,
                "source_name_key": source_name_key,
                "decision": decision,
                "confidence": confidence,
                "review_state": review_state,
                "match_reason": match_reason,
                **payload,
                "raw_match_fields": ";".join(raw_fields),
                "raw_contract_ids": ";".join(raw_contract_ids),
                "raw_xmids": ";".join(raw_xmids),
                "target_contract_ids": ";".join(str(contract.id) for contract in target_contracts),
                "fact_counts_json": json.dumps(fact_counts, ensure_ascii=False, sort_keys=True),
            }
        )

    output_dir = OUTPUT_DIR
    output_csv = OUTPUT_CSV
    output_json = OUTPUT_JSON
    for candidate in (OUTPUT_DIR, *FALLBACK_OUTPUT_DIRS):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        output_dir = candidate
        output_csv = output_dir / OUTPUT_CSV.name
        output_json = output_dir / OUTPUT_JSON.name
        break
    else:
        raise RuntimeError("No writable output directory for project reconciliation artifacts")

    summary = {
        "database": env.cr.dbname,  # noqa: F821
        "excel_unique_names": len(set(excel_names)),
        "raw_visible_contract_rows": len(raw_rows),
        "db_legacy_out_non_direct_project_names": len(db_contract_project_names),
        "reconciliation_rows": len(rows),
        "decision_counts": {},
        "review_state_counts": {},
        "outputs": {"csv": str(output_csv), "json": str(output_json)},
        "repo_artifact_write_fallback": str(output_dir) != str(OUTPUT_DIR),
    }
    for row in rows:
        summary["decision_counts"][row["decision"]] = summary["decision_counts"].get(row["decision"], 0) + 1
        summary["review_state_counts"][row["review_state"]] = summary["review_state_counts"].get(row["review_state"], 0) + 1

    fieldnames = [
        "source_name",
        "source_name_key",
        "decision",
        "confidence",
        "review_state",
        "match_reason",
        "project_id",
        "canonical_project_name",
        "canonical_legacy_project_id",
        "raw_match_fields",
        "raw_contract_ids",
        "raw_xmids",
        "target_contract_ids",
        "fact_counts_json",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PROJECT_CONTRACT_FACT_ALIAS_RECONCILIATION=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


main()
