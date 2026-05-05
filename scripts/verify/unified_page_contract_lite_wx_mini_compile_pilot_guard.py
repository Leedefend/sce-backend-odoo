#!/usr/bin/env python3
"""Guard the wx_mini Lite compile pilot preflight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = ROOT / "frontend"
WEB_PACKAGE = FRONTEND_ROOT / "apps/web/package.json"
MOBILE_PACKAGE = FRONTEND_ROOT / "apps/mobile/package.json"
MOBILE_MANIFEST = FRONTEND_ROOT / "apps/mobile/src/manifest.json"
MAKEFILE_PATH = ROOT / "Makefile"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    observations: list[str] = []
    errors: list[str] = []
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""

    if not WEB_PACKAGE.exists():
        errors.append("frontend web package is missing")
    if MOBILE_PACKAGE.exists():
        observations.append("mobile package exists")
    else:
        observations.append("mobile package missing: frontend/apps/mobile/package.json")
    if MOBILE_MANIFEST.exists():
        observations.append("mobile manifest exists")
    else:
        observations.append("mobile manifest missing: frontend/apps/mobile/src/manifest.json")

    if "verify.unified_page_contract.lite.wx_mini_compile_pilot.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.lite.wx_mini_compile_pilot.host")
    mobile_package_text = read_text(MOBILE_PACKAGE) if MOBILE_PACKAGE.exists() else ""
    if MOBILE_PACKAGE.exists() and '"build:mp-weixin"' not in mobile_package_text:
        errors.append("mobile package missing script: build:mp-weixin")

    workspace_files = [
        path.relative_to(ROOT).as_posix()
        for path in (
            FRONTEND_ROOT / "package.json",
            FRONTEND_ROOT / "apps/web/package.json",
            FRONTEND_ROOT / "apps/mobile/package.json",
            FRONTEND_ROOT / "packages/schema/package.json",
            FRONTEND_ROOT / "packages/sdk/package.json",
            FRONTEND_ROOT / "packages/tools/package.json",
            FRONTEND_ROOT / "packages/ui/package.json",
        )
        if path.exists()
    ]
    has_mobile_workspace = MOBILE_PACKAGE.exists() and MOBILE_MANIFEST.exists() and '"build:mp-weixin"' in mobile_package_text
    decision = (
        "wx_mini_compile_pilot_ready"
        if has_mobile_workspace and not errors
        else "wx_mini_compile_pilot_blocked_missing_uniapp_workspace"
    )

    report = {
        "ok": not errors,
        "clientType": "wx_mini",
        "decision": decision,
        "compileReady": has_mobile_workspace,
        "requiredWorkspace": {
            "package": "frontend/apps/mobile/package.json",
            "manifest": "frontend/apps/mobile/src/manifest.json",
            "compileScript": "build:mp-weixin",
        },
        "workspacePackages": workspace_files,
        "observations": observations,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite wx_mini compile pilot preflight failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite wx_mini compile pilot preflight passed")
    print(f"- decision: {decision}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
