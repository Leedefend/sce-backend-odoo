# Authority Runtime Upgrade v1

## 目的

将已提交的付款审批角色继承关系应用到 `sc_demo` 运行库，使 `付款中心-审批` 真实继承 `smart_core.group_smart_core_finance_approver`。

## 执行

```bash
CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo make mod.upgrade
```

升级结果：PASS

## 升级后权限事实

- `smart_construction_custom.group_sc_role_payment_manager` 已继承 `smart_core.group_smart_core_finance_approver`
- canonical approver users:
  - `wutao`
  - `duanyijun`
  - `wennan`
  - `lina`
  - `jiangyijiao`
  - `chenshuai`
  - `shuiwujingbanren`
  - `luomeng`

## E2E 验证

rollback-only daily no-contract payment E2E：PASS

- source payment: `1`
- operator: `wutao`
- operator email: `default@smartconstruction.local`
- authority runtime applied: true
- final state: `done`
- validation status: `validated`
- payment ledger generated: yes
- contract selected: no
- settlement selected: no
- rollback check:
  - payment request: `0`
  - payment ledger: `0`
  - attachment: `0`

## 结论

新系统已经可以用真实运行库权限和真实默认邮箱，继续办理无合同、无结算单的企业日常付款业务。

本轮没有源码改动，只执行运行库模块升级并记录验证结果。
