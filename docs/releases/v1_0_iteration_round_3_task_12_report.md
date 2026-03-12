# v1.0 Iteration Round 3 · Task 12 收口报告

## 1. Task 12 目标

继续完成“产品表达层迭代”的第 12 项收口：

- 将列表语义进一步下沉至场景配置层；
- 保持前端表达一致性；
- 保持验证链路可运行。

## 2. 已完成内容

1. 风险工作台场景语义下沉
   - 文件：`addons/smart_construction_scene/data/sc_scene_layout.xml`
   - 增加 `risk.center` 的：
     - `page.page_mode=workspace`
     - `list_profile`（字段顺序 + 中文标签）
     - `default_sort`

2. 列表表达增强延续
   - `projects.list` 增加总览 Summary Strip；
   - `task.center` / `risk.center` / `cost.project_boq` 保持统一顶部统计卡与字段优先级。

3. 语义映射补强
   - many2one 数组值优先展示 display name；
   - 中文状态关键词映射风险/预警/完成语义色。

## 3. 边界说明

- 未触碰 scene governance、ACL、部署回滚主逻辑；
- 未重构 contract envelope；
- 仅做表达层和场景 payload 语义增强。

## 4. 备注

`task.center` 与 `cost.project_boq` 当前在运行时主要依赖 action contract，已在前端侧提供 scene-aware 列表预设；后续如需进一步下沉到 scene version，可在对应场景正式建模后补齐。
