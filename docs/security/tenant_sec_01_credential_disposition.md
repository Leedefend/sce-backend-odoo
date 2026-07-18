# TENANT-SEC-01 凭据风险处置

English: [tenant_sec_01_credential_disposition.en.md](tenant_sec_01_credential_disposition.en.md)

状态：`ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE`

本记录不包含凭据值、可逆特征、脱敏指纹或原始匹配上下文。未使用旧凭据登录，
未访问旧系统，也未执行公共 Git 历史重写。

## 脱敏分类

| 编号 | 类型 | 首次出现提交 | 当前 HEAD | 旧系统仍需使用 | 撤销/轮换 | 风险负责人 | 最终处置 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CRED-01` | 旧系统用户名 | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | 不存在 | 是 | 否 | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |
| `CRED-02` | 旧系统密码 | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | 不存在 | 是 | 否 | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |
| `CRED-03` | 旧系统密码 | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | 不存在 | 是 | 否 | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |

## 临时风险接受边界

```text
LEGACY_SYSTEM_STILL_REQUIRED=true
ALLOWED_USE=data_completion_and_migration_only
CREDENTIAL_STORED_OUTSIDE_GIT=true
RETIREMENT_TRIGGER=new_system_cutover
RISK_ACCEPTED_BY=Delivery owner
```

凭据能力只能通过仓库外受控 secret 提供，不允许存在 Git 内置默认值、跨系统
fallback、URL 内嵌认证或日志回显。新系统切换时必须撤销凭据并使相关会话失效。

## 历史裁决

`HISTORY_REWRITE=NOT_EXECUTED_DURING_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE`

当前凭据仍未被证明撤销、轮换或由提供方失效，因此不能宣称
`HISTORY_REWRITE_NOT_REQUIRED_AFTER_REVOCATION`。本轮根据明确风险接受保留历史，
不执行 filter-repo、BFG、强推、tag 删除或 fork/cache 清理。切换时若凭据仍无法撤销，
必须重新进入 `HISTORY_REWRITE_DECISION_REQUIRED` 裁决。
