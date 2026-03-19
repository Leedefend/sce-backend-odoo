# ARCHITECTURE_GUARD

本文件是仓库级架构护栏入口，面向：
- 开发者
- Codex / Cursor / Copilot / 其他 AI 执行体

## 必须遵守
- 先声明 `Layer Target / Module / Reason`，再实施改动。
- 严禁跨层实现功能（业务逻辑不得进入 Page/Frontend，数据库访问不得进入 Scene）。
- 平台能力统一归属 `addons/smart_core`，行业模块不得重复实现平台内核。

## 核心参考
- 详细规则：`docs/architecture/ai_development_guard.md`
- 前端页面规范：`docs/architecture/native_view_reuse_frontend_spec_v1.md`
- 五层核心边界：`docs/architecture/five_layer_core_boundary_v1.md`
- 场景编排层设计：`docs/architecture/scene_orchestration_layer_design_v1.md`
- 场景契约规范：`docs/architecture/scene_contract_spec_v1.md`
- 导航分组标准词表（中）：`docs/architecture/nav_group_terms_v1.md`
- Navigation Group Terms (EN): `docs/architecture/nav_group_terms_v1.en.md`
- 文档双语一致性检查清单（中）：`docs/architecture/doc_bilingual_consistency_checklist_v1.md`
- Documentation Bilingual Consistency Checklist (EN): `docs/architecture/doc_bilingual_consistency_checklist_v1.en.md`
- 执行与验证白名单：`docs/ops/codex_execution_allowlist.md`

## PR 最低要求
PR 描述必须包含：
- `Architecture Impact`
- `Layer Target`
- `Affected Modules`

缺失任一项，不允许合并。
