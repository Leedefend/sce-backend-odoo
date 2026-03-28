#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from common import AGENT_OPS, ROOT, load_yaml, repo_relative
from diff_parser import get_changed_files

RUNTIME_EXCLUDES = {
    "agent_ops/state/last_run.json",
    "agent_ops/state/iteration_cursor.json",
    "agent_ops/state/run_iteration.lock",
}


def sorted_unique(items: list[str]) -> list[str]:
    return sorted({item for item in items if item and item not in RUNTIME_EXCLUDES})


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a dirty-baseline candidate without overwriting the canonical baseline.")
    parser.add_argument(
        "--output",
        default="agent_ops/policies/repo_dirty_baseline.candidate.yaml",
        help="Candidate yaml output path",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    current_paths = sorted_unique(get_changed_files())
    current_baseline = load_yaml(AGENT_OPS / "policies" / "repo_dirty_baseline.yaml") or {}
    baseline_paths = sorted_unique(list(current_baseline.get("known_dirty_paths", [])))

    candidate = {"known_dirty_paths": current_paths}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(candidate, handle, sort_keys=False, allow_unicode=False)

    added = sorted(set(current_paths) - set(baseline_paths))
    removed = sorted(set(baseline_paths) - set(current_paths))
    payload = {
        "status": "PASS",
        "candidate_path": repo_relative(output_path),
        "current_dirty_count": len(current_paths),
        "baseline_count": len(baseline_paths),
        "delta": {
            "added": added,
            "removed": removed,
        },
        "review_required": True,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
