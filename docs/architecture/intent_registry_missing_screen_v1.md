# Intent Registry Missing Screen v1

来源：`artifacts/architecture/intent_registry_audit_v1.json`
阶段：`screen`

## Screen规则

- 仅基于现有 missing 列表分类，不重扫仓库。
- 仅分类，不做注册实现。
- 分层口径：
  - **Tier-1**：`system/ui/meta/app` 前缀
  - **Tier-2**：`scene/workspace/page/permission/chatter/file/execute/load*`
  - **Tier-3**：其余（主要 `api.*` / `release.*`）

## 分类摘要

- missing_count: `42`
- Tier-1: `11`
- Tier-2: `22`
- Tier-3: `9`

## next_batch 冻结顺序

1. Tier-1：先补平台内核公开面（system/ui/meta/app）
2. Tier-2：再补场景与交互相关入口
3. Tier-3：最后补 `api.*` 与 `release.*` 高变动面

详见：`artifacts/architecture/intent_registry_missing_screen_v1.json` 的 `next_batch` 字段。
