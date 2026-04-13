# ITER-2026-04-10-1777 Report

## Batch
- Batch: `FORM-Consumer-Align`
- Mode: `implement`
- Stage: `frontend form consumer structure alignment`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `form structure consumer and detail shell renderer`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 用户要求先完成消费对齐迭代，优先消除前端对 form contract 结构语义还原不足。

## Change summary
- 收敛 form 结构消费入口：
  - `ContractFormPage` 的布局节点解析新增 `attributes.string/title/name` 标签回退，减少分组标题退化为泛化占位。
  - `container` 节点按语义映射：`oe_button_box -> group`、`oe_title -> header`，避免关键结构丢失。
  - 布局节点新增 `columns` 提取（`cols/col`），并传递到 detail shell 渲染层。
- 收敛 detail shell 渲染：
  - `detailLayoutRuntime` / `detailLayout.types` 增加 `section.columns`，消费层按结构列信息渲染。
  - `DetailShellLayout` 按 section 列数渲染（1/2 列），并在 native-like 模式下移除多余卡片边框与内边距。
- 收敛页签过滤：
  - 项目详情对齐模式下放宽 tab 可见条件，避免存在标题/提示但字段较轻时被误过滤。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1777.yaml` → `PASS`
- `rg -n "resolveLayoutNodeLabel|attributes.string|columns|shell.tabs|projectDetailStructureAlignMode" ...` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：
  - 本批仅改前端消费和模板渲染，不触碰后端语义与业务模型；
  - 主要风险是样式收敛导致局部页面密度变化，需用户前端实测确认视觉一致性。

## Rollback suggestion
- 可按文件级回滚：
  - `git restore frontend/apps/web/src/pages/ContractFormPage.vue`
  - `git restore frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts`
  - `git restore frontend/apps/web/src/components/template/detailLayout.types.ts`
  - `git restore frontend/apps/web/src/components/template/DetailShellLayout.vue`

## Next suggestion
- 建议立即进行“前端页面实测回归”：
  - 项目详情页验证 `header/statusbar/notebook/button_box` 对齐程度；
  - 若仍有结构缺口，再进入后端 `form parser` 定向补齐批次。
