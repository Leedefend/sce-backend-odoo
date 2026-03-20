# 一周封板计划（Week-1）v1

## 目标
- 在 1 周内将交付状态从“可演示”推进到“可试点”。

## Day 1-2：前端封板
- 清零 `frontend gate` 红线（lint/typecheck/build）。
- 封板文件优先级：`ActionView.vue`、`useActionViewBatchRuntime.ts`、`useActionViewGroupedRowsRuntime.ts`、`AppShell.vue`。
- 输出：前端 gate 连续通过记录。

## Day 2-3：契约与引擎封口
- 补齐交付包关键 scene 的 contract/provider shape 验证。
- 确认 9 模块关键场景接入 scene_engine 主链。
- 输出：guard 通过清单与失败归因。

## Day 3-4：真实 gap backlog 建档
- 建立三层 gap：`Blocker` / `Pilot Risk` / `Post-GA`。
- 每条 gap 必须有 owner、截止时间、状态。
- 输出：可追踪 backlog 文档与看板链接。

## Day 4-5：交付证据收口
- 为 9 模块和 4 角色旅程生成 system-bound 验证证据。
- 形成一页式 readiness scoreboard（commit/db/seed/通过率）。
- 输出：发布评审包。

## 通过标准（周五）
- P0 Blocker 全部关闭。
- 9 模块验收矩阵无 `FAIL`。
- 交付证据可复现、可审计、可演示。

