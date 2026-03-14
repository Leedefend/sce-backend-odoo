# SCEMS v1.0 Round 4 工作台点击链路与验收清单

## 1. 目的

本清单用于把“工作台是否像产品”转化为可验证事实：

- 点击是否触发了预期意图；
- 埋点是否非阻塞；
- 用户是否能一跳进入业务处理页。

## 2. 工作台主链路（用户视角）

### 2.1 首跳加载

1. 打开工作台路由（`/` 或 `/s/portal.dashboard`）；
2. 首次初始化读取 `system.init`；
3. 渲染 `workspace_home`（`hero/today_actions/risk/metrics`）；
4. 上报 `workspace.view`（`telemetry.track`，非阻塞）。

### 2.2 行动点击

1. 点击“今日行动”卡片：
   - 先上报 `workspace.enter_click`（`telemetry.track`）；
   - 进入目标 scene（路由跳转后触发 `ui.contract` / `load_view` / `api.data`）。
2. 点击“风险动作”：
   - 上报 `workspace.risk_action_click`（`telemetry.track`）；
   - 跳转风险中心或对应业务页。

### 2.3 英雄区快捷动作

- 打开默认入口 / 我的工作 / 其它导航：
  - 上报 `workspace.nav_click`（`telemetry.track`）；
  - 跳转对应路径。

## 3. 点击 -> intent 对照表

| 入口动作 | 预期事件 | 预期 intent | 阻塞性 |
| --- | --- | --- | --- |
| 页面进入工作台 | `workspace.view` | `telemetry.track` | 否 |
| 点击今日行动 | `workspace.enter_click` | `telemetry.track` | 否 |
| 今日行动跳转结果 | `workspace.enter_result` | `telemetry.track` | 否 |
| 点击风险动作 | `workspace.risk_action_click` | `telemetry.track` | 否 |
| 打开默认入口/我的工作 | `workspace.nav_click` | `telemetry.track` | 否 |
| 进入目标业务页面 | - | `ui.contract/load_view/api.data` | 是（业务主链） |

## 4. 10 秒 / 30 秒产品验收

### 10 秒验收

- 一眼看到“今日行动 + 风险提醒”；
- 能判断今天先处理什么；
- 页面不出现调试字段噪音。

### 30 秒验收

- 至少完成一条行动一跳进入；
- 风险动作可直达风险中心；
- 若数据偏少，页面提示“核对项目归属与示例数据分配”。

## 5. 最小回归命令

- `make verify.frontend.typecheck.strict`
- `make verify.frontend.build`
- `make verify.phase_next.evidence.bundle ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069`
- `make verify.workbench.extraction_hit_rate.report ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069`
