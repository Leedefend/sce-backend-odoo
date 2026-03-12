# v1.0 Iteration Round 1 产品表达验证清单

## 1. 页面模式区分

- [ ] `dashboard/workspace/list` 在视觉与信息结构上可明显区分
- [ ] `project.management` 呈现为驾驶舱
- [ ] `projects.ledger` 呈现为工作台型台账
- [ ] `projects.list` / `task.center` / `risk.center` / `cost.project_boq` 呈现为列表型台账

## 2. 核心页面一眼可懂

- [ ] `project.management` 第一屏可读出：指标、风险、进度
- [ ] `projects.ledger` 第一屏先看到项目群总览
- [ ] `projects.list` 关键列优先（名称/状态/负责人/金额/更新时间）

## 3. 风险表达

- [ ] 驾驶舱风险区视觉权重高于普通辅助块
- [ ] 列表与卡片中的异常状态具备轻量风险信号

## 4. 列表产品化程度

- [ ] 列表页不再是裸数据库浏览器体验
- [ ] 顶部信息层包含标题、记录数、搜索筛选排序
- [ ] 批量操作条在列表中位置统一

## 5. 技术字段直出治理

- [ ] 核心页面无 `draft`/`done`/`01_in_progress`/`No` 直出
- [ ] 金额按 `万/亿` 规则可读
- [ ] 百分比字段统一为 `%`

## 6. 演示数据可演示性

- [ ] 核心 6 页打开时有可读数据
- [ ] 驾驶舱与风险/任务/BOQ 页面可串讲

## 7. 发布链路安全性

- [ ] 未破坏 `verify.project.dashboard.contract`
- [ ] 未破坏前端 build/typecheck
- [ ] 未破坏 phase evidence bundle

## 8. 截图清单建议

1. `project.management`：
   - 第一屏（指标 + 风险 + 进度）
   - 风险区放大图
2. `projects.ledger`：
   - 总览层 + 项目卡片同屏
3. `projects.list`：
   - 关键列排序后视图
4. `task.center`：
   - 顶部信息层 + 列表状态列
5. `risk.center`：
   - 状态色与风险信号
6. `cost.project_boq`：
   - 金额字段友好展示
