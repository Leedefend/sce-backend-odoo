#!/usr/bin/env python3
"""Guard the harmony_h5 device/container acceptance pilot environment."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DIST_ROOT = ROOT / "frontend/apps/mobile/dist/build/h5"
INDEX_HTML = DIST_ROOT / "index.html"
MAKEFILE_PATH = ROOT / "Makefile"

RUNNER_ENV = ("HARMONY_HDC", "HARMONY_DEVTOOLS_CLI", "DEVECO_CLI")
PATH_COMMANDS = ("hdc", "deveco", "deveco-studio")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def find_runner() -> str | None:
    for env_name in RUNNER_ENV:
        value = os.environ.get(env_name)
        if value and Path(value).exists():
            return value
    for command in PATH_COMMANDS:
        value = shutil.which(command)
        if value:
            return value
    return None


def run_runner_probe(runner: str, project_path: Path) -> dict[str, Any]:
    commands = ([runner, "version"], [runner, "--version"], [runner, "-v"])
    last: subprocess.CompletedProcess[str] | None = None
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        last = completed
        if completed.returncode == 0:
            return {
                "command": command,
                "returnCode": completed.returncode,
                "outputTail": completed.stdout[-2000:],
                "projectPath": project_path.relative_to(ROOT).as_posix(),
            }
    assert last is not None
    return {
        "command": commands[-1],
        "returnCode": last.returncode,
        "outputTail": last.stdout[-2000:],
        "projectPath": project_path.relative_to(ROOT).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--probe-runner", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    observations: list[str] = []
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    if "verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host")

    if INDEX_HTML.exists():
        observations.append(f"artifact exists: {INDEX_HTML.relative_to(ROOT).as_posix()}")
        index_html = read_text(INDEX_HTML)
        if 'id="app"' not in index_html:
            errors.append("H5 index.html must include app mount node")
        if "/assets/" not in index_html:
            errors.append("H5 index.html must reference compiled assets")
    else:
        errors.append(f"missing compiled artifact: {INDEX_HTML.relative_to(ROOT).as_posix()}")

    asset_dir = DIST_ROOT / "assets"
    asset_files = [path.name for path in asset_dir.iterdir()] if asset_dir.exists() else []
    if not any(name.startswith("index-") and name.endswith(".js") for name in asset_files):
        errors.append("missing compiled H5 index JavaScript asset")
    if not any(name.startswith("pages-contract-index.") and name.endswith(".js") for name in asset_files):
        errors.append("missing compiled H5 contract page JavaScript asset")
    if not any(name.startswith("pages-login-index.") and name.endswith(".js") for name in asset_files):
        errors.append("missing compiled H5 login page JavaScript asset")
    if not any(name.startswith("pages-home-index.") and name.endswith(".js") for name in asset_files):
        errors.append("missing compiled H5 home page JavaScript asset")

    runner = find_runner()
    runner_probe: dict[str, Any] | None = None
    if runner:
        observations.append(f"harmony device runner found: {runner}")
        if args.probe_runner:
            runner_probe = run_runner_probe(runner, DIST_ROOT)
            if runner_probe.get("returnCode") != 0:
                errors.append("harmony device runner probe failed")
    else:
        observations.append("harmony device runner missing")

    if errors:
        decision = "harmony_h5_device_acceptance_pilot_failed"
        ok = False
    elif runner:
        decision = "harmony_h5_device_acceptance_runner_ready_manual_device_pending"
        ok = True
    else:
        decision = "harmony_h5_device_acceptance_pilot_blocked_missing_harmony_runner"
        ok = True

    report = {
        "ok": ok,
        "clientType": "harmony_h5",
        "decision": decision,
        "distRoot": DIST_ROOT.relative_to(ROOT).as_posix(),
        "deviceRunner": runner,
        "runnerProbe": runner_probe,
        "observations": observations,
        "errors": errors,
    }
    write_report(args.report, report)

    if not ok:
        print("Unified Semantic Page Contract Lite harmony_h5 device acceptance pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite harmony_h5 device acceptance pilot checked")
    print(f"- decision: {decision}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
