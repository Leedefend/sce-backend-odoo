#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "flow": ROOT / "docs/ops/production_release_flow_standard_v1.md",
    "ops_readme": ROOT / "docs/ops/README.md",
    "deploy_runbook": ROOT / "docs/ops/production_deployment_runbook_v1.md",
    "verify_readme": ROOT / "docs/ops/verify/README.md",
    "release_checklist": ROOT / "docs/ops/release_checklist_v2.0.0.md",
    "release_index_en": ROOT / "docs/ops/releases/README.md",
    "release_index_zh": ROOT / "docs/ops/releases/README.zh.md",
    "template": ROOT / "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "record_guard": ROOT / "scripts/verify/production_deployment_record_guard.py",
    "makefile": ROOT / "Makefile",
}

FLOW_TOKENS = (
    "生产发布链路规范 v1",
    "发布包对齐",
    "模块版本对齐",
    "全量代码树对齐",
    "数据对齐",
    "生产不得直接用日常开发目录整包覆盖",
    "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "make verify.production_deployment.record.guard",
    "生产与日常开发服务器完全一致",
    "发布结论区分了“发布包对齐”和“全量对齐”",
)

TEMPLATE_TOKENS = (
    "# Production Deployment Record",
    "## 1. 基本信息",
    "## 2. 发布范围声明",
    "## 4. 备份",
    "## 7. 发布后验证",
    "## 9. 收口结论",
    "`verify.non_demo_data_contamination`",
    "smart_construction_demo",
    "生产与日常开发服务器不是全量一致",
)

MAKEFILE_TOKENS = (
    ".PHONY: verify.production_deployment.record.guard",
    "python3 -m py_compile scripts/verify/production_deployment_record_guard.py",
    "python3 scripts/verify/production_deployment_record_guard.py",
)

VERIFY_README_TOKENS = (
    "`make verify.production_deployment.record.guard`",
    "Verifies concrete production deployment records",
    "explicit non-full-alignment wording",
)

CHECKLIST_TOKENS = (
    "docs/ops/production_release_flow_standard_v1.md",
    "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "make verify.production_deployment.record.guard",
)

INDEX_TOKENS = (
    "production_deployment_record_TEMPLATE.zh.md",
)

RECORD_GUARD_TOKENS = (
    "DEFAULT_GLOB = \"docs/ops/releases/current/production_deployment_*.md\"",
    "REQUIRED_VALIDATION_TOKENS",
    "REQUIRED_CLOSURE_TOKENS",
    "smart_construction_demo XMLID count=0",
    "full-tree alignment unchecked but non-full-alignment statement missing",
)


def _read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def _require_tokens(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{label}: missing token: {token}")


def _require_order(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    positions = []
    for token in tokens:
        index = text.find(token)
        if index < 0:
            errors.append(f"{label}: missing ordered token: {token}")
            return
        positions.append(index)
    if positions != sorted(positions):
        errors.append(f"{label}: token order mismatch: {tokens!r}")


def main() -> int:
    errors: list[str] = []
    contents = {label: _read(path, errors) for label, path in FILES.items()}

    _require_tokens("flow", contents["flow"], FLOW_TOKENS, errors)
    _require_order(
        "flow",
        contents["flow"],
        (
            "## 1. 目标",
            "## 2. 环境职责",
            "## 3. 对齐定义",
            "## 4. 硬规则",
            "## 5. 标准发布流程",
            "## 6. 发布后差异登记",
            "## 7. 后续迭代节奏",
            "## 8. 收口判定",
        ),
        errors,
    )
    _require_tokens("template", contents["template"], TEMPLATE_TOKENS, errors)
    _require_tokens("makefile", contents["makefile"], MAKEFILE_TOKENS, errors)
    _require_tokens("verify_readme", contents["verify_readme"], VERIFY_README_TOKENS, errors)
    _require_tokens("release_checklist", contents["release_checklist"], CHECKLIST_TOKENS, errors)
    _require_tokens("release_index_en", contents["release_index_en"], INDEX_TOKENS, errors)
    _require_tokens("release_index_zh", contents["release_index_zh"], INDEX_TOKENS, errors)
    _require_tokens("record_guard", contents["record_guard"], RECORD_GUARD_TOKENS, errors)

    if "production_release_flow_standard_v1.md" not in contents["ops_readme"]:
        errors.append("ops_readme: missing production release flow entry")
    if "production_release_flow_standard_v1.md" not in contents["deploy_runbook"]:
        errors.append("deploy_runbook: missing production release flow reference")

    if errors:
        print("[production_release_flow_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[production_release_flow_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
