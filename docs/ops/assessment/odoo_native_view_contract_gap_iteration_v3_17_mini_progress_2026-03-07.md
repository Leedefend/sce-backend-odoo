# Odoo 原生承载差距迭代进展（v3.17-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端契约增强：
   - `api.data(list)` 的 `group_paging` 新增 `window_digest`
   - digest 由当前窗口 `group_key/count` 投影计算并以 SHA1 输出
2. 前端契约消费增强：
   - schema 新增 `group_paging.window_digest`
   - ActionView 新增 `groupWindowDigest` 状态并在 HUD 暴露 `group_window_digest`
3. 保障链路同步：
   - grouped runtime guard 新增 `window_digest` 标记约束
   - grouped semantic smoke/guard 新增 `window_digest` 形状与 hex 一致性校验
4. 文档同步：
   - grouped pagination contract 文档新增 `window_digest` 字段说明

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 契约从“查询身份 + 窗口定位”扩展到“窗口内容摘要”层，可更快定位窗口内容漂移与诊断不一致问题。
