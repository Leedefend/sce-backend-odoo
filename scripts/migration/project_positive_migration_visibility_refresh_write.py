# -*- coding: utf-8 -*-
"""Apply the positive project migration visibility decision to a dev database.

Run through Odoo shell, for example:
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
  make odoo.shell.exec < scripts/migration/project_positive_migration_visibility_refresh_write.py

This script only changes project.project.active. It does not delete projects or
rewrite business facts.
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
OUTPUT_CSV = OUTPUT_DIR / "project_positive_migration_visibility_refresh_v1.csv"
OUTPUT_JSON = OUTPUT_DIR / "project_positive_migration_visibility_refresh_v1.json"
FALLBACK_OUTPUT_DIRS = (
    Path("/mnt/tmp") / "migration" / "project_positive_migration_visibility_refresh",
    Path("/tmp") / "project_positive_migration_visibility_refresh",
)

USER_KEEP_REVIEW = {
    "周超工程（德阳二重工程项目）": "用户确认该名称有大量业务事实，名称可能发生演变，保留为肯定式迁移项目",
}

USER_MANUAL_CANONICAL_PROJECT = {
    "周超工程（德阳二重工程项目）": {
        "name": "易静工程（德阳二重工程项目）",
        "reason": "positive_user_confirmed_manual_alias_to_canonical_project",
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


def guard_database():
    dbname = env.cr.dbname  # noqa: F821
    allowlist = {item.strip() for item in os.environ.get("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
    if dbname not in allowlist:
        raise RuntimeError(
            "Refusing to write project visibility: database %r is not in MIGRATION_REPLAY_DB_ALLOWLIST=%r"
            % (dbname, sorted(allowlist))
        )
    return dbname


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


def fact_counts_for_project(project):
    counts = {}
    for model_name in FACT_MODELS:
        model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        counts[model_name] = model.search_count([("project_id", "=", project.id)]) if "project_id" in model._fields else 0
    return counts


def find_same_name_project(project_model, source_name):
    exact = project_model.search([("name", "=", source_name)], limit=1)
    if exact:
        return exact
    source_key = norm(source_name)
    for project in project_model.search([("name", "!=", False)]):
        if norm(project.name) == source_key:
            return project
    return project_model.browse()


def output_paths():
    for output_dir in (OUTPUT_DIR, *FALLBACK_OUTPUT_DIRS):
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        return output_dir, output_dir / OUTPUT_CSV.name, output_dir / OUTPUT_JSON.name
    raise RuntimeError("No writable output directory for project visibility refresh artifacts")


def main():
    dbname = guard_database()
    project_model = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    contract_model = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821

    excel_names = read_excel_names(EXCEL_PATH)
    excel_unique = {norm(name): name for name in excel_names}
    discard_keys = {norm(name) for name in USER_DISCARD}
    positive_keys = set(excel_unique) - discard_keys
    raw_rows = read_raw_contracts(RAW_CONTRACT_CSV)

    raw_by_name = {}
    for row in raw_rows:
        for field_name in RAW_NAME_FIELDS:
            value = norm(row.get(field_name))
            if value:
                raw_by_name.setdefault(value, []).append((field_name, row))

    project_by_legacy = {
        clean(project.legacy_project_id): project
        for project in project_model.search([("legacy_project_id", "!=", False)])
    }
    contract_by_legacy = {
        clean(contract.legacy_contract_id): contract
        for contract in contract_model.search([("legacy_contract_id", "!=", False), ("type", "=", "out")])
    }

    contract_projects = contract_model.search(
        [("project_id", "!=", False), ("legacy_contract_id", "!=", False), ("type", "=", "out")]
    ).mapped("project_id")

    keep_map = {}
    resolved_positive_keys = set()

    def keep(project, reason, source_name="", source_key=""):
        if not project:
            return
        if source_key:
            resolved_positive_keys.add(source_key)
        keep_map[project.id] = {
            "project_id": project.id,
            "project_name": clean(project.name),
            "legacy_project_id": clean(getattr(project, "legacy_project_id", "")),
            "operation_strategy": clean(getattr(project, "operation_strategy", "")),
            "reason": reason,
            "source_name": source_name,
            "fact_counts_json": json.dumps(fact_counts_for_project(project), ensure_ascii=False, sort_keys=True),
        }

    direct_projects = project_model.search([("operation_strategy", "=", "direct")])
    for project in direct_projects:
        keep(project, "direct_project_exemption")

    for project in contract_projects:
        project_key = norm(project.name)
        if project_key in positive_keys:
            keep(
                project,
                "positive_excel_name_matches_current_out_contract_project",
                excel_unique[project_key],
                project_key,
            )

    for source_key in sorted(positive_keys):
        source_name = excel_unique[source_key]
        raw_matches = raw_by_name.get(source_key, [])
        raw_contract_ids = sorted({clean(row.get("Id")) for _field, row in raw_matches if clean(row.get("Id"))})
        raw_xmids = sorted({clean(row.get("XMID")) for _field, row in raw_matches if clean(row.get("XMID"))})

        target_project = project_model.browse()
        for contract_id in raw_contract_ids:
            contract = contract_by_legacy.get(contract_id)
            if contract and contract.project_id:
                target_project = contract.project_id
                break
        if not target_project:
            for xmid in raw_xmids:
                target_project = project_by_legacy.get(xmid) or project_model.browse()
                if target_project:
                    break
        if target_project:
            keep(target_project, "positive_raw_contract_alias_to_canonical_project", source_name, source_key)
            continue

        manual_target = USER_MANUAL_CANONICAL_PROJECT.get(source_name)
        if manual_target:
            manual_project = project_model.search([("name", "=", manual_target["name"])], limit=1)
            if manual_project and any(fact_counts_for_project(manual_project).values()):
                keep(manual_project, manual_target["reason"], source_name, source_key)
                continue

        same_name_project = find_same_name_project(project_model, source_name)
        if same_name_project:
            same_name_counts = fact_counts_for_project(same_name_project)
            if any(same_name_counts.values()) or source_name in USER_KEEP_REVIEW:
                keep(same_name_project, "positive_project_fact_alias_or_user_keep_review", source_name, source_key)

    unresolved_positive_keys = sorted(positive_keys - resolved_positive_keys)
    if unresolved_positive_keys:
        unresolved_names = [excel_unique[key] for key in unresolved_positive_keys[:20]]
        raise RuntimeError(
            "Refusing to archive projects: %s positive project names were not resolved to project anchors. "
            "First unresolved names: %s" % (len(unresolved_positive_keys), unresolved_names)
        )

    keep_ids = set(keep_map)
    all_projects = project_model.search([])
    archive_projects = all_projects.filtered(lambda project: project.id not in keep_ids)
    activate_projects = project_model.browse(sorted(keep_ids)).filtered(lambda project: not project.active)
    already_active_kept = project_model.browse(sorted(keep_ids)).filtered(lambda project: project.active)

    if archive_projects:
        archive_projects.write({"active": False})
    if activate_projects:
        activate_projects.write({"active": True})

    output_dir, output_csv, output_json = output_paths()
    rows = list(keep_map.values())
    rows.extend(
        {
            "project_id": project.id,
            "project_name": clean(project.name),
            "legacy_project_id": clean(getattr(project, "legacy_project_id", "")),
            "operation_strategy": clean(getattr(project, "operation_strategy", "")),
            "reason": "archived_not_in_positive_migration_or_direct_exemption",
            "source_name": "",
            "fact_counts_json": json.dumps(fact_counts_for_project(project), ensure_ascii=False, sort_keys=True),
        }
        for project in archive_projects
    )
    rows.sort(key=lambda row: (row["reason"], row["project_name"], row["project_id"]))

    fieldnames = [
        "project_id",
        "project_name",
        "legacy_project_id",
        "operation_strategy",
        "reason",
        "source_name",
        "fact_counts_json",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    active_ids_after = set(project_model.search([("active", "=", True)]).ids)
    inactive_ids_after = set(project_model.search([("active", "=", False)]).ids)
    missing_expected_active_ids = sorted(keep_ids - active_ids_after)
    unexpected_active_ids = sorted(active_ids_after - keep_ids)
    archived_kept_ids = sorted(keep_ids & inactive_ids_after)

    summary = {
        "database": dbname,
        "excel_unique_names": len(excel_unique),
        "positive_excel_names_after_user_discard": len(positive_keys),
        "positive_resolved_name_count": len(resolved_positive_keys),
        "positive_unresolved_name_count": len(unresolved_positive_keys),
        "user_discard_names": len(USER_DISCARD),
        "direct_project_exemptions": len(direct_projects),
        "kept_project_count": len(keep_ids),
        "kept_already_active_count": len(already_active_kept),
        "activated_project_count": len(activate_projects),
        "archived_project_count": len(archive_projects),
        "active_project_count_after": len(active_ids_after),
        "inactive_project_count_after": len(inactive_ids_after),
        "visibility_exact_match": not missing_expected_active_ids and not unexpected_active_ids and not archived_kept_ids,
        "missing_expected_active_ids": missing_expected_active_ids[:20],
        "unexpected_active_ids": unexpected_active_ids[:20],
        "archived_kept_ids": archived_kept_ids[:20],
        "outputs": {"csv": str(output_csv), "json": str(output_json)},
        "repo_artifact_write_fallback": str(output_dir) != str(OUTPUT_DIR),
    }
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    env.cr.commit()  # noqa: F821
    print("PROJECT_POSITIVE_MIGRATION_VISIBILITY_REFRESH=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


main()
