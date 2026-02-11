#!/usr/bin/env python3
"""Guard frozen baseline files from accidental edits."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "scripts" / "verify" / "baselines" / "baseline_frozen_paths.json"


def _run(cmd: list[str]) -> str:
    out = subprocess.check_output(cmd, cwd=ROOT, text=True)
    return out.strip()


def _load_policy() -> tuple[list[str], list[str]]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    protected = [str(x) for x in (payload.get("protected_paths") or [])]
    exempt = [str(x) for x in (payload.get("exempt_paths") or [])]
    return protected, exempt


def _changed_files(base_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    out = _run(cmd)
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _resolve_base() -> str:
    for candidate in ("origin/main", "main"):
        try:
            _run(["git", "rev-parse", "--verify", candidate])
            return candidate
        except Exception:
            continue
    raise RuntimeError("cannot resolve base ref (origin/main or main)")


def main() -> int:
    if not POLICY_PATH.exists():
        print("[FAIL] baseline freeze guard")
        print(f"- policy missing: {POLICY_PATH.relative_to(ROOT)}")
        return 2

    allow = os.environ.get("BASELINE_FREEZE_ALLOW", "0") == "1"
    try:
        protected, exempt = _load_policy()
        base_ref = _resolve_base()
        changed = _changed_files(base_ref)
    except Exception as exc:
        print("[FAIL] baseline freeze guard")
        print(f"- {exc}")
        return 2

    protected_hits = []
    for rel in changed:
        if rel in exempt:
            continue
        if rel in protected:
            protected_hits.append(rel)

    print("[OK] baseline freeze guard scan")
    print(f"- base_ref: {base_ref}")
    print(f"- changed_files: {len(changed)}")
    print(f"- protected_hits: {len(protected_hits)}")

    if protected_hits and not allow:
        print("[FAIL] baseline freeze guard")
        for p in protected_hits:
            print(f"- frozen path touched: {p}")
        print("- set BASELINE_FREEZE_ALLOW=1 only for approved exceptions")
        return 2

    if protected_hits and allow:
        print("[WARN] baseline freeze guard bypassed with BASELINE_FREEZE_ALLOW=1")
        for p in protected_hits:
            print(f"- exception path: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
