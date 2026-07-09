# 配置工作台专业产品化走查 round 1

## 目标

本轮不是证明功能能跑通，而是从专业产品视角主动发现问题。操作门禁和专业门禁负责防回退；产品走查负责发现门禁还没有定义的问题。

## 用户角色

| 角色 | 目标 | 关注点 |
| --- | --- | --- |
| 业务配置管理员 | 调整业务页面的表单、列表、菜单和审批规则 | 能快速找到页面、理解影响范围、完成配置并确认生效 |
| 实施顾问 | 初始交付时检查配置完整性 | 能定位缺口、避免技术参数暴露给业务用户 |
| 业务负责人 | 审核配置是否符合实际办理习惯 | 能看懂配置项含义和生效范围，不需要理解模型和动作 ID |

## 核心任务

| 任务 | 走查问题 |
| --- | --- |
| 找到项目合同汇总页面 | 用户能否靠页面名称和目录定位，而不是靠技术模型 |
| 理解当前页面可配置内容 | 四张配置卡片是否解释清楚能改什么、影响哪里 |
| 配置表单字段 | 是否明确这是当前页面字段配置，是否知道保存后只影响当前页面 |
| 配置列表与搜索 | 是否能理解列表列、搜索条件、默认分组的区别 |
| 配置审批规则 | 是否能理解规则开关、审批方式、步骤编排 |
| 配置菜单入口 | 是否能理解这是菜单显示、排序和角色可见性，不是业务数据 |
| 从子能力返回 | 返回后是否仍然知道自己在配置哪个业务页面 |
| 小屏操作 | 当前配置是否先于页面目录展示，是否无横向溢出 |

## 发现问题

| 编号 | 等级 | 问题 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| CW-P1-001 | P1 | 已选页面直达起始态显示 `对象 construction.contract · 页面 562`，业务用户需要理解技术模型和动作 ID | `03-direct-selected.png` | 已修复：默认摘要改为“当前页面配置，只影响这个业务页面” |
| CW-P1-002 | P1 | 菜单配置备注显示 `synced_from_daily_dev...` 同步来源，破坏业务界面语言一致性 | `07-menu-config.png` | 已修复：默认隐藏同步/迁移/技术来源备注 |
| CW-P1-003 | P1 | 自动化专业门禁没有检测完整可见文字，导致技术词泄漏仍可获得满分 | 本轮增强前报告 | 已修复：新增可见技术词扫描，覆盖工作台、表单设计器、菜单配置 |
| CW-P1-004 | P1 | 点击列表与搜索或审批配置后，页面仍可能停留在工作台概览区，目标编辑面没有成为当前视觉焦点 | `04-list-search-entry.png`、`05-approval-entry.png` | 已修复：内嵌编辑面打开后自动进入首屏焦点，并新增首屏位置指标 |
| CW-P1-005 | P1 | 表单字段配置态仍露出业务办理动作“保存草稿”“提交”，配置动作与业务提交动作混淆 | `06-form-designer-entry.png` | 已修复：低代码字段配置作用域下隐藏业务办理动作，只保留配置动作 |
| CW-P1-006 | P1 | 默认交付状态直接展示“版本与快照 1212 项”“覆盖检查 1040 项”，业务配置管理员被内部审计指标打断 | `03-direct-selected.png` | 已修复：默认只展示表单、列表搜索、菜单、审批四项用户任务状态；高级设置展开后仍可查看完整审计信息 |
| CW-P1-007 | P1 | 移动端配置工作台默认展示平台副标题和配置快照，挤占首屏并暴露内部审计信息 | `08-mobile-selected.png` | 已修复：配置中心使用紧凑顶栏；默认隐藏配置快照，保留高级设置查看 |
| CW-P1-008 | P1 | 列表与搜索字段池默认展示 `affiliated_person`、`category_id` 等技术字段名，以及 `Can Review` 英文兜底标签 | `04-list-search-entry.png` | 已修复：默认只展示业务字段名；高级设置展开后才显示短字段名提示；补充可见技术词硬断言 |
| CW-P1-009 | P1 | 表单设计器内部上下文正确，但全局顶栏标题回退为“角色首页”，用户无法从全局区域判断正在配置哪个页面 | `06-form-designer-entry.png` | 已修复：低代码表单配置态的全局顶栏显示“配置：业务页面名称”，并补充顶栏上下文断言 |
| CW-P1-010 | P1 | 移动端选择业务页面后真实视口仍停在页面目录滚动位置，fullPage 截图看起来顺序正确但用户当前看不到配置任务入口 | `08-mobile-selected.png`、`09-mobile-viewport.png` | 已修复：移动端选页后自动回到当前配置区；门禁新增真实视口截图、首屏位置和 `scrollY` 证据 |
| CW-P1-011 | P1 | 当前配置任务区把业务页面名称截断为“项目合...”，用户在核心任务区不能完整确认正在配置的对象 | `01-selected-from-scan.png` | 已修复：当前页面名允许换行完整展示；门禁新增视觉截断检测 |
| CW-P1-012 | P1 | 点击列表与搜索后编辑面虽然进入首屏，但仍被上方卡片区压低，用户视线没有直接落到正在编辑的配置面 | `04-list-search-entry.png` | 已修复：编辑面打开后按固定顶栏留白定位到视口上部；门禁新增列表与审批编辑主焦点断言 |
| CW-P1-013 | P1 | 证据目录残留旧截图，人工验收可能打开非本次报告引用的页面状态 | `artifacts/playwright/config-workbench-operation` | 已修复：验收运行前清理专题产物目录；门禁要求目录截图集合与本次报告完全一致 |
| CW-P1-014 | P1 | 表单设计器“当前页面”显示为“新建项目合同汇总这个页面”，配置对象被误表达成业务新建动作 | `06-form-designer-entry.png` | 已修复：配置态使用独立业务页面名“项目合同汇总”；门禁新增当前页面名精确断言 |
| CW-P1-015 | P1 | 列表与搜索配置面没有明确返回工作台动作，审批配置面使用“关闭”，子能力恢复路径语义不一致 | `04-list-search-entry.png`、`05-approval-entry.png` | 已修复：两个内嵌配置面统一提供“返回工作台”；门禁新增恢复动作断言 |
| CW-P2-001 | P2 | 专业门禁能防回退，但不能替代主动走查；如果只扩展评分，容易产生“看起来专业但不发现问题”的假象 | 本轮讨论 | 已固化：新增本走查文档，后续迭代必须先走查再补门禁 |

