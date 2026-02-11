# Ops 文档入口

本目录聚合发布、验证、运行治理相关文档。

## 主要入口
- Release 证据目录: `docs/ops/releases/`
- 验证入口（含 strict/兼容模式说明）: `docs/ops/verify/README.md`
- 场景观测命令分层:
  - preflight smoke: `make verify.portal.scene_observability_preflight_smoke.container`
  - gate smoke aggregate: `make verify.portal.scene_observability_gate_smoke.container`
  - smoke aggregate: `make verify.portal.scene_observability_smoke.container`
  - strict aggregate: `make verify.portal.scene_observability_strict.container`
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`
- 临时归档（非正式、仅追溯）: `docs/ops/releases/archive/temp/`

## 与契约/审计的关系
- Contract 总览: `docs/contract/README.md`
- Audit 入口: `docs/audit/README.md`

## Bilingual
- English version: `docs/ops/README.en.md`
