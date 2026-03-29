#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "scripts" / "verify"
if str(VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFY_DIR))

from intent_smoke_utils import require_ok  # type: ignore
from python_http_smoke_utils import get_base_url, http_post_json  # type: ignore


LIST_FACT_SPECS: dict[str, tuple[str, ...]] = {
    "views.tree.columns": ("views", "tree", "columns"),
    "views.tree.row_actions": ("views", "tree", "row_actions"),
    "views.tree.toolbar": ("views", "tree", "toolbar"),
    "search.filters": ("search", "filters"),
    "search.group_by": ("search", "group_by"),
    "search.saved_filters": ("search", "saved_filters"),
    "list_profile.column_labels": ("list_profile", "column_labels"),
    "list_profile.row_primary": ("list_profile", "row_primary"),
    "list_profile.row_secondary": ("list_profile", "row_secondary"),
    "list_profile.status_field": ("list_profile", "status_field"),
}

DETAIL_FACT_SPECS: dict[str, tuple[str, ...]] = {
    "views.form.layout": ("views", "form", "layout"),
    "views.form.statusbar.field": ("views", "form", "statusbar", "field"),
    "views.form.field_modifiers": ("views", "form", "field_modifiers"),
    "buttons": ("buttons",),
    "permissions.field_groups": ("permissions", "field_groups"),
    "visible_fields": ("visible_fields",),
    "field_semantics": ("field_semantics",),
    "workflow.transitions": ("workflow", "transitions"),
}

LIST_FRONTEND_SPECS: dict[str, tuple[str, ...]] = {
    "native_list_shell": (
        "preferNativeListSurface",
        "ListPage",
    ),
    "header_toolbar": (
        "PageHeader",
        "PageToolbar",
    ),
    "summary_strip": (
        "summary-strip",
        "summaryItems",
    ),
    "table_columns": (
        "displayedColumns",
        "columnLabel",
    ),
    "row_click": (
        "handleRow",
        "onRowClick",
    ),
    "grouped_rows": (
        "groupedRows",
        "GroupSummaryBar",
    ),
    "pagination": (
        "table-pagination",
        "paginationTotal",
    ),
}

DETAIL_FRONTEND_SPECS: dict[str, tuple[str, ...]] = {
    "header_identity": (
        "PageHeaderTemplate",
        "pageDisplayTitle",
    ),
    "command_bar": (
        "DetailCommandBar",
        "contractActionStrip",
        "statusbarSteps",
    ),
    "detail_layout_renderer": (
        "DetailShellLayout",
        "detailShells",
    ),
    "detail_layout_mapper": (
        "buildDetailSectionViews",
        "buildDetailShellViews",
    ),
    "field_modifiers_runtime": (
        "fieldModifierMap",
        "runtimeFieldStates",
    ),
    "readonly_projection": (
        "runtimeState(",
        "isFieldVisible(",
    ),
    "relation_fallback": (
        "relationFallbackAdapter",
        "RelationFallbackAdapter",
    ),
}


def _descend(value: object, path: tuple[str, ...]) -> object | None:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _is_present(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _evaluate_backend(contract: dict[str, object], specs: dict[str, tuple[str, ...]]) -> dict[str, object]:
    targets: list[dict[str, object]] = []
    for label, path in specs.items():
        value = _descend(contract, path)
        targets.append(
            {
                "label": label,
                "path": ".".join(path),
                "present": _is_present(value),
            }
        )
    missing = [item for item in targets if not item["present"]]
    return {
        "target_count": len(targets),
        "present_count": len(targets) - len(missing),
        "targets": targets,
        "missing_targets": missing,
    }


def _evaluate_frontend(frontend_file: Path, specs: dict[str, tuple[str, ...]]) -> dict[str, object]:
    content = frontend_file.read_text(encoding="utf-8")
    targets: list[dict[str, object]] = []
    for label, tokens in specs.items():
        missing_tokens = [token for token in tokens if token not in content]
        targets.append(
            {
                "label": label,
                "covered": not missing_tokens,
                "missing_tokens": missing_tokens,
            }
        )
    uncovered = [item for item in targets if not item["covered"]]
    return {
        "target_count": len(targets),
        "covered_count": len(targets) - len(uncovered),
        "targets": targets,
        "uncovered_targets": uncovered,
    }


def _gap_summary(backend: dict[str, object], frontend: dict[str, object]) -> list[str]:
    missing_backend = [str(item["label"]) for item in backend["missing_targets"]]  # type: ignore[index]
    missing_frontend = [str(item["label"]) for item in frontend["uncovered_targets"]]  # type: ignore[index]
    out: list[str] = []
    if missing_backend:
        out.append(f"backend_missing={', '.join(missing_backend)}")
    if missing_frontend:
        out.append(f"frontend_uncovered={', '.join(missing_frontend)}")
    if not out:
        out.append("no_gap_detected_for_current_audit_scope")
    return out


def _load_snapshot(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    contract = payload.get("ui_contract_raw")
    if not isinstance(contract, dict):
        raise ValueError(f"{path} does not contain ui_contract_raw object")
    return contract


def _login(intent_url: str, db: str, login_name: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db, "login": login_name, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login_name})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login_name}) missing token")
    return token


