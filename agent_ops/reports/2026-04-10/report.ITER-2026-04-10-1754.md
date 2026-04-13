# ITER-2026-04-10-1754 Report

## Batch
- Batch: `P1-Batch77`
- Mode: `implement`
- Stage: `frontend form container-hierarchy native parity root-fix`

## Architecture declaration
- Layer Target: `frontend contract-consumer runtime`
- Module: `form container hierarchy title consumption`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 用户要求继续结构对齐，本批移除前端对容器标题的隐式抹平，回归契约真值消费。

## Change summary
- 更新 `frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts`
  - 移除 `buildContainerSections` 对 `page/sheet/header` 的空标题覆盖。
  - 容器标题改为直接继承 contract 结构语义。
- 更新 `frontend/apps/web/src/components/template/DetailShellLayout.vue`
  - 移除 native-like 下对 `信息分组/分组` 的标题隐藏逻辑。
  - tab panel 中 section 标题不再因通用词被静默抹除。
- 更新 `scripts/verify/form_render_profile_frontend_consumer_audit.py`
  - 新增容器层级防回退门禁：
    - `has_container_title_override_blank=false`
    - `hides_generic_group_title_in_tab=false`
    - `hides_generic_group_title_in_normalize=false`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1754.yaml` ✅
- `python3 scripts/verify/form_render_profile_frontend_consumer_audit.py --json` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：仅前端容器标题消费策略收敛，不改后端契约、不改业务事实。

## Rollback suggestion
- `git restore frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts`
- `git restore frontend/apps/web/src/components/template/DetailShellLayout.vue`
- `git restore scripts/verify/form_render_profile_frontend_consumer_audit.py`

## Next suggestion
- 用户复测项目详情页，重点核对 group/page/notebook 标题显示是否与 `tmp/json/form.json` 一致。
