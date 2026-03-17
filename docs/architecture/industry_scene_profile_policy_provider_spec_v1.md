# Industry Scene Profile / Policy / Provider Spec v1

## 三件套职责冻结

### Profile

- 管什么：页面结构（`page.zones`、`blocks`、默认动作位、默认搜索位）。
- 不管什么：动态业务规则、运行时数据查询。

### Policy

- 管什么：角色/租户/环境下的可见性、动作门控、排序与阈值策略。
- 不管什么：页面字段定义、底层数据库读取。

### Provider

- 管什么：向编排层提供运行时数据片段（guide、metrics、next actions、workflow context）。
- 不管什么：发明新契约协议。

## 统一约束

- 行业层不得定义独立 schema；必须复用平台 scene-ready schema。
- 行业层不得直接下发页面私有 payload 给前端绕过编排层。

## 推荐目录

- `addons/smart_construction_scene/scenes/`
- `addons/smart_construction_scene/policies/`
- `addons/smart_construction_scene/providers/`

