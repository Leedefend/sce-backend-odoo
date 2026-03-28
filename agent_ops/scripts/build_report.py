#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import LAST_RUN_PATH, REPORTS_DIR, load_json, load_task, repo_relative, today_str


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a markdown report from the latest iteration state.")
    parser.add_argument("task", help="Task yaml path")
    args = parser.parse_args()

    task_path, task = load_task(args.task)
    run = load_json(LAST_RUN_PATH, default={})
    report_day = today_str()
    report_dir = REPORTS_DIR / report_day
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report.{task['task_id']}.md"

    classification = run.get("classification", {})
    risk_scan = run.get("risk_scan", {})
    verify = run.get("verify", {})
    validate = run.get("validate", {})

    lines = [
        f"# Iteration Report: {task['task_id']}",
        "",
        f"- task: `{repo_relative(task_path)}`",
        f"- title: `{task.get('title', '')}`",
        f"- layer target: `{task.get('architecture', {}).get('layer_target', '')}`",
        f"- module: `{task.get('architecture', {}).get('module', '')}`",
        f"- reason: `{task.get('architecture', {}).get('reason', '')}`",
        f"- classification: `{classification.get('classification', 'UNKNOWN')}`",
        f"- report source: `{repo_relative(LAST_RUN_PATH)}`",
        f"- validation passed: `{validate.get('passed', False)}`",
        f"- verification passed: `{verify.get('passed', False)}`",
        "",
        "## Goal",
        "",
        task.get("goal", ""),
        "",
        "## User Visible Outcome",
        "",
    ]
    for item in task.get("user_visible_outcome", []):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Verification",
            "",
        ]
    )
    for result in verify.get("results", []):
        state = "PASS" if result.get("exit_code") == 0 else "FAIL"
        lines.append(f"- `{state}` `{result.get('command')}`")
        stderr = (result.get("stderr") or "").strip()
        if stderr:
            lines.append(f"  stderr: `{stderr[:200]}`")

    lines.extend(
        [
            "",
            "## Risk Scan",
            "",
            f"- risk_level: `{risk_scan.get('risk_level', 'unknown')}`",
            f"- stop_required: `{risk_scan.get('stop_required', False)}`",
            f"- matched_rules: `{', '.join(risk_scan.get('matched_rules', [])) or 'none'}`",
            f"- changed_files: `{len(risk_scan.get('changed_files', []))}`",
            f"- added_lines: `{risk_scan.get('diff_summary', {}).get('added_lines', 0)}`",
            f"- removed_lines: `{risk_scan.get('diff_summary', {}).get('removed_lines', 0)}`",
            "",
            "## Changed Files",
            "",
        ]
    )
    for path in risk_scan.get("changed_files", []):
        lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## Risk Evidence",
            "",
            f"- critical_hits: `{len(risk_scan.get('critical_hits', []))}`",
            f"- high_risk_hits: `{len(risk_scan.get('high_risk_hits', []))}`",
            f"- sensitive_pattern_hits: `{', '.join(risk_scan.get('sensitive_pattern_hits', [])) or 'none'}`",
        ]
    )

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- classification: `{classification.get('classification', 'UNKNOWN')}`",
            f"- reasons: `{', '.join(classification.get('reasons', [])) or 'none'}`",
            f"- triggered_stop_conditions: `{', '.join(classification.get('triggered_stop_conditions', [])) or 'none'}`",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
