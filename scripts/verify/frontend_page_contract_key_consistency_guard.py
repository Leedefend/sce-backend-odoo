#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = ROOT / "frontend/apps/web/src/views"
PAGE_CONTRACTS_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_key_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extract_contract_keys_from_views() -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    marker = "usePageContract('"
    for view in sorted(VIEWS_DIR.glob("*.vue")):
        text = _read(view)
        if not text:
            continue
        start = 0
        while True:
            idx = text.find(marker, start)
            if idx < 0:
                break
            key_start = idx + len(marker)
            key_end = text.find("'", key_start)
            if key_end > key_start:
                key = text[key_start:key_end].strip()
                if key:
                    usage.setdefault(key, set()).add(view.relative_to(ROOT).as_posix())
            start = key_start
    return usage


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_key_consistency_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not PAGE_CONTRACTS_BUILDER.is_file():
        return _fail([f"missing file: {PAGE_CONTRACTS_BUILDER.relative_to(ROOT).as_posix()}"])

    try:
        builder_mod = _load_builder_module(PAGE_CONTRACTS_BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder_mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in page_contracts_builder.py"])

    payload = builder_mod.build_page_contracts({})
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, dict) or not pages:
        return _fail(["page contracts payload missing pages object"])

    backend_keys = {str(k).strip() for k in pages.keys() if str(k).strip()}
    frontend_usage = _extract_contract_keys_from_views()
    frontend_keys = set(frontend_usage.keys())

    errors: list[str] = []
    missing_in_backend = sorted(frontend_keys - backend_keys)
    if missing_in_backend:
        for key in missing_in_backend:
            refs = ", ".join(sorted(frontend_usage.get(key, set())))
            errors.append(f"frontend uses missing contract key '{key}' in: {refs}")

    missing_in_frontend = sorted(backend_keys - frontend_keys)
    if missing_in_frontend:
        for key in missing_in_frontend:
            errors.append(f"backend contract key '{key}' has no frontend usePageContract consumer")

    if errors:
        return _fail(errors)

    print(
        "[frontend_page_contract_key_consistency_guard] PASS "
        f"(keys={len(backend_keys)}, views={len(list(VIEWS_DIR.glob('*.vue')))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
