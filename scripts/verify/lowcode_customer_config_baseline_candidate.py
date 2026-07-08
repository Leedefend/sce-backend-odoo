# -*- coding: utf-8 -*-
"""Export a reviewable customer-module low-code baseline candidate.

Run with Odoo shell through Make:
  ENV=dev DB_NAME=sc_demo make verify.lowcode_config.customer_baseline.candidate

This is intentionally a review artifact. It does not mutate module data.
Customer-confirmed rows must still be reviewed before being converted into
smart_construction_custom assets or a dedicated customer module.
"""

import hashlib
import json
import os

from odoo.addons.smart_core.handlers.form_field_configuration import _business_config_contract_summary
from odoo.addons.smart_core.utils.backend_contract_boundaries import view_orchestration_source_status


DEFAULT_OUTPUT = "/tmp/lowcode_customer_config_baseline_candidate.json"
DEFAULT_INCLUDED_SOURCE_STATUSES = ("tenant_runtime",)
REQUIRED_AFTER_PROMOTION = [
    "make verify.lowcode_config.boundary.guard",
    "make verify.lowcode_config.runtime_boundary.guard",
    "make verify.business_config.unit",
    "make verify.business_config.snapshot",
    "make verify.product.surface.clean",
]


def _env():
    return globals()["env"]


def _text(value):
    return str(value or "").strip()


def _ref_id(value):
    try:
        return int(getattr(value, "id", value) or 0)
    except Exception:
        return 0


def _hash_payload(payload):
    text = json.dumps(payload if isinstance(payload, dict) else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _menu_source_status(payload):
    orchestration = payload.get("menu_orchestration") if isinstance(payload.get("menu_orchestration"), dict) else {}
    explicit = _text(orchestration.get("source_status"))
    if explicit:
        return explicit, True
    if _text(orchestration.get("source")) == "smart_core.lowcode.menu_config":
        return "tenant_runtime", False
    return "product_release", False


def _view_source_status(payload):
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
    return view_orchestration_source_status(payload), bool(_text(context.get("source_status")))


def _source_status(payload):
    if not isinstance(payload, dict):
        return "product_release", False, "unknown"
    if isinstance(payload.get("menu_orchestration"), dict):
        status, explicit = _menu_source_status(payload)
        return status, explicit, "menu_orchestration"
    if isinstance(payload.get("view_orchestration"), dict):
        status, explicit = _view_source_status(payload)
        return status, explicit, "view_orchestration"
    return "product_release", False, "unknown"


def _surface_for(row):
    if row["config_carrier"] == "menu_orchestration" or row["model"] == "ir.ui.menu":
        return "menu_preferences"
    if row["view_type"] == "form":
        return "form_preferences"
    if row["view_type"] in {"tree", "list", "search"}:
        return "list_search_preferences"
    if row["view_type"] in {"pivot", "graph", "calendar", "dashboard"}:
        return "analysis_preferences"
    return "other_contracts"


def _contract_key(row):
    return "|".join([
        row["model"],
        row["view_type"],
        str(row["action_id"]),
        str(row["view_id"]),
        row["role_key"],
        row["name"],
    ])


def _contract_row(rec):
    payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
    source_status, source_status_explicit, carrier = _source_status(payload)
    row = {
        "id": int(rec.id or 0),
        "name": _text(rec.name),
        "model": _text(rec.model),
        "view_type": _text(rec.view_type),
        "action_id": _ref_id(rec.action_id),
        "view_id": _ref_id(rec.view_id),
        "role_key": _text(rec.role_key),
        "status": _text(rec.status),
        "version_no": int(rec.version_no or 0),
        "source_status": source_status,
        "source_status_explicit": source_status_explicit,
        "config_carrier": carrier,
        "payload_hash": _hash_payload(payload),
        "summary": _business_config_contract_summary(payload),
        "contract_json": payload,
    }
    row["surface"] = _surface_for(row)
    row["contract_key"] = _contract_key(row)
    return row


def _source_status_filter():
    raw = _text(os.getenv("LOWCODE_CUSTOMER_BASELINE_SOURCE_STATUSES"))
    if not raw:
        return set(DEFAULT_INCLUDED_SOURCE_STATUSES)
    return {item.strip() for item in raw.split(",") if item.strip()}


def _surface_payload(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["surface"], []).append(row)
    surfaces = []
    for surface, items in sorted(grouped.items()):
        surfaces.append({
            "surface": surface,
            "contract_count": len(items),
            "contracts": sorted(items, key=lambda item: item["contract_key"]),
        })
    return surfaces


def _counts(rows, key):
    out = {}
    for row in rows:
        value = row.get(key) or ""
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def build_candidate(env_obj):
    Contract = env_obj["ui.business.config.contract"].sudo()
    rows = [_contract_row(rec) for rec in Contract.search([("active", "=", True)], order="model, view_type, action_id, view_id, role_key, name, id")]
    included_source_statuses = _source_status_filter()
    included_rows = [row for row in rows if row["source_status"] in included_source_statuses]
    excluded_rows = [row for row in rows if row["source_status"] not in included_source_statuses]
    return {
        "schema_version": "lowcode_customer_config_baseline_candidate.v1",
        "database": env_obj.cr.dbname,
        "target_module": "smart_construction_custom",
        "generated_from": "ui.business.config.contract",
        "promotion_policy": {
            "artifact_status": "review_required",
            "default_included_source_statuses": sorted(included_source_statuses),
            "rule": "Only customer-confirmed runtime configuration should be promoted to smart_construction_custom or an explicit customer module.",
            "not_a_direct_module_asset": True,
        },
        "summary": {
            "total_contract_count": len(rows),
            "candidate_contract_count": len(included_rows),
            "excluded_contract_count": len(excluded_rows),
            "source_status_counts": _counts(rows, "source_status"),
            "candidate_surface_counts": _counts(included_rows, "surface"),
            "candidate_view_type_counts": _counts(included_rows, "view_type"),
        },
        "acceptance": {
            "required_after_promotion": list(REQUIRED_AFTER_PROMOTION),
            "required_review": [
                "Confirm each candidate row is customer-specific, not industry product_release.",
                "Convert accepted rows into smart_construction_custom assets, migration, or idempotent initializer.",
                "Keep ordinary user UI-only preferences out of global low-code baselines.",
            ],
        },
        "surfaces": _surface_payload(included_rows),
    }


def main():
    env_obj = _env()
    candidate = build_candidate(env_obj)
    output_path = os.getenv("LOWCODE_CUSTOMER_CONFIG_BASELINE_CANDIDATE_PATH", DEFAULT_OUTPUT)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(candidate, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print("[lowcode_customer_config_baseline_candidate] PASS %s" % json.dumps({
        "database": candidate["database"],
        "target_module": candidate["target_module"],
        "candidate_contract_count": candidate["summary"]["candidate_contract_count"],
        "candidate_surface_counts": candidate["summary"]["candidate_surface_counts"],
        "source_status_counts": candidate["summary"]["source_status_counts"],
        "output_path": output_path,
    }, ensure_ascii=False, sort_keys=True))


main()
