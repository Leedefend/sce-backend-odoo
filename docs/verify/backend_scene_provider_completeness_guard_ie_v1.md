# Backend Scene Provider Completeness Guard IE v1

状态：PASS  
批次：`ITER-2026-04-22-BE-SCENE-PROVIDER-COMPLETENESS-GUARD-IMPLEMENT-IE`

## 1. 目标

把 provider completeness 从场景治理规范里的要求推进到机器校验。

本批不改变任何 scene runtime 行为，只新增一个独立 verify surface：

- 每个已导出的治理态 scene 至少要满足其一：
  - 已注册 provider
  - 已声明 explicit fallback

## 2. 校验面

脚本：`python3 scripts/verify/backend_scene_provider_completeness_guard.py`

输入来源：

- `docs/architecture/scene-governance/assets/generated/provider_completeness_current_v1.csv`

## 3. 当前规则

- `provider_registered=true` 视为完整
- `explicit_fallback_present=true` 视为当前阶段可接受的 fallback-complete
- 只有当两者都不存在时才判定 FAIL

## 4. 产物

脚本运行后会输出：

- `artifacts/backend/backend_scene_provider_completeness_guard.json`
- `artifacts/backend/backend_scene_provider_completeness_guard.md`

## 5. 当前阶段意义

这一批通过以后，场景治理包已经不再把 provider completeness 停留在说明性文字，而是具备了最小可执行门禁。

后续如果某个治理态 scene 既没有 provider，又没有任何 route/menu/action fallback，guard 会直接拦住。
