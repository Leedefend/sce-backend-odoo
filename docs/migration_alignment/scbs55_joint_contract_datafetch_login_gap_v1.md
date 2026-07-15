# SCBS55 联营施工合同二次取数缺口 v1

Generated At: 2026-06-02T17:41:51Z

## 结论

`施工合同（旧业务）` 是联营 SCBS55 用户验收入口，当前新系统入口为：

- 新系统菜单：`智慧施工管理平台/用户核对菜单/合同/施工合同（旧业务）`
- 新系统路由：`/a/855?menu_id=655`
- 新系统模型：`construction.contract`
- 新系统动作：`SCBS55 030 施工合同`
- 当前可见记录数：1563

用户反馈的 `结算金额` 等字段缺失，根因不是前端显示问题，而是旧系统列表首层接口没有完整返回页面可见财务字段；旧系统页面还会继续调用 `LowCode/FormApi/GetFormDatabyDataSourceConfig` 做二次取数，再把返回字段合并到列表行。

当前缺口状态：脚本逻辑已补齐，但无法完成在线全量重抓和回填，因为联营旧系统 `SCBS` 登录接口当前对账号 `13518193984 / 890785` 返回 `500 {"Code":10002,"Msg":"操作失败"}`。该问题不能记为“等待网络恢复”，应作为外部登录态阻断缺口跟踪。

## 已确认事实

联营旧系统入口：

- URL：`https://www.builderp.cn/SCBS/System/User/Login`
- API Base：`https://www.builderp.cn/SCBS`
- 账号：`13518193984`
- 密码：`890785`
- 对应旧系统配置：`ConfigId=164b665cc3674384aeaa89f3122895cf`
- 旧系统菜单：`项目/综合/施工合同/施工合同`
- 旧系统主表：`T_ProjectContract_Out`

开发服务器当前新系统入口：

- 服务器：`1.95.85.92:18081`
- action：`855`
- menu：`655`
- model：`construction.contract`
- domain：`[('legacy_contract_id', '!=', False), ('legacy_income_surface_visible', '=', True)]`

浏览器网络录制证明旧系统施工合同列表二次接口返回以下可见字段：

- `ZJE`：结算金额候选字段
- `LJKP`：累计开票
- `LJSK`：累计收款
- `WSK`：未收款
- `WSKBL`：未收款比例
- `BGJE`：变更金额

录制证据：

- `artifacts/browser/scbs55-old-contract-network-20260602T082119/network.json`

关键观察：

- 旧系统前端登录使用 `IsEncrypt=true`
- `PasswordMd5=md5(890785)=df1caeaa09f66966d480d1c42497c1dc`
- `Password=sm3Digest(890785)=01d46e3ea6a183da6c99b88d3e761e8a0c324dc13f39293e3c8a46fc476d1183`
- 当前本地与开发服务器按该参数登录仍返回 `Code=10002 操作失败`
- `SCBS + 12345678` 明确返回密码错误，说明本缺口不是把直营密码误用于联营
- `SCBSLY_V2 + 12345678` 可登录，但这是直营口径，不可用于本入口

## 已完成代码修复

1. `scripts/verify/scbs_55_old_system_list_count_probe.py`

   - 增加 `sm3()`，按旧系统前端方式优先加密登录。
   - 增加 `OLD_SCBS_TOKEN` 直通，后续可以使用浏览器有效 Token 跳过登录接口阻断，直接在线取 `config/list/datafetch`。
   - 保留明文登录兜底，兼容旧脚本调用方式。

2. `scripts/verify/scbs_55_old_system_list_full_row_dump.py`

   - 收紧旧包复用条件。
   - 如果旧包没有 `data_fetch_count` 和 `datafetch_pages` 元信息，不再复用，必须重新在线抓取。
   - 该修复避免“严格验证”误把缺二次取数的首层包当作合格数据。

3. `scripts/migration/scbs55_contract_surface_online_patch.py`

   - 支持 `SCBS55_CONTRACT_SOURCE_PATH` 指定全量在线重抓包路径。
   - `legacy_visible_settlement_amount` 来源扩展为 `D_SCBSJS_JSJE`、`ZJE`、`GCJSZJ`。
   - 其中 `ZJE` 来自旧系统施工合同页面二次接口，必须保留。

本地与开发服务器均已同步并通过 `py_compile`。

## 未完成事项

以下动作尚未完成，不能标记施工合同数据合格：

1. 使用有效联营 SCBS 登录态在线重抓 `seq003 施工合同`。
2. 确认输出包包含 `data_fetch_count > 0` 和 `datafetch_pages > 0`。
3. 用二次取数后的全量包回填 action 855 对应的 `construction.contract`。
4. 对比 `legacy_visible_settlement_amount/LJKP/LJSK/WSK/WSKBL` 与旧系统在线页面可见值。
5. 浏览器打开 `http://1.95.85.92:18081/a/855?menu_id=655` 验证用户看面。

## 恢复执行方式

如果联营账号密码登录恢复，运行环境还必须按
`docs/security/online_capture_configuration_contract_v1.md` 注入 online 模式、目标 allowlist、采集窗口和输出目录：

```bash
OLD_SCBS_USERNAME=<provided-via-secret-environment> \
OLD_SCBS_PASSWORD=<provided-via-secret-environment> \
SCBS55_OLD_FULL_DUMP_SEQS=3 \
SCBS55_OLD_FULL_DUMP_REUSE_EXISTING=0 \
SCBS55_OLD_FULL_DUMP_DIR=/tmp/scbs55_seq003_datafetch \
python3 scripts/verify/scbs_55_old_system_list_full_row_dump.py
```

浏览器 Token 旁路已禁用；采集必须经过统一 username/password、显式 online 确认和目标 allowlist 门禁。

回填开发库：

```bash
SCBS55_CONTRACT_SOURCE_PATH=/tmp/scbs55_seq003_datafetch/scbs_55_old_live_full_rows_seq003_施工合同.json.gz \
odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --no-http < scripts/migration/scbs55_contract_surface_online_patch.py
```

## 风险

在没有完成在线二次取数全量重抓前，不能再把旧包复用结果作为严格验证结论。旧包如果没有 `data_fetch_count/datafetch_pages`，只能作为首层接口证据，不能证明用户旧系统看面一致。
