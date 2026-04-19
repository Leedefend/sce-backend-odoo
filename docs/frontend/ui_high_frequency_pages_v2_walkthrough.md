# High-Frequency Business Pages V2 Walkthrough

## Scope

- 项目列表 -> 项目详情 -> 返回
- 任务列表 -> 任务详情 -> 返回

## Artifacts

- 项目列表：
  - `artifacts/playwright/high_frequency_pages_v2/20260418T155454Z/project-list.png`
- 项目详情：
  - `artifacts/playwright/high_frequency_pages_v2/20260418T155454Z/project-detail.png`
- 任务列表入口落地图：
  - `artifacts/playwright/high_frequency_pages_v2/20260418T155454Z/task-list.png`
- 运行摘要：
  - `artifacts/playwright/high_frequency_pages_v2/20260418T155454Z/summary.json`

## Walkthrough Result

- `项目列表 -> 项目详情 -> 返回`：PASS
  - 入口路由：`/s/projects.list`
  - 实际列表页：`/a/484?menu_id=296&scene_key=projects.list&scene_label=项目列表`
  - 实际详情页：`/r/project.project/1?menu_id=296&action_id=484`
  - 返回后回到：`/a/484?menu_id=296&scene_key=projects.list&scene_label=项目列表`
- `任务列表 -> 任务详情 -> 返回`：BLOCKED
  - 当前 `wutao / demo` 真实链路下，任务入口只能从项目详情继续下钻
  - 二次验证确认：自动点击命中的落点为 `/a/594?menu_id=396`
  - `ui.contract(action_open=594)` 返回 `mail.activity / 待办提醒`，不是 `project.task` 列表
  - 项目详情的真实任务承接并不在头部统计卡，而在 `协作 / 系统` 页签下的 `task_ids` / `tasks` 关系子表
  - `ui.contract(project.project form)` 已确认：
    - `task_ids -> model=project.task -> action_id=457`
    - `task_ids` 子视图默认入口为 `list`，且 `can_open=true`
  - `api.data(read project.project#1)` 已确认当前项目存在任务：`task_ids=[1]`
  - `api.data(read project.task#1)` 已确认任务标题：`项目根任务（Project Root Task）`
  - `ui.contract(action_open=457, record=1)` 已确认可正常返回：`model=project.task`、`view_type=form`
  - `ui.contract(model=project.task, view_type=form, record=1)` 也可正常返回 `ok=true`
  - 但当前浏览器级证据仍未闭环：
    - 任务关系子表的页签切换/行点击尚未被脚本稳定命中
    - 直接打开 `/r/project.task/1?db=sc_demo` 或 `/r/project.task/1?db=sc_demo&action_id=457` 均未出现正常详情容器，也没有 `返回` 按钮
    - 因此当前剩余问题已收敛为：`project.task` 详情在自定义前端中的路由消费/装载挂起，而不是后端契约或任务数据缺失
  - 本轮未伪造任务入口，也未切换到其他演示账号

## Remaining Issues

- `wutao` 的任务入口未暴露独立菜单，任务链路依赖项目详情页上的对象级入口，稳定性不足
- 当前自动化阻断的根因已收敛为“项目详情关系页签 + 内嵌任务子表的稳定定位仍未完成”，不是“任务列表本身无数据”
- 如要完成 `任务列表 -> 任务详情 -> 返回` 的证据闭环，需要下一轮专门补一条：
  - 让脚本按 `task_ids` 页签和真实任务名定点点击内嵌任务行
  - 并单独修正 `project.task` 详情在自定义前端中的路由消费/装载问题，再补抓任务详情截图
- 新增 Batch `ITER-2026-04-19-FE-PROJECT-TASK-FORM-ROUTE-RECOVERY` 后，`ContractFormPage` 已改为“详情壳先渲染、关系选项后台补水合”，但浏览器直接证据仍未闭环：
  - 截图：`artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-probe.png`
  - 直达路由保持在 `/r/project.task/1?db=sc_demo&action_id=457`
  - `window.__scFormDebug` 仍为 `null`
  - 浏览器控制台只打印到 `system.init` 请求诊断，页面主体保持空白 `#app` 壳层
- 当前最新结论：剩余阻塞点已经前移到启动链 / 路由 bootstrap，而不是 `ContractFormPage` 内部的 render-time loading。
- 新的启动链恢复批次已把“白屏”恢复成“可见加载态”：
  - 8 秒窗口探针截图：`artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-bootstrap-8s.png`
  - 探针结果：`hasOverlay=true`、`hasLoading=true`、`hasReturn=false`
- 长等待探针已确认 `project.task` 详情最终可挂载：
  - 总耗时约 `38.6s`
  - 页面可见 `返回`、`保存`、`Convert to Task`
  - `window.__scFormDebug.status=ok`
- 因此当前主风险已从“启动失败/白屏”切换为“启动链过慢”。
- 进一步 shell 计时已确认这部分慢启动不主要是 Vite 代理造成：
  - `5174 /api/v1/intent system.init` 约 `18.1s`
  - `8069 /api/v1/intent system.init` 约 `20.2s`
  - 响应体约 `587 KB`
- 所以下一条真正需要开的线应是后端 / runtime 的 `system.init` 启动性能，而不是继续在任务详情页或前端代理层内打磨。
