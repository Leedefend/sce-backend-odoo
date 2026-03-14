# Odoo 原生承载差距迭代进展（v3.36-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 复核结论（P1）

1. 双表单引擎分叉：已基本补齐  
   - `/f/:model/:id` 与 `/r/:model/:id` 均已统一至 `ContractFormPage`
2. x2many 编辑语义：已补齐到当前目标  
   - 已具备命令语义层与 inline 编辑守卫
3. 搜索 `group_by/saved_filters` 消费：已补齐  
   - 前端 `ActionView` 与后端 `api.data` 已形成闭环

## 发现并补齐的缺口

1. `frontend_contract_route_guard` 仍要求旧 token `component: RecordView`，与当前单引擎实现不一致。
2. 已修复守卫：
   - `required_tokens` 改为要求 `ContractFormPage`
   - `forbidden_tokens` 新增禁止 `component: RecordView`

## 验证结果

1. `make verify.frontend.x2many_command_semantic.guard`：PASS
2. `make verify.frontend.x2many_inline_edit.guard`：PASS
3. `make verify.frontend.search_groupby_savedfilters.guard`：PASS
4. `make verify.frontend.contract_route.guard`：PASS

## 结论

评估报告定义的 P1 差距在当前分支已补齐；本轮完成了最后一处治理一致性缺口修复。

## 已知问题跟踪（新增）

- `usage.track` 并发序列化冲突问题记录：
  - 中文：`docs/ops/assessment/usage_track_serialization_issue_iteration_2026-03-14.md`
  - 英文：`docs/ops/assessment/usage_track_serialization_issue_iteration_2026-03-14.en.md`
- 当前状态：已完成止血，前端不再因该问题出现 `intent` 500；后续将按记录中的 backlog 继续做异步化与观测增强。
