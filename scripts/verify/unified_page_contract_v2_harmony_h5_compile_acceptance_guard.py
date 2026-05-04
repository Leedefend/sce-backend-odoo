#!/usr/bin/env python3
"""Guard the mobile v2 Harmony H5 compile acceptance path."""

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
MOBILE_CONTRACT_PAGE = MOBILE_ROOT / "src/pages/contract/index.vue"
FRONTEND_LOCK = FRONTEND_ROOT / "pnpm-lock.yaml"
MOBILE_NODE_MODULES = MOBILE_ROOT / "node_modules"
H5_DIST = MOBILE_ROOT / "dist/build/h5"
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
    page_text = read_text(MOBILE_CONTRACT_PAGE) if MOBILE_CONTRACT_PAGE.exists() else ""
    pnpm_bin = shutil.which("pnpm")

    if "verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host" not in makefile:
        errors.append("Makefile target missing: verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host")
    if not MOBILE_PACKAGE.exists():
        errors.append("mobile package missing: frontend/apps/mobile/package.json")
    if not MOBILE_MANIFEST.exists():
        errors.append("mobile manifest missing: frontend/apps/mobile/src/manifest.json")
    if not MOBILE_CONTRACT_PAGE.exists():
        errors.append("mobile v2 contract page missing: frontend/apps/mobile/src/pages/contract/index.vue")
    if MOBILE_PACKAGE.exists() and not package_has_script(package_text, "build:h5"):
        errors.append("mobile package missing script: build:h5")

    for token in (
        "ui.contract.v2",
        "delivery_profile: 'mobile_compact'",
        "isRemoteSearchableMany2OneField",
        "executeStandardFormAction",
        "requestIntentWithRetry",
        "removeRelationRow",
    ):
        if token not in page_text:
            errors.append(f"mobile v2 contract page missing acceptance token: {token}")

    lock_has_mobile = "@sc/mobile" in lock_text or "apps/mobile" in lock_text
    lock_has_uniapp = "@dcloudio/uni-app" in lock_text and "@dcloudio/vite-plugin-uni" in lock_text
    lock_has_h5 = "@dcloudio/uni-h5" in lock_text
    deps_ready = MOBILE_NODE_MODULES.exists()
    observations.extend([
        "frontend lockfile includes mobile workspace" if lock_has_mobile else "frontend lockfile missing mobile workspace entries",
        "frontend lockfile includes UniApp dependencies" if lock_has_uniapp else "frontend lockfile missing UniApp dependencies",
        "frontend lockfile includes UniApp H5 dependency" if lock_has_h5 else "frontend lockfile missing UniApp H5 dependency",
        "mobile node_modules exists" if deps_ready else "mobile node_modules missing",
        f"pnpm available: {pnpm_bin}" if pnpm_bin else "pnpm missing",
    ])

    can_execute = not errors and pnpm_bin is not None and lock_has_mobile and lock_has_uniapp and lock_has_h5 and deps_ready
    compile_result: dict[str, Any] | None = None
    if args.execute and can_execute:
        completed = subprocess.run(
            [pnpm_bin, "-C", str(MOBILE_ROOT), "build:h5"],
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
            "distIndexExists": (H5_DIST / "index.html").exists(),
        }
        if completed.returncode != 0:
            errors.append("harmony_h5 v2 compile command failed")
        if not (H5_DIST / "index.html").exists():
            errors.append("harmony_h5 v2 compile missing dist/build/h5/index.html")

    if errors:
        decision = "harmony_h5_v2_compile_acceptance_failed"
    elif args.execute and compile_result and compile_result.get("returnCode") == 0:
        decision = "harmony_h5_v2_compile_acceptance_passed"
    elif not can_execute:
        decision = "harmony_h5_v2_compile_acceptance_blocked_missing_dependencies"
    else:
        decision = "harmony_h5_v2_compile_acceptance_ready_not_executed"

    report = {
        "ok": not errors,
        "clientType": "harmony_h5",
        "contractVersion": "ui.contract.v2",
        "decision": decision,
        "executeRequested": args.execute,
        "canExecute": can_execute,
        "required": {
            "package": "frontend/apps/mobile/package.json",
            "manifest": "frontend/apps/mobile/src/manifest.json",
            "contractPage": "frontend/apps/mobile/src/pages/contract/index.vue",
            "compileScript": "build:h5",
            "distIndex": "frontend/apps/mobile/dist/build/h5/index.html",
        },
        "observations": observations,
        "compileResult": compile_result,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Page Contract v2 Harmony H5 compile acceptance failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Page Contract v2 Harmony H5 compile acceptance checked")
    print(f"- decision: {decision}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
