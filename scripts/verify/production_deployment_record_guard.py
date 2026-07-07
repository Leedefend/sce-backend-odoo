#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLOB = "docs/ops/releases/current/production_deployment_*.md"
REQUIRED_HEADINGS = [
    "# Production Deployment Record",
    "## 1. 基本信息",
    "## 2. 发布范围声明",
    "## 3. 发布前状态",
    "## 4. 备份",
    "## 5. Prod-Sim 验证",
    "## 6. 生产执行摘要",
    "## 7. 发布后验证",
    "## 8. 回滚点",
    "## 9. 收口结论",
    "## 10. 后续事项",
]
REQUIRED_VALIDATION_TOKENS = [
    "| `verify.baseline` | `PASS` |",
    "| `verify.p0` | `PASS` |",
    "| `smoke.business_full` | `PASS` |",
    "| `smoke.role_matrix` | `PASS` |",
    "| `verify.non_demo_data_contamination` | `PASS` |",
    "| `history.attachment.custody.probe.prod` | `PASS` |",
    "| 服务健康 | `PASS` |",
]
REQUIRED_CLOSURE_TOKENS = [
    "- [x] 本次发布包范围已与生产对齐。",
    "- [x] 生产服务健康检查通过。",
    "- [x] 生产验证矩阵全部通过。",
    "- [x] demo 模块和 demo XMLID 状态符合生产要求。",
]


def _records() -> list[Path]:
    explicit = os.getenv("PRODUCTION_DEPLOYMENT_RECORD", "").strip()
    if explicit:
        path = Path(explicit)
        return [path if path.is_absolute() else ROOT / path]
    return sorted(ROOT.glob(DEFAULT_GLOB))


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _check_record(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"record not found: {_relative(path)}"]

    text = path.read_text(encoding="utf-8")
    rel = _relative(path)

    if "TEMPLATE" in path.name:
        errors.append(f"{rel}: guard must run against a concrete deployment record, not template")

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"{rel}: missing heading: {heading}")

    if re.search(r"<[^>\n]+>", text):
        errors.append(f"{rel}: unresolved placeholder token remains")

    sha_matches = re.findall(r"\b[0-9a-f]{64}\b", text)
    if not sha_matches:
        errors.append(f"{rel}: missing 64-char sha256")

    if "发布类型 | `incremental package`" not in text and "发布类型 | `full tree`" not in text:
        errors.append(f"{rel}: release type must be explicit")

    if "/data/backups/" not in text:
        errors.append(f"{rel}: missing production backup path under /data/backups/")

    for token in REQUIRED_VALIDATION_TOKENS:
        if token not in text:
            errors.append(f"{rel}: validation token missing: {token}")

    for token in REQUIRED_CLOSURE_TOKENS:
        if token not in text:
            errors.append(f"{rel}: closure token missing: {token}")

    full_tree_checked = "- [x] 生产与日常开发服务器全量一致。" in text
    full_tree_unchecked = "- [ ] 生产与日常开发服务器全量一致。" in text
    if full_tree_checked and "全量代码树差异 | `0`" not in text:
        errors.append(f"{rel}: full-tree alignment checked without zero full-tree diff evidence")
    if full_tree_unchecked and "生产与日常开发服务器不是全量一致" not in text:
        errors.append(f"{rel}: full-tree alignment unchecked but non-full-alignment statement missing")

    if "smart_construction_demo XMLID count=0" not in text:
        errors.append(f"{rel}: demo XMLID zero evidence missing")
    if "smart_construction_demo|uninstalled|" not in text:
        errors.append(f"{rel}: demo module uninstalled evidence missing")

    if "history_attachment_custody_ready" not in text:
        errors.append(f"{rel}: attachment custody ready evidence missing")

    if "最终发布结论" not in text or "具备生产运行条件" not in text:
        errors.append(f"{rel}: final production-ready conclusion missing")

    return errors


def main() -> int:
    records = _records()
    errors: list[str] = []
    if not records:
        errors.append(f"no production deployment records found: {DEFAULT_GLOB}")
    for record in records:
        errors.extend(_check_record(record))

    if errors:
        print("[production_deployment_record_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print(f"[production_deployment_record_guard] PASS records={len(records)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
