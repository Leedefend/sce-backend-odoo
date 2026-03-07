# Odoo 原生承载差距迭代进展（v3.20-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端契约协议化：
   - `group_paging.window_identity` 新增 `version/algo`
   - `meta.group_window_identity` 同步新增 `version/algo`
2. 类型契约增强：
   - `ApiDataListResult.group_paging.window_identity` 新增 `version/algo`
3. 验证链路增强：
   - grouped smoke 新增 `window_identity_meta` 公式与 version/algo 一致性检查
   - semantic/consistency/runtime guards 同步新增对应约束
4. 文档同步：
   - grouped contract 增加 `window_identity` 协议字段说明与兼容规则

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 窗口身份从“结构统一”进一步升级到“协议可演进”，为后续摘要算法演进提供稳定契约锚点。
