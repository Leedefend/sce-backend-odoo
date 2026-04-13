# Envelope Candidate Screen v1

来源：`artifacts/architecture/envelope_consistency_audit_v1.json`
阶段：`screen`

## Screen规则

- 仅基于既有审计产物分类，不重扫仓库。
- 仅分类，不修改运行时代码。
- 按 `route_method_count` 划分治理优先级：
  - **Tier-1**：`<=1`
  - **Tier-2**：`2~3`
  - **Tier-3**：`>=4`

## 分类结果摘要

- candidate_count: `9`
- envelope_shape: `no_envelope_signal=9`
- Tier-1: `2`
- Tier-2: `4`
- Tier-3: `3`

## 下一批顺序（冻结）

1. Tier-1：`platform_scenes_api.py`, `platform_ui_contract_api.py`
2. Tier-2：`platform_capability_catalog_api.py`, `platform_portal_execute_api.py`, `platform_preference_insight_api.py`, `platform_scene_template_api.py`
3. Tier-3：`platform_auth_signup_web.py`, `platform_ops_api.py`, `platform_packs_api.py`

## next_batch 标记

见 `artifacts/architecture/envelope_candidate_screen_v1.json` 中每条的 `next_batch` 字段。
