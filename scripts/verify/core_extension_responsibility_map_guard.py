#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"
DOC = ROOT / "docs/engineering_convergence/core_extension_responsibility_map.md"
MAX_LINES = 4372


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    errors: list[str] = []
    if not TARGET.is_file():
        errors.append("core_extension.py missing")
    elif _line_count(TARGET) > MAX_LINES:
        errors.append(f"core_extension.py line budget exceeded: {_line_count(TARGET)} > {MAX_LINES}")

    if not DOC.is_file():
        errors.append("core_extension responsibility map missing")
    else:
        text = DOC.read_text(encoding="utf-8")
        required_tokens = [
            "Target file: `addons/smart_construction_core/core_extension.py`",
            "Current line budget: `<=4372`.",
            "`core_extension.py` is the construction-industry contribution facade",
            "`smart_core_register(registry)`",
            "`smart_core_extend_system_init(data, env, user)`",
            "`smart_core_finalize_projected_contract_data(env, data, context)`",
            "no extraction in this stage",
            "future PRs from this branch should include multiple commits",
            "open only when",
        ]
        for token in required_tokens:
            if token not in text:
                errors.append(f"responsibility map missing token: {token}")

    if errors:
        print("[core_extension_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[core_extension_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
