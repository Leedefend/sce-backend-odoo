---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# Seed 生命周期

本文件定义 seed 在不同环境中的使用方式以及生产环境的严格边界。

## 目的
- Seed 用于初始化**可用基线**。
- Seed **不是** demo 数据，也**不是**迁移。

## Profiles
- `base`：生产可用的最小基线。
- `demo` / `demo_full`：仅用于演示环境。

## 生产规则
- 生产仅允许 `PROFILE=base`。
- 生产 seed 必须显式 DB：`SEED_DB_NAME_EXPLICIT=1` 且 `DB_NAME=<目标库>`。
- 用户初始化为显式启用：
  - `SC_BOOTSTRAP_USERS=1` 必须同时提供 `SEED_ALLOW_USERS_BOOTSTRAP=1`。
  - 必填 `SC_BOOTSTRAP_ADMIN_PASSWORD`。

## 常用命令
- Base profile（生产可用）：
  - `ENV=prod SEED_DB_NAME_EXPLICIT=1 PROFILE=base DB_NAME=sc_prod make seed.run`
- Base + 用户初始化：
  - `ENV=prod SEED_DB_NAME_EXPLICIT=1 SEED_ALLOW_USERS_BOOTSTRAP=1 SC_BOOTSTRAP_USERS=1 \
    SC_BOOTSTRAP_ADMIN_PASSWORD='***' PROFILE=base DB_NAME=sc_prod make seed.run`

## 常见失败原因
- 启用 `SC_BOOTSTRAP_USERS=1` 但未提供密码。
- 生产未显式 DB。
- 在生产使用 `demo_full` profile（已被 guard 阻止）。

## 相关 SOP
- 生产命令策略：`docs/ops/prod_command_policy.md`
- 发布清单：`docs/ops/release_checklist_v0.3.0-stable.md`
