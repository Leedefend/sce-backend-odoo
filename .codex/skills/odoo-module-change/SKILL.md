---
name: odoo-module-change
description: 约束 Odoo 模块改动方式，确保模型、注册、依赖、升级与兼容路径完整。
metadata:
  short-description: Odoo 模块安全改动流程（强化版）
---

# Odoo Module Change

## Use When
- 修改 `addons/*` 内 model/service/controller/security/view/handler
- 涉及 contract / intent / registry / schema 变更
- 涉及升级（`-u`）或缓存刷新路径

## Pre-Change Map
1. 定位模块 `__manifest__.py`（依赖链、data、assets）。
2. 定位入口：model / service / controller / registry / handler。
3. 明确调用链：intent → service → model → view/contract。
4. 标记 public intent / route / contract 输出面。
5. 标记兼容面：alias / default / deprecate。
6. 评估升级路径：是否需要 `-u`、重启、清缓存。

## Change Order（强制顺序）
1. 先定义/更新 schema（contract / 字段 / response 结构）。
2. 再实现 model/service 逻辑。
3. 再接入 controller / intent。
4. 最后补 view / 数据 / seed。

## Hard Constraints
- 不得修改 public intent 名称（除非本批次声明破坏性变更）。
- 不得跳过升级路径评估（必须明确 `-u` / restart / cache）。
- 不得让前端承担后端语义缺失（contract 必须完整）。
- 新增字段/契约必须同步：
  - snapshot
  - schema/type
  - 验证脚本
- 保持 backwards compatibility：
  - alias 映射
  - default fallback
  - deprecate 标记
- 非本批次目标，禁止顺手重构（尤其 registry / intent router）。
- 未拍板语义禁止编码：
  - role 真源
  - compat 生命周期
  - default_route 策略
- 不得影响启动主链：`login → system.init → ui.contract`。
- 不得跨模块引入隐式依赖（必须 manifest 显式声明）。

## Compatibility Strategy
- alias：旧字段/intent → 新语义映射
- default：缺省值由后端补齐（不可前端兜底）
- deprecate：标记 + 日志提示 + 保留一周期
- remove：仅在明确批次执行

## Verification
- 模块升级：
  ```bash
  make mod.upgrade MODULE=xxx
  ```
- 启动链验证：
  ```bash
  make verify.system.init
  make verify.ui.contract
  ```
- 契约快照：
  ```bash
  make codex.snapshot.export
  ```
- 回归：相关 intent / 页面 smoke 测试通过

## Required Output
- 模块影响图（入口/依赖/调用）
- 变更清单（model/service/controller/view）
- 兼容策略（alias/default/deprecate）
- 升级步骤（命令 + 是否重启）
- 验证结果（命令 + artifacts 路径）
- 回滚方案（恢复 manifest / 字段 / snapshot）

## Rollback Strategy
- 保留旧字段/旧 intent（alias 保底）
- snapshot 回退
- 数据结构回滚（必要时 migration script）
- 快速降级到上一 tag / commit

## Anti-Patterns（禁止）
- 直接改 controller 输出绕过 service
- contract 未定义直接返回临时字段
- 前端兜底 default/compat
- 修改 intent/router 但未更新 snapshot
- 一个批次同时改：contract + 启动链 + UI
- 未升级模块直接验证功能

## Batch Reminder
```text
当前批次必须明确：
- 是否涉及 Odoo 模块变更
- 是否涉及 contract/schema 变更
- 是否需要升级（-u）

未明确，不允许进入编码
```
