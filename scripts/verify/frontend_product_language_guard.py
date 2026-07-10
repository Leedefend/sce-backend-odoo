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
    "Scene Packages": "管理员页面标题必须使用产品化中文表达",
    "Loading packages": "管理员页面加载状态必须使用产品化中文表达",
    "Package operation failed": "管理员页面错误状态必须使用产品化中文表达",
    "Installed Packages": "管理员页面区块标题必须使用产品化中文表达",
    "Import Package": "管理员页面操作标题必须使用产品化中文表达",
    "Package JSON": "管理员页面字段标签必须使用产品化中文表达",
    "Reason (required)": "管理员页面必填说明必须使用产品化中文表达",
    "Dry Run": "管理员页面操作按钮必须使用产品化中文表达",
    "Export Package": "管理员页面操作标题必须使用产品化中文表达",
    "Scene Health Dashboard": "管理员页面标题必须使用产品化中文表达",
    "Loading scene health": "管理员页面加载状态必须使用产品化中文表达",
    "Governance Actions": "管理员页面区块标题必须使用产品化中文表达",
    "Target Channel": "管理员页面字段标签必须使用产品化中文表达",
    "Set Channel": "管理员页面操作按钮必须使用产品化中文表达",
    "Pin Stable": "管理员页面操作按钮必须使用产品化中文表达",
    "Export Contract": "管理员页面操作按钮必须使用产品化中文表达",
    "Confirm import scene package": "确认弹窗必须使用产品化中文表达",
    "Confirm rollback to stable pinned mode": "确认弹窗必须使用产品化中文表达",
    "reason is required": "表单校验提示必须使用产品化中文表达",
    "health request failed": "页面错误提示必须使用产品化中文表达",
    "Copy trace": "通用状态面板按钮必须使用产品化中文表达",
    ">Retry<": "通用状态面板按钮必须使用产品化中文表达",
    "Add line": "关联明细操作必须使用产品化中文表达",
    "No related records": "关联明细空状态必须使用产品化中文表达",
    "Loading related records": "关联明细加载状态必须使用产品化中文表达",
    "Add related record": "关联明细弹窗标题必须使用产品化中文表达",
    "Edit related record": "关联明细弹窗标题必须使用产品化中文表达",
    "Delete this related record": "确认弹窗必须使用产品化中文表达",
    "Usage Analytics": "管理员分析页面标题必须使用产品化中文表达",
    "Loading usage report": "管理员分析页面加载状态必须使用产品化中文表达",
    "Failed to load usage report": "管理员分析页面错误状态必须使用产品化中文表达",
    "Scene Open Total": "管理员分析页面统计卡片必须使用产品化中文表达",
    "Capability Open Total": "管理员分析页面统计卡片必须使用产品化中文表达",
    "Generated At": "管理员分析页面统计卡片必须使用产品化中文表达",
    "Top Scenes": "管理员分析页面表格标题必须使用产品化中文表达",
    "Top Capabilities": "管理员分析页面表格标题必须使用产品化中文表达",
    "Visibility Reason Counts": "管理员分析页面表格标题必须使用产品化中文表达",
    "Hidden Capability Samples": "管理员分析页面表格标题必须使用产品化中文表达",
    "Resolving menu": "菜单解析页面加载状态必须使用产品化中文表达",
    "Menu group": "菜单解析页面状态标题必须使用产品化中文表达",
    "Menu resolve failed": "菜单解析页面错误状态必须使用产品化中文表达",
    "resolve menu failed": "菜单解析页面错误信息必须使用产品化中文表达",
    "invalid menu id": "菜单解析页面错误信息必须使用产品化中文表达",
    "Dynamic View Placeholder": "占位页面必须使用产品化中文表达",
    "Record Context": "记录详情页诊断标题必须使用产品化中文表达",
    "Loading record": "记录详情页加载状态必须使用产品化中文表达",
    "Saving record": "记录详情页保存状态必须使用产品化中文表达",
    "View node unsupported": "记录详情页错误状态必须使用产品化中文表达",
    "Saved. Changes have been applied.": "记录详情页保存反馈必须使用产品化中文表达",
    "Record load failed": "记录详情页错误状态必须使用产品化中文表达",
    "Failed to load chatter": "记录详情页协作错误必须使用产品化中文表达",
    "Failed to post chatter message": "记录详情页协作错误必须使用产品化中文表达",
    "Failed to upload file": "记录详情页附件错误必须使用产品化中文表达",
    "Failed to download file": "记录详情页附件错误必须使用产品化中文表达",
    "failed to load record": "记录详情页错误状态必须使用产品化中文表达",
    "failed to execute button": "记录详情页操作错误必须使用产品化中文表达",
    "failed to save record": "记录详情页保存错误必须使用产品化中文表达",
    "scene render target missing": "场景页错误状态必须使用产品化中文表达",
    "scene resolve failed": "场景页错误状态必须使用产品化中文表达",
    "Release Operator Surface": "发布运营页面标题必须使用产品化中文表达",
    "Active Released Snapshot": "发布运营页面指标必须使用产品化中文表达",
    "Latest Action": "发布运营页面指标必须使用产品化中文表达",
    "Approval State": "发布运营页面指标必须使用产品化中文表达",
    ">draft<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">preview<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">stable<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">archived<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">public<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">internal<": "发布运营页面枚举选项必须使用产品化中文表达",
    ">role_restricted<": "发布运营页面枚举选项必须使用产品化中文表达",
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
