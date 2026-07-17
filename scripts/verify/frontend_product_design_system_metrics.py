#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WEB = Path("frontend/apps/web/src")
BASELINE_REF = sys.argv[1] if len(sys.argv) > 1 else "86f9b29eb5c8866e96dbfaf32c7f496a0a159308"
OUTPUT = ROOT / "artifacts/frontend-professional/fe-pro-04/complexity-report.json"


def git_files(ref: str) -> dict[str, str]:
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", ref, str(WEB)], cwd=ROOT, text=True,
    ).splitlines()
    result: dict[str, str] = {}
    for name in names:
        if Path(name).suffix not in {".vue", ".ts", ".css"}:
            continue
        result[name] = subprocess.check_output(["git", "show", f"{ref}:{name}"], cwd=ROOT, text=True)
    return result


def worktree_files() -> dict[str, str]:
    result: dict[str, str] = {}
    root = ROOT / WEB
    for path in root.rglob("*"):
        if path.suffix in {".vue", ".ts", ".css"}:
            result[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8", errors="ignore")
    return result


def metric(files: dict[str, str]) -> dict[str, object]:
    vue = {name: text for name, text in files.items() if name.endswith(".vue")}
    line_counts = {name: len(text.splitlines()) for name, text in vue.items()}
    largest = max(line_counts.items(), key=lambda row: row[1])
    design_prefix = f"{WEB.as_posix()}/components/design-system/"

    def implementation_count(pattern: str) -> int:
        regex = re.compile(pattern, re.IGNORECASE)
        return sum(bool(regex.search(text)) for name, text in vue.items() if not name.startswith(design_prefix))

    legacy_candidates = [
        f"{WEB}/views/RecordView.vue",
        f"{WEB}/pages/ModelFormPage.vue",
        f"{WEB}/views/WorkbenchView.vue",
    ]
    return {
        "vue_component_count": len(vue),
        "vue_over_600": sum(lines > 600 for lines in line_counts.values()),
        "vue_over_1000": sum(lines > 1000 for lines in line_counts.values()),
        "largest_vue": {"path": largest[0], "lines": largest[1]},
        "named_design_components": sum(name.startswith(design_prefix) and name.endswith(".vue") for name in files),
        "inline_style_literals": sum(len(re.findall(r"\sstyle\s*=\s*['\"]", text)) for text in files.values()),
        "hardcoded_colors": sum(len(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", text)) for text in files.values()),
        "model_specific_css": sum(len(re.findall(r"\.(?:project|contract|settlement|payment)[-_][\w-]+\s*\{", text)) for text in files.values()),
        "wide_global_is_selectors": sum(text.count(":is(") for text in files.values()),
        "raw_button_implementation_files": implementation_count(r"<button\b"),
        "raw_status_implementation_files": implementation_count(r"class\s*=\s*['\"][^'\"]*(?:status|badge)"),
        "raw_dialog_implementation_files": implementation_count(r"<dialog\b|role\s*=\s*['\"]dialog['\"]"),
        "money_formatter_files": sum(bool(re.search(r"Intl\.NumberFormat|function\s+format(?:Money|Amount)", text)) for text in files.values()),
        "legacy_entry_candidates": sum(name in files for name in legacy_candidates),
        "tracked_files": len(files),
    }


def main() -> int:
    baseline = metric(git_files(BASELINE_REF))
    current = metric(worktree_files())
    report = {
        "schema_version": "frontend_product_design_system_complexity.v1",
        "baseline_ref": BASELINE_REF,
        "baseline": baseline,
        "current": current,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = []
    for key in ["hardcoded_colors", "model_specific_css"]:
        if current[key] > baseline[key]:
            failures.append(f"{key} increased: {baseline[key]} -> {current[key]}")
    if current["wide_global_is_selectors"] >= baseline["wide_global_is_selectors"]:
        failures.append(
            f"wide_global_is_selectors did not decrease: {baseline['wide_global_is_selectors']} -> {current['wide_global_is_selectors']}"
        )
    if current["largest_vue"]["lines"] >= baseline["largest_vue"]["lines"]:
        failures.append("largest Vue file did not decrease")
    if failures:
        print("[frontend_product_design_system_metrics] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("[frontend_product_design_system_metrics] PASS")
    print(json.dumps({"baseline": baseline, "current": current}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
