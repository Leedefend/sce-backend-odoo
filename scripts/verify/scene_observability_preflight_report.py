#!/usr/bin/env python3
"""Summarize scene observability preflight artifacts into readiness output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = ROOT / "artifacts" / "codex" / "portal-scene-observability-preflight-v10_4"
DEFAULT_OUT = ROOT / "artifacts" / "scene_observability_preflight_readiness.latest.json"


def _latest_dir(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"preflight root not found: {root}")
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        raise FileNotFoundError(f"no preflight runs under: {root}")
    return sorted(dirs, key=lambda p: p.name)[-1]


def _has_any(required: list[str], available: list[str]) -> bool:
    if not required:
        return True
    av = set(available or [])
    return any(item in av for item in required)


def _load_report(run_dir: Path) -> dict:
    report_path = run_dir / "preflight.log"
    if not report_path.exists():
        raise FileNotFoundError(f"missing report: {report_path}")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid preflight.log: expected JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    run_dir = _latest_dir(Path(args.root))
    payload = _load_report(run_dir)

    req = payload.get("required_any") if isinstance(payload.get("required_any"), dict) else {}
    governance_required = [str(x) for x in (req.get("governance") or [])]
    notify_required = [str(x) for x in (req.get("notify") or [])]

    governance = payload.get("governance") if isinstance(payload.get("governance"), dict) else {}
    notify = payload.get("notify") if isinstance(payload.get("notify"), dict) else {}
    governance_available = [str(x) for x in (governance.get("available") or [])]
    notify_available = [str(x) for x in (notify.get("available") or [])]

    governance_ready = _has_any(governance_required, governance_available)
    notify_ready = _has_any(notify_required, notify_available)
    strict_ready = governance_ready and notify_ready
    strict_failure_reasons: list[str] = []
    if not governance_ready:
        strict_failure_reasons.append(
            "governance_missing_any:" + "|".join(governance_required)
        )
    if not notify_ready:
        strict_failure_reasons.append("notify_missing_any:" + "|".join(notify_required))

    out_payload = {
        "run_dir": str(run_dir.relative_to(ROOT)),
        "trace_id": payload.get("trace_id"),
        "strict_mode_from_run": bool(payload.get("strict")),
        "required_any": {
            "governance": governance_required,
            "notify": notify_required,
        },
        "available": {
            "governance": governance_available,
            "notify": notify_available,
        },
        "missing": {
            "governance": [str(x) for x in (governance.get("missing") or [])],
            "notify": [str(x) for x in (notify.get("missing") or [])],
        },
        "readiness": {
            "governance_ready": governance_ready,
            "notify_ready": notify_ready,
            "strict_ready": strict_ready,
            "strict_failure_reasons": strict_failure_reasons,
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print("[OK] scene observability preflight report")
    print(f"- run_dir: {out_payload['run_dir']}")
    print(f"- governance_ready: {governance_ready}")
    print(f"- notify_ready: {notify_ready}")
    print(f"- strict_ready: {strict_ready}")
    if strict_failure_reasons:
        print(f"- strict_failure_reasons: {', '.join(strict_failure_reasons)}")
    print(f"- out: {out_path.relative_to(ROOT)}")

    if args.strict and not strict_ready:
        print("[FAIL] strict readiness required but unmet")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
