#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "action_runtime",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "assemblers",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "contracts",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "suggested_action",
    ROOT / "frontend" / "apps" / "web" / "src" / "components",
    ROOT / "frontend" / "apps" / "web" / "src" / "composables",
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
    "retry_unknown_reason_code', 'UNKNOWN": "我的工作台失败原因默认值必须使用产品化中文表达",
    "trace_id 已复制": "我的工作台复制反馈必须使用产品化中文表达",
    "复制 trace_id 失败": "我的工作台复制反馈必须使用产品化中文表达",
    "Retry failed items from my-work": "我的工作台重试备注必须使用产品化中文表达",
    "Retry failed group": "我的工作台重试备注必须使用产品化中文表达",
    "显示模式: ": "我的工作台复制摘要必须使用产品化中文表达",
    "retry_visible_display_grouped', 'grouped": "我的工作台复制摘要不得暴露英文显示模式",
    "retry_visible_display_flat', 'flat": "我的工作台复制摘要不得暴露英文显示模式",
    "Refresh now": "建议动作默认按钮必须使用产品化中文表达",
    "Retry now": "建议动作默认按钮必须使用产品化中文表达",
    "Copy trace": "建议动作默认按钮必须使用产品化中文表达",
    "Refresh the latest data and retry.": "建议动作默认说明必须使用产品化中文表达",
    "Copy trace id for troubleshooting.": "建议动作默认说明必须使用产品化中文表达",
    "Authentication required": "通用错误标题必须使用产品化中文表达",
    "Permission denied": "通用错误标题必须使用产品化中文表达",
    "Invalid request": "通用错误标题必须使用产品化中文表达",
    "Write conflict": "通用错误标题必须使用产品化中文表达",
    "Business rule blocked": "通用错误标题必须使用产品化中文表达",
    "System exception": "通用错误标题必须使用产品化中文表达",
    "Network error": "通用错误标题必须使用产品化中文表达",
    "Request failed": "通用错误标题必须使用产品化中文表达",
    "No work items": "通用空状态必须使用产品化中文表达",
    "No records returned for this action.": "通用空状态必须使用产品化中文表达",
    "return `Context:": "通用错误上下文必须使用产品化中文表达",
    "trace_id={{": "首页入口错误诊断信息必须使用产品化中文表达",
    "label: 'trace_id'": "HUD 标签必须使用产品化中文表达",
    "label: 'record_id'": "HUD 标签必须使用产品化中文表达",
    "Loading cards...": "看板页加载状态必须使用产品化中文表达",
    "Card load failed": "看板页错误状态必须使用产品化中文表达",
    "scene.health response missing": "场景健康契约错误必须转换为产品化中文表达",
    "scene.health missing key": "场景健康契约错误必须转换为产品化中文表达",
    "scene.health.summary critical counters missing": "场景健康契约错误必须转换为产品化中文表达",
    "scene.health.details arrays missing": "场景健康契约错误必须转换为产品化中文表达",
    "页面地址') }}:": "占位页字段展示必须使用中文标点",
    "页面参数') }}:": "占位页字段展示必须使用中文标点",
    "empty contract": "表单契约错误必须转换为产品化中文表达",
    "contract surface markers invalid": "表单契约错误必须转换为产品化中文表达",
    "form config audit failed": "表单页错误兜底必须使用产品化中文表达",
    "action execute failed": "表单页错误兜底必须使用产品化中文表达",
    "chatter timeline load failed": "表单页协作错误兜底必须使用产品化中文表达",
    "chatter post failed": "表单页协作错误兜底必须使用产品化中文表达",
    "chatter activity schedule failed": "表单页协作错误兜底必须使用产品化中文表达",
    "'load failed'": "表单页错误兜底必须使用产品化中文表达",
    "unknown render error": "表单页渲染错误必须使用产品化中文表达",
    "ContractFormPage render error": "表单页渲染错误必须使用产品化中文表达",
    "ActionView render error": "列表页渲染错误必须使用产品化中文表达",
    "contract action failed": "表单页配置操作错误必须使用产品化中文表达",
    "field policy update failed": "表单页字段配置错误必须使用产品化中文表达",
    "custom field create failed": "表单页字段配置错误必须使用产品化中文表达",
    "field order update failed": "表单页字段配置错误必须使用产品化中文表达",
    "contract open action missing action_id": "表单页打开操作错误必须使用产品化中文表达",
    "scene mutation execute failed": "表单页场景操作错误必须使用产品化中文表达",
    "contract not renderable": "表单契约错误必须转换为产品化中文表达",
    "Failed to load my work": "我的工作台错误兜底必须使用产品化中文表达",
    "Legacy List Route": "列表入口页面必须使用产品化中文表达",
    "contract-driven ActionView": "列表入口页面不能暴露前端实现名称",
    "View Context": "页面诊断标题必须使用产品化中文表达",
    "block_type={{": "页面区块兜底不能暴露工程字段名",
    "'unknown error'": "页面错误兜底必须使用产品化中文表达",
    "unknown v2 contract decode error": "表单契约解析错误必须使用产品化中文表达",
    "能力包 JSON": "能力包页面字段标签必须使用产品化中文表达",
    "场景能力包 JSON": "能力包页面占位说明必须使用产品化中文表达",
    "快照 JSON": "配置快照页面错误提示必须使用产品化中文表达",
    "make verify.business_config.snapshot": "配置工作台不能在用户界面暴露工程命令",
    "make verify.lowcode_config.runtime_boundary.guard": "配置工作台不能在用户界面暴露工程命令",
    "make verify.product.surface.clean": "配置工作台不能在用户界面暴露工程命令",
    "Only ui.business.config.contract": "配置整改清单必须使用产品化中文表达",
    "This plan is review evidence": "配置整改清单必须使用产品化中文表达",
    "hud_value_na', 'N/A": "诊断面板空值必须使用产品化中文表达",
    "type={{": "诊断面板不能暴露工程字段名",
    "例如 action_id": "工作台提示不能暴露工程字段名",
    "License:": "授权提示必须使用产品化中文表达",
    "advisory-only": "场景交付提示不能暴露工程阶段术语",
    "direct delivery": "场景交付提示不能暴露工程阶段术语",
    "scope || 'unknown'": "分析页面错误上下文必须使用产品化中文表达",
    "导出重试 JSON": "我的工作台操作按钮必须使用产品化中文表达",
    "复制 Trace": "我的工作台操作按钮必须使用产品化中文表达",
    "导出失败 CSV": "我的工作台操作按钮必须使用产品化中文表达",
    "重试请求 JSON": "我的工作台反馈必须使用产品化中文表达",
    "失败明细 CSV": "我的工作台反馈必须使用产品化中文表达",
    "当前 License": "授权提示必须使用产品化中文表达",
    "导出 CSV": "分析页面操作按钮必须使用产品化中文表达",
    "Scene 能力包": "能力包页面说明必须使用产品化中文表达",
    "JSON.stringify(packages": "能力包页面不能直接展示原始结构数据",
    "JSON.stringify(dryRunResult": "能力包预检查结果必须使用产品化摘要",
    "<pre v-if=\"exportResult\"": "能力包导出结果必须使用产品化摘要",
    "JSON.stringify(health.details": "场景健康明细必须使用产品化清单",
    "replay_audit_id:": "我的工作台重放审计信息必须使用产品化中文表达",
    "replay_age_ms:": "我的工作台重放耗时必须使用产品化中文表达",
    "payload.action || 'unknown'": "我的工作台建议动作反馈必须使用产品化兜底",
    "已触发=": "场景健康状态必须使用产品化中文标点与表达",
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
