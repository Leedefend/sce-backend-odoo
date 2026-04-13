# Dispatcher Purity Screen v1

状态：Screen Freeze（B2 前置筛查）

## 1. 目标

在不改运行时代码的前提下，对 `addons/smart_core/controllers/intent_dispatcher.py` 做纯分发边界筛查，冻结下一批 implement 的优先级。

纯分发目标定义（B2）：

- Dispatcher 负责：`registry 查找 / request 校验编排 / handler 调用 / 统一异常包装`
- Dispatcher 不负责：`DB 选择策略 / 权限细节构造 / commit 决策 / response 领域语义补丁`

## 2. 现状扫描摘要

扫描函数（热点）：

- `_prepare_dispatch_request`
- `_finalize_dispatch_response`
- `_execute_intent_request`

已识别混合逻辑类型：

1. **上下文策略混入**
   - `_prepare_dispatch_request` 内存在 DB 来源优先级、dev/admin 条件分支、session 回写。
2. **提交策略混入**
   - `_finalize_dispatch_response` 内包含 `_is_write_request` + `request.env.cr.commit()`。
3. **错误语义构造混入**
   - `_permission_error_details` 在 dispatcher 层拼接 `api.data.*` 细节。
4. **兼容补丁混入**
   - `_finalize_dispatch_response` 对 `load_view` legacy 结果进行结构修补。

## 3. Tier 分类（仅 screen，不下结论实现）

### Tier-1（优先实现）

1. `commit policy` 外移
   - 现状：`_finalize_dispatch_response` 中直接 commit。
   - 目标：迁移到独立 `execution/effect policy`，dispatcher 只消费结果。
2. `db resolution policy` 外移
   - 现状：`_prepare_dispatch_request` 包含多来源和环境防护分支。
   - 目标：迁移到 `request context resolver/policy`。

### Tier-2（次优先）

1. `permission error detail` 语义外移
   - 现状：dispatcher 识别 `api.data.*` 并补 model/op。
   - 目标：迁移到 permission/policy 层统一 reason detail builder。
2. `intent alias + schema key` 规则集中
   - 现状：别名与 schema map 在 dispatcher 文件内。
   - 目标：迁移到 registry 元数据或 intent governance helper。

### Tier-3（收尾）

1. `load_view legacy` 兼容修补剥离
   - 现状：response 归一时做 legacy data 提升。
   - 目标：迁移到专门 compatibility adapter，避免污染 dispatcher 主流程。
2. `request normalization` 细节拆分
   - 现状：`params/context/header` 合流集中在同一函数。
   - 目标：拆到独立 normalizer，dispatcher 仅调度。

## 4. next implement batch（冻结）

建议按以下顺序推进：

1. `B2-1`：抽离 DB resolution policy + request normalizer（不改外部契约）
2. `B2-2`：抽离 commit/effect policy（保持 envelope 不变）
3. `B2-3`：抽离 permission detail builder 与 alias/schema governance helper
4. `B2-4`：收口 legacy compatibility adapter

## 5. 风险与停止条件

- 本批是 screen，未修改运行时代码。
- 若 implement 批次涉及 `security/**` 或 financial 语义，必须触发 stop 并新开授权任务线。
