# 原生视图治理下的企业启用页策略 v1

状态：`Frozen`

## 结论

企业启用页不采用“前端重建页面结构”的路线。

固定口径：

- Odoo 原生视图是结构真源
- 后端治理层负责对白名单字段、动作、下一步路径做语义裁剪
- 前端只消费治理后的 contract，不再以模型名硬编码页面规则

## 适用范围

- `res.company`
- `hr.department`
- `res.users`

仅适用于当前产品交付阶段的企业启用主路径。

## 允许的治理

- 字段白名单
- 字段中文业务标签
- 表单 layout 收敛
- header/body/workflow/search action 白名单
- 下一步动作定义
- create/edit/read 的用户表面收敛

## 禁止的做法

- 前端直接重建一套独立页面结构
- 前端绕过 contract 自行决定字段顺序
- 前端按模型名长期硬编码动作白名单
- 行业模块重复实现平台级视图治理能力

## 当前治理协议

后端 contract 可输出：

```json
{
  "form_governance": {
    "surface": "enterprise_enablement",
    "hide_workflow": true,
    "hide_search_filters": true,
    "hide_body_actions": true,
    "suppress_contract_header_actions": true,
    "next_action": {
      "step_key": "department",
      "label": "进入组织架构"
    }
  }
}
```

前端只消费以上治理协议，不再自行推断。

## 当前阶段页面语义

### 公司信息

- 只保留企业基础信息字段
- 主动作：`保存`
- 下一步：`进入组织架构`

### 组织架构

- 只保留组织基础信息字段
- 主动作：`保存`
- 下一步：`进入用户设置`

### 用户设置

- 只保留用户主数据与产品角色表面
- 主动作：`保存`
- 不在本页承接高级权限治理

## 架构要求

- 平台治理归属：`addons/smart_core`
- 企业启用模块只声明原生视图与业务入口：`addons/smart_enterprise_base`
- 前端只做 contract 消费：`frontend/apps/web`

## 一句话执行口径

不是前端重建企业启用页，而是后端治理原生视图的用户表面，再由前端消费。
