# 文档总入口（Docs Hub）

本目录为系统文档导航入口，围绕当前已落地能力组织：`contract` / `ops` / `audit`。

## 方向锚点
- 项目方向锚定文: `docs/00_overview/project_direction.md`
- English mirror: `docs/00_overview/project_direction.en.md`

## 能力域导航
- Contract（契约与目录）: `docs/contract/README.md`
- Ops（发布与运行证据）: `docs/ops/README.md`
- Audit（审计方法与产物入口）: `docs/audit/README.md`
- Baseline Freeze（基线冻结策略）: `docs/ops/baseline_freeze_policy.md`

## 当前权威 Contract Exports
- Intent Catalog: `docs/contract/exports/intent_catalog.json`
- Scene Catalog: `docs/contract/exports/scene_catalog.json`

## 当前阶段 Release 证据（暂不迁移）
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`

## 快速生成/导出（现有 Make 目标）
```bash
make contract.catalog.export
make contract.evidence.export
make audit.intent.surface
```

## Bilingual
- English version: `docs/README.en.md`
