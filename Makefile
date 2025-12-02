# ================== 基本配置 ==================
COMPOSE        := docker-compose
DB_NAME        := sc_odoo
DB_USER        := odoo
DB_CONTAINER   := sc-db
ODOO_CONTAINER := sc-odoo
INIT_MODULES   := base

# ================== 基础操作 ==================
.PHONY: up down restart ps logs odoo-shell db-reset

# 启动全部服务
up:
	@echo "== docker-compose up -d =="
	$(COMPOSE) up -d

# 停止全部服务
down:
	@echo "== docker-compose down =="
	$(COMPOSE) down

# 重启（先 down 再 up）
restart:
	@echo "== docker-compose restart (down + up) =="
	$(COMPOSE) down
	$(COMPOSE) up -d

# 查看容器简表
ps:
	@echo "== docker ps (table) =="
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看 Odoo 日志
logs:
	@echo "== docker-compose logs -f $(ODOO_CONTAINER) =="
	$(COMPOSE) logs -f $(ODOO_CONTAINER)

# 进入 Odoo 容器
odoo-shell:
	@echo "== docker exec -it $(ODOO_CONTAINER) bash =="
	docker exec -it $(ODOO_CONTAINER) bash

# ================== 重置数据库并初始化模块 ==================
db-reset:
	@echo "== Reset PostgreSQL database [$(DB_NAME)] and reinstall modules: $(INIT_MODULES) =="
	@echo "== 1) stop $(ODOO_CONTAINER) to release DB connections =="
	- docker stop $(ODOO_CONTAINER)

	@echo "== 2) terminate existing connections to $(DB_NAME) =="
	- docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB_NAME)' AND pid <> pg_backend_pid();"

	@echo "== 3) drop & recreate database $(DB_NAME) =="
	- docker exec $(DB_CONTAINER) dropdb  -U $(DB_USER) $(DB_NAME)
	- docker exec $(DB_CONTAINER) createdb -U $(DB_USER) $(DB_NAME) -O $(DB_USER) -E UTF8 -T template0

	@echo "== 4) start $(ODOO_CONTAINER) =="
	- docker start $(ODOO_CONTAINER)

	@echo "== 5) init modules: $(INIT_MODULES) =="
	- docker exec $(ODOO_CONTAINER) odoo -c /etc/odoo/odoo.conf -d $(DB_NAME) -i $(INIT_MODULES) --without-demo=all --stop-after-init

	@echo "== ✅ db-reset done. You can now run: make up 或 docker-compose up -d =="
