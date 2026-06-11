# 在线可见面核实协议 - 2026-06-11

## 目的

用户在线系统的实时可见面是业务口径核实的最高优先级证据。本地开发库、迁移产物和 SQL 画像只能用于解释和实现，不能替代用户实际登录后看到的菜单、列表字段、记录数量、表单字段和办理动作。

后续登记、申请、审批、确认、执行等业务闭环迭代，必须优先使用两类在线系统核实：

- 旧在线系统：证明用户原来如何看到业务、如何分类、哪些字段和记录是验收口径。
- 在线开发系统：证明新系统用户实际可见面、办理入口和业务数据是否与目标口径一致。

## 证据优先级

1. 旧在线系统真实登录后的菜单、列表、表单、记录数量和接口返回。
2. 在线开发系统真实用户登录后的菜单、列表、表单、办理动作和接口返回。
3. 本地 `sc_demo` / 迁移产物 / SQL 画像 / Odoo shell 审计。
4. 静态代码、XML、文档和历史推断。

如果 1、2 与本地数据分析冲突，先按在线可见面复核用户认知和旧系统实际行为，再决定是否修正本地模型、迁移数据或产品口径。

## 标准核实链路

每个用户可见业务域收口前，至少形成以下三段证据：

- 旧系统在线证据：旧菜单是否可见、列表字段是否一致、记录数量是否匹配、关键样本是否能打开。
- 新系统在线证据：新菜单是否可见、入口是否清晰、列表字段和记录数量是否对齐、表单能否新增/提交/审批/完成。
- 后端事实证据：正式模型、锁定事实、投影台账、审批日志和附件追溯是否能解释在线可见面。

## 现有工具

旧系统在线可见面：

```bash
OLD_SCBS_LOGIN_URL=https://www.builderp.cn/SCBS/System/User/Login \
OLD_SCBS_USERNAME=... \
OLD_SCBS_PASSWORD=... \
python3 scripts/migration/scbs_55_old_system_visible_surface_login_probe.py
```

旧系统与新系统浏览器对比：

```bash
OLD_SCBS_BASE_URL=https://www.builderp.cn/SCBS \
OLD_SCBS_USERNAME=... \
OLD_SCBS_PASSWORD=... \
FRONTEND_URL=http://127.0.0.1:5174 \
DB_NAME=sc_demo \
E2E_LOGIN=wutao \
E2E_PASSWORD=... \
node scripts/verify/scbs_55_old_new_browser_surface_compare.js
```

用户验收在线记录数复核：

```bash
OLD_SCBS_USERNAME=... \
OLD_SCBS_PASSWORD=... \
python3 scripts/verify/scbs55_user_acceptance_online_probe.py
```

增量在线证据拉取（日常默认方式）：

```bash
set -a
source .env.local
set +a
ONLINE_VISIBLE_SURFACE_MODE=incremental \
ONLINE_VISIBLE_SURFACE_SEQS=022,023,027,028,032,037,038 \
DB_NAME=sc_demo \
bash scripts/ops/validate_online_visible_surface_verification.sh
```

完整旧新系统实时一致性门禁（最终交付前运行）：

```bash
set -a
source .env.local
set +a
ONLINE_VISIBLE_SURFACE_MODE=full \
DB_NAME=sc_demo \
bash scripts/ops/validate_online_visible_surface_verification.sh
```

默认策略是按需增量：每次只拉当前业务域需要的旧系统菜单序号，复用已有在线 dump 作为定位缓存，避免重复拉取全量数据。最终交付收口必须显式运行 `ONLINE_VISIBLE_SURFACE_MODE=full`，缓存的旧系统 dump 只能作为定位辅助，不能作为最终收口证据。

## 使用原则

- 不在代码、文档或日志中记录密码、Token、Cookie。
- 在线系统证据优先用于“用户认知”和“可见面”确认，不直接覆盖本地数据模型。
- 发现旧系统可见面与当前新系统口径不一致时，先记录差异，再判断是旧系统特例、迁移缺口、产品口径错误还是新系统实现缺陷。
- 菜单入口可以整合，但业务类别必须以用户可见数据和在线办理行为为依据，沉淀为可维护字典。
- 收付款申请、往来款、公司-承包人责任、项目资金状态、资金日报必须分层核实，不能只凭表名或旧菜单名归类。
- 每次业务域收口时，把在线证据路径、运行命令、产物路径和未覆盖残差写入对应迭代文档。
- 日常迭代只运行当前业务域所需的 `ONLINE_VISIBLE_SURFACE_SEQS`；不得因为单点核实触发全量在线抓取。

## 当前状态

在线登录变量应保存在本地忽略文件 `.env.local` 或当前 shell 环境中，不进入仓库。后续业务域推进时优先运行增量在线核实命令；最终交付前再运行完整门禁。
