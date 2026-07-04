# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


NON_BUSINESS_CREATOR_VALUES = {
    "admin",
    "administrator",
    "false",
    "none",
    "null",
    "odoobot",
    "system",
    "系统",
    "系统导入",
}
LEGACY_SYSTEM_ADMIN_LABEL = "旧系统管理员"


def clean(value):
    if value is None or value is False:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def non_business_values():
    return sorted(NON_BUSINESS_CREATOR_VALUES | {value.title() for value in NON_BUSINESS_CREATOR_VALUES})


def is_business_name(value):
    text = clean(value)
    return bool(text and text not in non_business_values())


def artifact_root():
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FORMAL_ENTRY_METADATA_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path.cwd() / "artifacts"])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def fix_records(model_name, resolver):
    Model = env[model_name].sudo().with_context(active_test=False, tracking_disable=True, mail_notrack=True)  # noqa: F821
    if "creator_name" not in Model._fields:
        return {"model": model_name, "updated": 0, "rows": []}
    domain = [("creator_name", "in", non_business_values())]
    if "active" in Model._fields:
        domain.insert(0, ("active", "=", True))
    rows = []
    for record in Model.search(domain):
        replacement = resolver(record)
        if not is_business_name(replacement) and clean(replacement) != LEGACY_SYSTEM_ADMIN_LABEL:
            replacement = LEGACY_SYSTEM_ADMIN_LABEL
        before = clean(record.creator_name)
        record.write({"creator_name": replacement})
        rows.append(
            OrderedDict(
                [
                    ("id", record.id),
                    ("name", clean(getattr(record, "name", "")) or clean(record.display_name)),
                    ("before", before),
                    ("after", replacement),
                ]
            )
        )
    return {"model": model_name, "updated": len(rows), "rows": rows}


def expense_claim_creator(record):
    if is_business_name(getattr(record, "applicant_name", "")):
        return clean(record.applicant_name)
    return LEGACY_SYSTEM_ADMIN_LABEL


def receipt_income_creator(_record):
    return LEGACY_SYSTEM_ADMIN_LABEL


results = [
    fix_records("sc.expense.claim", expense_claim_creator),
    fix_records("sc.receipt.income", receipt_income_creator),
]
env.cr.commit()  # noqa: F821
result = OrderedDict(
    [
        ("status", "PASS"),
        ("database", env.cr.dbname),  # noqa: F821
        ("mode", "formal_entry_metadata_non_business_creator_write"),
        ("updated_total", sum(item["updated"] for item in results)),
        ("results", results),
    ]
)

target = artifact_root() / f"formal_entry_metadata_non_business_creator_write.{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
print("FORMAL_ENTRY_METADATA_NON_BUSINESS_CREATOR_WRITE=%s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
