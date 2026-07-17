# 前端产品设计系统 v1

本契约服务于通用工作平台。共享组件只消费后端提供的展示契约和语义状态，不读取角色码、模型名、XML ID，也不按业务字段名推断展示。

## 视觉基础

- 色彩仅使用 `surface`、`surface-subtle`、`surface-raised`、`border`、`border-strong`、`text-primary`、`text-secondary`、`text-muted`、`interactive`、`focus` 以及 `success`、`warning`、`danger`、`info` 语义 token。
- 字体层级固定为页面标题、分区标题、卡片标题、正文、辅助文字、数据/金额和字段标签；单页默认不超过四个明显字号层级。
- 间距遵循 8px 节奏，页面、分区、面板、字段和行内间距从正式 token 获取。
- 控件、面板和对话框分别使用固定圆角；阴影仅用于浮层和必要的层级提升。
- 正式组件不得新增硬编码颜色、页面级 inline style、model-specific CSS 或宽范围全站补丁。

## 正式组件

`components/design-system` 是通用组件唯一正式目录，包含页面、分区、面板、按钮、状态、金额、字段、错误、空状态、对话框、抽屉、列表、移动记录、关系和审计组件。业务页面负责把正式契约转换为这些组件的 props，不得向组件传递模型判断逻辑。

| 组件族 | 正式组件 | 责任边界 |
| --- | --- | --- |
| 页面 | `ScPage`、`ScPageHeader`、`ScSection`、`ScPanel` | 页面结构和视觉层级，不加载业务数据 |
| 操作 | `ScButton`、`ScIconButton`、`ScActionBar` | 呈现后端 action presentation，不裁决权限 |
| 状态 | `ScStatusBadge`、`ScEmptyState`、`ScErrorState` | 呈现正式状态语义和恢复建议，不翻译状态码 |
| 数据 | `ScMoney`、`ScDataTable`、`ScMobileRecordCard` | 格式化正式事实，不汇总或换算业务金额 |
| 字段 | `ScField`、`ScSelect`、`ScRelationField`、`ScDateField`、`ScErrorSummary` | 消费字段契约，不按字段名推断类型 |
| 浮层 | `ScDialog`、`ScDrawer` | 统一语义、焦点和关闭行为，不承载业务状态机 |
| 关系与审计 | `ScRelationshipFlow`、`ScAuditTrail` | 呈现已授权引用，不自行查询或泄露不可读记录 |

## 可访问性

- 每页一个 `main` 和一个 `h1`。
- 自定义字段通过稳定 field key 关联 label、帮助和错误；required、invalid、disabled、readonly 各自表达。
- dialog/drawer 打开后获得焦点，关闭后由调用方恢复触发点。
- 图标按钮必须有可访问名称；装饰图标对读屏隐藏；状态不只依赖颜色。

## 兼容边界

旧页面样式只有在存在正式调用方证据时保留。迁移完成的组件必须删除对应全局补丁，禁止通过提高 CSS specificity 维持并行实现。

## 架构门禁

`make verify.frontend.style_system.guard` 同时检查：正式组件齐备、共享组件不读取角色码/模型名/XML ID、生产组件硬编码颜色为零、核心页面复杂度预算、自定义字段 ARIA 契约，以及已退役详情代理不回升。该门禁复用现有前端样式守卫，不建立平行扫描体系。
