#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_governance_history_archive_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(item, ensure_ascii=False) for item in rows)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _git_short_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, timeout=5)
        return _text(out)
    except Exception:
        return "unknown"


def _snapshot_summary(report: dict) -> dict:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return {
        "queue_policy_aligned": bool(summary.get("queue_policy_aligned")),
        "consumption_policy_aligned": bool(summary.get("consumption_policy_aligned")),
        "drop_policy_aligned": bool(summary.get("drop_policy_aligned")),
        "capture_time_skew_aligned": bool(summary.get("capture_time_skew_aligned")),
        "consumption_enabled": bool(summary.get("consumption_enabled")),
        "queue_size": _safe_int(summary.get("queue_size"), 0),
        "scene_count": _safe_int(summary.get("scene_count"), 0),
        "scene_type_count": _safe_int(summary.get("scene_type_count"), 0),
    }


def _diff_summary(previous: dict, current: dict) -> dict:
    prev_metrics = previous.get("summary") if isinstance(previous.get("summary"), dict) else {}
    curr_metrics = current.get("summary") if isinstance(current.get("summary"), dict) else {}
    changed: list[dict[str, Any]] = []
    for key in sorted(set(prev_metrics.keys()) | set(curr_metrics.keys())):
        prev_value = prev_metrics.get(key)
        curr_value = curr_metrics.get(key)
        if prev_value != curr_value:
            changed.append({"key": key, "previous": prev_value, "current": curr_value})
    return {
        "changed_count": len(changed),
        "changed": changed,
    }


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_governance_history_archive_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    report_path = ROOT / _text(baseline.get("report_source"))
    history_jsonl_path = ROOT / _text(baseline.get("history_jsonl"))
    archive_dir = ROOT / _text(baseline.get("archive_dir"))
    diff_json_path = ROOT / _text(baseline.get("diff_summary_json"))
    diff_md_path = ROOT / _text(baseline.get("diff_summary_md"))
    max_history_entries = _safe_int(baseline.get("max_history_entries"), 200)

    report = _load_json(report_path)
    if not report:
        print("[scene_governance_history_archive_guard] FAIL")
        print(f" - missing or invalid source report: {report_path.relative_to(ROOT).as_posix()}")
        return 1

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    sha = _git_short_sha()
    summary = _snapshot_summary(report)
    sample = {
        "captured_at": timestamp,
        "commit": sha,
        "report_source": report_path.relative_to(ROOT).as_posix(),
        "summary": summary,
    }

    history_rows = _load_jsonl(history_jsonl_path)
    previous = history_rows[-1] if history_rows else {}
    history_rows.append(sample)
    if max_history_entries > 0 and len(history_rows) > max_history_entries:
        history_rows = history_rows[-max_history_entries:]
    _dump_jsonl(history_jsonl_path, history_rows)

    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"scene_governance_{timestamp}_{sha}.json"
    _write(archive_path, json.dumps(sample, ensure_ascii=False, indent=2) + "\n")

    diff = {
        "ok": True,
        "current": sample,
        "previous": previous,
        "diff": _diff_summary(previous, sample) if previous else {"changed_count": 0, "changed": []},
        "history_size": len(history_rows),
        "history_jsonl": history_jsonl_path.relative_to(ROOT).as_posix(),
        "archive_path": archive_path.relative_to(ROOT).as_posix(),
    }

    _write(diff_json_path, json.dumps(diff, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Scene Governance History Diff Summary",
        "",
        f"- commit: `{sha}`",
        f"- captured_at: `{timestamp}`",
        f"- history_size: `{len(history_rows)}`",
        f"- archive_path: `{archive_path.relative_to(ROOT).as_posix()}`",
        f"- changed_count: `{_safe_int(_diff_summary(previous, sample).get('changed_count'), 0) if previous else 0}`",
    ]
    if previous:
        lines.extend(["", "## Changed Metrics"])
        for row in _diff_summary(previous, sample).get("changed", []):
            if isinstance(row, dict):
                lines.append(f"- {row.get('key')}: {row.get('previous')} -> {row.get('current')}")
    _write(diff_md_path, "\n".join(lines) + "\n")

    print(archive_path)
    print(diff_json_path)
    print(diff_md_path)
    print("[scene_governance_history_archive_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

