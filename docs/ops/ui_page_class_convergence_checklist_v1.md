# UI Page-Class Convergence Checklist v1

## Scope
- Target classes: `ListPage` / `ContractFormPage` / `KanbanPage`
- Objective: 同一交互语法，降低用户学习成本与交付偏差

## Unified Regions (Mandatory)
- `PageHeader`: 必须有业务标题，禁止模型名主展示
- `PageToolbar`: 主按钮最多 1 个，辅按钮最多 2 个
- `PageFilter`: 搜索语义化，筛选单体系
- `PageContent`: 单页面单业务目标
- `PageFeedback`: 空态/错误态/成功反馈完整

## Class Rules

### ListPage
- 字段列建议 <= 6，主业务字段优先
- 行点击必须可进入详情
- 错误态必须可重试，空态必须可引导下一步

### ContractFormPage
- 标题采用业务语义（示例：`工程结构详情`）
- 操作区统一存在 `返回 + 保存`
- 分组标题必须语义化，禁止 `信息分组`
- Tab 名称不得重复
- 错误反馈必须包含可诊断上下文（reason_code/trace_id）

### KanbanPage
- Header/Filter/Feedback 与 ListPage 语法一致
- 卡片主信息/状态信息语义清晰
- 卡片点击进入同一详情链路

## Prohibited Patterns
- 页面主标题直出模型名（如 `xxx.model 详情`）
- 多套筛选体系并存
- “信息分组/分组/页面分组”作为最终业务标题
- 超过 `1 主 + 2 辅` 的页面级主操作

## Acceptance Gate
- `python3 scripts/verify/page_class_convergence_audit.py` PASS
- `node scripts/verify/unified_system_menu_click_usability_smoke.mjs` PASS
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` PASS

## Next Execution Line
- 在每个页面收敛批次中，把本清单映射为“页面差异单 + 修复项 + 回归证据”。
