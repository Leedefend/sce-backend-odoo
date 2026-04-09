# ITER-2026-04-09-1466 Report

## Batch
- Batch: `1/1`
- Mode: `scan`

## Scan evidence
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1466.yaml` ✅
- bounded `rg` scan on declared files ✅

## Candidate output (scan-only)
```json
[
  {
    "path": "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py",
    "module": "smart_core.app_config_engine.page_assembler",
    "feature": "search contract fallback to empty",
    "reason": "当 app.search.config 缺失时 data.search 直接置空（{ }），可能导致前端搜索/筛选/分组面板输入源缺失"
  },
  {
    "path": "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py",
    "module": "smart_core.app_config_engine.page_assembler",
    "feature": "tree columns strict fallback only",
    "reason": "tree 视图在无解析列时仅回填 columns/default_order，未见同级编辑/交互语义回填"
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue",
    "module": "frontend.action_view",
    "feature": "preferNativeListSurface gating",
    "reason": "list 模式下多个契约区块按 vm.content.kind 与 preferNativeListSurface 条件隐藏，可能与原生列表工具条表达口径不同"
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue",
    "module": "frontend.action_view",
    "feature": "searchPanel/searchableFields merge",
    "reason": "搜索面板候选由 sceneReadyListSurface 与本地去重集合合并生成，存在契约消费路径分叉候选"
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "frontend.page_toolbar",
    "feature": "advanced filter source composition",
    "reason": "saved/group/searchpanel 三组 chips 由本地 advancedFiltersSource 组合与开关控制，可能影响原生筛选交互一致性"
  },
  {
    "path": "frontend/apps/web/src/pages/ListPage.vue",
    "module": "frontend.list_page",
    "feature": "grouped sorting and grouped blocks",
    "reason": "列表页存在 groupedRows/sortedGroupedRows 与分组块渲染分支，需核对是否与原生分组+排序行为等价"
  },
  {
    "path": "frontend/apps/web/src/pages/ContractFormPage.vue",
    "module": "frontend.contract_form_page",
    "feature": "native fallback and writable value pipeline",
    "reason": "form 页面同时存在 native fallback、policy validation 与 collectWritableValues 写入链，需核对只读/可写态与原生一致性"
  },
  {
    "path": "scripts/verify/native_business_admin_config_center_intent_parity_verify.py",
    "module": "verify.native_parity",
    "feature": "parity verification scope",
    "reason": "当前验证文档显示字段与 rights 对齐，但未直接覆盖原生搜索/分类/排序/行内编辑交互语义"
  }
]
```

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：扫描批次仅输出候选，不做结论与实现。

## Next suggestion
- 进入 `screen`：仅对上述候选做“后端契约承载不足 / 前端消费岔路 / 验证覆盖不足”三类归档。
