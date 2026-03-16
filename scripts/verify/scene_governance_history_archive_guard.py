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


def _git_branch() -> str:
    try:
        out = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True, timeout=5)
        return _text(out) or "unknown"
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
    index_json_path = ROOT / _text(baseline.get("index_json") or "artifacts/backend/history/scene_governance_index.json")
    index_md_path = ROOT / _text(baseline.get("index_md") or "artifacts/backend/history/scene_governance_index.md")
    diff_json_path = ROOT / _text(baseline.get("diff_summary_json"))
    diff_md_path = ROOT / _text(baseline.get("diff_summary_md"))
    max_history_entries = _safe_int(baseline.get("max_history_entries"), 200)
    max_index_entries = _safe_int(baseline.get("max_index_entries"), 400)

    report = _load_json(report_path)
    if not report:
        print("[scene_governance_history_archive_guard] FAIL")
        print(f" - missing or invalid source report: {report_path.relative_to(ROOT).as_posix()}")
        return 1

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    sha = _git_short_sha()
    branch = _git_branch()
    summary = _snapshot_summary(report)
    sample = {
        "captured_at": timestamp,
        "commit": sha,
        "branch": branch,
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

    index_payload = _load_json(index_json_path)
    index_entries = index_payload.get("entries") if isinstance(index_payload.get("entries"), list) else []
    branch_map = index_payload.get("branches") if isinstance(index_payload.get("branches"), dict) else {}
    index_entries.append(
        {
            "captured_at": timestamp,
            "branch": branch,
            "commit": sha,
            "archive_path": archive_path.relative_to(ROOT).as_posix(),
            "history_sample_source": history_jsonl_path.relative_to(ROOT).as_posix(),
        }
    )
    if max_index_entries > 0 and len(index_entries) > max_index_entries:
        index_entries = index_entries[-max_index_entries:]
    branch_map[branch] = {
        "latest_commit": sha,
        "latest_captured_at": timestamp,
        "latest_archive_path": archive_path.relative_to(ROOT).as_posix(),
    }
    index_payload = {
        "entries": index_entries,
        "branches": branch_map,
        "summary": {
            "entry_count": len(index_entries),
            "branch_count": len(branch_map),
        },
    }
    _write(index_json_path, json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n")
    index_lines = [
        "# Scene Governance History Index",
        "",
        f"- entry_count: `{len(index_entries)}`",
        f"- branch_count: `{len(branch_map)}`",
        "",
        "## Branch Latest",
    ]
    for branch_key in sorted(branch_map.keys()):
        row = branch_map.get(branch_key) if isinstance(branch_map.get(branch_key), dict) else {}
        index_lines.append(
            f"- {branch_key}: commit={row.get('latest_commit')} captured_at={row.get('latest_captured_at')}"
        )
    _write(index_md_path, "\n".join(index_lines) + "\n")

    diff = {
        "ok": True,
        "current": sample,
        "previous": previous,
        "diff": _diff_summary(previous, sample) if previous else {"changed_count": 0, "changed": []},
        "history_size": len(history_rows),
        "history_jsonl": history_jsonl_path.relative_to(ROOT).as_posix(),
        "archive_path": archive_path.relative_to(ROOT).as_posix(),
        "index_json": index_json_path.relative_to(ROOT).as_posix(),
        "index_md": index_md_path.relative_to(ROOT).as_posix(),
    }

    _write(diff_json_path, json.dumps(diff, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Scene Governance History Diff Summary",
        "",
        f"- commit: `{sha}`",
        f"- branch: `{branch}`",
        f"- captured_at: `{timestamp}`",
        f"- history_size: `{len(history_rows)}`",
        f"- archive_path: `{archive_path.relative_to(ROOT).as_posix()}`",
        f"- index_json: `{index_json_path.relative_to(ROOT).as_posix()}`",
        f"- index_md: `{index_md_path.relative_to(ROOT).as_posix()}`",
        f"- changed_count: `{_safe_int(_diff_summary(previous, sample).get('changed_count'), 0) if previous else 0}`",
    ]
    if previous:
        lines.extend(["", "## Changed Metrics"])
        for row in _diff_summary(previous, sample).get("changed", []):
            if isinstance(row, dict):
                lines.append(f"- {row.get('key')}: {row.get('previous')} -> {row.get('current')}")
    _write(diff_md_path, "\n".join(lines) + "\n")

    print(archive_path)
    print(index_json_path)
    print(index_md_path)
    print(diff_json_path)
    print(diff_md_path)
    print("[scene_governance_history_archive_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
