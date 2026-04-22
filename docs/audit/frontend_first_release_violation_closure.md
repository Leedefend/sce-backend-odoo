# Frontend First Release Violation Closure

## 范围

- 本轮仅收口首发链路相关越层
- 允许扫描文件：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/views/SceneView.vue`
  - `frontend/apps/web/src/layouts/AppShell.vue`
- 说明：
  - 用户清单中的 `frontend/apps/web/src/AppShell.vue` 与仓库实际路径不一致，实际文件为 `frontend/apps/web/src/layouts/AppShell.vue`

## 越层点清单

### A. 首发链路关键点

- [HomeView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/HomeView.vue#L1249)
  - 旧点位：
    - `todoActionLabel()` 通过关键词推断“审批/合同/风险/变更/任务”
    - `actionLabel()` 通过标题/sceneKey/entryKey 关键词推断业务动作
  - 问题：
    - 前端根据文本猜业务语义
    - 不属于纯 contract consumption

### B. 非首发链路或非本轮最短路径

- [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2678)
  - `load()`、`runContractAction()`、batch runtime 仍偏重，属于页面运行时过载
- [SceneView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/SceneView.vue#L280)
  - scene resolve + route rewrite 仍耦合
- [AppShell.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/layouts/AppShell.vue#L296)
  - role/delivery 文案归一、topbar 形态 heuristics 仍在 shell 内

## 已修复清单

- [HomeView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/HomeView.vue#L95)
  - `todoActionLabel()` 改为：
    - 优先消费后端提供的 `action_label`
    - 缺失时仅使用中性 fallback `查看详情`
  - [HomeView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/HomeView.vue#L1672)
  - `actionLabel()` 改为：
    - 锁定/预览/只读继续用状态型 UI 文案
    - READY 场景优先消费 `entry.actionLabel`
    - 缺失时仅使用中性 fallback `进入处理`
  - [HomeView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/HomeView.vue#L1064)
  - `concreteTodos`、`entries` 增补 `actionLabel` 字段承接 contract/数据侧标签
- [SceneView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/SceneView.vue#L304)
  - `scene not found` 不再直接打到错误页
  - 改为统一走 `workbench` 诊断降级，保持首发链路异常处理口径一致
- [AppShell.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/layouts/AppShell.vue#L319)
  - `normalizeDeliveryText()` 不再做角色业务映射，只保留中性展示清洗
  - `resolveDeliveryRoleLabel()` 不再按 role code 推导“项目经理/财务主管/采购经理”等业务角色名
  - shell 对角色展示改为优先消费 contract/后端标签，缺失时仅回退到原始 code 文本

## 未修复清单

- [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue)
  - 运行时装配仍重
  - 但当前文件已明显拆到 runtime/composable 驱动，库存文档行号与现状有漂移，不适合作为本轮最短收口目标
- [SceneView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/SceneView.vue)
  - 路由/目标解析仍偏厚

## 风险评估

- 本轮修复消除了首发链路内最直观的“前端文本关键词猜业务”问题
- 同时收口了首发链路场景缺项时的错误页分叉
- 同时收口了 shell 对业务角色名的前端推导
- 但前端尚未整体回到纯渲染层
- 因此结论是：
  - `首发链路更接近 contract-only`
  - `前端整体仍未完成架构冻结`
