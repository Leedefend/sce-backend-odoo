#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
AGENT_OPS = ROOT / "agent_ops"
STATE_DIR = AGENT_OPS / "state"
REPORTS_DIR = AGENT_OPS / "reports"
TASK_RESULTS_DIR = STATE_DIR / "task_results"
LAST_RUN_PATH = STATE_DIR / "last_run.json"
ITERATION_CURSOR_PATH = STATE_DIR / "iteration_cursor.json"


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_command(command: str, cwd: Path | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def git(*args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def pattern_roots(patterns: Iterable[str]) -> list[str]:
    roots: set[str] = set()
    for pattern in patterns:
        normalized = pattern.replace("\\", "/").strip()
        if not normalized:
            continue
        literal_parts = []
        for part in normalized.split("/"):
            if any(token in part for token in ("*", "?", "[")):
                break
            literal_parts.append(part)
        if literal_parts:
            roots.add("/".join(literal_parts))
    return sorted(roots)


def parse_status_paths(status_output: str) -> list[str]:
    names = set()
    for line in status_output.splitlines():
        match = re.match(r"^[ MARCUD?!]{2} (.+)$", line)
        if not match:
            continue
        path = match.group(1).strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            names.add(path)
    return sorted(names)


def changed_files(monitored_roots: Iterable[str]) -> list[str]:
    roots = list(monitored_roots)
    output = git("status", "--short", "--untracked-files=all", "--", *roots, check=False)
    return parse_status_paths(output)


def diff_numstat(monitored_roots: Iterable[str], changed: Iterable[str]) -> tuple[int, int]:
    roots = list(monitored_roots)
    added = 0
    removed = 0
    output = git("diff", "--numstat", "--", *roots, check=False)
    if output:
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                if parts[0].isdigit():
                    added += int(parts[0])
                if parts[1].isdigit():
                    removed += int(parts[1])
    output_cached = git("diff", "--cached", "--numstat", "--", *roots, check=False)
    if output_cached:
        for line in output_cached.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                if parts[0].isdigit():
                    added += int(parts[0])
                if parts[1].isdigit():
                    removed += int(parts[1])
    tracked = set()
    for blob in (output, output_cached):
        for line in blob.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                tracked.add(parts[2].strip())
    for path in changed:
        if path in tracked:
            continue
        file_path = ROOT / path
        if file_path.exists() and file_path.is_file():
            added += file_path.read_text(encoding="utf-8").count("\n") + 1
    return added, removed


def match_any(path: str, patterns: Iterable[str]) -> bool:
    from fnmatch import fnmatch

    normalized = path.replace("\\", "/")
    return any(fnmatch(normalized, pattern) for pattern in patterns)


def task_result_path(task_id: str) -> Path:
    return TASK_RESULTS_DIR / f"{task_id}.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_str() -> str:
    return date.today().isoformat()


def load_task(task_arg: str) -> tuple[Path, dict[str, Any]]:
    task_path = Path(task_arg)
    if not task_path.is_absolute():
        task_path = ROOT / task_arg
    task_path = task_path.resolve()
    payload = load_yaml(task_path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Task payload must be a mapping: {repo_relative(task_path)}")
    return task_path, payload


def save_last_run(payload: dict[str, Any]) -> None:
    dump_json(LAST_RUN_PATH, payload)
    task_id = payload.get("task_id")
    if task_id:
        dump_json(task_result_path(task_id), payload)


def stop_condition_ids() -> set[str]:
    policy = load_yaml(AGENT_OPS / "policies" / "stop_conditions.yaml") or {}
    return {
        item.get("id")
        for item in policy.get("stop_conditions", [])
        if isinstance(item, dict) and item.get("id")
    }


def fail(message: str, details: list[str] | None = None) -> None:
    payload = {"status": "FAIL", "message": message, "details": details or []}
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    sys.exit(1)
