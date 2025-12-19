# Razor DB Init（Odoo 17 + smart_construction_core）

目标：在开发/演示环境快速得到“可登录、可用、低噪音、可回滚”的数据库。

- DB 全新重建
- 只安装指定模块
- 降噪（高噪音 cron / 易炸 server action）
- 所有变更可审计、可回滚

## 目录与文件

- `Makefile`：`up / db.drop / db.create / install / noiseoff / noiseon / verify.noise / db.rebuild.noiseoff`
- `addons/smart_construction_core/tools/sql/noiseoff.sql`：降噪 + 审计（表 `sc_noise_audit_cron`）
- `addons/smart_construction_core/tools/sql/noiseon.sql`：按最近一批审计记录回滚 cron

## 一键路径（推荐）

```bash
make db.rebuild.noiseoff MODULE=smart_construction_core DB=sc
```

验收点：
- DB `sc` 重建，无脏数据
- 模块 `smart_construction_core` 安装完成
- 降噪执行输出清单
- `make verify.noise DB=sc` 通过（active_noise_cron=0，易炸 action=0）

## 分步路径（精细控制）

```bash
make up
make db.drop   DB=sc
make db.create DB=sc
make install   MODULE=smart_construction_core DB=sc
make noiseoff  DB=sc
make verify.noise DB=sc
# 如需恢复默认生态：
make noiseon   DB=sc
```

## 降噪策略（为什么）

默认 cron/server action 在核心模块不全时易触发 KeyError/AttributeError、日志刷屏。剃刀流程在开发 DB 里按名称关闭高噪音 cron，并钝化已知易炸的 server action，确保环境可控、可预测。

## 审计与回滚

- `noiseoff.sql`：记录本次关闭的 cron（id/name/old_active/new_active/audited_at），再执行关闭，并输出本次清单。
- `noiseon.sql`：按最近一批审计记录恢复 cron 状态并输出结果。

## 验收清单（可用于 CI 前置检查）

1) DB 可连接：`SELECT 1;`
2) 核心模块：`SELECT name, state FROM ir_module_module WHERE name='smart_construction_core';`
3) 降噪验证：
   - active_noise_cron = 0
   - bad_server_actions = 0
4) Web 能登录、菜单正常（人工或自动探测）

## 常见问题定位

- `Skipping database ... modules to install/upgrade`：执行 `-u/-i` 中，完成后再跑 `noiseoff + verify`。
- `relation "ir_actions_server" does not exist`：Odoo 17 表名是 `ir_act_server`（脚本已使用）。
- 日志刷屏但页面可用：高概率 cron 噪音，先 `make noiseoff`。

## 后续可选迭代

- `make demo.load` / `seed.load`：加载自定义核心 demo（项目/合同/清单/付款链路）。
- `make smoke`：跑 `sc_smoke` 标签的测试。
- `make db.rebuild.dev`：集成 rebuild + install core + noiseoff + seed + smoke，形成完整一键复现链路。
