#!/usr/bin/env python3
"""Guard the wx_mini Lite compiled runtime artifact acceptance pilot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MOBILE_ROOT = ROOT / "frontend/apps/mobile"
DIST_ROOT = MOBILE_ROOT / "dist/build/mp-weixin"
APP_JSON = DIST_ROOT / "app.json"
PROJECT_CONFIG = DIST_ROOT / "project.config.json"
MAKEFILE_PATH = ROOT / "Makefile"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    observations: list[str] = []
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""

    if "verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host")

    compile_result: dict[str, Any] | None = None
    if args.execute and not errors:
        completed = subprocess.run(
            ["pnpm", "-C", str(MOBILE_ROOT), "build:mp-weixin"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
        compile_result = {
            "returnCode": completed.returncode,
            "outputTail": completed.stdout[-4000:],
        }
        if completed.returncode != 0:
            errors.append("wx_mini compile command failed before runtime artifact acceptance")

    required_files = [
        APP_JSON,
        PROJECT_CONFIG,
        DIST_ROOT / "app.js",
        DIST_ROOT / "app.wxss",
        DIST_ROOT / "App.wxml",
        DIST_ROOT / "common/vendor.js",
        DIST_ROOT / "pages/contract/index.js",
        DIST_ROOT / "pages/contract/index.json",
        DIST_ROOT / "pages/contract/index.wxml",
        DIST_ROOT / "pages/contract/index.wxss",
    ]
    for path in required_files:
        if path.exists():
            observations.append(f"artifact exists: {path.relative_to(ROOT).as_posix()}")
        else:
            errors.append(f"missing compiled artifact: {path.relative_to(ROOT).as_posix()}")

    app_json = read_json(APP_JSON) if APP_JSON.exists() else {}
    pages = app_json.get("pages") if isinstance(app_json, dict) else None
    if not isinstance(pages, list) or "pages/contract/index" not in pages:
        errors.append("app.json must register pages/contract/index")
    window = app_json.get("window") if isinstance(app_json, dict) else None
    if not isinstance(window, dict) or not window.get("navigationBarTitleText"):
        errors.append("app.json must include a window navigation title")

    report = {
        "ok": not errors,
        "clientType": "wx_mini",
        "decision": "wx_mini_runtime_artifact_acceptance_pilot_passed" if not errors else "blocked",
        "executeRequested": args.execute,
        "compileResult": compile_result,
        "distRoot": DIST_ROOT.relative_to(ROOT).as_posix(),
        "registeredPages": pages if isinstance(pages, list) else [],
        "observations": observations,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite wx_mini runtime artifact acceptance pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite wx_mini runtime artifact acceptance pilot passed")
    print("- decision: wx_mini_runtime_artifact_acceptance_pilot_passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
