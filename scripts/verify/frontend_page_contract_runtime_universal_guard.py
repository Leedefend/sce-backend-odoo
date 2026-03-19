#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = ROOT / "frontend/apps/web/src/views"
ACTION_HEADER_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewHeaderRuntime.ts"

REQUIRED_TOKENS = (
    "executePageContractAction",
    "pageContract.actionIntent",
    "pageContract.actionTarget",
    "pageContract.globalActions",
)


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_runtime_universal_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    if not VIEWS_DIR.is_dir():
        return _fail([f"missing directory: {VIEWS_DIR.relative_to(ROOT).as_posix()}"])

    errors: list[str] = []
    checked = 0
    action_header_runtime_text = _read(ACTION_HEADER_RUNTIME)

    for view in sorted(VIEWS_DIR.glob("*.vue")):
        text = _read(view)
        if not text:
            continue
        page_match = re.search(r"usePageContract\('([^']+)'\)", text)
        if not page_match:
            continue
        checked += 1
        page_key = page_match.group(1).strip()
        rel = view.relative_to(ROOT).as_posix()

        for token in REQUIRED_TOKENS:
            if token not in text:
                errors.append(f"{rel} (page={page_key}) missing token: {token}")

        has_invocation = "await executePageContractAction({" in text or "executePageContractAction({" in text
        if page_key == "action":
            has_runtime_invocation = (
                "await options.executePageContractAction({" in action_header_runtime_text
                or "options.executePageContractAction({" in action_header_runtime_text
            )
            if not has_invocation and not has_runtime_invocation:
                errors.append(f"{rel} (page={page_key}) missing executePageContractAction(...) invocation")
        elif not has_invocation:
            errors.append(f"{rel} (page={page_key}) missing executePageContractAction(...) invocation")

    if checked == 0:
        errors.append("no usePageContract(...) views found")

    if errors:
        return _fail(errors)

    print(f"[frontend_page_contract_runtime_universal_guard] PASS (checked_views={checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
