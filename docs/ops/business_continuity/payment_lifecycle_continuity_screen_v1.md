# Payment Lifecycle Continuity Screen v1

## 目的

确认 no-contract submit 能力补齐后，导入付款事实在提交、审批、办结、台账链路上是否还存在明显阻断。

## 架构定位

- Layer Target: Business Fact Screening
- Module: imported payment lifecycle continuity
- Ownership: construction industry business continuity
- Backend sub-layer: business-fact layer

## 只读筛查结果

筛查范围为导入付款记录，共 `30102` 条。

| 分类 | 数量 |
| --- | ---: |
| done + validated | 12194 |
| draft + no validation | 17908 |
| linked payment ledger | 12194 |
| done without ledger | 0 |
| approved without ledger | 0 |
| submit not validated | 0 |
| draft no contract and no settlement | 10429 |
| draft with settlement and no contract | 0 |
| draft with contract | 7479 |

## 判断

- 已完成付款事实与台账事实一致：`done` 记录均有 `payment.ledger`。
- 当前导入数据没有停留在 `submit` 或 `approved` 的半流程记录。
- 剩余可继续办理的重点是 `draft` 记录。
- `10429` 条 `draft` 付款为无合同、无结算单场景，符合企业日常支出候选；上一批 no-contract submit 修复后，业务规则层已经允许其继续提交。
- `draft with settlement and no contract = 0`，当前没有结算付款绕过合同一致性的导入候选。

## 风险

本轮未发现审批后半程的已知数据阻断风险。

## 下一步

执行 rollback-only 端到端探针：选择真实导入项目和无合同、无结算付款候选，模拟提交、审批通过、生成付款台账、办结，全程回滚，验证新系统可以继续办理日常付款。
