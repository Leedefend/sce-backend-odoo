# 项目立项草稿后端能力设计 v1（设计稿）

## 1. 背景
- 当前立项页已具备前端本地暂存能力（`localStorage`），可防止同终端输入丢失。
- 该方案无法覆盖跨终端（跨浏览器/跨设备）一致性。
- 需要补充后端草稿能力，作为“用户无感”的底层支撑。

## 2. 目标
- 为 `projects.intake` 新建态提供跨终端草稿存储与恢复。
- 保持用户心智简单：用户只看到“创建项目”，不暴露“草稿管理”流程。
- 不修改现有 scene key / page key / 主路由 / 主数据协议。

## 3. 非目标
- 本阶段不实现多人协同编辑。
- 不实现复杂版本分支与三方合并。
- 不改变项目创建主流程（创建成功即落 `project.project`）。

## 4. 分层与边界
- Layer Target: Domain + Scene 表达层（不动平台核心机制）。
- Domain 层：草稿模型、服务、权限校验、TTL 清理。
- Scene/UI 层：仅透出“是否有草稿可恢复”的轻量语义。
- Frontend：调用草稿接口，按策略自动保存/恢复，不增加复杂 UI。

## 5. 数据模型建议
模型：`project.intake.draft`

核心字段：
- `user_id`（Many2one, required）
- `company_id`（Many2one, required）
- `scene_key`（Char, default `projects.intake`）
- `draft_key`（Char, required, unique with user+company+scene）
- `payload_json`（Text/Json）
- `schema_version`（Char, default `v1`）
- `status`（Selection: `active`, `consumed`, `expired`）
- `updated_at`（Datetime）
- `expires_at`（Datetime）

唯一约束建议：
- `(user_id, company_id, scene_key, draft_key)`

## 6. 草稿键策略
`draft_key` 组成建议：
- `project.project:intake:standard`
- `project.project:intake:quick`

说明：
- 单用户单模式仅维护一条活跃草稿，避免碎片化。

## 7. 接口契约建议
基于现有 intent 风格，新增 `project.intake.draft.*`。

### 7.1 保存草稿
Intent: `project.intake.draft.save`

入参：
- `scene_key`
- `draft_key`
- `payload`
- `schema_version`

出参：
- `saved: true`
- `updated_at`
- `expires_at`

### 7.2 读取草稿
Intent: `project.intake.draft.get`

入参：
- `scene_key`
- `draft_key`

出参：
- `exists`
- `payload`
- `updated_at`

### 7.3 消费草稿
Intent: `project.intake.draft.consume`

触发：
- 项目创建成功后调用

行为：
- 将草稿标记为 `consumed` 或直接软删

### 7.4 清理过期
Intent/cron: `project.intake.draft.gc`

行为：
- 清理 `expires_at < now()` 的记录

## 8. 生命周期与状态机
- `active`：可恢复、可覆盖保存
- `consumed`：已用于成功创建，默认不再恢复
- `expired`：过期不可用，等待清理

建议 TTL：
- 默认 7 天（可配置）

## 9. 恢复与冲突策略
最小策略（v1）：
- Last-write-wins（按 `updated_at` 最新覆盖）
- 单端编辑不提示冲突

后续可升级：
- 若检测到多终端写入时间差过小，提示“检测到其他终端更新”。

## 10. 安全与权限
- 草稿严格按 `user_id + company_id` 隔离。
- 仅本人可读写本人的草稿。
- 草稿接口沿用现有 ACL/权限基线，不绕过身份验证。

## 11. 前端接入建议（后续实施）
- 打开立项页时：优先请求后端草稿；无草稿则回退本地缓存。
- 输入节流保存：`800ms` debounce。
- 创建成功后：先 `consume` 后端草稿，再清本地缓存。

## 12. 兼容与迁移
- 兼容当前本地缓存方案：
  - 读取优先级：后端草稿 > 本地缓存
  - 写入双轨（过渡期）：后端 + 本地
- 稳定后可降级本地缓存为兜底。

## 13. 验收标准（设计阶段）
- 有明确模型字段与状态机定义。
- 有完整接口清单与调用时机。
- 有跨终端一致性策略与安全边界。
- 明确“不改主流程，仅增强底层能力”。

## 14. 风险与注意事项
- 过于激进的自动保存可能带来无效写放大，需要节流。
- 草稿 payload 需限制大小（建议 < 32KB）。
- schema 升级需有兼容处理（`schema_version`）。

## 15. 结论
- 当前可继续使用本地暂存保障同终端体验。
- 发布前建议补齐后端草稿能力，实现跨终端一致性。
- 本文档为下一阶段实施蓝图，本轮不落代码。

