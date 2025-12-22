# Smart Construction 权限架构蓝图（v1.0）

## 0. 设计目标
- 语义清晰：管理员只勾 SC 能力组，原生组不出现在业务配置视野。
- 可演进：新增中心/岗位/模块不破坏链路。
- 可审计：任何权限都能沿 implied 链路追溯到 SC 组。
- 升级友好：尽量不改原生定义，只做 SC 层封装与可见性隔离。

## 1. 三层权限模型
- **L1 原生能力层**：字段 groups、模型 ACL 依赖的原子组（示例：`base.group_user`、`project.group_project_user`、`base.group_partner_manager`、`account.group_account_readonly`）。只允许被 implied，不给管理员直接勾；分类放 Hidden。
- **L2 SC 能力层**：管理员配置用户的“岗位能力包”。三段式：`*_read` → `*_user` → `*_manager`。分类统一为 “Smart Construction / 业务能力”。
- **L3 系统角色层（未来扩展）**：角色绑定多个 SC 能力组，不是 res.groups，可后续用自定义模型实现。

## 2. 分类与可见性
- SC 能力组（L2）：分类 `Smart Construction / 业务能力`。
- 原生组与技术组（L1）：分类 `Hidden`（`base.module_category_hidden`）。

## 3. SC 能力组设计规范
- **基础组**：`group_sc_internal_user`（唯一 implied `base.group_user`），可选隐藏。
- **中心三段式链路**：
  - read implied `group_sc_internal_user`（必要时再 implied 原生字段组，如项目 read implied `project.group_project_user` 以读阶段）。
  - user implied read。
  - manager implied user（不要在 manager 重拼链路，除非有硬性理由）。
- **横切能力组**：例如 `group_sc_cap_contact_manager`（implied `base.group_partner_manager`）、`group_sc_cap_config_admin`、`group_sc_cap_data_read`。
- **超级管理员**：`group_sc_super_admin`，仅测试/运维，implied 全部 SC manager 能力组 + 必要原生管理组。

## 4. 命名规范
- XML ID：`group_sc_cap_<domain>_<level>`，基础：`group_sc_internal_user`，超管：`group_sc_super_admin`。
- 展示名：`SC 能力 - <中心/域><级别>`；横切示例：`SC 能力 - 联系人管理`、`SC 能力 - 配置管理员`；基础：`SC 基础 - 内部用户`；超管：`SC 超级管理员（全能力）`。
- 分类：所有 SC 能力组放 “Smart Construction / 业务能力”；原生/技术组放 Hidden。

## 5. 权限实现分工
- 字段 groups：自定义字段优先绑 SC 能力组；原生字段依赖保留或通过 SC 链路 implied 其原生组。
- 模型 ACL：优先绑 SC 能力组，read/user/manager 三档；原生模型扩展谨慎，必要时通过 SC 能力组 implied 原生组。
- 记录规则：明确指定组；注意 create 场景是否被 domain 阻断。
- 菜单/动作 groups：入口控制用 SC 能力组；不要用菜单开放替代权限。

## 6. 禁止清单
1) 禁止给业务用户直接勾任何原生组（项目/联系人/会计等）。  
2) 禁止在 manager 组里重拼 implied 链路（应 manager→user→read→internal_user）。  
3) 禁止用菜单可见性代替权限控制。  
4) 禁止写阻断 create 的 record rule 而不验证新建场景。  
5) 禁止同一能力在多处重复定义（能力散落不可追溯）。

## 7. 管理员操作规范
- 给用户授权：只勾 SC 能力组（read/user/manager + 横切），不碰原生组。
- 配置模式：普通岗位用中心 user + 必要横切；审批岗位用中心 manager；测试账号用 `SC 超级管理员（全能力）`。

## 8. 验收标准
- 管理员日常只需勾 SC 组即可授权。
- 隐藏原生组后业务功能不受影响（SC 链路完整）。
- 权限问题可追溯：缺哪一组 / 哪条 ACL / 哪条 rule / 哪个字段 groups 依赖。

## 9. 立即落地建议（当前系统）
- 隐藏所有原生组分类（或至少不在业务界面暴露），确保链路完整。 
- 确认 SC 组覆盖必要原生依赖（如联系人管理 implied `base.group_partner_manager`）。 
- 将本规范入库并纳入运维手册。

---

> 如果需要进一步的 XML Patch（分类隔离、隐藏原生组、验证脚本清单），可在当前规范基础上追加。该文档已基于 Odoo 17 与现有 SC 能力组体系整理。 
