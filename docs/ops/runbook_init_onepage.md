# 初始化 Runbook（一页版）

目标：10 分钟内完成基线/演示/降噪三条路径初始化，并能验收与回滚。

## 前置检查（必做）

1) dbfilter 是否允许目标库

```bash
rg -n "ODOO_DBFILTER" .env
```

期望结果：
- ODOO_DBFILTER 至少包含 sc_odoo|sc_demo

2) runtime 目录权限（部署/本地均适用）

```bash
ls -al runtime
```

期望结果：
- runtime 目录 owner 与 odoo 运行 uid 一致（否则 init 可能失败）

## 路径 A：基线库（sc_odoo，无 demo/seed）

⚠️ 禁止在 sc_odoo 上执行任何 demo/seed 相关命令

```bash
make db.reset DB=sc_odoo
make verify.baseline DB=sc_odoo
```

验收点：
- 语言 zh_CN、时区 Asia/Shanghai、生效币种 CNY
- 模块 `smart_construction_bootstrap` installed

## 路径 B：演示库（sc_demo，含 seed/demo）

```bash
make db.demo.reset
make verify.demo DB=sc_demo
```

验收点：
- verify.demo PASS ALL
- demo users exist / demo contracts exist
- settlement/payment 示例存在
- 任一项缺失即视为初始化失败（需重新 reset）

## 路径 C：开发降噪（razor flow）

```bash
make db.rebuild.noiseoff MODULE=smart_construction_core DB=sc_dev
make verify.noise DB=sc_dev
```

验收点：
- active_noise_cron=0
- bad_server_actions=0

⚠️ sc_dev 仅用于本地开发调试，不得用于 demo/CI/验收

## 应急回滚（最小动作）

原则：先回滚行为（noise），再回滚状态（DB）

1) 回滚降噪

```bash
make noiseon DB=sc_dev
```

2) 重建 DB

```bash
make db.drop DB=sc_dev
make db.create DB=sc_dev
make install MODULE=smart_construction_core DB=sc_dev
```

## 常见卡点

- dbfilter 未放开：重启 odoo 后再试（见：docs/ops/db_strategy.md）
- demo/seed 缺失：verify.demo 会失败（预期行为）