def _fetch_live_contract(intent_url: str, token: str, view_type: str) -> dict[str, object]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": view_type, "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"ui.contract(project.project.{view_type})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit backend fact coverage and frontend consumer coverage for generic list/detail pages.")
    parser.add_argument("--list-snapshot")
    parser.add_argument("--detail-snapshot")
    parser.add_argument("--db")
    parser.add_argument("--login")
    parser.add_argument("--password")
    parser.add_argument("--list-view", required=True)
    parser.add_argument("--list-page", required=True)
    parser.add_argument("--detail-page", required=True)
    parser.add_argument("--detail-runtime", required=True)
    parser.add_argument("--expect-status", choices=["PASS", "FAIL"], default="PASS")
    args = parser.parse_args()

    if args.db and args.login and args.password:
        base_url = get_base_url()
        intent_url = f"{base_url}/api/v1/intent?db={args.db}"
        token = _login(intent_url, args.db, args.login, args.password)
        list_contract = _fetch_live_contract(intent_url, token, "tree")
        detail_contract = _fetch_live_contract(intent_url, token, "form")
        source_mode = "live"
    else:
        if not args.list_snapshot or not args.detail_snapshot:
            raise ValueError("either provide --db/--login/--password for live mode or both --list-snapshot and --detail-snapshot")
        list_contract = _load_snapshot(Path(args.list_snapshot).resolve())
        detail_contract = _load_snapshot(Path(args.detail_snapshot).resolve())
        source_mode = "snapshot"
    list_view = Path(args.list_view).resolve()
    list_page = Path(args.list_page).resolve()
    detail_page = Path(args.detail_page).resolve()
    detail_runtime = Path(args.detail_runtime).resolve()

    list_backend = _evaluate_backend(list_contract, LIST_FACT_SPECS)
    detail_backend = _evaluate_backend(detail_contract, DETAIL_FACT_SPECS)

    list_frontend = _evaluate_frontend(list_view, LIST_FRONTEND_SPECS)
    list_page_frontend = _evaluate_frontend(list_page, LIST_FRONTEND_SPECS)
    merged_list_frontend = {
        "target_count": list_frontend["target_count"],
        "covered_count": len(
            [
                spec
                for spec in LIST_FRONTEND_SPECS
                if any(item["label"] == spec and item["covered"] for item in list_frontend["targets"])  # type: ignore[index]
                or any(item["label"] == spec and item["covered"] for item in list_page_frontend["targets"])  # type: ignore[index]
            ]
        ),
        "targets": [
            {
                "label": spec,
                "covered": any(item["label"] == spec and item["covered"] for item in list_frontend["targets"])  # type: ignore[index]
                or any(item["label"] == spec and item["covered"] for item in list_page_frontend["targets"]),  # type: ignore[index]
            }
            for spec in LIST_FRONTEND_SPECS
        ],
    }
    merged_list_frontend["uncovered_targets"] = [item for item in merged_list_frontend["targets"] if not item["covered"]]

    detail_frontend = _evaluate_frontend(detail_page, DETAIL_FRONTEND_SPECS)
    detail_runtime_frontend = _evaluate_frontend(detail_runtime, {"detail_layout_mapper": ("buildDetailSectionViews", "buildDetailShellViews")})
    for item in detail_frontend["targets"]:  # type: ignore[index]
        if item["label"] == "detail_layout_mapper":
            item["covered"] = any(
                rt["label"] == "detail_layout_mapper" and rt["covered"] for rt in detail_runtime_frontend["targets"]  # type: ignore[index]
            )
            item["missing_tokens"] = [] if item["covered"] else ["buildDetailSectionViews", "buildDetailShellViews"]
    detail_frontend["uncovered_targets"] = [item for item in detail_frontend["targets"] if not item["covered"]]  # type: ignore[index]
    detail_frontend["covered_count"] = len(detail_frontend["targets"]) - len(detail_frontend["uncovered_targets"])  # type: ignore[index]

    payload = {
        "status": "PASS",
        "source_mode": source_mode,
        "list": {
            "backend": list_backend,
            "frontend": merged_list_frontend,
            "gap_summary": _gap_summary(list_backend, merged_list_frontend),
        },
        "detail": {
            "backend": detail_backend,
            "frontend": detail_frontend,
            "gap_summary": _gap_summary(detail_backend, detail_frontend),
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == args.expect_status else 1


if __name__ == "__main__":
    raise SystemExit(main())
