#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"


def _assert_contains(content: str, marker: str, failures: list[str]) -> None:
    if marker not in content:
        failures.append(f"missing marker: {marker}")


def main() -> None:
    if not SESSION_STORE.exists():
        raise SystemExit("[native_business_admin_config_role_entry_frontend_consumer_verify] FAIL missing session store file")

    content = SESSION_STORE.read_text(encoding="utf-8")
    failures: list[str] = []

    _assert_contains(content, "export interface RoleEntryContractGroup", failures)
    _assert_contains(content, "roleEntries: RoleEntryContractGroup[];", failures)
    _assert_contains(content, "roleEntries: [],", failures)
    _assert_contains(content, "this.roleEntries = parsed.roleEntries ?? [];", failures)
    _assert_contains(content, "roleEntries: this.roleEntries,", failures)
    _assert_contains(content, "(result as AppInitResponse & { role_entries?: unknown[] }).role_entries", failures)

    if failures:
        raise SystemExit(
            "[native_business_admin_config_role_entry_frontend_consumer_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_admin_config_role_entry_frontend_consumer_verify] PASS session role_entries ingest markers present")


if __name__ == "__main__":
    main()
