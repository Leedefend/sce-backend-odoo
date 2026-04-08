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
        raise SystemExit("[native_business_admin_config_role_entry_frontend_filter_verify] FAIL missing session store")

    content = SESSION_STORE.read_text(encoding="utf-8")
    failures: list[str] = []

    _assert_contains(content, "function applyRoleEntryNavFilter(", failures)
    _assert_contains(content, "return filteredTree.length ? filteredTree : tree;", failures)
    _assert_contains(content, "const roleCode = String(this.roleSurface?.role_code || '').trim();", failures)
    _assert_contains(content, "this.menuTree = applyRoleEntryNavFilter(menuTreeWithKeys, this.roleEntries, roleCode);", failures)
    _assert_contains(content, "this.releaseNavigationTree = applyRoleEntryNavFilter(releaseNavigationTreeWithKeys, this.roleEntries, roleCode);", failures)
    _assert_contains(content, "return tree;", failures)

    if failures:
        raise SystemExit(
            "[native_business_admin_config_role_entry_frontend_filter_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_admin_config_role_entry_frontend_filter_verify] PASS generic role-entry nav filtering markers present")


if __name__ == "__main__":
    main()
