# Handler / Parse / Governance 编码约束 v1

## 1. Handler 约束

### 1.1 允许
- 参数归一化、op 分发。
- 调用 parse/service。
- 调用治理入口并返回 envelope。

### 1.2 禁止
- 直接改写 `views/form/layout` 等布局结构。
- 在 handler 内做字段分组重排、按钮治理重排。
- 绕开治理入口直接返回生产契约。

### 1.3 守卫
- `verify.contract.handler_boundary.guard`

## 2. Parse 约束

### 2.1 允许
- 原生结构解析。
- 解析失败 fallback。
- 结构清洗（native 安全清洗）。

### 2.2 禁止
- `contract_mode/contract_surface` 治理语义注入。
- 用户角色运行时治理裁剪。
- 治理映射生成（应由治理层统一执行）。

### 2.3 守卫
- `verify.contract.parse_boundary.guard`

## 3. Governance 约束

### 3.1 允许
- 单一入口治理：`apply_contract_governance`。
- surface 元字段注入。
- native -> governed 映射证据生成。
- user/hud 策略裁剪与语义增强。

### 3.2 禁止
- 改写业务事实（模型语义）。
- 侵入 scene 编排逻辑。

## 4. PR Review Checklist

1. 是否在 handler 中出现布局重排代码？
2. parse 代码是否出现 runtime governance 关键字？
3. 生产 contract 是否含完整 surface 元字段？
4. `surface_mapping` 是否完整且结构合法？
5. scene 是否越层读取 parser/XML 输入？
6. 相关 guard 是否通过：
   - `verify.contract.handler_boundary.guard`
   - `verify.contract.parse_boundary.guard`
   - `verify.contract.surface_mapping_guard`
   - `verify.scene.input_boundary.guard`

