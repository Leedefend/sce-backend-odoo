# 仓库在线凭据暴露事件记录（2026-07-15）

## 事件事实

- 发现时间：2026-07-15（Asia/Shanghai）。
- 受影响文件：`scbs55_migration_asset_freeze_topic_v1.md`、`scbs55_joint_contract_datafetch_login_gap_v1.md`。
- 受影响变量类型：SCBS 用户名、密码；当前树共六处重复非占位赋值。
- 脱敏指纹：用户名 `ec2b5afa5f5f`；密码 `05278d964396`、`2efb1047074f`。均为 SHA256 截断值，原值和新值不得进入本文件。
- 当前树处置：所有已确认赋值已替换为 `<provided-via-secret-environment>`。
- session 撤销状态：未执行。
- 凭据撤销状态：用户明确决定保留至旧系统历史数据整理完成后下线。
- 异常访问调查：未提供仓库外调查结论。
- Security owner：由旧系统管理责任方承担，组织内具体标识未提供给仓库。

## Git 历史裁决

只读历史扫描定位到 4 个相关 reachable commits：首次出现 `e8cbc880f692d504f2849f75d099aeabd0fb7220`，最后相关变更 `73cb51a37c17223e1b47120c2f284f0ae15b07ca`；后者被 3 个本地/远端引用分支包含，无 tag 包含。扫描只输出提交、路径、规则和脱敏指纹，不回显匹配值。

本次不重写 Git 历史。理由是仓库存在 GitHub/Gitee 双远端、既有 PR、发布 SHA、CI 基线和开发者 clone；重写无法保证清除 fork、clone 或 CI cache，且用户决定旧系统继续作为只读历史数据源。

该裁决不代表历史中的凭据已经消失或失效。旧系统下线前，历史访问权限应按最小范围控制；下线时必须禁用账号并使 session/token 失效。

## 后续控制

- 当前树 secret guard 覆盖 Markdown 中的在线凭据赋值、内置默认值、跨系统 fallback、URL 内嵌凭据和私钥/token 高置信度形态。
- 所有在线访问默认 `offline`；online 模式要求专用 secret、显式确认和目标 allowlist。
- SCBSLY 不再回退使用 SCBS 凭据。
- preflight 覆盖正式采集、在线 replay、列表/表单探针、浏览器对照和旧附件读取入口，并在创建采集产物、网络客户端或数据库入口前失败。
- 在线附件镜像的写入默认值已改为关闭；只有 online 门禁和原脚本写入确认同时满足才可能执行。
- 后续采集产物、日志、trace 和截图不得包含 secret 或真实认证响应。

## 残余风险

旧凭据仍可能存在于 reachable Git 历史、远端缓存和既有 clone 中，并可能在旧系统下线前保持有效。此风险由用户明确接受；它阻止将本事件标记为“凭据已撤销”，但不改变当前树清理和防复发门禁的技术事实。

2026-07-16 后续状态：SEC-POST-01 的离线门禁与候选清单见
`legacy_credential_incident_v1.md`。Delivery owner 明确接受旧系统在数据
补充和迁移期间继续使用，风险状态为
`ACCEPTED_UNTIL_LEGACY_SYSTEM_RETIREMENT`，不再阻塞后续生产只读审计和
产品迭代，但绝不等于 `CLOSED`。正式切换时仍必须关闭入口并撤销全部
旧会话。

English: [repository_credential_incident_20260715.en.md](repository_credential_incident_20260715.en.md)
