#!/usr/bin/env python3
"""Guard the wx_mini device acceptance pilot environment."""

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
DIST_ROOT = ROOT / "frontend/apps/mobile/dist/build/mp-weixin"
APP_JSON = DIST_ROOT / "app.json"
PROJECT_CONFIG = DIST_ROOT / "project.config.json"
MAKEFILE_PATH = ROOT / "Makefile"

CLI_CANDIDATES = (
    "WECHAT_DEVTOOLS_CLI",
    "WX_DEVTOOLS_CLI",
)
PATH_COMMANDS = (
    "wechat-devtools",
    "wechatwebdevtools",
    "wxdt",
    "cli",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def find_devtools_cli() -> str | None:
    for env_name in CLI_CANDIDATES:
        value = os.environ.get(env_name)
        if value and Path(value).exists():
            return value
    for command in PATH_COMMANDS:
        value = shutil.which(command)
        if value:
            return value
    return None


def run_cli_probe(cli: str, project_path: Path) -> dict[str, Any]:
    commands = [
        [cli, "--version"],
        [cli, "-v"],
    ]
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
        if completed.returncode == 0:
            return {
                "command": command,
                "returnCode": completed.returncode,
                "outputTail": completed.stdout[-2000:],
                "projectPath": project_path.relative_to(ROOT).as_posix(),
            }
    return {
        "command": commands[-1],
        "returnCode": completed.returncode,
        "outputTail": completed.stdout[-2000:],
        "projectPath": project_path.relative_to(ROOT).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--probe-cli", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    observations: list[str] = []
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    if "verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host")

    required_files = [
        APP_JSON,
        PROJECT_CONFIG,
        DIST_ROOT / "app.js",
        DIST_ROOT / "pages/contract/index.wxml",
    ]
    for path in required_files:
        if path.exists():
            observations.append(f"artifact exists: {path.relative_to(ROOT).as_posix()}")
        else:
            errors.append(f"missing compiled artifact: {path.relative_to(ROOT).as_posix()}")

    app_json = read_json(APP_JSON) if APP_JSON.exists() else {}
    pages = app_json.get("pages") if isinstance(app_json, dict) else []
    if "pages/contract/index" not in pages:
        errors.append("app.json must register pages/contract/index")

    cli = find_devtools_cli()
    cli_probe: dict[str, Any] | None = None
    if cli:
        observations.append(f"wechat devtools cli found: {cli}")
        if args.probe_cli:
            cli_probe = run_cli_probe(cli, DIST_ROOT)
            if cli_probe.get("returnCode") != 0:
                errors.append("wechat devtools cli probe failed")
    else:
        observations.append("wechat devtools cli missing")

    if errors:
        decision = "wx_mini_device_acceptance_pilot_failed"
        ok = False
    elif cli:
        decision = "wx_mini_device_acceptance_runner_ready_manual_device_pending"
        ok = True
    else:
        decision = "wx_mini_device_acceptance_pilot_blocked_missing_wechat_devtools_cli"
        ok = True

    report = {
        "ok": ok,
        "clientType": "wx_mini",
        "decision": decision,
        "distRoot": DIST_ROOT.relative_to(ROOT).as_posix(),
        "registeredPages": pages,
        "devtoolsCli": cli,
        "cliProbe": cli_probe,
        "observations": observations,
        "errors": errors,
    }
    write_report(args.report, report)

    if not ok:
        print("Unified Semantic Page Contract Lite wx_mini device acceptance pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite wx_mini device acceptance pilot checked")
    print(f"- decision: {decision}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
