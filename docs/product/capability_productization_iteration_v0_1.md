# Phase-Capability-Productization-v0.1 交付清单

## 目标

将稳定的五层架构组织为可交付产品能力，完成能力目录化、场景产品化、用户入口产品化与模板化编排。

## 产物映射

1. Task 1 能力总表
- `docs/product/capability_catalog_v1.md`
- `docs/product/capability_catalog_v1.json`

2. Task 2 能力分组规范
- `docs/product/capability_grouping_v1.md`

3. Task 3 Scene Catalog v2
- `docs/product/scene_catalog_v2.md`
- `docs/product/scene_catalog_v2.json`

4. Task 4 Capability → Scene 映射
- `docs/product/capability_scene_mapping_v1.md`
- `docs/product/capability_scene_mapping_v1.json`

5. Task 5 角色视角场景矩阵
- `docs/product/role_scene_matrix_v1.md`

6. Task 6 Portal 菜单能力/场景双维导航
- 前端已有场景入口主链，能力侧通过 Home 能力分组与过滤消费：
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/layouts/AppShell.vue`

7. Task 7 首页/工作台产品总入口
- 首页已按“我的工作/核心场景/风险/经营/能力分组”组织：
  - `frontend/apps/web/src/views/HomeView.vue`

8. Task 8 Capability/Scene Inspector
- HUD 增补 scene-capability 诊断字段：
  - `frontend/apps/web/src/layouts/AppShell.vue`

9. Task 9 能力成熟度矩阵
- `docs/product/capability_maturity_matrix_v1.md`

10. Task 10 能力缺口 backlog
- `docs/product/capability_gap_backlog_v1.md`

11. Task 11 施工企业模板
- `docs/product/templates/construction_enterprise_template_v1.md`

12. Task 12 业主管理模板草案
- `docs/product/templates/owner_management_template_draft_v1.md`

## 生成方式

本轮目录类产物由脚本统一生成，避免手工漂移：

- `scripts/product/build_capability_productization_v1.py`

执行：

```bash
python3 scripts/product/build_capability_productization_v1.py
```

## 本轮最小验证结果

- `make verify.frontend.quick.gate` PASS
- `make verify.portal.dashboard` PASS
- `make verify.portal.load_view_smoke.container` PASS
- `make verify.portal.scene_target_smoke.container` PASS
