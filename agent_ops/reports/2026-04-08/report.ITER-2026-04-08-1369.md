# ITER-2026-04-08-1369 Report

## Batch
- Batch: `1/1`

## Summary of change
- 针对“原生有值、自定义同页无值（--）”执行契约消费链修复（frontend contract-consumer）。
- 根因 1：`resolveMetaFromContract` 未把 `head.domain/context` 带入 action meta，导致列表请求失去默认筛选。
- 根因 2：场景列在部分路径可能以中文标签进入请求字段，未映射回技术字段名，触发后端字段回退到 `id,name`。
- 修复文件：
  - `frontend/apps/web/src/app/resolvers/actionResolver.ts`
    - 在 fallback meta 中补齐 `domain/context/order`。
  - `frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts`
    - 在 `convergeColumnsForSurface` 中增加“标签 -> 字段名”映射（基于 contract fields 的 `string` 标签）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1369.yaml` ✅
- `make verify.frontend.build` ✅
- `FRONTEND_PROFILE=daily bash scripts/dev/frontend_dev_reset.sh` ✅
- `curl -I --max-time 8 http://127.0.0.1:5174/` ✅ (`HTTP/1.1 200 OK`)

## Risk analysis
- 结论：`PASS`
- 风险级别：medium
- 说明：本批次仅修改前端契约消费逻辑，不涉及 ACL/财务语义/模型结构；仍需你在浏览器对目标页面做一次可视化复核。

## Rollback suggestion
- `git restore frontend/apps/web/src/app/resolvers/actionResolver.ts`
- `git restore frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts`
- `make verify.frontend.build`
- `FRONTEND_PROFILE=daily bash scripts/dev/frontend_dev_reset.sh`

## Next suggestion
- 立即在 `5174` 打开目标页面（系统参数配置）对比原生：
  - 核对筛选后记录数量是否一致
  - 核对 `字典类型/作用域/作用域标识/编码/配置值文本` 不再大面积 `--`
