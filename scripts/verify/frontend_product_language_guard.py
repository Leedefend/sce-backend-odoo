#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "contracts",
    ROOT / "frontend" / "apps" / "web" / "src" / "components",
    ROOT / "frontend" / "apps" / "web" / "src" / "layouts",
    ROOT / "frontend" / "apps" / "web" / "src" / "pages",
    ROOT / "frontend" / "apps" / "web" / "src" / "views",
]
SCAN_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".vue"}

FORBIDDEN_PHRASES = {
    "待完善配置": "用户界面不能暴露工程整改口径，应使用产品状态口径",
    "待完善：": "用户界面不能用工程整改汇总，应使用明确状态",
    "当前待完善项": "用户界面不能要求用户理解后台配置缺口",
    "配置缺口提示": "用户界面提示应表达配置状态，而不是工程缺口",
    "后端配置缺口": "用户界面不能暴露后端实现边界",
    "后端兜底": "用户界面不能暴露兜底实现机制",
}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCAN_DIRS:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in SCAN_SUFFIXES:
                files.append(path)
    return sorted(files)


def main() -> int:
    errors: list[str] = []
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        for phrase, reason in FORBIDDEN_PHRASES.items():
            if phrase not in text:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if phrase in line:
                    rel = path.relative_to(ROOT)
                    errors.append(f"{rel}:{line_no}: {reason}: {phrase}")

    if errors:
        print("[frontend_product_language_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[frontend_product_language_guard] PASS files={len(iter_files())} phrases={len(FORBIDDEN_PHRASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
