#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_chatter_attachment_v1.json"


def _load_payload(input_path: str) -> dict[str, Any]:
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if isinstance(raw.get("data"), dict):
        return raw.get("data")
    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    if isinstance(result.get("data"), dict):
        return result.get("data")
    return raw if isinstance(raw, dict) else {}


def run_audit(input_path: str) -> dict[str, Any]:
    data = _load_payload(input_path)
    form = ((data.get("views") or {}).get("form") or {}) if isinstance(data, dict) else {}
    chatter = form.get("chatter") if isinstance(form.get("chatter"), dict) else {}
    attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}

    issues: list[str] = []
    chatter_enabled = bool(chatter.get("enabled", False))
    attachments_enabled = bool(attachments.get("enabled", False))

    chatter_source = str(chatter.get("source") or "").strip()
    chatter_reason = str(chatter.get("reason") or "").strip()
    attachments_source = str(attachments.get("source") or "").strip()
    attachments_reason = str(attachments.get("reason") or "").strip()

    if not chatter_source:
        issues.append("CHATTER_SOURCE_MISSING")
    if not attachments_source:
        issues.append("ATTACHMENTS_SOURCE_MISSING")
    if (not chatter_enabled) and (not chatter_reason):
        issues.append("CHATTER_REASON_MISSING_WHEN_DISABLED")
    if (not attachments_enabled) and (not attachments_reason):
        issues.append("ATTACHMENTS_REASON_MISSING_WHEN_DISABLED")

    payload = {
        "version": "v1",
        "audit": "form_chatter_attachment",
        "target": {
            "input": input_path,
        },
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
            "chatter_enabled": chatter_enabled,
            "attachments_enabled": attachments_enabled,
        },
        "chatter": chatter,
        "attachments": attachments,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form chatter and attachment surfaces.")
    parser.add_argument("--input", default="tmp/json/form.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args.input)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} chatter={chatter} attachments={attachments}".format(
                status=payload["summary"]["status"],
                chatter=payload["summary"]["chatter_enabled"],
                attachments=payload["summary"]["attachments_enabled"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
