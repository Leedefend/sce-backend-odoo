# 系统管理员产品入口策略 v1

状态：`Frozen`

适用阶段：`当前产品交付阶段`

## 一句话原则

> `base.group_system` 只代表系统管理权限，不自动代表任何施工业务角色。`

## 1. 真源边界

- 系统管理身份真源：`base.group_system`
- 施工业务角色真源：正式角色组与能力组链
- 产品入口开放真源：业务角色/能力链，不是系统管理员身份

## 2. 禁止事项

- 禁止把 `base.group_system` 直接映射成 `executive`
- 禁止把系统管理员默认视为 `pm / finance / executive / owner`
- 禁止仅因为用户是系统管理员，就开放施工业务工作台、驾驶舱、生命周期视图

## 3. 允许事项

- 系统管理员可以保留系统治理入口
- 系统管理员可以保留运维/配置/审计类入口
- 若系统管理员需要进入施工业务产品页，必须显式获得正式业务角色或能力链

## 4. 正式准入路径

系统管理员进入施工业务产品入口，必须满足以下至少一条：

1. 获得正式业务角色组
   - 例如：`smart_construction_custom.group_sc_role_executive`
2. 获得正式能力组链
   - 例如：`group_sc_cap_project_read -> group_sc_bridge_project_base -> project.group_project_stages`
3. 获得明确的业务桥接角色
   - 通过角色面过桥，不允许直接绕过能力模型

## 5. 产品表面规则

- `IdentityResolver` 不得因 `base.group_system` 自动解析业务角色
- 业务 capability registry 不得因 `base.group_system` 自动添加 `executive`
- 工作台、驾驶舱、生命周期等业务入口，必须以正式业务角色/能力链为准

## 6. 适用示例

### 示例 A：纯系统管理员

- 拥有：`base.group_system`
- 不拥有：`group_sc_role_executive`
- 结果：
  - 可进入系统配置与治理页
  - 不自动进入施工业务管理层工作台

### 示例 B：系统管理员 + 正式管理层角色

- 拥有：`base.group_system`
- 同时拥有：`smart_construction_custom.group_sc_role_executive`
- 结果：
  - 可进入系统治理页
  - 也可按正式角色链进入施工业务管理层入口

## 7. 当前批次落地要求

- `base.group_system -> executive` 伪映射必须移除
- `system admin` 与 `business role` 必须解耦
- 后续任何产品页入口新增，必须先验证是否误把系统管理员当业务角色
