# SCEMS v1.0 部署指南（Deployment Guide）

## 1. 适用范围
- 目标版本：`SCEMS v1.0`
- 适用环境：`dev` / `test` / `prod`
- 部署方式：Docker Compose + Makefile 编排

## 2. 环境前置条件
- 已安装 Docker / Docker Compose。
- 已准备 `.env`（或 `.env.dev` / `.env.test` / `.env.prod`），并校验 `COMPOSE_PROJECT_NAME`、`DB_NAME`、`ENV`。
- 执行预检：
  - `make check-compose-project`
  - `make check-compose-env`

## 3. 标准部署流程

### 3.1 启动基础服务
- `make up`
- `make ps`

### 3.2 初始化数据库与演示数据（dev/test）
- 重置数据库：`make db.reset DB_NAME=<db>`
- 导入演示基线：`make demo.reset DB=<db>`

### 3.3 安装/升级模块
- 安装模块：`make mod.install MODULE=smart_construction_core DB_NAME=<db>`
- 升级模块：`make mod.upgrade MODULE=smart_construction_core DB_NAME=<db>`

### 3.4 关键验证
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`

## 4. 升级与回滚

### 4.1 升级流程
- 执行升级：`make mod.upgrade MODULE=<module_list> DB_NAME=<db>`
- 执行回归验证：
  - `make verify.phase_next.evidence.bundle`
  - `make verify.runtime.surface.dashboard.strict.guard`

### 4.2 回滚流程（分支/代码）
- 使用 Codex 回滚编排：`make codex.rollback`

### 4.3 场景层回滚（scene channel）
- `make scene.rollback.stable`
- 验证：`make verify.portal.scene_rollback_smoke.container`

## 5. 环境参数建议

### 5.1 dev
- `ENV=dev`
- `DB_NAME=sc_demo`

### 5.2 test
- `ENV=test`
- 建议独立 `DB_NAME`，并固定验证账号密码

### 5.3 prod
- `ENV=prod`
- 禁止直接执行重置命令；先执行变更评审与回滚演练

## 6. 部署完成判定
- 服务进程正常（`make ps`）。
- Phase 5 验证命令链通过。
- 验证证据产物已归档到 `artifacts/`。

## 7. 生产模拟（隔离环境，80 直达前端）
- 使用隔离环境文件：`.env.prod.sim`（独立 `COMPOSE_PROJECT_NAME`/DB/Volume）。
- 反向代理行为：`80 -> 前端静态站点`，`/api/* -> Odoo`。
- 一键部署命令（服务器可直接执行）：
  - `make deploy.prod.sim.oneclick ENV=test ENV_FILE=.env.prod.sim`
