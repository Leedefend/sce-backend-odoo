# ITER-2026-04-10-1750 Report

## Batch
- Batch: `P1-Batch73`
- Mode: `implement`
- Stage: `frontend form semantic consumption full-loop closure`

## Architecture declaration
- Layer Target: `frontend contract-consumer runtime`
- Module: `form semantic title/label consumption`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 进入前端消费链完整闭环，确保后端语义标签被前端直接消费而非前端重命名覆盖。

## Change summary
- 更新 `frontend/apps/web/src/pages/ContractFormPage.vue`
  - 新增 `resolveLayoutNodeLabel`，统一优先消费 `node.title`，其次 `string/label`。
  - layout node 与 tree node 字段标签提取统一接入 `title`。
  - 分组树收敛调整：仅在 page/notebook 标题缺失或通用占位时才回退前端默认标题，避免覆盖后端语义。
  - 调试输出中的 rawLayoutFieldOrder 标签同步接入 `node.title`。
- 更新 `frontend/apps/web/src/components/template/DetailShellLayout.vue`
  - `nativeLike` 模式下仅隐藏通用占位标题（`信息分组/分组`），不再隐藏 `主体信息/项目信息` 等业务语义标题。
- 更新 `scripts/verify/form_render_profile_frontend_consumer_audit.py`
  - 增加前端消费链闭环门禁：
    - `consumes_node_title=true`
    - `generic_hide_overbroad=false`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1750.yaml` ✅
- `python3 scripts/verify/form_render_profile_frontend_consumer_audit.py --json` ✅
- `make restart`（服务重启）✅

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：仅前端消费与审计收敛，不改变业务事实/ACL/财务语义。

## Rollback suggestion
- `git restore frontend/apps/web/src/pages/ContractFormPage.vue`
- `git restore frontend/apps/web/src/components/template/DetailShellLayout.vue`
- `git restore scripts/verify/form_render_profile_frontend_consumer_audit.py`

## Next suggestion
- 进入用户侧最终验收：登录前端后抽样验证 `action_id=531`（项目看板详情）分组与页签标题展示一致性。

