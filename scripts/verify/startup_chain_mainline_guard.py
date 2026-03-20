#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SESSION_STORE = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
LOGIN_VIEW = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "LoginView.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_contains(text: str, token: str, errors: list[str], label: str) -> None:
    if token not in text:
        errors.append(f"{label} missing token: {token}")


def _assert_not_contains(text: str, token: str, errors: list[str], label: str) -> None:
    if token in text:
        errors.append(f"{label} contains forbidden token: {token}")


def main() -> int:
    errors: list[str] = []
    session_text = _read(SESSION_STORE)
    login_view_text = _read(LOGIN_VIEW)

    _assert_contains(session_text, "intent: 'login'", errors, "session.ts")
    _assert_contains(session_text, "intent: 'system.init'", errors, "session.ts")
    _assert_not_contains(session_text, "intent: 'app.init'", errors, "session.ts")
    _assert_contains(session_text, "allowedBootstrapIntents", errors, "session.ts")
    _assert_contains(session_text, "'system.init'", errors, "session.ts")
    _assert_contains(session_text, "'session.bootstrap'", errors, "session.ts")

    _assert_contains(login_view_text, "await session.login", errors, "LoginView.vue")
    _assert_contains(login_view_text, "await session.loadAppInit", errors, "LoginView.vue")

    if errors:
        for row in errors:
            print(f"[startup_chain_mainline_guard] {row}")
        print("[startup_chain_mainline_guard] FAIL")
        return 2

    print("[startup_chain_mainline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

