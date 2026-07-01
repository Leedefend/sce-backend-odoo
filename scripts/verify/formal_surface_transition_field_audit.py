# -*- coding: utf-8 -*-
"""Audit transition fields that still appear in formal product surfaces.

This guard intentionally starts as a budgeted debt gate: the current debt is
recorded in a baseline, and the check fails when new transition fields enter
formal surfaces or when existing budgets increase. As fields are formalized,
the baseline should only move downward.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts/verify/baselines/formal_surface_transition_field_budget_v1.json"
OUT_JSON = ROOT / "artifacts/backend/formal_surface_transition_field_audit.json"
OUT_CSV = ROOT / "artifacts/backend/formal_surface_transition_field_audit_rows.csv"

TRANSITION_PATTERNS = {
    "p1_visible": re.compile(r"\bp1_visible_[A-Za-z0-9_]+\b"),
    "legacy_visible": re.compile(r"\blegacy_visible_[A-Za-z0-9_]+\b"),
    "legacy_attachment_ref": re.compile(r"\blegacy_attachment_ref\b"),
    "legacy_line_attachment_ref": re.compile(r"\blegacy_line_attachment_ref\b"),
    "legacy_attachment_name": re.compile(r"\blegacy_attachment_name\b"),
    "legacy_attachment_path": re.compile(r"\blegacy_attachment_path\b"),
    "creator_legacy_user_id": re.compile(r"\bcreator_legacy_user_id\b"),
    "legacy_residual_reason": re.compile(r"\blegacy_residual_reason\b"),
    "accepted_visible": re.compile(r"\baccepted_visible_[A-Za-z0-9_]+\b"),
    "user_acceptance": re.compile(r"\buser_acceptance_[A-Za-z0-9_]+\b"),
    "codex_sentinel": re.compile(r"\bCODEX_[A-Za-z0-9_]+\b"),
}

SCAN_PATHS = {
    "formal_core_model": [
        "addons/smart_construction_core/models/core",
    ],
    "formal_projection_model": [
        "addons/smart_construction_core/models/projection",
    ],
    "formal_core_view": [
        "addons/smart_construction_core/views/core",
    ],
    "formal_confirmed_view": [
        "addons/smart_construction_core/views/support/user_confirmed_formal_form_views.xml",
        "addons/smart_construction_core/views/support/user_confirmed_formal_list_views.xml",
        "addons/smart_construction_core/views/support/user_confirmed_formal_list_alignment_views.xml",
        "addons/smart_construction_core/views/menu_user_acceptance_cleanup.xml",
    ],
    "formal_config_contract": [
        "addons/smart_construction_core/data/business_category_seed.xml",
        "addons/smart_construction_core/data/view_orchestration_contract_generated_data.xml",
        "addons/smart_construction_core/data/view_orchestration_contract_data.xml",
        "addons/smart_construction_core/data/view_orchestration_form_section_contract_data.xml",
        "addons/smart_construction_core/data/p1_daily_business_form_orchestration_contract_data.xml",
    ],
}

INTERNAL_ALLOWED_PATH_PARTS = (
    "/models/support/",
    "/views/support/legacy_",
    "/views/support/p1_daily_business_visible_alias_views.xml",
    "/views/support/audit_",
)


def _iter_files(path: Path):
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for child in sorted(path.rglob("*")):
        if child.suffix in {".py", ".xml", ".json", ".csv"} and child.is_file():
            yield child


def _line_category(relative_path: str) -> str:
    normalized = "/" + relative_path.replace("\\", "/")
    if any(part in normalized for part in INTERNAL_ALLOWED_PATH_PARTS):
        return "internal_allowed"
    for category, paths in SCAN_PATHS.items():
        for item in paths:
            if relative_path == item or relative_path.startswith(item.rstrip("/") + "/"):
                return category
    return "unscanned"


def _scan():
    rows = []
    scanned_roots = [Path(item) for paths in SCAN_PATHS.values() for item in paths]
    seen_files: set[Path] = set()
    for root_item in scanned_roots:
        for path in _iter_files(ROOT / root_item):
            if path in seen_files:
                continue
            seen_files.add(path)
            relative_path = path.relative_to(ROOT).as_posix()
            category = _line_category(relative_path)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line_no, line in enumerate(lines, start=1):
                for prefix, pattern in TRANSITION_PATTERNS.items():
                    for match in pattern.finditer(line):
                        rows.append({
                            "category": category,
                            "prefix": prefix,
                            "field": match.group(0),
                            "path": relative_path,
                            "line": line_no,
                        })
    return rows


def _summary(rows):
    by_category_prefix = Counter((row["category"], row["prefix"]) for row in rows)
    by_prefix = Counter(row["prefix"] for row in rows)
    by_category = Counter(row["category"] for row in rows)
    files = sorted({row["path"] for row in rows})
    return {
        "total_hits": len(rows),
        "by_prefix": dict(sorted(by_prefix.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_category_prefix": {
            "%s.%s" % (category, prefix): count
            for (category, prefix), count in sorted(by_category_prefix.items())
        },
        "files": files,
    }


def _load_baseline():
    if not BASELINE.exists():
        return {"budgets": {}, "forbidden_new_prefixes": []}
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _evaluate(report, baseline):
    failures = []
    budgets = baseline.get("budgets") if isinstance(baseline.get("budgets"), dict) else {}
    actual = report["summary"]["by_category_prefix"]
    for key, budget in sorted(budgets.items()):
        count = int(actual.get(key, 0) or 0)
        limit = int(budget)
        if count > limit:
            failures.append({
                "kind": "budget_increase",
                "key": key,
                "actual": count,
                "budget": limit,
            })
    for key, count in sorted(actual.items()):
        if key not in budgets and int(count or 0) > 0:
            failures.append({
                "kind": "new_transition_surface",
                "key": key,
                "actual": int(count),
                "budget": 0,
            })
    return failures


def _write_csv(rows):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8") as handle:
        handle.write("category,prefix,field,path,line\n")
        for row in rows:
            handle.write(
                "%s,%s,%s,%s,%s\n"
                % (
                    row["category"],
                    row["prefix"],
                    row["field"],
                    row["path"],
                    row["line"],
                )
            )


def main():
    rows = _scan()
    report = {
        "mode": "formal_surface_transition_field_audit",
        "boundary": {
            "formal_surfaces": sorted(SCAN_PATHS),
            "forbidden_transition_prefixes": sorted(TRANSITION_PATTERNS),
            "policy": "transition fields may remain in internal audit/migration carriers, but must not increase in formal product surfaces",
            "stabilization_rule": "budgets should only move downward as fields are promoted to formal model/view names",
        },
        "summary": _summary(rows),
        "rows": rows[:1000],
    }
    baseline = _load_baseline()
    failures = _evaluate(report, baseline)
    report["baseline"] = {
        "path": BASELINE.relative_to(ROOT).as_posix(),
        "budgets": baseline.get("budgets", {}),
    }
    report["failures"] = failures
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(rows)
    status = "FAIL" if failures else "PASS"
    print(
        "[formal_surface_transition_field_audit] %s total=%s files=%s failures=%s"
        % (status, report["summary"]["total_hits"], len(report["summary"]["files"]), len(failures))
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"failures": failures[:50]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
