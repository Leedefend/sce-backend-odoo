# C-line Boundary Screen v1

状态：Screen Freeze（C-line 前置筛查）

## 1. 目标

针对 `handler/orchestrator/service/builder` 混合职责进行结构筛查，冻结可执行切片，避免在高耦合路径直接做跨层改造。

## 2. 扫描范围

- `addons/smart_core/core/intent_router.py`
- `addons/smart_core/core/base_handler.py`
- `addons/smart_core/core/handler_registry.py`
- `addons/smart_core/handlers/system_init.py`
- `addons/smart_core/handlers/load_contract.py`

## 3. 核心发现

1. `intent_router` 仍混合 `env 构建 + dispatch + 扩展加载 + extra cursor commit`。
2. `system_init` handler 聚合面过大（scene/build/governance/data fetch 混于单用例入口）。
3. `load_contract` handler 同时承担模块探测、模型探测、契约返回组装。
4. handler 层与 builder/service 层之间仍有“直接跳层调用”现象。

## 4. Tier 分类（screen only）

### Tier-1（优先 implement）

1. `intent_router` 的 env/cursor 责任拆分
   - 目标：抽离 `env resolver + cursor lifecycle policy`，router 只做分发。
2. `system_init` 的 data fetch 与 contract assembly 拆分
   - 目标：handler 只做用例编排，数据抓取/组装下沉到 service/builder。

### Tier-2（次优先）

1. `load_contract` 结构拆分
   - 目标：模型存在性探测、权限探测、输出组装分到 dedicated helper。
2. `handler_registry` 与 intent metadata 对齐
   - 目标：保留兼容扫描，但优先走已冻结的 registry entries 元数据源。

### Tier-3（收尾）

1. `BaseIntentHandler` 输入/输出对象标准化
   - 目标：为 `IntentExecutionResult` 接入做适配，避免裸 dict 漫延。
2. 历史兼容 alias/路径的最小化
   - 目标：通过 adapter 保留兼容，主链仅保留冻结命名。

## 5. next implement slices（冻结）

1. `C1-1`：intent_router env/cursor policy 抽离（保持外部行为不变）
2. `C1-2`：system_init 用例内 data fetch helper 化（先提取再替换）
3. `C1-3`：load_contract handler 边界收敛
4. `C1-4`：handler output object 化接入与兼容 adapter 收尾

## 6. 风险与停止条件

- 本批仅 screen，不改运行时代码。
- C-line implement 如触及 `security/**`、`ir.model.access.csv`、`record_rules/**`，必须触发 stop 并单独授权。
- 若发现契约字段口径变化风险，先开 verify/snapshot 批次再实施。
