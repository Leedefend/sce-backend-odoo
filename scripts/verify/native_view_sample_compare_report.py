#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "docs" / "ops" / "audits" / "native_view_audit_sample_cases"
SNAPSHOT_DIR = ROOT / "docs" / "contract" / "snapshots" / "native_view"
LOAD_CONTRACT = ROOT / "addons" / "smart_core" / "handlers" / "load_contract.py"
OUT_JSON = ROOT / "artifacts" / "backend" / "native_view_sample_compare_report.json"
OUT_MD = ROOT / "artifacts" / "backend" / "native_view_sample_compare_report.md"


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _snapshot(path: str):
    return _load(SNAPSHOT_DIR / path)


def _has_case01():
    form = _snapshot("semantic_page_project_form_v1.json").get("semantic_page", {})
    rel = _snapshot("semantic_page_project_form_relation_v1.json").get("semantic_page", {})
    collab = _snapshot("semantic_page_project_form_collab_v1.json").get("semantic_page", {})
    perms = _snapshot("semantic_page_project_permissions_v1.json").get("semantic_page", {})
    return all(
        [
            any((z.get("key") == "detail_zone") for z in form.get("zones", [])),
            any((z.get("key") == "relation_zone") for z in rel.get("zones", [])),
            any((z.get("key") == "collaboration_zone") for z in collab.get("zones", [])),
            isinstance(perms.get("permission_verdicts"), dict),
        ]
    )


def _has_tree_actions():
    candidates = [
        _snapshot("semantic_page_project_tree_v1.json").get("semantic_page", {}),
        _snapshot("semantic_page_project_tree_kanban_actions_v1.json").get("semantic_page", {}),
    ]
    for tree in candidates:
        zones = tree.get("zones") if isinstance(tree.get("zones"), list) else []
        for zone in zones:
            for block in zone.get("blocks", []) if isinstance(zone, dict) else []:
                if block.get("type") != "relation_table_block":
                    continue
                actions = ((block.get("data") or {}).get("row_actions")) or []
                if actions and all(isinstance(item, dict) and "reason_code" in item for item in actions):
                    return True
    return False


def _has_kanban_semantics():
    kanban = _snapshot("semantic_page_project_kanban_semantics_v1.json").get("semantic_page", {})
    sem = kanban.get("kanban_semantics")
    return isinstance(sem, dict) and bool(sem.get("title_field")) and isinstance(sem.get("card_fields"), list)


def _has_search_semantics():
    search = _snapshot("semantic_page_project_search_semantics_v1.json").get("semantic_page", {})
    sem = search.get("search_semantics")
    return (
        isinstance(sem, dict)
        and isinstance(sem.get("filters"), list)
        and isinstance(sem.get("group_by"), list)
        and isinstance((sem.get("favorites") or {}).get("items"), list)
    )


def _load_view_alias_ok():
    text = LOAD_CONTRACT.read_text(encoding="utf-8") if LOAD_CONTRACT.exists() else ""
    return "def aliases" in text and "load_view" in text


def _has_button_gate():
    text = LOAD_CONTRACT.read_text(encoding="utf-8") if LOAD_CONTRACT.exists() else ""
    return "def _with_action_gate(" in text and "action_gating" in text


def _has_relation_items():
    rel = _snapshot("semantic_page_project_form_x2many_editable_v1.json").get("semantic_page", {})
    zones = rel.get("zones") if isinstance(rel.get("zones"), list) else []
    for zone in zones:
        for block in zone.get("blocks", []) if isinstance(zone, dict) else []:
            items = ((block.get("data") or {}).get("items")) or []
            if items and isinstance(items, list):
                return True
    return False


def _evaluate_case(case_key: str):
    checks = {
        "project.project_form_complex": _has_case01,
        "project.project_tree": _has_tree_actions,
        "project.project_kanban": _has_kanban_semantics,
        "project.project_search": _has_search_semantics,
        "load_view_form_only": _load_view_alias_ok,
        "load_view_non_form_gap": _load_view_alias_ok,
        "button_semantics_cross_path": _has_button_gate,
        "relation_x2many_contract": _has_relation_items,
    }
    fn = checks.get(case_key)
    if not fn:
        return False
    return bool(fn())


def main() -> int:
    case_files = sorted(CASES_DIR.glob("case_*.json"))
    rows = []
    pass_count = 0

    for file in case_files:
        payload = _load(file)
        case_key = str(payload.get("case") or "")
        baseline_status = str(payload.get("status") or "unknown")
        ok = _evaluate_case(case_key)
        current_status = "pass" if ok else "gap"
        if ok:
            pass_count += 1
        rows.append(
            {
                "case": case_key,
                "baseline_status": baseline_status,
                "current_status": current_status,
                "improved": baseline_status != "pass" and current_status == "pass",
            }
        )

    total = len(rows)
    report = {
        "ok": pass_count == total and total > 0,
        "summary": {
            "case_count": total,
            "pass_count": pass_count,
            "gap_count": total - pass_count,
            "pass_ratio": round(pass_count / total, 4) if total else 0.0,
        },
        "rows": rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Native View Sample Compare Report",
        "",
        f"- ok: {report['ok']}",
        f"- case_count: {report['summary']['case_count']}",
        f"- pass_count: {report['summary']['pass_count']}",
        f"- gap_count: {report['summary']['gap_count']}",
        f"- pass_ratio: {report['summary']['pass_ratio']}",
        "",
        "## Cases",
    ]
    for row in rows:
        lines.append(
            f"- {row['case']}: baseline={row['baseline_status']} -> current={row['current_status']} improved={row['improved']}"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    print("[native_view_sample_compare_report] PASS" if report["ok"] else "[native_view_sample_compare_report] WARN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
