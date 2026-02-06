# TEMP Systematic Scene Target Audit Summary

Last updated: 2026-02-06
Branch: `codex/systematic-scene-target-audit`
Scope: 系统性排查“菜单/Scene 落到 Workbench Unknown”同类问题

## Problem Statement

- 现象：除已修复入口外，仍有部分菜单/Scene 会落到 `workbench`，并出现 Unknown 异常态。
- 目标：系统性收口，确保核心 Scene 不再依赖 `TARGET_MISSING` fallback。

## Root Cause (Confirmed)

1. `projects.intake` 在历史数据（DB scene/imported scene）中可能保留旧值：
   - `target.route=/workbench?scene=projects.intake&reason=TARGET_MISSING`
2. 原有 merge 逻辑仅做“缺失字段补齐”，不会主动把旧 fallback route 升级成可执行 target。
3. 因此即使代码 fallback 已定义更优 target，历史数据仍可继续触发 Workbench fallback。

## Implemented Fixes

1. 明确 `projects.intake` 默认 target
- 文件：`addons/smart_construction_scene/scene_registry.py`
- 变更：为 `projects.intake` 增加
  - `action_xmlid: smart_construction_core.action_project_initiation`
  - 保留 `menu_xmlid: smart_construction_core.menu_sc_project_initiation`

2. 增加历史 fallback 自动升级
- 文件：`addons/smart_construction_scene/scene_registry.py`
- 新增逻辑：`_upgrade_fallback_target(scene, defaults)`
- 行为：当 scene.target 仍是 `/workbench?scene=<code>...TARGET_MISSING`，且 fallback 默认 target 可解析（action/menu/model）时，自动将 target 升级为 fallback 默认 target。

3. 增加核心 Scene 守护脚本
- 文件：`scripts/verify/fe_scene_core_openable_guard.js`
- 目标：防止 `projects.list / projects.ledger / projects.intake` 缺失 action 级 target 定义。

## Verification (Executed)

Passed:
- `node scripts/verify/fe_scene_core_openable_guard.js`
- `node scripts/verify/fe_menu_no_action_smoke.js`

Observation:
- 当前仓库 `docs/contract/exports/scenes/stable/LATEST.json` 仍可见旧 fallback（如 `projects.intake -> workbench`），属于“运行环境未完成模块升级/contract刷新”状态，不代表本次代码修复无效。

## Pending Runtime Steps

1. 升级模块（至少包含 `smart_construction_scene`）使修复进入运行环境。
2. 重新导出 scenes contract（stable）。
3. 复测核心入口：
   - `/s/projects.list`
   - `/s/projects.ledger`
   - `/s/projects.intake`
4. 确认不再落到 `Navigation unavailable / Unknown`。

## Files Changed (This Fix Batch)

- `addons/smart_construction_scene/scene_registry.py`
- `scripts/verify/fe_scene_core_openable_guard.js`

## Status

- 代码修复：已完成（待提交）
- 运行态生效：待执行模块升级与 contract 刷新
