#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _parse_major(version_text: str) -> int | None:
    match = re.search(r"(\d+)", version_text or "")
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-fast preflight for frontend eslint environment.")
    parser.add_argument("--frontend-dir", default="frontend/apps/web", help="Frontend app directory.")
    args = parser.parse_args()

    frontend_dir = Path(args.frontend_dir).resolve()
    package_json = frontend_dir / "package.json"
    payload: dict[str, object] = {
        "frontend_dir": str(frontend_dir),
        "status": "PASS",
        "blocked": False,
        "reason_code": "",
        "node": {},
        "eslint": {},
        "notes": [],
    }

    if not package_json.exists():
        payload["status"] = "FAIL"
        payload["blocked"] = True
        payload["reason_code"] = "FRONTEND_PACKAGE_JSON_MISSING"
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    package = json.loads(package_json.read_text(encoding="utf-8"))
    eslint_version = str(((package.get("devDependencies") or {}).get("eslint")) or "")

    node_code, node_stdout, node_stderr = _run(["node", "-v"], frontend_dir)
    node_version = (node_stdout or node_stderr).strip()
    node_major = _parse_major(node_version)
    eslint_major = _parse_major(eslint_version)

    payload["node"] = {
        "exit_code": node_code,
        "version": node_version,
        "major": node_major,
    }
    payload["eslint"] = {
        "declared_version": eslint_version,
        "major": eslint_major,
    }

    if node_code != 0:
        payload["status"] = "FAIL"
        payload["blocked"] = True
        payload["reason_code"] = "NODE_RUNTIME_UNAVAILABLE"
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if node_major is not None and eslint_major is not None and node_major >= 24 and eslint_major <= 8:
        payload["status"] = "BLOCKED"
        payload["blocked"] = True
        payload["reason_code"] = "NODE24_ESLINT8_INCOMPATIBLE"
        payload["notes"] = [
            "Current environment uses Node >= 24 while frontend package declares ESLint 8.x.",
            "Recent probes show eslint CLI startup can hang before printing env info.",
            "Choose an alternate verification path or align the frontend runtime/toolchain first.",
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    payload["notes"] = ["No known fail-fast blocker detected for frontend eslint startup."]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
