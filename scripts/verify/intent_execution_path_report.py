#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTENT_MATRIX_JSON = ROOT / "artifacts" / "backend" / "intent_permission_matrix.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_execution_path_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "intent_execution_path_report.json"

WRITE_CALL_PATTERN = re.compile(r"\.(create|write|unlink)\(")
ENV_MODEL_PATTERN = re.compile(r"self\.env\[['\"]([^'\"]+)['\"]\]")
PATH_ALLOWLIST_PREFIX = (
    "execute_button",
    "api.data.",
    "payment.request.",
    "scene.governance.",
    "scene.package.",
    "my.work.complete",
    "usage.track",
    "chatter.post",
    "file.upload",
    "system.ping.construction",
)


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_line(line: str) -> str:
    out = line.strip()
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\b\d+\b", "<num>", out)
    out = re.sub(r"'[^']*'", "'<str>'", out)
    out = re.sub(r'"[^"]*"', '"<str>"', out)
    return out


def _extract_write_signature(source_path: Path) -> dict:
    text = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
    lines = text.splitlines()
    write_lines = [_normalize_line(line) for line in lines if WRITE_CALL_PATTERN.search(line)]
    models = sorted(set(ENV_MODEL_PATTERN.findall(text)))
    basis = "\n".join(write_lines) if write_lines else "|".join(models)
    sig = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12] if basis else ""
    return {
        "signature": sig,
        "write_line_count": len(write_lines),
        "models": models,
    }


def _is_allowlisted_intent(intent: str) -> bool:
    low = intent.lower()
    return any(low.startswith(prefix) for prefix in PATH_ALLOWLIST_PREFIX)


def main() -> int:
    matrix = _safe_json(INTENT_MATRIX_JSON)
    rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    write_rows = [row for row in rows if isinstance(row, dict) and bool(row.get("is_write"))]

    intent_signatures: list[dict] = []
    for row in write_rows:
        intent = str(row.get("intent") or "").strip()
        source = str(row.get("source") or "").strip()
        if not intent or not source:
            continue
        source_path = ROOT / source
        sig_info = _extract_write_signature(source_path)
        intent_signatures.append(
            {
                "intent": intent,
                "source": source,
                "signature": sig_info["signature"],
                "write_line_count": sig_info["write_line_count"],
                "models": sig_info["models"],
            }
        )

    by_signature: dict[str, list[dict]] = {}
    for row in intent_signatures:
        sig = row["signature"]
        if not sig:
            continue
        by_signature.setdefault(sig, []).append(row)

    collisions = []
    for sig, bucket in sorted(by_signature.items()):
        intents = sorted({item["intent"] for item in bucket})
        if len(intents) < 2:
            continue
        collisions.append(
            {
                "signature": sig,
                "intent_count": len(intents),
                "intents": intents,
                "sources": sorted({item["source"] for item in bucket}),
            }
        )

    non_allowlisted_write = sorted(
        [
            {
                "intent": row["intent"],
                "source": row["source"],
            }
            for row in intent_signatures
            if not _is_allowlisted_intent(row["intent"])
        ],
        key=lambda item: item["intent"],
    )

    payload = {
        "ok": True,
        "summary": {
            "write_intent_count": len(intent_signatures),
            "collision_count": len(collisions),
            "non_allowlisted_write_count": len(non_allowlisted_write),
        },
        "write_intents": intent_signatures,
        "signature_collisions": collisions,
        "non_allowlisted_write_intents": non_allowlisted_write,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Intent Execution Path Report",
        "",
        f"- write_intent_count: {payload['summary']['write_intent_count']}",
        f"- collision_count: {payload['summary']['collision_count']}",
        f"- non_allowlisted_write_count: {payload['summary']['non_allowlisted_write_count']}",
        "",
        "## Signature Collisions",
        "",
    ]
    if collisions:
        for item in collisions:
            lines.append(f"- `{item['signature']}` intents={', '.join(item['intents'])}")
    else:
        lines.append("- none")

    lines.extend(["", "## Non-Allowlisted Write Intents", ""])
    if non_allowlisted_write:
        for item in non_allowlisted_write:
            lines.append(f"- `{item['intent']}` ({item['source']})")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print("[intent_execution_path_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
