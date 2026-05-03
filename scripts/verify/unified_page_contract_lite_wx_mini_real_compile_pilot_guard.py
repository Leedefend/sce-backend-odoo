#!/usr/bin/env python3
"""Guard the wx_mini Lite real compile pilot."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = ROOT / "frontend"
MOBILE_ROOT = FRONTEND_ROOT / "apps/mobile"
MOBILE_PACKAGE = MOBILE_ROOT / "package.json"
MOBILE_MANIFEST = MOBILE_ROOT / "src/manifest.json"
FRONTEND_LOCK = FRONTEND_ROOT / "pnpm-lock.yaml"
MOBILE_NODE_MODULES = MOBILE_ROOT / "node_modules"
MAKEFILE_PATH = ROOT / "Makefile"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_has_script(package_text: str, script_name: str) -> bool:
    try:
        package = json.loads(package_text)
    except json.JSONDecodeError:
        return False
    scripts = package.get("scripts")
    return isinstance(scripts, dict) and script_name in scripts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    observations: list[str] = []
    errors: list[str] = []
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    package_text = read_text(MOBILE_PACKAGE) if MOBILE_PACKAGE.exists() else ""
    lock_text = read_text(FRONTEND_LOCK) if FRONTEND_LOCK.exists() else ""
    pnpm_bin = shutil.which("pnpm")

    if "verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host")
    if not MOBILE_PACKAGE.exists():
        errors.append("mobile package missing: frontend/apps/mobile/package.json")
    if not MOBILE_MANIFEST.exists():
        errors.append("mobile manifest missing: frontend/apps/mobile/src/manifest.json")
    if MOBILE_PACKAGE.exists() and not package_has_script(package_text, "build:mp-weixin"):
        errors.append("mobile package missing script: build:mp-weixin")

    lock_has_mobile = "@sc/mobile" in lock_text or "apps/mobile" in lock_text
    lock_has_uniapp = "@dcloudio/uni-app" in lock_text and "@dcloudio/vite-plugin-uni" in lock_text
    deps_ready = MOBILE_NODE_MODULES.exists()
    if lock_has_mobile:
        observations.append("frontend lockfile includes mobile workspace")
    else:
        observations.append("frontend lockfile missing mobile workspace entries")
    if lock_has_uniapp:
        observations.append("frontend lockfile includes UniApp dependencies")
    else:
        observations.append("frontend lockfile missing UniApp dependencies")
    if deps_ready:
        observations.append("mobile node_modules exists")
    else:
        observations.append("mobile node_modules missing")
    if pnpm_bin:
        observations.append(f"pnpm available: {pnpm_bin}")
    else:
        observations.append("pnpm missing")

    can_execute = (
        not errors
        and pnpm_bin is not None
        and lock_has_mobile
        and lock_has_uniapp
        and deps_ready
    )

    compile_result: dict[str, Any] | None = None
    if args.execute and can_execute:
        completed = subprocess.run(
            [pnpm_bin, "-C", str(MOBILE_ROOT), "build:mp-weixin"],
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
            errors.append("wx_mini real compile command failed")

    if errors:
        decision = "wx_mini_real_compile_pilot_failed"
    elif args.execute and compile_result and compile_result.get("returnCode") == 0:
        decision = "wx_mini_real_compile_pilot_passed"
    elif not can_execute:
        decision = "wx_mini_real_compile_pilot_blocked_missing_lockfile_or_dependencies"
    else:
        decision = "wx_mini_real_compile_pilot_ready_not_executed"

    report = {
        "ok": not errors,
        "clientType": "wx_mini",
        "decision": decision,
        "executeRequested": args.execute,
        "canExecute": can_execute,
        "required": {
            "package": "frontend/apps/mobile/package.json",
            "manifest": "frontend/apps/mobile/src/manifest.json",
            "lockfileContainsMobileWorkspace": True,
            "lockfileContainsUniAppDependencies": True,
            "mobileDependenciesInstalled": True,
            "compileScript": "build:mp-weixin",
        },
        "observations": observations,
        "compileResult": compile_result,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite wx_mini real compile pilot failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite wx_mini real compile pilot checked")
    print(f"- decision: {decision}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
