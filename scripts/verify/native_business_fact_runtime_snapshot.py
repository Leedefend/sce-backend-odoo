#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Tuple

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8069").rstrip("/")


def _run_curl(args: list[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _probe_native() -> dict:
    payload = json.dumps({"intent": "app.init", "params": {}, "context": {}})
    cmd = [
        "curl",
        "-sS",
        "-i",
        "--max-time",
        "8",
        "-X",
        "POST",
        f"{BASE_URL}/api/v1/intent",
        "-H",
        "Content-Type: application/json",
        "-d",
        payload,
    ]
    code, out, err = _run_curl(cmd)
    return {"name": "native", "returncode": code, "stdout": out, "stderr": err}


def _probe_legacy() -> dict:
    cmd = [
        "curl",
        "-sS",
        "-i",
        "--max-time",
        "8",
        f"{BASE_URL}/api/scenes/my",
    ]
    code, out, err = _run_curl(cmd)
    return {"name": "legacy", "returncode": code, "stdout": out, "stderr": err}


def _extract_status(stdout: str, stderr: str, returncode: int) -> str:
    first_line = (stdout.splitlines() or [""])[0]
    if first_line.startswith("HTTP/"):
        parts = first_line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            return parts[1]
    if returncode != 0:
        return f"CURL_ERROR_{returncode}:{stderr.strip()}"
    return "UNKNOWN"


def main() -> None:
    native = _probe_native()
    legacy = _probe_legacy()

    native_status = _extract_status(native["stdout"], native["stderr"], native["returncode"])
    legacy_status = _extract_status(legacy["stdout"], legacy["stderr"], legacy["returncode"])

    print(f"[native_business_fact_runtime_snapshot] base_url={BASE_URL}")
    print(f"[native_business_fact_runtime_snapshot] native_status={native_status}")
    print(f"[native_business_fact_runtime_snapshot] legacy_status={legacy_status}")

    if native_status.startswith("CURL_ERROR") or legacy_status.startswith("CURL_ERROR"):
        raise RuntimeError(
            "runtime snapshot probe failed: "
            f"native={native_status} legacy={legacy_status}"
        )

    if native_status not in {"200", "401", "403"}:
        raise RuntimeError(f"unexpected native status: {native_status}")
    if legacy_status not in {"200", "401", "403"}:
        raise RuntimeError(f"unexpected legacy status: {legacy_status}")

    print("[native_business_fact_runtime_snapshot] PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[native_business_fact_runtime_snapshot] FAIL: {exc}", file=sys.stderr)
        raise
