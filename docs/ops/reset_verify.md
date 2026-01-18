---
capability_stage: P0
status: frozen
since: v0.3.0-stable
---
## Reset & Verify 手册

### 目标
- 一键重置干净开发库（base + bootstrap，不含 demo/seed）
- 一键重置演示库（base + bootstrap + seed + demo）
- 一键验收基线/演示初始化是否正确

### 常用命令

```bash
# 开发库（干净基线）
make db.reset DB=sc_odoo
make verify.baseline DB=sc_odoo

# 演示库（包含 seed + demo，内部启用 SC_SEED_ENABLED=1）
make db.demo.reset   # 默认 DB=sc_demo
make verify.demo DB=sc_demo

# 聚合门禁（重置 + 验收）
make gate.baseline   # 等同 db.reset + verify.baseline，默认 DB=sc_odoo
make gate.demo       # 等同 db.demo.reset + verify.demo，默认 DB=sc_demo
```

### 验收项（当前检查）
- 语言 zh_CN 已激活
- admin 的语言/时区为 zh_CN / Asia/Shanghai
- 公司币种为 CNY
- 模块状态：bootstrap installed；演示库还需 seed/demo installed
- seed 开关：演示库 `sc.bootstrap.seed_enabled = 1`

### 参数说明
- `DB` / `DB_NAME`：目标数据库名（缺省 gate/verify 已设默认值）
- `SC_SEED_ENABLED` / `SC_BOOTSTRAP_MODE`：演示库 reset 时已自动传入，无需额外设置

### 相关 SOP
- 生产命令策略：`docs/ops/prod_command_policy.md`
- 发布清单：`docs/ops/release_checklist_v0.3.0-stable.md`
