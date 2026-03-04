#!/usr/bin/env python3
"""Guard operation gateway wiring for execute/onchange remains available."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py"
GATEWAY = ROOT / "addons/smart_core/models/app_action_gateway.py"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    try:
        dispatcher = _read(DISPATCHER)
        gateway = _read(GATEWAY)
    except FileNotFoundError as exc:
        print("[FAIL] operation_gateway_contract_guard")
        print(f"- {exc}")
        return 1

    dispatcher_markers = [
        "def _resolve_action_gateway(self):",
        "if 'app.action.gateway' in self.env:",
        "gw = self._resolve_action_gateway()",
        "run_object_method(",
        "run_onchange(",
    ]
    for marker in dispatcher_markers:
        if marker not in dispatcher:
            errors.append(f"dispatcher missing marker: {marker}")

    gateway_markers = [
        '_name = "app.action.gateway"',
        "def run_object_method(",
        "def run_onchange(",
        "ApiOnchangeHandler",
    ]
    for marker in gateway_markers:
        if marker not in gateway:
            errors.append(f"gateway missing marker: {marker}")

    if errors:
        print("[FAIL] operation_gateway_contract_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] operation_gateway_contract_guard")
    print(f"- dispatcher: {DISPATCHER}")
    print(f"- gateway: {GATEWAY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
