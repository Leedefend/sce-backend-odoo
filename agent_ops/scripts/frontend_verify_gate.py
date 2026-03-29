#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from frontend_eslint_preflight import evaluate_frontend_eslint_env


def _run(cmd: list[str], cwd: Path, timeout_seconds: int) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description="Frontend verify gate with fail-fast preflight.")
    parser.add_argument("--frontend-dir", default="frontend/apps/web", help="Frontend app directory.")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Timeout for the lint phase.")
    parser.add_argument("--expect-status", choices=["PASS", "BLOCKED", "FAIL"], help="Assert expected final status.")
    parser.add_argument("--expect-route", help="Assert expected selected route from the preflight/gate payload.")
    parser.add_argument("--expect-preferred-node-major", type=int, help="Assert expected preferred Node major in route metadata.")
    parser.add_argument("targets", nargs="*", help="Optional eslint targets to verify after preflight passes.")
    args = parser.parse_args()

    frontend_dir = Path(args.frontend_dir).resolve()
    preflight = evaluate_frontend_eslint_env(frontend_dir)
    route = dict(preflight.get("route") or {})
    payload: dict[str, object] = {
        "frontend_dir": str(frontend_dir),
        "status": str(preflight.get("status") or "FAIL"),
        "preflight": preflight,
        "route": route,
        "verify": None,
    }

    if payload["status"] == "PASS" and args.targets:
        eslint_bin = frontend_dir / "node_modules" / ".bin" / "eslint"
        cmd = [str(eslint_bin), *args.targets]
        try:
            exit_code, stdout, stderr = _run(cmd, frontend_dir, args.timeout_seconds)
            payload["verify"] = {
                "command": cmd,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
            payload["status"] = "PASS" if exit_code == 0 else "FAIL"
            payload["route"]["selected"] = "local_frontend_verify"
            payload["route"]["verify_mode"] = "local"
            payload["route"]["next_step"] = "inspect_verify_result"
        except subprocess.TimeoutExpired:
            payload["verify"] = {
                "command": cmd,
                "exit_code": 124,
                "stdout": "",
                "stderr": f"eslint timed out after {args.timeout_seconds}s",
            }
            payload["status"] = "FAIL"
            payload["route"]["selected"] = "local_frontend_verify_failed"
            payload["route"]["verify_mode"] = "local"
            payload["route"]["next_step"] = "inspect_timeout_and_fix_runtime"

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.expect_status and payload["status"] != args.expect_status:
        return 1
    if args.expect_route and str((payload.get("route") or {}).get("selected") or "") != args.expect_route:
        return 1
    if args.expect_preferred_node_major is not None:
        actual_major = (payload.get("route") or {}).get("preferred_node_major")
        if actual_major != args.expect_preferred_node_major:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
