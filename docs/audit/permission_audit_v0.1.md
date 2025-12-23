# 权限审计报告 v0.1（Smart Construction Core）

## 1. 范围与方法
- 范围：`smart_construction_core` 模块内所有菜单、action、ACL、记录规则。
- 方法：
  - 菜单/Action 一致性扫描（入口闸门）；
  - Actions 无 groups 盘点（本地 XML + DB 补丁收口后应为 0）；
  - ACL/Record Rule 快审（高风险模型）；
  - 最小账号矩阵回归（仅项目/物资/财务/成本/全权）。

## 2. 主要风险结论
- 原风险：菜单有限流但 actions 未设 groups，URL 可绕（初扫 51 个）。
- 重复入口：预算 action 多处定义，已统一 canonical 到 cost_domain 版。
- 当前状态：通过 `security/action_groups_patch.xml` 补闸，合同/资金/结算/成本/物资/采购/字典/工作流/运营/文档/审批回调等核心入口已加 groups，DB 级缺组清单为 0（见附录）。

## 3. 整改批次与结果
- Batch-1（合同/资金/结算）：已补闸，升级验证通过。
- Batch-2（预算/成本）：已补闸，canonical 定为 cost_domain；快速入口同步收口。
- Batch-3（物资/采购）：物资计划、询价向导、审批回调、WBS/BOQ 相关入口补闸。
- Batch-4（字典/工作流/运营/文档/驾驶舱/报表）：补闸完毕。

## 4. 验收标准与回归
- 无权限账号 URL 直达应 AccessError/无权。
- 只读账号可开列表/表单，不可写。
- 经理账号可写/审批。
- URL_BYPASS 风险项目标：0（当前补丁后 DB 清单为 0）。

## 5. 附录
- `docs/audit/action_groups_missing_db.csv`：DB 级 actions 无 groups 清单（当前为空）。
- `docs/audit/action_groups_missing_local_20251223_125555.csv`：XML 层初扫结果（补丁前的原始定义参考）。
- 需生成：菜单-Action-模型-组矩阵 CSV（建议使用 Odoo shell 脚本导出 DB 状态）。

## 6. 后续建议
- 将 “actions 必须有 groups” 纳入 CI 守门（白名单除外）。
- 对 budget 非 canonical action 做 internal 化或删除，避免入口漂移。
- 定期（发布前）跑 DB 级缺组扫描和菜单-Action 矩阵生成，附在发布报告。