## 已加入门禁

新增可见技术词泄漏检查，默认业务界面不得出现：

- Odoo/模型技术名：如 `construction.contract`、`ui.*`
- URL/动作技术参数：如 `action_id`、`view_id`、`role_key`、`root_menu_xmlid`
- 同步/迁移来源：如 `synced_from_`、`generated_from_`、`migrated_from_`、`daily_dev`
- 技术备注前缀：如 `user_confirmed_`、`technical_`

该检查进入：

- `product_usability.user_language`
- `professional_readiness.naming_and_language_consistency`

只要出现可见技术词，`delivery_ready` 和 `professional_ready` 都会失败。

新增操作焦点与动作语义检查：

- 点击“配置列表”后，列表与搜索编辑面必须进入首屏主焦点。
- 点击“配置审批”后，审批规则编辑面必须进入首屏主焦点。
- 表单字段配置态不得出现业务办理动作按钮“保存草稿”“提交”。
- 默认交付状态只展示表单、列表搜索、菜单、审批四项用户任务状态。
- 默认交付状态不得展示配置快照审计信息。
- 移动端配置工作台顶栏必须是紧凑模式，不展示平台副标题。
- 移动端选页后当前配置区必须进入真实视口首屏，不能只用 fullPage 截图证明整体顺序。
- 当前配置区和直达态必须完整展示业务页面名称，不得用省略号截断核心对象。
- 验收证据目录只能包含本次运行生成的截图，不能残留旧截图。
- 默认可见界面不得展示字段技术名、技术参数或英文兜底标签。
- 表单设计器所在全局顶栏必须显示当前配置页面上下文。

该检查进入：

- `product_usability.operation_convention`
- `product_usability.task_efficiency`
- `professional_readiness.capability_depth`

只要配置入口打开后焦点不清楚，或配置态混入业务办理动作，`delivery_ready` 和 `professional_ready` 都会失败。

## 本轮验收结果

命令：

```bash
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 make verify.business_config.config_workbench_operation_acceptance
```

结果：

- `delivery_status = delivery_ready`
- `product_usability.score_total = 22 / 22`
- `professional_readiness.status = professional_ready`
- `professional_readiness.score_total = 30 / 30`
- `assertion_passed_count = 38 / 38`
- `formDesignerBusinessActionButtons = []`
- `formDesignerShellTitle = 配置：项目合同汇总`
- `formDesignerCurrentPageLabel = 项目合同汇总`
- `pageStructureDesktop.currentConfig.overviewLabelTruncated = false`
- `mobileViewport.currentConfigVisibleInPrimaryViewport = true`
- `listSearchPanelViewport.startsInPrimaryViewport = true`
- `listSearchPanelViewport.startsInEditorFocusViewport = true`
- `approvalPanelViewport.startsInPrimaryViewport = true`
- `approvalPanelViewport.startsInEditorFocusViewport = true`
- `deliveryReadinessLabels = ["表单配置", "列表与搜索配置", "菜单配置", "审批配置"]`
- `directDeliveryReadinessLabels = ["表单配置", "列表与搜索配置", "菜单配置", "审批配置"]`
- `defaultSnapshotSummaryCount = 0`
- `mobileConfigurationTopbar.platformEyebrowVisible = false`
- `mobileSnapshotSummaryCount = 0`
- `listSearchVisibleTechnicalTerms = []`
- `visibleTechnicalTerms = []`
- `browser_console_error_count = 0`
- `browser_request_failed_count = 0`

## 后续推进规则

1. 每轮产品化迭代先走查，再定义门禁。
2. 走查必须输出 P0/P1/P2/P3 问题，不允许只输出通过结论。
3. P0/P1 必须当轮修复；P2 可进入下一轮体验优化；P3 进入打磨清单。
4. 修复后必须补自动化门禁，防止同类问题回退。
5. 如果门禁满分但走查发现问题，以走查问题为准，继续迭代。
