"""Read-only usability review for the 100-row project create-only sample.

Run only through:

    DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_create_only_expand_usability_review.py

The script expects the Odoo shell global ``env``. It performs no create, write,
unlink, delete, state transition, rollback, or commit.
"""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from odoo.addons.smart_construction_core.services.insight.project_insight_service import (
    ProjectInsightService,
)
from odoo.addons.smart_construction_core.services.project_context_contract import (
    build_project_context,
)
from odoo.addons.smart_construction_core.services.project_dashboard_builders.project_header_builder import (
    ProjectHeaderBuilder,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)
from odoo.addons.smart_construction_core.services.project_execution_service import (
    ProjectExecutionService,
)
from odoo.addons.smart_construction_core.services.project_state_explain_service import (
    ProjectStateExplainService,
    lifecycle_state_label,
)


INPUT_CSV = Path("/mnt/artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv")
LOCK_RESULT_JSON = Path("/mnt/artifacts/migration/project_expand_rollback_dry_run_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_create_only_expand_manual_review_result_v1.json")

EXPECTED_LOCKED_ROWS = 100
DEEP_COUNT = 10
QUICK_COUNT = 20


def read_locked_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    if "legacy_project_id" not in (reader.fieldnames or []):
        raise RuntimeError("legacy_project_id column is required")
    return rows


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def deterministic_sample(rows, count):
    if len(rows) <= count:
        return rows
    indexes = []
    if count == 10:
        indexes = [0, 1, 2, 9, 19, 39, 59, 79, 98, 99]
    elif count == 20:
        indexes = list(range(20))
    else:
        indexes = list(range(count))
    return [rows[index] for index in indexes if index < len(rows)]


def _dict_get_path(data, path):
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _view_payload(model, view_type):
    last_error = ""
    for call in (
        lambda: model.get_view(view_type=view_type),
        lambda: model.get_view(False, view_type),
        lambda: model.fields_view_get(view_type=view_type),
    ):
        try:
            return call(), ""
        except AttributeError as exc:
            last_error = str(exc)
        except TypeError as exc:
            last_error = str(exc)
        except Exception as exc:
            return {}, str(exc)
    return {}, last_error or "view api unavailable"


def _field_refs_from_arch(env, model_name, arch):
    refs = set()
    missing = []
    if not arch:
        return refs, missing, "empty arch"
    try:
        root = ET.fromstring(arch)
    except Exception as exc:
        return refs, missing, f"xml parse failed: {exc}"

    def walk(node, current_model_name):
        try:
            current_model = env[current_model_name]
        except Exception:
            current_model = None
        current_fields = getattr(current_model, "_fields", {}) if current_model is not None else {}
        for child in list(node):
            if child.tag != "field":
                walk(child, current_model_name)
                continue
            name = child.attrib.get("name")
            if not name:
                walk(child, current_model_name)
                continue
            refs.add(f"{current_model_name}.{name}")
            field = current_fields.get(name)
            if field is None:
                missing.append(f"{current_model_name}.{name}")
                continue
            relation_model = getattr(field, "comodel_name", "") or ""
            subview_nodes = [grand for grand in list(child) if grand.tag in {"tree", "list", "form", "kanban"}]
            if relation_model and subview_nodes:
                for subview in subview_nodes:
                    walk(subview, relation_model)
            else:
                walk(child, current_model_name)

    walk(root, model_name)
    return refs, sorted(set(missing)), ""


def native_view_checks(model):
    checks = []
    for view_type in ("form", "tree", "kanban"):
        payload, error = _view_payload(model, view_type)
        arch = payload.get("arch") if isinstance(payload, dict) else ""
        refs, missing, parse_error = _field_refs_from_arch(model.env, model._name, arch)
        checks.append(
            {
                "view_type": view_type,
                "view_loaded": bool(arch) and not error,
                "field_ref_count": len(refs),
                "missing_field_refs": missing,
                "error": error or parse_error,
                "status": "PASS" if arch and not error and not parse_error and not missing else "FAIL",
            }
        )
    return checks


