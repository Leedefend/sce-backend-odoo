# Odoo 17 Clean Baseline 部署文档（可复现 / 无 Demo）

> 适用对象：
>
> * 工程化部署
> * 多环境（本地 / 云服务器）
> * 二次开发 / 产品化
> * **不含 demo 数据，数据库可重复初始化**

---

## 1. 目标与架构说明

### 1.1 部署目标

* Odoo 17 Community
* 无 demo 数据
* 单一数据库（`sc_odoo`）
* 可重复初始化（删 runtime 重新拉起即可）
* 支持大文件导入（Excel / 定额 / 清单）
* 支持 WebSocket
* 双层反向代理（宿主机 nginx + 容器 nginx）

### 1.2 总体架构

```
Browser
  │
  ▼
Host Nginx (80 / 443)
  │   - 入口、安全、TLS
  │
  ▼
Docker sc-nginx (18080)
  │   - Odoo 专用反代 / websocket
  │
  ▼
Docker sc-odoo (8069)
  │   - Odoo 17
  │
  ▼
PostgreSQL 15  +  Redis 7
```

---

## 2. 服务器基础要求

| 项目 | 要求 |
| --- | --- |
| OS | Ubuntu 20.04 / 22.04 |
| CPU | ≥ 2 核 |
| 内存 | ≥ 4 GB（推荐 8 GB） |
| Docker | ≥ 24 |
| Docker Compose | v2 |
| nginx（宿主机） | ≥ 1.20 |

---

## 3. 仓库结构约定

```text
sc-backend-odoo/
├── docker-compose.yml
├── docker-compose.ci.yml
├── .env.example
├── config/
│   ├── odoo.conf.template
│   └── nginx.conf           # sc-nginx 使用
├── scripts/
│   ├── render_odoo_conf.py
│   ├── odoo-entrypoint.sh
│   └── db-init/
│       ├── 001-init-db.sql
│       └── README.md
├── runtime/                 # 运行态数据（不入库）
│   ├── odoo/
│   ├── postgres/
│   └── redis/
└── docs/
    └── ops/
```

---

## 4. 首次部署步骤（标准流程）

### 4.1 拉取代码

```bash
git clone https://github.com/Leedefend/sce-backend-odoo.git
cd sc-backend-odoo
git checkout main
```

确认版本：

```bash
git log -1
# chore(env): stable clean Odoo 17 baseline (no demo, reproducible init)
```

### 4.2 初始化环境变量

```bash
cp .env.example .env
```

至少确认以下字段：

```env
DB_USER=odoo
DB_PASSWORD=odoo
ADMIN_PASSWD=********
JWT_SECRET=********
```

> ⚠️ 生产环境务必修改 `ADMIN_PASSWD` 与 `JWT_SECRET`

### 4.3 初始化 runtime 目录权限（关键）

```bash
rm -rf runtime
mkdir -p runtime/{odoo,postgres,redis}

# Odoo 官方镜像 uid=101
sudo chown -R 101:101 runtime/odoo

# postgres 官方镜像 uid=999
sudo chown -R 999:999 runtime/postgres

# redis（可选）
sudo chown -R 999:999 runtime/redis
```

> ❗ 未设置权限会导致：
>
> * res_lang 加载失败
> * `/var/lib/odoo/.local` PermissionError
> * 数据库初始化中断

### 4.4 启动 Docker 服务

```bash
docker compose down --remove-orphans
docker compose up -d --force-recreate
```

确认状态：

```bash
docker compose ps
```

期望结果：

* sc-db：healthy
* sc-redis：healthy
* sc-odoo：Up
* sc-nginx：Up

### 4.5 验证 Odoo 初始化日志

```bash
docker logs -n 200 sc-odoo
```

关键特征：

* `init db`
* `Module base loaded`
* `Registry loaded`
* `HTTP service running on :8069`

---

## 5. 宿主机 nginx 配置（入口层）

### 5.1 文件路径

```
/etc/nginx/conf.d/default.conf
```

### 5.2 最小可用配置（IP 访问）

```nginx
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 512m;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host              $http_host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout    1800s;
        proxy_read_timeout    1800s;
    }
}
```

测试并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. 访问验证

### 6.1 宿主机直连 sc-nginx

```bash
curl -I http://127.0.0.1:18080/web/login
# HTTP/1.1 200 OK
```

### 6.2 外部访问

浏览器访问：

```
http://<服务器IP>/web/login
```

应出现 **Odoo 登录页面**。

---

## 7. 数据库状态验证

```bash
docker exec -it sc-db psql -U odoo -d sc_odoo \
  -c "select name from ir_module_module where state='installed';"
```

期望结果（基础模块）：

```
base
web
auth_totp
base_import
base_setup
bus
iap
web_editor
web_tour
web_unsplash
```

---

## 8. 重置环境（可复现核心能力）

```bash
docker compose down
rm -rf runtime
# 重做 4.3 → 4.4
```

> ⚠️ 数据将完全清空
> ✔ 适用于测试 / CI / 环境修复

---

## 9. 常见问题速查

### Q1：502 Bad Gateway

* 检查宿主机 nginx 是否 proxy_pass 到 18080
* 检查 `server_name` 是否命中（IP 访问需 `_` 或 `default_server`）

### Q2：PermissionError: /var/lib/odoo/.local

* runtime/odoo 权限未 chown 为 101

### Q3：数据库初始化卡住

* 检查 scripts/db-init 是否只执行一次
* 确认 DB_PASSWORD 一致

---

## 10. 基线声明（非常重要）

> **env-baseline-odoo17-clean** 是后续所有开发、部署、排障的唯一参考基线。
> 所有模块、功能问题，必须在该基线可正常启动的前提下进行。

## 11. 生产与发布参考

- 生产命令策略：`docs/ops/prod_command_policy.md`
- 发布清单：`docs/ops/release_checklist_v0.3.0-stable.md`

---

后续可选动作：

1. 将本文拆成「新服务器 30 分钟上线 checklist」
2. 做一份 CI 用的无交互初始化脚本
3. 在此基线之上，开始接入 smart_construction_core
