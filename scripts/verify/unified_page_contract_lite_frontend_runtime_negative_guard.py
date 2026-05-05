#!/usr/bin/env python3
"""Guard that frontend runtime only consumes Lite preview through approved paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOTS = (
    ROOT / "frontend" / "apps" / "web",
    ROOT / "frontend" / "packages",
)
EXCLUDED_DIRS = {
    "dist",
    "node_modules",
    ".vite",
    ".cache",
}
TEXT_SUFFIXES = {
    ".js",
    ".ts",
    ".tsx",
    ".vue",
    ".json",
}
FORBIDDEN_TOKENS = (
    "lite_preview",
    "payloadType",
    "lite_patch",
    "lite_contract",
    "runtimeContract",
    "UnifiedPageContractLite",
    "unified_page_contract_lite",
)
ALLOWED_PILOT_FILES = {
    "frontend/apps/web/src/api/contract.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminal.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalPageIntegration.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRenderer.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRendererInput.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRuntimeMount.ts",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalStore.ts",
    "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts",
}


def iter_frontend_files():
    for root in FRONTEND_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
                continue
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                yield path


def find_hits() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in iter_frontend_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in ALLOWED_PILOT_FILES:
            continue
        matched = sorted({token for token in FORBIDDEN_TOKENS if token in text})
        if matched:
            hits.append({"path": relative, "tokens": matched})
    return sorted(hits, key=lambda item: item["path"])


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/backend/unified_page_contract_lite_frontend_runtime_negative.json")
    args = parser.parse_args()

    hits = find_hits()
    report = {
        "ok": not hits,
        "policy": "frontend runtime may consume Lite preview only through approved default-off pilot and shared terminal boundary files",
        "frontend_roots": [root.relative_to(ROOT).as_posix() for root in FRONTEND_ROOTS],
        "forbidden_tokens": list(FORBIDDEN_TOKENS),
        "allowed_pilot_files": sorted(ALLOWED_PILOT_FILES),
        "hit_count": len(hits),
        "hits": hits,
    }
    write_report(args.report, report)

    if hits:
        print("Unified Semantic Page Contract Lite frontend runtime negative guard failed:")
        for hit in hits:
            print("- %s: %s" % (hit["path"], ",".join(hit["tokens"])))
        print("- report: %s" % args.report)
        return 1

    print("Unified Semantic Page Contract Lite frontend runtime negative guard passed")
    print("- policy: default-off pilot and shared terminal boundary files only")
    print("- report: %s" % args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
