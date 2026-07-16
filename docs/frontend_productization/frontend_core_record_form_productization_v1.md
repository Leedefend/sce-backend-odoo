# FE-PRO-03 核心详情与表单产品化证据

## 交付边界

本分支只覆盖 `project.project`、`construction.contract`、`sc.settlement.order`、`payment.request` 与 `sc.payment.execution` 的正式详情，以及合同、付款申请的正式表单。台账继续作为只读付款事实与关系结果展示。ACL、record rule、角色权限、70 个权威导航叶节点、金额公式、状态机、汇率和数据库结构均未改变。

共享前端只渲染正式契约。五类对象的业务名称、状态语义、事实分组、金额语义、上下游关系、审计信息与操作 presentation 由 `smart_construction_core` 行业契约声明；`RecordView`、`ContractFormPage` 和 `components/product-record` 不维护模型、XML ID、中文字段或状态字典。

## 正式页面结构

五类对象共用以下结构：页面身份与状态、主操作、关键业务事实、金额事实、上下游关系、业务明细、审计信息。正式详情路径统一为 `RecordView -> ContractFormPage -> FinancialRelationshipWorkspace -> product-record components`；`RecordView` 不再维护第二套详情渲染。表单继续使用 `ContractFormPage` 的唯一正式契约路径，合同与付款申请的字段顺序、必填、只读、关系、domain、默认值、币种、帮助和 onchange 均来自正式 page/form contract。

状态契约同时返回原始值、用户标签、`default/info/success/warning/danger` 语义和状态说明。付款动作契约显式返回 `primary/secondary`、`destructive`、`requires_confirmation` 与 `requires_reason`，My Work 和详情不再依赖 `actions[0]` 推断主操作。每个页面首屏最多三个可执行动作，其他动作进入正式溢出层级。

## 金额与关系事实

| 对象 | 权威金额事实 | 关系 |
| --- | --- | --- |
| 项目 | 无前端推导金额 | 合同 |
| 合同 | 原始金额、当前/最终金额、累计实付 | 项目、结算 |
| 结算 | 原始金额、调整/扣款、调整后付款基数、已占额、实际已付、剩余可占额 | 合同、付款申请 |
| 付款申请 | 申请金额、结算占额、实际台账金额 | 合同、结算、付款执行、台账结果 |
| 付款执行 | 执行金额、实际支付结果 | 付款申请、合同、台账结果 |

金额使用后端字段与既有 `operating_metrics`，前端不重算、不汇总、不换算。0、null、无台账和无权限分别表达；币种随事实返回，混合币种只显示风险。关系标题先通过当前用户 ACL/record rule 读取；不可读关系不返回业务标题、金额或裸 ID，前端只显示通用无权状态或隐藏。公司、项目、用户 context epoch 变化后旧关系结果不得写回。

## 表单恢复能力

合同和付款申请表单提供统一错误摘要与字段跳转，首个错误字段自动聚焦；保存中禁用，成功后权威重读。新建成功后切换到真实记录 URL。dirty form 同时受 Vue Router 全局离开守卫和 `beforeunload` 保护，取消离开保留输入。409 显示“记录已被其他操作更新”，保留本地输入并允许确认加载最新版本；422 映射字段/业务错误；403 进入安全无权状态；401 清理 session 后返回登录。

onchange 已改为契约驱动：只有 action contract 为字段声明服务端 `change/select/blur` 规则时才请求 `api.onchange`。普通字段编辑只标记 dirty，不再产生未授权或无意义的网络请求。

## 规模与路径收敛

| 文件 | 修改前 | 修改后 |
| --- | ---: | ---: |
| `RecordView.vue` | 1525 | 15 |
| `ContractFormPage.vue` | 5947 | 5587 |
| 两者合计 | 7472 | 5602（下降 25.0%） |
| `FinancialRelationshipWorkspace.vue` | 196 | 86 |

新增 product-record Vue 文件均低于 100 行，新增 contract-form Vue/TS 文件均低于 700 行。`ContractFormPage.vue` 仍是显著架构债务；本分支只抽取产品页头、动作 presentation、错误聚焦、未保存守卫和详情组件，没有把其余通用表单引擎机械搬入新巨型文件。

## 浏览器与效率证据

`artifacts/frontend-professional/fe-pro-03/` 保存基线 24 张和最终 32 张截图、baseline/final/comparison 报告及 J12/J13 报告。最终八类页面在 1440×900、1280×800、768×1024、390×844 均满足：一个 H1、技术标题 0、页面横向溢出 0、axe critical/serious 0、console/pageerror/非预期 HTTP 0、首屏可执行动作不超过 3。

六项效率任务全部可完成：合同最终金额、结算调整后金额和关系链均位于首屏或一次自然展开内；付款申请创建/提交保持既有最短合法路径；字段错误从无统一可定位路径变为错误摘要单击聚焦；409 从通用失败且无法恢复变为保留输入并权威重载。后两项基线为 `NOT_COMPLETABLE`，最终由 J13 证明可恢复；结算金额/关系从基线不可直接定位变为正式事实区可定位。未通过减少权限检查、隐藏事实或缩短等待伪造效率。

J04–J06、J07/J08、J09–J11、J12/J13 全部 PASS。J12 验证合同 dirty guard、取消保留、保存与刷新；J13 验证必填错误聚焦、一次 409、输入保留和权威重载。权威导航保持 finance 42、project member 9、PM 14、owner 5，共 70/70；action 876/menu 606、越权详情、Project A 隔离和公司 A→B→A 均保持原有拒绝与隔离。

## 已知问题

`ContractFormPage.vue` 仍有 5587 行，后续应依据真实修改热点继续抽离通用表单加载、relation、one2many 与低代码配置责任，但不得在本分支扩成全表单引擎重写。自动审计中的付款申请 create validation probe 为 `NOT_APPLICABLE`，因为正式金额控件不使用原生 `required` 选择器；真实必填错误与焦点行为由 J13 直接覆盖并通过。
