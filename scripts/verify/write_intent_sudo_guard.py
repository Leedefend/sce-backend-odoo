#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_JSON = ROOT / "artifacts" / "backend" / "intent_permission_matrix.json"
POLICY_JSON = ROOT / "scripts" / "verify" / "baselines" / "write_intent_sudo_allowlist.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "write_intent_sudo_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _scan_sudo_lines(path: Path) -> list[int]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    return [idx for idx, line in enumerate(text.splitlines(), start=1) if ".sudo(" in line]


def main() -> int:
    matrix = _load_json(MATRIX_JSON)
    policy = _load_json(POLICY_JSON)
    failures: list[str] = []

    rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    allow_entries = policy.get("allowlist") if isinstance(policy.get("allowlist"), list) else []
    max_unallowlisted = int(policy.get("max_unallowlisted") or 0)

    allow_by_source: dict[str, dict] = {}
    for item in allow_entries:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        if not source:
            continue
        allow_by_source[source] = item
        if not str(item.get("reason") or "").strip():
            failures.append(f"{source}: allowlist reason missing")

    write_sources: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not bool(row.get("is_write")):
            continue
        source = str(row.get("source") or "").strip()
        intent = str(row.get("intent") or "").strip()
        if not source or not intent:
            continue
        write_sources.setdefault(source, set()).add(intent)

    findings: list[dict] = []
    unallowlisted = 0
    for source in sorted(write_sources.keys()):
        path = ROOT / source
        sudo_lines = _scan_sudo_lines(path)
        if not sudo_lines:
            continue

        allow = allow_by_source.get(source) if source in allow_by_source else None
        max_sudo_calls = int((allow or {}).get("max_sudo_calls") or 0)
        allowed_intents = {
            str(item).strip()
            for item in ((allow or {}).get("intents") if isinstance((allow or {}).get("intents"), list) else [])
            if str(item).strip()
        }
        intents = sorted(write_sources[source])

        finding = {
            "source": source,
            "intents": intents,
            "sudo_lines": sudo_lines,
            "allowlisted": bool(allow),
            "max_sudo_calls": max_sudo_calls,
        }
        findings.append(finding)

        if not allow:
            unallowlisted += 1
            failures.append(f"{source}: write-intent sudo usage not allowlisted (lines={sudo_lines})")
            continue
        if len(sudo_lines) > max_sudo_calls:
            failures.append(
                f"{source}: sudo call count exceeded ({len(sudo_lines)} > {max_sudo_calls})"
            )
        if allowed_intents:
            missing_intents = [intent for intent in intents if intent not in allowed_intents]
            if missing_intents:
                failures.append(
                    f"{source}: allowlist intents missing {', '.join(missing_intents)}"
                )

    if unallowlisted > max_unallowlisted:
        failures.append(
            f"unallowlisted write-intent sudo sources exceeded policy ({unallowlisted} > {max_unallowlisted})"
        )

    report = {
        "ok": len(failures) == 0,
        "summary": {
            "write_source_count": len(write_sources),
            "sources_with_sudo_count": len(findings),
            "unallowlisted_count": unallowlisted,
            "failure_count": len(failures),
            "policy_file": str(POLICY_JSON.relative_to(ROOT)),
        },
        "findings": findings,
        "errors": failures,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_JSON))
    print(
        f"[write_intent_sudo_guard] write_sources={len(write_sources)} "
        f"sudo_sources={len(findings)} failures={len(failures)}"
    )
    if failures:
        for item in failures:
            print(f"- {item}")
        print("[write_intent_sudo_guard] FAIL")
        return 2
    print("[write_intent_sudo_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
