---
name: playwright-ui-check
description: 使用 Playwright 对关键页面进行契约消费与启动链回归检查。
metadata:
  short-description: UI 回归与契约消费检查（强化版）
---

# Playwright UI Check

## Use When
- 契约结构（schema / ui.contract / role_surface）发生变化
- 启动链（login / system.init / default_route）发生变化
- 页面消费逻辑（store / schema / block 渲染）发生变化
- 引入新页面或调整关键场景（projects / portal / dashboard）

## Test Scope（分层覆盖）

1. 启动链层：登录 → system.init → ui.contract
2. 路由层：default_route / scene 跳转 / fallback
3. 页面层：block 渲染 / 空态 / 错误态
4. 契约消费层：是否存在前端推导行为

## Core Test Cases（必须覆盖）

1. 登录链路

   - 登录成功后必须触发：`system.init → ui.contract`
   - store 状态完整初始化（role / capabilities / menu）

2. 默认路由

   - 首屏跳转符合 `default_route`
   - 不允许 fallback 到 workbench（除非明确）

3. 契约消费

   - 页面仅消费 contract 提供字段
   - 不存在前端补字段 / 推导语义

4. 页面渲染

   - block 正确渲染（list / form / tiles）
   - 空态（empty）可见且无报错
   - 错误态（error）展示 trace_id

5. 关键交互

   - suggested_action 可执行
   - execute_button 正常返回
   - 页面刷新无状态丢失

## Hard Constraints

- 不允许跳过启动链测试。
- 不允许仅验证 UI 表面（必须校验 contract 数据）。
- 不允许使用 mock 替代真实 contract（除非明确隔离测试）。
- 不允许在失败状态下进入下一批次。
- 不允许将 UI 问题归因模糊（必须区分 contract vs frontend）。

## Execution

```bash
# 基础回归
make verify.portal.e2e

# 指定场景
make verify.portal.scene SCENE=projects.list

# 启动链专项
make verify.portal.bootstrap
```

## Assertions（关键断言）

- `system.init` 返回成功且字段完整
- `ui.contract` 包含：
  - role_surface.role_code
  - default_route
  - capabilities
- 当前 route === default_route
- 页面无 console error / uncaught exception

## Result Output（必须产出）

- 用例清单（case_id / 场景 / 覆盖点）
- 通过率（pass / total）
- 失败用例：
  - 截图路径
  - trace_id
  - 对应接口响应（system.init / ui.contract）
- 失败归因：
  - contract 缺失
  - contract 错误
  - frontend 消费错误

## Artifacts Path（标准路径）

- `/artifacts/playwright/screenshots/*`
- `/artifacts/playwright/traces/*`
- `/artifacts/playwright/logs/*`

## Failure Classification

- CONTRACT_MISSING：后端未提供字段
- CONTRACT_INVALID：字段结构错误
- FRONTEND_OVER_DERIVE：前端自行推导
- ROUTE_MISMATCH：default_route 不一致
- RENDER_ERROR：组件渲染异常

## Rollback Strategy

- 回退 contract snapshot
- 回退 frontend schema/store
- 临时启用 compat/default fallback
- 标记失败用例并阻断发布

## Anti-Patterns（禁止）

- 仅看页面截图判断通过
- 忽略 console error
- contract 变更未更新测试用例
- 用 try/catch 吞掉错误通过测试
- 未记录 trace_id 即判定失败原因

## Batch Reminder

```text
当前批次必须明确：
- 是否影响启动链
- 是否影响 contract/schema
- 是否影响 default_route

未明确，不允许执行 UI 回归
```
