# 迭代问题记录：`usage.track` 并发序列化冲突（2026-03-14）

日期：2026-03-14  
分支：`feat/fix-my-work-scene-target`

## 问题现象

- 前端控制台出现单次 `POST /api/v1/intent?db=sc_prod_sim` 返回 `500`。
- 同一批请求中，`login`、`app.init`、`api.data`、`my.work.summary` 多数正常。
- 典型报错表现为偶发、瞬时，页面主链路通常可继续执行。

## 根因定位

- 后端日志确认错误为 PostgreSQL 事务序列化冲突：
  - `psycopg2.errors.SerializationFailure`
  - `could not serialize access due to concurrent update`
- 冲突位置：`sc_usage_counter`（埋点计数表）并发更新。
- 触发链路：`intent=usage.track` -> `smart_construction_core.handlers.usage_track` -> `sc.usage.counter.bump`。

## 本迭代已做处理（止血）

- `sc.usage.counter.bump` 改为原子 `UPSERT`（`INSERT ... ON CONFLICT DO UPDATE value=value+delta`）。
- 增加 `SerializationFailure(40001)` 的有限重试与降级告警，避免冒泡成接口 500。
- `usage.track` handler 增加兜底，单次计数失败不影响主业务响应。
- 增加并发回归脚本与 Make 目标：
  - `scripts/verify/fe_usage_track_concurrency_smoke.js`
  - `make verify.portal.usage_track_concurrency_smoke.container`

## 当前状态

- 现网体验层面：该类冲突已不再触发 `intent dispatcher failed` 的 500（本次复验窗口内）。
- 仍可见数据库层 `could not serialize access` 噪音日志（已被降级处理）。
- 结论：问题已“止血”，但并发计数路径仍有优化空间。

## 后续迭代待办

- 将 `usage.track` 写入改为异步化/队列化，彻底降低事务竞争。
- 针对热点 key（如 `usage.scene_open.role.admin.*`）做聚合缓冲与批量落库。
- 增加指标观测：
  - 重试次数
  - 降级次数
  - 丢计数估算（可选）
- 在 CI 或 nightly 中固定运行并发 smoke，作为回归门禁之一。

