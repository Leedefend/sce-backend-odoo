# Controller Thin Screen v1

来源：`artifacts/architecture/controller_thin_guard_audit_v1.json`
阶段：`screen`

## Screen规则

- 仅基于 `orm_hints` 候选分类，不重扫仓库。
- 仅分类，不实施代码改造。
- 按 `line_count` 分层：
  - **Tier-1**：`>=35`
  - **Tier-2**：`25~34`
  - **Tier-3**：`<25`

## 分类摘要

- candidate_count: `4`
- Tier-1: `1`
- Tier-2: `1`
- Tier-3: `2`

## next_batch 顺序

1. Tier-1：`platform_meta_api.describe_model`
2. Tier-2：`platform_portal_execute_api.portal_execute_button`
3. Tier-3：`platform_meta_api.describe_project_capabilities`, `platform_execute_api.execute_button`

详见：`artifacts/architecture/controller_thin_screen_v1.json` 的 `next_batch` 字段。
