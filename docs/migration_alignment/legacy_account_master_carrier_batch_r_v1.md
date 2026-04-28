# 历史账户主数据承载 Batch-R

## 1. 批次定位

- Layer Target：Domain Carrier
- Module：`addons/smart_construction_core`、`scripts/migration`、`Makefile`
- Reason：旧库“账户收支统计表”以 `C_Base_ZHSZ` 为账户维度主表。没有账户主数据，无法正确承载账户类型、账户名称、账号、期初余额和当前账户余额口径。

## 2. 新增承载

新增模型：

```text
sc.legacy.account.master
```

核心字段：

- `legacy_account_id`：旧账户 ID
- `project_legacy_id` / `project_id`：旧项目与新项目关联
- `name`：账户名称
- `account_no`：账号
- `account_type`：账户类型
- `opening_balance`：期初余额
- `bank_name`：开户行
- `is_default`：默认账户
- `fixed_account`：固定账户
- `legacy_state`：旧账户状态

新增入口：

- Action：`smart_construction_core.action_sc_legacy_account_master`
- Menu：`smart_construction_core.menu_sc_legacy_account_master`
- 菜单名称：历史账户
- 父级：财务账款

## 3. 可重建能力

新增旧库 adapter：

```bash
make fresh_db.legacy_account_master.replay.adapter
```

输出：

```text
artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv
artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json
```

新增写入脚本：

```bash
make fresh_db.legacy_account_master.replay.write
```

并接入：

```text
scripts/migration/history_continuity_oneclick.sh
```

保证完整重建时会在项目锚点之后重放历史账户主数据。

## 4. 模拟生产验证

- 旧库 payload：`117` 条账户
- 写入模拟生产：`117` 条账户
- 有效账户：`63`
- 账户类型：`12`
- 账号数：`112`
- Action：存在，模型为 `sc.legacy.account.master`
- Menu：存在，父级为 `财务账款`

## 5. 下一步

在该账户主数据基础上建立 `账户收支统计表` 只读聚合：

- 一级账户类型行
- 二级账户行
- 支出金额、收入金额、期初余额、累计收款、累计支出、账户往来、当前账户余额
