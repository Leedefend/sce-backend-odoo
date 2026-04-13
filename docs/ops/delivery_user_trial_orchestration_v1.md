# Delivery User Trial Orchestration v1

## Trial Objective

- 在冻结基线下组织真实用户试用，验证“可打开/可理解/可操作/可返回/可观测”五项体验。
- 输出可执行问题清单，作为交付前最后一轮收口输入。

## Trial Scope

- baseline: `docs/ops/delivery_freeze_baseline_v1.md`
- menu_snapshot: `artifacts/menu/delivery_user_navigation_v1.json`
- formal_entry_review: `docs/ops/delivery_formal_entry_page_review_v2.md`
- smoke_baseline: `artifacts/codex/unified-system-menu-click-usability-smoke/20260411T181557Z/summary.json`

## Trial Roles

- 业务用户（主试用）：按业务路径执行。
- 交付支持（记录员）：记录问题、trace_id、复现步骤。
- 技术陪同（非干预）：仅在阻断时协助采证，不引导业务判断。

## Trial Paths

### Path A：项目立项主链

1. 进入 `项目立项`
2. 完成最小字段输入并保存
3. 返回列表/工作台
4. 记录是否存在卡顿、迷路、报错

### Path B：执行与成本链

1. 进入 `执行结构`
2. 进入任一详情并返回
3. 进入 `预算/成本`
4. 返回上一级入口

### Path C：合同与付款链

1. 进入 `收入合同` 或 `支出合同`
2. 完成“打开列表→进入详情→返回”闭环
3. 进入 `付款记录` 验证页面可用性

## Acceptance Checklist

- 可打开：页面在 10s 内进入可交互状态。
- 可理解：标题、核心信息、下一步动作可被业务用户独立理解。
- 可操作：至少 1 条关键动作可成功执行。
- 可返回：返回路径稳定，无空白页与路由挂起。
- 可观测：错误态可见 `错误码/TraceID` 或可定位上下文。

## Issue Triage Rule

- P0：阻断流程（无法进入/无法操作/数据丢失风险）
- P1：主要能力受损（高频路径失败）
- P2：体验缺陷（不阻断但明显影响效率）
- P3：文案/样式/次要一致性问题

## Trial Output

- issue_template: `docs/ops/delivery_user_trial_issue_template_v1.md`
- output_board: `artifacts/delivery/user_trial_issue_board_v1.json`（试用后生成）
- decision_note: `GO / GO_WITH_FIXES / NO_GO`
