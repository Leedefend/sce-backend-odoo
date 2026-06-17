# -*- coding: utf-8 -*-
"""Export and optionally diff low-code business config contract snapshots.

Run with Odoo shell, for example:
  ENV=dev DB_NAME=sc_demo make verify.business_config.snapshot

Optional environment:
  BUSINESS_CONFIG_SNAPSHOT_PATH=/tmp/business_config_contract_snapshot.json
  BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH=/mnt/artifacts/backend/other_snapshot.json
"""

import hashlib
import json
import os

from odoo.addons.smart_core.handlers.form_field_configuration import _business_config_contract_summary


def _env():
    return globals()["env"]


def _ref_id(value):
    return int(getattr(value, "id", 0) or 0)


def _contract_key(row):
    return "|".join([
        str(row.get("model") or ""),
        str(row.get("view_type") or ""),
        str(row.get("action_id") or 0),
        str(row.get("view_id") or 0),
        str(row.get("role_key") or ""),
        str(row.get("name") or ""),
    ])


def _hash_payload(payload):
    text = json.dumps(payload if isinstance(payload, dict) else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _contract_row(rec):
    payload = rec.contract_json or {}
    return {
        "id": int(rec.id or 0),
        "name": str(rec.name or ""),
        "model": str(rec.model or ""),
        "view_type": str(rec.view_type or ""),
        "action_id": _ref_id(rec.action_id),
        "view_id": _ref_id(rec.view_id),
        "role_key": str(rec.role_key or ""),
        "status": str(rec.status or ""),
        "version_no": int(rec.version_no or 0),
        "payload_hash": _hash_payload(payload),
        "summary": _business_config_contract_summary(payload),
    }


def _snapshot(env_obj):
    Contract = env_obj["ui.business.config.contract"].sudo()
    rows = [_contract_row(rec) for rec in Contract.search([], order="model, view_type, action_id, view_id, role_key, name, id")]
    rows = sorted(rows, key=_contract_key)
    status_counts = {}
    view_type_counts = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        view_type_counts[row["view_type"] or "all"] = view_type_counts.get(row["view_type"] or "all", 0) + 1
    return {
        "database": env_obj.cr.dbname,
        "contract_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "view_type_counts": dict(sorted(view_type_counts.items())),
        "contracts": rows,
    }


def _load_snapshot(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    contracts = data.get("contracts") if isinstance(data, dict) else []
    return {
        _contract_key(row): row
        for row in contracts
        if isinstance(row, dict)
    }


def _diff(current, compare_path):
    previous = _load_snapshot(compare_path)
    current_rows = {
        _contract_key(row): row
        for row in current.get("contracts", [])
        if isinstance(row, dict)
    }
    added_keys = sorted(set(current_rows) - set(previous))
    removed_keys = sorted(set(previous) - set(current_rows))
    common_keys = sorted(set(current_rows) & set(previous))
    changed = []
    for key in common_keys:
        left = previous[key]
        right = current_rows[key]
        if left.get("payload_hash") == right.get("payload_hash") and left.get("status") == right.get("status"):
            continue
        changed.append({
            "key": key,
            "name": right.get("name") or left.get("name") or "",
            "model": right.get("model") or left.get("model") or "",
            "view_type": right.get("view_type") or left.get("view_type") or "",
            "previous_status": left.get("status") or "",
            "current_status": right.get("status") or "",
            "previous_version_no": int(left.get("version_no") or 0),
            "current_version_no": int(right.get("version_no") or 0),
            "previous_hash": left.get("payload_hash") or "",
            "current_hash": right.get("payload_hash") or "",
        })
    return {
        "compare_path": compare_path,
        "added_count": len(added_keys),
        "removed_count": len(removed_keys),
        "changed_count": len(changed),
        "added": [current_rows[key] for key in added_keys[:50]],
        "removed": [previous[key] for key in removed_keys[:50]],
        "changed": changed[:100],
    }


def main():
    env_obj = _env()
    report = _snapshot(env_obj)
    compare_path = os.getenv("BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH", "").strip()
    if compare_path:
        report["diff"] = _diff(report, compare_path)

    report_path = os.getenv(
        "BUSINESS_CONFIG_SNAPSHOT_PATH",
        "/tmp/business_config_contract_snapshot.json",
    )
    if report_path:
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    diff = report.get("diff") or {}
    print("[business_config_contract_snapshot] contracts=%s changed=%s added=%s removed=%s" % (
        report["contract_count"],
        int(diff.get("changed_count") or 0),
        int(diff.get("added_count") or 0),
        int(diff.get("removed_count") or 0),
    ))
    if os.getenv("BUSINESS_CONFIG_SNAPSHOT_VERBOSE", "").strip() in {"1", "true", "yes"}:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "database": report["database"],
            "contract_count": report["contract_count"],
            "status_counts": report["status_counts"],
            "view_type_counts": report["view_type_counts"],
            "diff": diff,
            "report_path": report_path,
        }, ensure_ascii=False, indent=2))


main()
