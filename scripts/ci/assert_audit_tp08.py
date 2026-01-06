#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


CSV_PATH = Path("docs/audit/object_button_visibility_by_role.csv")
NODE_NOTES_PATH = Path("docs/audit/node_missing_notes.md")

REQUIRED = [
    ("project.edit_project:form:action_view_tasks", "action_view_tasks"),
    ("project.edit_project:form:project_update_all_action", "project_update_all_action"),
    ("project.view_project_kanban:kanban:action_view_tasks", "action_view_tasks"),
    ("project.view_project_kanban:kanban:action_view_tasks_analysis", "action_view_tasks_analysis"),
    ("project.view_project_kanban:kanban:action_project_task_burndown_chart_report", "action_project_task_burndown_chart_report"),
    ("project.project_project_view_form_simplified_footer:form:action_view_tasks", "action_view_tasks"),
    ("project.project_view_kanban_inherit_project:kanban:project_update_all_action", "project_update_all_action"),
]

EXCEPTION_REF = "project.view_project_kanban:kanban:action_get_list_view"
EXCEPTION_BUTTON = "action_get_list_view"


def load_rows():
    if not CSV_PATH.exists():
        return None, f"missing_csv:{CSV_PATH}"
    rows = []
    with CSV_PATH.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows, None


def check_role(rows, role, expected_visible, errors):
    for ref_source, button_name in REQUIRED:
        matches = [
            row for row in rows
            if row.get("role") == role
            and row.get("ref_source") == ref_source
            and row.get("button_name_raw") == button_name
        ]
        if not matches:
            errors.append(f"missing:{role}:{ref_source}:{button_name}")
            continue
        bad = [m for m in matches if m.get("visible") != expected_visible]
        if bad:
            errors.append(f"visible_mismatch:{role}:{ref_source}:{button_name}:expected={expected_visible}")


def check_exception(rows, errors):
    notes_text = ""
    if NODE_NOTES_PATH.exists():
        notes_text = NODE_NOTES_PATH.read_text(encoding="utf-8", errors="ignore")
    for role in ("demo_pm", "admin"):
        matches = [
            row for row in rows
            if row.get("role") == role
            and row.get("ref_source") == EXCEPTION_REF
            and row.get("button_name_raw") == EXCEPTION_BUTTON
        ]
        for row in matches:
            if row.get("visible") == "0" and EXCEPTION_REF not in notes_text:
                errors.append(f"exception_missing_note:{role}:{EXCEPTION_REF}:{EXCEPTION_BUTTON}")


def main():
    rows, err = load_rows()
    if err:
        print("[GATE][FAIL]", err)
        return 2

    errors = []
    check_role(rows, "demo_pm", "0", errors)
    check_role(rows, "admin", "1", errors)
    check_exception(rows, errors)

    if errors:
        print("[GATE][FAIL]")
        for err in errors:
            print(err)
        return 2

    print("[GATE][PASS]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
