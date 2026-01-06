# TP-08｜项目叙事表面（Project Story Surface）v0.1

## 目标（一句话）
把“项目中心”从字段展示升级为“叙事 + 软提示 + 可解释信号”，并保证 PM 视角无可见但不可用入口。

## 适用范围

- 项目详情页（PM 视角）
- 叙事卡与软提示的呈现方式

## 约束（红线）

- 不新增业务流程
- PM 入口不可跳转（除非明确说明）
- 新增字段仅限只读表达字段

## 叙事卡呈现规范

- 位置：项目概览区顶部，优先于关键指标卡
- 数量上限：最多 1 条
- 优先级：黄 > 蓝 > 灰
- 缺失口径：依赖字段缺失则不提示

## 软提示呈现规范

- 位置：关键指标卡下方或右侧摘要区
- 数量上限：最多 2 条（黄优先）
- 缺失口径：依赖字段缺失则不提示

## 可解释性要求

- 每条叙事/软提示必须能回溯到规则编号与字段来源
- 规则表以 `TP-08_story_rules.table.md` 为唯一事实源

## 审计联动（TP-08 执行验收）

- 跑审计：
  - `DB=sc_demo make audit.project.actions`
  - 输出：`docs/audit/action_list_all.csv`、`action_visibility_by_role.csv`、`action_references.csv`、`action_verdict_candidates.csv`
- 角色验收：
  - 对照 `docs/audit/tp08_role_surface_checklist.md` 逐项勾选
- 目标：PM 视角 0 点炸、0 AccessError，且表达层一致

## 变更记录

- v0.1：定义叙事卡/软提示呈现规则与审计联动