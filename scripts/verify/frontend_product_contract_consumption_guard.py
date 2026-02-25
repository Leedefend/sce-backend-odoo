#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
REPORT_JSON = ROOT / "artifacts/backend/frontend_product_contract_consumption_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_product_contract_consumption_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _has_all(text: str, tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in tokens if token not in text]
    return not missing, missing


def main() -> int:
    session_text = _read(SESSION_STORE)
    home_text = _read(HOME_VIEW)
    errors: list[str] = []

    if not session_text:
        errors.append(f"missing file: {SESSION_STORE.relative_to(ROOT).as_posix()}")
    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")

    required_session_tokens = [
        "capability_groups",
        "capabilityCatalog",
        "this.capabilityCatalog = rawCapabilities.reduce",
        "this.capabilityGroups = rawCapabilityGroups",
        "const extFacts =",
        "const productFacts =",
        "this.productFacts =",
        "license:",
        "bundle:",
    ]
    required_home_tokens = [
        "const productFacts = computed(() => session.productFacts);",
        "const capabilityGroups = computed(() => session.capabilityGroups);",
        "const capabilityCatalog = session.capabilityCatalog || {};",
        "normalizeEntryWithCapabilityMeta(",
        "capabilityStateLabel(",
        "const capabilityGroupScoreMap = computed(() => {",
        "group.state_counts?.READY",
        "suggestionEntryScore(",
        "licenseLevelLabel",
        "bundleNameLabel",
        "capabilityGroupCards",
        "<section v-if=\"capabilityGroupCards.length\" class=\"group-overview\"",
    ]

    ok_session, missing_session = _has_all(session_text, required_session_tokens)
    ok_home, missing_home = _has_all(home_text, required_home_tokens)
    if not ok_session:
        errors.extend([f"session.ts missing token: {token}" for token in missing_session])
    if not ok_home:
        errors.extend([f"HomeView.vue missing token: {token}" for token in missing_home])

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_files": 2,
            "error_count": len(errors),
            "contract_signals": {
                "capability_groups": "consumed" if ok_session else "missing",
                "ext_facts.product.license": "consumed" if ok_session else "missing",
                "ext_facts.product.bundle": "consumed" if ok_session else "missing",
                "home_product_surface": "rendered" if ok_home else "missing",
                "capability_metadata_state_reason": "consumed" if ok_session and ok_home else "missing",
            },
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Product Contract Consumption Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_files: `{report['summary']['checked_files']}`",
        f"- error_count: `{report['summary']['error_count']}`",
        "",
        "## Contract Signals",
    ]
    for key, val in report["summary"]["contract_signals"].items():
        lines.append(f"- {key}: `{val}`")
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_product_contract_consumption_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[frontend_product_contract_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
