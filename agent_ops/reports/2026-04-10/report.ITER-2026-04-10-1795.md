# ITER-2026-04-10-1795 Report

## Batch
- Batch: `FORM-Consumer-Align-R19`
- Mode: `implement`
- Stage: `tab duplication and business-tab loss root fix`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `detail shell/tab projection and rendering`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 用户反馈 tab 重复与业务 tab 缺失，本轮从渲染重复和过滤误删两处做根因修复。

## Change summary
- `DetailShellLayout.vue`：tab 壳存在时隐藏壳头标题，避免“容器标题 + tab 标签”重复展示。
- `ContractFormPage.vue`：放宽 tab 过滤规则，保留“有业务 label 的 tab”，不再只按 section 字段量过滤。
- 结果：减少重复观感，避免业务 tab 被误吞。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1795.yaml` → `PASS`
- `rg -n "shell.tabs|filteredTabs|normalizeTabLabel" frontend/apps/web/src/components/template/DetailShellLayout.vue frontend/apps/web/src/pages/ContractFormPage.vue` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`low`
- 风险说明：仅前端渲染层与过滤策略调整，不改后端 contract。

## Rollback suggestion
- 文件级回滚：
  - `git restore frontend/apps/web/src/components/template/DetailShellLayout.vue frontend/apps/web/src/pages/ContractFormPage.vue`

## Next suggestion
- 收集新一轮结构摘要与页面截图，确认业务 tab 是否完整回归，再决定是否进入顶部信息区对齐。
