# Native View Contract Gap Remediation Plan v1

## Phase A — Contract Baseline Freeze (P0)
目标：统一契约 shape，定义唯一页面结构事实源。

### Actions
1. 冻结统一 shape：`native_view + semantic_page + actions + permissions + record`。
2. 定义 zone/block 标准枚举，建立 schema。
3. 明确 `load_contract` 为主路径，`load_view` 进入 legacy/compat 标识。

### Exit Criteria
- 至少 form/tree/search 三类页面有统一 shape 样例。

## Phase B — Form Closure (P0)
目标：form 页面解析闭环。

### Actions
1. 统一 header/button_box/stat_button 输出。
2. 统一 group/notebook/x2many/chatter/ribbon/statusbar 语义映射。
3. 输出最终 verdict（visible/editable/executable）+ reason。

### Exit Criteria
- 复杂 form 页面可 80%+ 由通用渲染器直接消费。

## Phase C — Tree/Search/Kanban Closure (P1)
目标：列表/搜索/看板进入统一复用体系。

### Actions
1. tree columns/row actions/batch semantics 统一。
2. search filters/group_by/searchpanel 边界统一。
3. kanban card semantic extraction 与 grouping hints 统一。

### Exit Criteria
- 前端不再为特定模型手写列或卡片结构。

## Phase D — Governance & Verification (P0/P1)
目标：能力进入持续治理。

### Actions
1. 增加 semantic shape snapshot。
2. 增加样本页面 compare（8 类）。
3. 增加 capability coverage 报告。
4. 接入 release gate（退化即阻断）。

### Exit Criteria
- 任意一次契约能力退化可被自动检测。
