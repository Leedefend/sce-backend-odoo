# Menu Fact Layer v1

## 1. 定位

菜单事实层（Menu Fact Layer）是菜单系统的**唯一事实发布层**。

- 它只发布菜单与 action 原始绑定的可审计事实。
- 它不做导航解释，不做前端展示推理。

## 2. 唯一数据来源

菜单事实层唯一数据来源：`ir.ui.menu`。

补充来源仅限事实读取：

- `ir.actions.*`：用于验证 `action_raw` 绑定是否存在及读取原始 action 元数据。
- `ir.model.data`：用于读取 `groups` 的 XMLID 映射。

## 3. 输出字段定义（v1）

节点字段（`flat` 与 `tree` 统一口径）：

- `menu_id`: 菜单 ID（int）
- `key`: 稳定键（`menu:{menu_id}`）
- `name`: 菜单名称
- `parent_id`: 父菜单 ID（根节点为 `null`）
- `complete_name`: 完整路径名
- `sequence`: 排序值
- `groups`: 组事实列表（id/xmlid/name）
- `web_icon`: 原始菜单图标
- `has_children`: 是否有子菜单
- `child_ids`: 子菜单 ID 列表（仅 flat）
- `children`: 子树列表（仅 tree）
- `action_raw`: `ir.ui.menu.action` 原始值
- `action_type`: 解析动作类型（如 `ir.actions.act_window`）
- `action_id`: 解析动作 ID
- `action_exists`: 动作记录是否存在
- `action_meta`: 动作原始元数据（当前 v1 对 `act_window` 输出 `res_model/view_mode/view_id/domain/context`）
- `action_parse_error`: 解析失败原因（无错误时为空）

## 4. 事实层职责

菜单事实层负责：

1. 扫描并输出当前用户可见菜单事实（树形+扁平）
2. 解析 `action_raw` 到标准 action 事实
3. 标记动作解析失败与动作不存在
4. 产出异常审计输入（孤儿菜单/空菜单/混乱菜单/sequence 风险）

## 5. 明确不负责（边界冻结）

菜单事实层**不负责**：

- route 生成
- scene 映射 / `scene_key` 推导
- `target_type` / `delivery_mode` 判断
- active 高亮匹配策略
- 前端 Sidebar 结构或样式
- custom/native 承接决策

## 6. 与解释层关系

后续菜单目标解释器/导航契约层只能消费本层输出，不得反向要求事实层增加解释字段。

单向关系：

`ir.ui.menu` -> `menu fact layer v1` -> `menu target interpreter` -> `frontend sidebar`

## 7. 版本约束

本文件冻结为 `v1`。

- 新增字段必须保持 facts-only 语义。
- 解释层字段不得进入 `v1` 输出。
- 若确需扩展，使用 `v2` 演进而非破坏性改写 `v1`。
