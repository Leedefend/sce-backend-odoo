# 工作台产品验收清单（v1）

## 目标

用于验证工作台是否从“系统能力摘要页”转向“业务行动中枢”。

## A. 10 秒可理解（首屏）

- [ ] 首屏第一优先区域为 `today_focus`（今日行动 + 系统提醒）。
- [ ] 用户无需滚动即可看到“先做什么”（至少 3 条行动项）。
- [ ] 行动项文案为业务语义（如待审批/待处理/待跟进），非技术字段。

## B. 30 秒可执行（行动闭环）

- [ ] 今日行动每条都有可用跳转目标（scene/route）。
- [ ] 风险提醒至少有 1 条可执行动作（进入风险场景或处理页）。
- [ ] 业务动作优先命中，能力兜底仅在业务数据不足时出现。

## C. 信息结构收敛

- [ ] 主区仅保留 `hero` / `today_focus` / `analysis` / `quick_entries` 四区。
- [ ] `hero` 降级为补充区，不抢占首屏行动位。
- [ ] `analysis` 展示业务运营指标，不混入平台能力计数。
- [ ] 平台能力计数进入 `platform_metrics`/`diagnostics`，不作为主叙事。

## D. 协议与兼容

- [ ] `page_orchestration_v1` 为主协议。
- [ ] `page_orchestration` 保留 legacy 兼容，不新增主逻辑依赖。
- [ ] contract 中存在 `contract_protocol.primary=page_orchestration_v1` 声明。

## E. 调试字段分层

- [ ] 用户主视图不出现 `result_summary/active_filters` 等调试词。
- [ ] 调试类信息收敛到 `diagnostics` 或 HUD 通道。

## F. 回归链路

- [ ] `make verify.frontend.build`
- [ ] `make verify.frontend.typecheck.strict`
- [ ] `make verify.project.dashboard.contract`
- [ ] `make verify.phase_next.evidence.bundle`

