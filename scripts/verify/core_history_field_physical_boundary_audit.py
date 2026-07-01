#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit physical history/user-data carriers that remain in core models.

The formal surface audit proves transition fields do not leak into released
views or configuration contracts. This audit is stricter: it tracks textual
history-field carriers still defined or referenced inside core/projection
models so the remaining physical coupling can only move downward.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts/verify/baselines/core_history_field_physical_boundary_budget_v1.json"
OUT_JSON = ROOT / "artifacts/backend/core_history_field_physical_boundary_audit.json"
OUT_CSV = ROOT / "artifacts/backend/core_history_field_physical_boundary_audit_rows.csv"

SCAN_PATHS = {
    "core_model": "addons/smart_construction_core/models/core",
    "projection_model": "addons/smart_construction_core/models/projection",
}

MARKERS = {
    "legacy_visible": re.compile(r"legacy_visible"),
    "legacy_visible_constructed": re.compile(
        r"(legacy_[\"']\s*\+\s*[\"']visible|[\"']legacy_%s_%s[\"']\s*%\s*\(\s*[\"']vis(?:ible|[\"']\s*\+\s*[\"']ible))"
    ),
    "user_acceptance": re.compile(r"user_acceptance"),
    "accepted_visible": re.compile(r"accepted_visible"),
    "p1_visible": re.compile(r"p1_visible"),
    "creator_legacy_user_id": re.compile(r"creator_legacy_user_id"),
    "legacy_residual_reason": re.compile(r"legacy_residual_reason"),
}


def _iter_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _scan():
    rows = []
    for category, relative_root in SCAN_PATHS.items():
        for path in _iter_files(ROOT / relative_root):
            relative_path = path.relative_to(ROOT).as_posix()
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line_no, line in enumerate(lines, start=1):
                for marker, pattern in MARKERS.items():
                    if pattern.search(line):
                        rows.append(
                            {
                                "category": category,
                                "marker": marker,
                                "path": relative_path,
                                "line": line_no,
                                "text": line.strip()[:240],
                            }
                        )
    return rows


def _summary(rows):
    by_marker = Counter(row["marker"] for row in rows)
    by_category = Counter(row["category"] for row in rows)
    by_category_marker = Counter((row["category"], row["marker"]) for row in rows)
    by_file = Counter(row["path"] for row in rows)
    return {
        "total_hits": len(rows),
        "by_marker": dict(sorted(by_marker.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_category_marker": {
            f"{category}.{marker}": count
            for (category, marker), count in sorted(by_category_marker.items())
        },
        "by_file": dict(sorted(by_file.items())),
    }


def _load_baseline():
    if not BASELINE.exists():
        return {"budgets": {}}
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _evaluate(summary, baseline):
    failures = []
    budgets = baseline.get("budgets") if isinstance(baseline.get("budgets"), dict) else {}
    actual = {
        "total_hits": summary["total_hits"],
        **summary["by_category_marker"],
    }
    for key, budget in sorted(budgets.items()):
        count = int(actual.get(key, 0) or 0)
        limit = int(budget)
        if count > limit:
            failures.append(
                {
                    "kind": "physical_history_field_budget_increase",
                    "key": key,
                    "actual": count,
                    "budget": limit,
                }
            )
    for key, count in sorted(actual.items()):
        if key not in budgets and int(count or 0) > 0:
            failures.append(
                {
                    "kind": "new_physical_history_field_marker",
                    "key": key,
                    "actual": int(count),
                    "budget": 0,
                }
            )
    return failures


def _write_csv(rows):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8") as handle:
        handle.write("category,marker,path,line,text\n")
        for row in rows:
            text = row["text"].replace('"', '""')
            handle.write(
                f'{row["category"]},{row["marker"]},{row["path"]},{row["line"]},"{text}"\n'
            )


def main():
    rows = _scan()
    summary = _summary(rows)
    baseline = _load_baseline()
    failures = _evaluate(summary, baseline)
    report = {
        "mode": "core_history_field_physical_boundary_audit",
        "boundary": {
            "policy": "history/user-data carriers may not increase inside smart_construction_core core/projection models",
            "target": "move remaining user/history storage toward smart_construction_custom or support/history carriers while keeping core formal fields stable",
            "scan_paths": SCAN_PATHS,
            "markers": sorted(MARKERS),
        },
        "summary": summary,
        "baseline": {
            "path": BASELINE.relative_to(ROOT).as_posix(),
            "budgets": baseline.get("budgets", {}),
        },
        "failures": failures,
        "rows": rows[:1000],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(rows)
    status = "FAIL" if failures else "PASS"
    print(
        "[core_history_field_physical_boundary_audit] %s total=%s failures=%s"
        % (status, summary["total_hits"], len(failures))
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"failures": failures[:50]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