def _block_ok(block):
    if not isinstance(block, dict):
        return False, "not a dict"
    if block.get("state") == "error":
        return False, str(((block.get("error") or {}).get("code")) or "error block")
    error = block.get("error") or {}
    if isinstance(error, dict) and (error.get("code") or error.get("message")):
        return False, str(error.get("code") or error.get("message") or "error")
    if error and not isinstance(error, dict):
        return False, str(error)
    return True, ""


def review_deep_project(project, services):
    dashboard = services["dashboard"]
    state_explain_service = services["state_explain"]
    insight_service = services["insight"]
    header_builder = services["header"]
    execution_service = services["execution"]

    expected_label = lifecycle_state_label(project)
    project_payload = dashboard.project_payload(project)
    state_explain = state_explain_service.build(project)
    dashboard_state_explain = dashboard.build_state_explain(project)
    project_context = build_project_context(project)
    insight = insight_service.get_insight(project)
    header = header_builder.build(project=project, context={})
    flow_map = dashboard.build_flow_map(project)
    dashboard_next_actions = dashboard.build_block("next_actions", project=project, context={})
    execution_next_actions = execution_service.build_block("next_actions", project=project, context={})

    header_summary_stage = _dict_get_path(header, ["data", "summary", "stage_name"])
    header_semantic_stage = _dict_get_path(header, ["data", "semantic_summary", "current_stage"])
    labels = {
        "expected_lifecycle_label": expected_label,
        "payload_stage_name": project_payload.get("stage_name"),
        "state_explain_stage_label": state_explain.get("stage_label"),
        "dashboard_state_explain_stage_label": dashboard_state_explain.get("stage_label"),
        "project_context_stage_label": project_context.get("stage_label"),
        "insight_stage": insight.get("stage"),
        "header_stage_name": header_summary_stage,
        "header_current_stage": header_semantic_stage,
    }
    label_mismatches = [
        key
        for key, value in labels.items()
        if key != "expected_lifecycle_label" and str(value or "") != str(expected_label or "")
    ]

    dashboard_actions_ok, dashboard_actions_error = _block_ok(dashboard_next_actions)
    execution_actions_ok, execution_actions_error = _block_ok(execution_next_actions)
    header_ok, header_error = _block_ok(header)
    flow_ok = isinstance(flow_map, dict) and bool(flow_map.get("current_stage")) and bool(flow_map.get("items"))

    read_outputs = {
        "project_payload": {
            "ok": isinstance(project_payload, dict) and project_payload.get("id") == project.id and bool(project_payload.get("name")),
            "stage_name": project_payload.get("stage_name"),
        },
        "state_explain": {
            "ok": isinstance(state_explain, dict) and bool(state_explain.get("stage_label")),
            "stage_label": state_explain.get("stage_label"),
        },
        "project_context": {
            "ok": isinstance(project_context, dict) and project_context.get("project_id") == project.id,
            "stage_label": project_context.get("stage_label"),
        },
        "project_insight": {
            "ok": isinstance(insight, dict) and insight.get("object_id") == project.id and bool(insight.get("summary")),
            "stage": insight.get("stage"),
        },
        "header_summary": {
            "ok": header_ok,
            "error": header_error,
            "stage_name": header_summary_stage,
            "current_stage": header_semantic_stage,
        },
        "flow_map": {
            "ok": flow_ok,
            "current_stage": flow_map.get("current_stage") if isinstance(flow_map, dict) else "",
            "item_count": len(flow_map.get("items") or []) if isinstance(flow_map, dict) else 0,
        },
        "dashboard_next_actions": {
            "ok": dashboard_actions_ok,
            "error": dashboard_actions_error,
            "state": dashboard_next_actions.get("state") if isinstance(dashboard_next_actions, dict) else "",
            "action_count": len(_dict_get_path(dashboard_next_actions, ["data", "actions"]) or []),
        },
        "execution_next_actions": {
            "ok": execution_actions_ok,
            "error": execution_actions_error,
            "state": execution_next_actions.get("state") if isinstance(execution_next_actions, dict) else "",
            "action_count": len(_dict_get_path(execution_next_actions, ["data", "actions"]) or []),
        },
    }
    output_failures = [key for key, value in read_outputs.items() if not value.get("ok")]

    return {
        "project_id": project.id,
        "legacy_project_id": project.legacy_project_id or "",
        "name": project.name or "",
        "lifecycle_state": project.lifecycle_state or "",
        "stage_id": project.stage_id.id if project.stage_id else None,
        "stage_name": project.stage_id.display_name if project.stage_id else "",
        "labels": labels,
        "label_mismatches": label_mismatches,
        "read_outputs": read_outputs,
        "output_failures": output_failures,
        "status": "PASS" if not label_mismatches and not output_failures else "FAIL",
    }


