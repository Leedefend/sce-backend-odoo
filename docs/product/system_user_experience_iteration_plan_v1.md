# 全系统用户体验覆盖提升专题 v1

## 目标

本专题不再以“底层数据通了”作为主要结论，而是从真实用户使用视角覆盖全系统。目标是让用户可以稳定完成登录、定位工作、进入业务、查询列表、办理表单、查看详情、配置系统、诊断问题和移动端使用。

本轮专题分支：`topic/system-user-experience-coverage`。

## 判断原则

1. 用户先于功能：先确认用户要完成的任务，再判断页面和能力是否合格。
2. 操作先于静态：功能存在不等于好用，必须覆盖点击、搜索、保存、返回、错误、空态和刷新。
3. 页面结构先于视觉细节：先统一 Header、Toolbar、Summary、Main Surface、Feedback，再处理局部样式。
4. 后端契约先于前端推断：页面模式、导航、权限、业务对象、配置对象必须来自后端或正式产品契约，前端只做通用渲染。
5. 证据先于结论：没有浏览器证据、结构化报告或问题清单，不给出“可交付用户”的结论。

## 覆盖矩阵

权威矩阵文件：`docs/product/system_user_experience_coverage_v1.json`。

矩阵必须覆盖：

- 角色：领导、项目经理、财务、经营人员、配置管理员、支持人员。
- 页面类型：登录、首页、导航、驾驶舱、工作台、列表、表单、详情、后台配置、支持、移动端。
- 页面模式：`dashboard/workspace/list/form/detail/admin`。
- 操作动作：登录、展开导航、打开页面、搜索、筛选、分页、新建、填写、保存、上传、返回、刷新、诊断。
- 证据：自动化门禁、浏览器验收、人工问题清单。

## 执行方式

### 第一阶段：基线锁定

- 固化用户体验覆盖矩阵。
- 增加矩阵 guard，防止覆盖范围缩水。
- 建立问题分类：信息架构、任务流、页面结构、用户语言、数据可理解性、性能与反馈、移动端、权限与可达性。

### 第二阶段：浏览器走查

- 先覆盖 4 类高频面：登录/首页、主导航/业务列表、业务表单、配置后台。
- 每个页面记录：首屏截图、操作步骤、失败请求、console error、页面模式、区域对齐、用户语言问题。
- 每轮至少输出问题清单，不允许只输出通过。

### 第三阶段：批量优化

按问题类型批量处理：

- 页面结构类：统一壳层、区域边界、间距、反馈区。
- 任务流类：统一主动作、保存反馈、返回路径、空态下一步。
- 用户语言类：清理技术词、模型名、action id、字段技术名。
- 数据理解类：补主字段、状态、金额、来源、附件证据。
- 性能反馈类：补骨架屏、加载提示、长列表控制。
- 移动端类：处理横向溢出和首屏任务可达。

### 第四阶段：收口门禁

本专题收口至少需要通过：

```bash
make verify.system_user_experience.coverage_guard
make verify.product.page_structure
make verify.product.navigation_boundary
make verify.business_system.usability_readiness
make verify.business_config.config_workbench_operation_local_closeout
make verify.system_user_experience.shell_acceptance
make verify.system_user_experience.full_browser
```

## 合格结论格式

最终结论必须同时说明：

- 覆盖了哪些角色和用户旅程。
- 发现并修复了哪些问题类型。
- 哪些页面已有浏览器证据。
- 哪些问题仍属于下一轮 backlog。
- 本地、日常开发服务器、生产服务器分别是否已验证。
