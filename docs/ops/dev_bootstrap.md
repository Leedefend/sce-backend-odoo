# 开发环境一键启动与 Demo 重置指南

本页用于：开发者本地启动、反向代理访问验证、以及一键重置/装载 demo 数据。
适用于本仓库的 Docker Compose 开发模式。

## 1. 启动服务

在仓库根目录执行：

```bash
docker compose up -d
docker compose ps
```

期望看到（示例）：

* `sc-db` / `sc-redis` / `sc-odoo` / `sc-nginx` 均为 `Up`
* `sc-db` 为 `healthy`
* 若配置了 Odoo healthcheck，`sc-odoo` 也会显示 `healthy`

## 2. 反向代理登录入口（Nginx）

反代入口（推荐）：

* http://localhost:18080/web

直连入口（仅用于对比排障）：

* http://localhost:8069/web

### 常见问题：能打开但无法登录/重定向异常

若出现从 `:18080` 跳到 `http://localhost/web/...`（端口丢失）：

* 检查 `config/nginx/conf.d/default.conf` 中 `proxy_set_header Host` 是否使用 `$http_host`
* 该仓库默认配置已修复此问题（保留端口，避免错误重定向）

快速验收命令：

```bash
curl -I http://localhost:18080/web | head -n 20
```

期望：

* 返回 `200` 或 `303`
* 若有 `Location`，应保留 `:18080`（例如 `http://localhost:18080/...`）

## 3. Demo 一键重置与装载

### 3.1 一键执行（推荐）

```bash
make demo.full DB=sc_demo
```

### 3.2 分步执行（排障用）

```bash
make demo.reset DB=sc_demo
make demo.load.all DB=sc_demo
make demo.verify DB=sc_demo
```

说明：`reset` 只负责重置数据库并初始化基础；`load` 负责装载 demo 数据。

## 4. DB Reset 安全护栏（重要）

`scripts/db/reset.sh` 内置安全护栏，防止误删：

* `DB_NAME` 为空：直接拒绝执行
* 系统库名：`postgres/template0/template1` 直接拒绝执行
* 若设置了 `PROJECT`，会校验 db 容器所属 compose project 是否匹配，不匹配则拒绝执行

这些护栏用于避免在多项目/多 compose 环境下误操作数据库。

## 5. 常用排障命令

### 5.1 查看 Nginx 生效配置

```bash
docker compose exec -T nginx nginx -T | sed -n '1,220p'
```

### 5.2 查看 Nginx 最近日志

```bash
docker compose logs --tail=200 nginx
```

### 5.3 查看 Odoo 最近日志

```bash
docker compose logs --tail=200 odoo
```

### 5.4 快速确认 Odoo upstream 可达（从 Nginx 容器内）

```bash
docker compose exec -T nginx sh -lc 'apk add --no-cache curl >/dev/null 2>&1 || true; curl -I http://odoo:8069/web | head -n 20'
```

## 6. 约定的默认端口

* Odoo: 8069
* Nginx (reverse proxy): 18080