def review_quick_project(project, model):
    search_rows = model.search_read(
        [("name", "=", project.name)],
        fields=["id", "name", "legacy_project_id", "lifecycle_state", "stage_id"],
        limit=5,
        order="id",
    )
    list_hit = any(row.get("id") == project.id for row in search_rows)
    form_fields_ok = bool(project.exists()) and bool(project.name)
    kanban_fields_ok = bool(project.display_name) and bool(project.stage_id)
    expected_label = lifecycle_state_label(project)
    return {
        "project_id": project.id,
        "legacy_project_id": project.legacy_project_id or "",
        "name": project.name or "",
        "list_search_hit": list_hit,
        "form_readable": form_fields_ok,
        "kanban_readable": kanban_fields_ok,
        "header_state_label": expected_label,
        "status": "PASS" if list_hit and form_fields_ok and kanban_fields_ok and expected_label else "FAIL",
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    locked_rows = read_locked_rows(INPUT_CSV)
    lock_result = load_json(LOCK_RESULT_JSON)
    locked_ids = [(row.get("legacy_project_id") or "").strip() for row in locked_rows]
    locked_ids = [identity for identity in locked_ids if identity]
    locked_counts = Counter(locked_ids)

    model = env["project.project"].sudo()  # noqa: F821
    records = model.search([("legacy_project_id", "in", locked_ids)], order="id")
    record_by_identity = {rec.legacy_project_id: rec for rec in records}

    deep_rows = deterministic_sample(locked_rows, DEEP_COUNT)
    quick_rows = deterministic_sample(locked_rows, QUICK_COUNT)
    deep_ids = [(row.get("legacy_project_id") or "").strip() for row in deep_rows]
    quick_ids = [(row.get("legacy_project_id") or "").strip() for row in quick_rows]

    services = {
        "dashboard": ProjectDashboardService(env),  # noqa: F821
        "state_explain": ProjectStateExplainService(env),  # noqa: F821
        "insight": ProjectInsightService(env),  # noqa: F821
        "header": ProjectHeaderBuilder(env),  # noqa: F821
        "execution": ProjectExecutionService(env),  # noqa: F821
    }

    native_views = native_view_checks(model)
    deep_results = [review_deep_project(record_by_identity[identity], services) for identity in deep_ids if identity in record_by_identity]
    quick_results = [review_quick_project(record_by_identity[identity], model) for identity in quick_ids if identity in record_by_identity]

    blocking_reasons = []
    minor_notes = []

    if len(locked_ids) != EXPECTED_LOCKED_ROWS:
        blocking_reasons.append(f"expected {EXPECTED_LOCKED_ROWS} locked ids, got {len(locked_ids)}")
    if any(count > 1 for count in locked_counts.values()):
        blocking_reasons.append("duplicate locked legacy_project_id in input snapshot")
    if lock_result.get("status") != "ROLLBACK_READY":
        blocking_reasons.append("1836 rollback dry-run is not ROLLBACK_READY")
    if int(lock_result.get("matched_rows") or 0) != EXPECTED_LOCKED_ROWS:
        blocking_reasons.append("1836 matched rows count is not 100")
    if len(records) != EXPECTED_LOCKED_ROWS:
        blocking_reasons.append(f"current matched records count is {len(records)}, expected 100")
    if len(deep_results) != DEEP_COUNT:
        blocking_reasons.append(f"deep review count is {len(deep_results)}, expected {DEEP_COUNT}")
    if len(quick_results) != QUICK_COUNT:
        blocking_reasons.append(f"quick review count is {len(quick_results)}, expected {QUICK_COUNT}")

    failed_views = [row for row in native_views if row.get("status") != "PASS"]
    if failed_views:
        blocking_reasons.append("native view server-side readability check failed")

    failed_deep = [row for row in deep_results if row.get("status") != "PASS"]
    failed_quick = [row for row in quick_results if row.get("status") != "PASS"]
    if failed_deep:
        blocking_reasons.append("deep read-side review failures")
    if failed_quick:
        blocking_reasons.append("quick page review failures")

    long_names = [row for row in quick_results if len(row.get("name") or "") > 80]
    if long_names:
        minor_notes.append("some sample project names are long; native list/form wrapping should be watched during human observation")

    if blocking_reasons:
        status = "BLOCKED"
        target_state = "USABILITY_REVIEW_BLOCKED"
        recommendation = "enter rollback authorization path after reviewing blockers"
    else:
        status = "PASS_WITH_MINOR_NOTES" if minor_notes else "PASS"
        target_state = "USABILITY_REVIEW_READY"
        recommendation = "keep sample for observation"

    payload = {
        "status": status,
        "target_state": target_state,
        "mode": "read_only_business_usability_review",
        "db": env.cr.dbname,  # noqa: F821
        "input": str(INPUT_CSV),
        "lock_result": {
            "source": str(LOCK_RESULT_JSON),
            "status": lock_result.get("status"),
            "total_targets": lock_result.get("total_targets"),
            "matched_rows": lock_result.get("matched_rows"),
            "missing_rows": lock_result.get("missing_rows"),
            "duplicate_matches": len(lock_result.get("duplicate_matches") or []),
            "out_of_scope_matches": len(lock_result.get("out_of_scope_matches") or []),
            "projection_mismatches": len(lock_result.get("projection_mismatches") or []),
        },
        "summary": {
            "locked_rows": len(locked_ids),
            "current_matched_records": len(records),
            "deep_review_rows": len(deep_results),
            "quick_review_rows": len(quick_results),
            "native_view_checks": len(native_views),
            "native_view_failures": len(failed_views),
            "deep_review_failures": len(failed_deep),
            "quick_review_failures": len(failed_quick),
            "recommendation": recommendation,
        },
        "sample_strategy": {
            "deep_legacy_project_ids": deep_ids,
            "quick_legacy_project_ids": quick_ids,
        },
        "native_views": native_views,
        "deep_results": deep_results,
        "quick_results": quick_results,
        "minor_notes": minor_notes,
        "blocking_reasons": blocking_reasons,
        "decision": {
            "keep_for_observation": not blocking_reasons,
            "enter_real_rollback_authorization_batch": bool(blocking_reasons),
            "next_batch": (
                "ITER-2026-04-13-1838 project create-only 100-row observation sample retention decision"
                if not blocking_reasons
                else "ITER-2026-04-13-1838R project create-only 100-row real rollback authorization and execution"
            ),
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    env.cr.rollback()  # noqa: F821 - keep shell transaction read-only
    print(
        "ITER_1837_USABILITY_REVIEW="
        + json.dumps(
            {
                "status": payload["status"],
                "target_state": payload["target_state"],
                "locked_rows": payload["summary"]["locked_rows"],
                "deep_review_rows": payload["summary"]["deep_review_rows"],
                "quick_review_rows": payload["summary"]["quick_review_rows"],
                "native_view_failures": payload["summary"]["native_view_failures"],
                "deep_review_failures": payload["summary"]["deep_review_failures"],
                "quick_review_failures": payload["summary"]["quick_review_failures"],
                "recommendation": payload["summary"]["recommendation"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
