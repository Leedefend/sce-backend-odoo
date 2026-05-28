#!/usr/bin/env python3
"""Write action-scoped SCBS55 form contracts from the user-visible list plan."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_action_form_contract_write_result_v1.json"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_form_contract/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_form_contract/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def slug(value: str) -> str:
    raw = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return raw[:56] or hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def contract_labels(record) -> list[str]:
    labels: list[str] = []
    for item in record.list_field_contract or []:
        if isinstance(item, dict):
            label = str(item.get("legacy_label") or "").strip()
            if label:
                labels.append(label)
    return labels


def payload_for(record, labels: list[str]) -> dict[str, Any]:
    fields = [
        {
            "name": alias_field_name(label),
            "sequence": index * 10,
            "readonly": True,
            "legacy_label": label,
        }
        for index, label in enumerate(labels, start=1)
    ]
    sections = record.form_section_contract or []
    return {
        "view_orchestration": {
            "views": {
                "form": {
                    "sections": sections
                    or [
                        {"title": "老系统列表字段", "sequence": 10},
                        {"title": "附件", "sequence": 90, "required": bool(record.attachment_required)},
                        {"title": "日志", "sequence": 100, "required": bool(record.chatter_required)},
                    ],
                    "fields": fields,
                }
            }
        }
    }


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")

written = 0
skipped: list[dict[str, Any]] = []
failures: list[dict[str, Any]] = []
result_rows: list[dict[str, Any]] = []

for record in rows:
    labels = contract_labels(record)
    model = str(record.target_model or "")
    action = record.target_action_id
    if not labels:
        skipped.append({"seq": int(record.priority_sequence or 0), "name": record.legacy_menu_name, "reason": "empty_list_contract"})
        continue
    if not model or model not in env or not action:  # noqa: F821
        skipped.append(
            {
                "seq": int(record.priority_sequence or 0),
                "name": record.legacy_menu_name,
                "reason": "missing_model_or_action",
                "model": model,
                "action_id": int(action.id or 0),
            }
        )
        continue
    missing = [label for label in labels if alias_field_name(label) not in env[model]._fields]  # noqa: F821
    if missing:
        failures.append(
            {
                "seq": int(record.priority_sequence or 0),
                "name": record.legacy_menu_name,
                "model": model,
                "missing_labels": missing,
            }
        )
        continue

    name = "scbs55_%03d_%s_action_form_facts_v1" % (record.priority_sequence, slug(record.legacy_menu_name or "menu"))
    values = {
        "name": name,
        "model": model,
        "view_type": "form",
        "action_id": action.id,
        "view_id": False,
        "priority": 87,
        "company_id": False,
        "active": True,
        "status": "published",
        "version_no": 1,
        "contract_json": payload_for(record, labels),
    }
    contract = Contract.search([("name", "=", name), ("company_id", "=", False)], limit=1)
    if contract:
        contract.write(values)
    else:
        contract = Contract.create(values)
    written += 1
    result_rows.append(
        {
            "seq": int(record.priority_sequence or 0),
            "name": record.legacy_menu_name or "",
            "model": model,
            "action_id": int(action.id),
            "contract_id": int(contract.id),
            "field_count": len(labels),
        }
    )

payload = {
    "status": "PASS" if not failures else "FAIL",
    "mode": "scbs_55_user_visible_action_form_contract_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "written_count": written,
    "skipped_count": len(skipped),
    "failure_count": len(failures),
    "skipped": skipped,
    "failures": failures,
    "rows": result_rows,
    "db_writes": written,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
if payload["status"] == "PASS":
    env.cr.commit()  # noqa: F821
print(
    "SCBS_55_USER_VISIBLE_ACTION_FORM_CONTRACT_WRITE="
    + json.dumps(
        {
            "status": payload["status"],
            "written_count": payload["written_count"],
            "skipped_count": payload["skipped_count"],
            "failure_count": payload["failure_count"],
            "output_json": str(artifact_dir / OUTPUT_JSON_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if payload["status"] != "PASS":
    raise SystemExit(2)
