# Contract Alignment Acceptance v1 · Batch B

## 目标
- 核对六对象在 `create/edit/readonly/restricted/deny-path` 语义上，contract 表达与原生事实是否一致。
- 本批次仅做证据核对，不修改前后端实现。

## 证据基线
- Contract 消费门禁：
  - `frontend/apps/web/src/api/contract.ts:47`
  - `frontend/apps/web/src/views/ActionView.vue:1713`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:469`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:505`
- 原生可办理与拒绝验证：
  - `scripts/verify/native_business_fact_native_operability_closure_verify.py:149`
  - `scripts/verify/native_business_fact_native_operability_closure_verify.py:201`
  - `scripts/verify/native_business_fact_native_operability_closure_verify.py:292`
  - `scripts/verify/native_business_fact_payment_settlement_operability_verify.py:168`
  - `scripts/verify/native_business_fact_payment_settlement_operability_verify.py:176`
  - `scripts/verify/native_business_fact_payment_settlement_operability_verify.py:231`
- 批次运行结果：
  - `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1296.md:25`
  - `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1297.md:7`

## 一致性矩阵（Contract ↔ Native）
| 对象 | create | edit | readonly/restricted | deny-path | 结论 |
|---|---|---|---|---|---|
| `project.project` | Contract 以 `rights.create` + runtime 门禁控制可创建；native 由 owner 成功创建项目 | Contract 以 `rights.write` + runtime 门禁控制可编辑；native 成功写入关键岗位字段 | Contract `render_profile` + `scene runtime` 可进入只读/受限态 | native 侧 outsider 计数为 0（不可见） | 一致 |
| `project.task` | Contract 通用 form/create 链路；native 由 PM 成功创建 task | Contract 写入依赖 `canSave`；native 成功编辑名称与阶段 | Contract runtime 受限即不可持久化 | native outsider 不可见且写入拒绝 | 一致 |
| `project.budget` | Contract 通用 create 门禁；native 成功创建 budget | Contract 通用 edit/write 门禁；native 写能力在授权成员条件下成立 | Contract runtime `restricted` 时阻断提交 | native outsider 不可见且写入拒绝 | 一致 |
| `project.cost.ledger` | Contract 通用 create；native 成功创建 cost 记录 | Contract 通用 edit/write 门禁；native 写能力在授权成员条件下成立 | Contract runtime 受限时阻断提交 | native outsider 不可见 | 一致 |
| `payment.request` | Contract 通用 create + action 面；native finance 角色创建成功 | Contract 通用 edit/write + action 约束；native finance 编辑成功 | Contract runtime 可声明 readonly/restricted | native outsider 不可见且写入拒绝 | 一致 |
| `sc.settlement.order` | Contract 通用 create；native finance 创建成功 | Contract 通用 edit/write；native finance 编辑成功 | Contract runtime 只读/受限态可表达 | native outsider 不可见且写入拒绝 | 一致 |

## 结论
- 六对象在最小办理链上，`create/edit/deny-path` 与 contract 门禁表达同向一致。
- `readonly/restricted` 的前端门禁由 contract runtime 统一承载，语义对齐原生“不可写”结果。
- 本批次结论：`PASS`（无 contract-native 语义冲突）。

## Batch C 输入（contract-frontend 消费核对）
- 检查前端真实读取字段集合是否与 Batch A 冻结候选一致。
- 检查是否存在前端兜底掩盖 contract 不规范字段的情况。
- 输出 consumer dependency 清单，并标注可冻结字段面。
