# User Default Email Sync v1

## 目的

为真实业务用户补齐统一默认邮箱，避免 Odoo `message_post` 在付款提交等流程中因 sender email 缺失阻断。

## 默认邮箱

`default@smartconstruction.local`

用户后续可自行修改为个人真实邮箱。

## 写入范围

仅写入 active 内部业务用户，且只写入空邮箱用户。

排除：

- 停用用户
- share/portal 用户
- service/bot 类用户
- fixture 类账号 `sc_fx_*`
- 已有邮箱的用户

## 实际写入

写入 `8` 个真实业务用户：

| login | name | new email |
| --- | --- | --- |
| `wutao` | 吴涛 | `default@smartconstruction.local` |
| `duanyijun` | 段奕俊 | `default@smartconstruction.local` |
| `wennan` | 文楠 | `default@smartconstruction.local` |
| `lina` | 李娜 | `default@smartconstruction.local` |
| `jiangyijiao` | 江一娇 | `default@smartconstruction.local` |
| `chenshuai` | 陈帅 | `default@smartconstruction.local` |
| `shuiwujingbanren` | 税务经办人 | `default@smartconstruction.local` |
| `luomeng` | 罗萌 | `default@smartconstruction.local` |

未覆盖任何已有邮箱。

## 验证

- scoped real business users: `9`
- missing sender email after sync: `0`
- default email users: `8`
- rollback-only daily no-contract payment E2E: PASS

E2E 探针结果：

- source payment: `1`
- operator: `wutao`
- operator email: `default@smartconstruction.local`
- final state: `done`
- validation status: `validated`
- generated ledger: yes
- contract selected: no
- settlement selected: no
- rollback check: payment/ledger/attachment all `0`

## 注意

本轮只补用户邮箱主数据。

上一批 authority alignment 代码已经提交，但当前运行库还需要模块升级或执行角色矩阵同步后，付款审批角色才会真实继承 `smart_core.group_smart_core_finance_approver`。本轮 E2E 为隔离验证邮箱修复效果，使用了 rollback-only 临时角色继承，不落库。
