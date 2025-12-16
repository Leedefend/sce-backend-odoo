# ================== 基本配置 ==================
COMPOSE        := docker-compose
DB_NAME        := sc_odoo
DB_USER        := odoo
DB_CONTAINER   := sc-db
ODOO_CONTAINER := sc-odoo
INIT_MODULES   := base

# 默认模块 / 测试标签
MODULE ?= smart_construction_core
TEST_TAGS ?= sc_smoke

# 自定义模块集合
CUSTOM_MODULES := smart_construction_core smart_construction_demo

# ================== 基础操作 ==================
.PHONY: up down restart restart-odoo ps logs odoo-shell db-reset upgrade upgrade-all test validate

up:
	@echo "== docker-compose up -d =="
	$(COMPOSE) up -d

down:
	@echo "== docker-compose down =="
	$(COMPOSE) down

restart:
	@echo "== docker-compose restart =="
	$(COMPOSE) down
	$(COMPOSE) up -d

restart-odoo:
	@echo "== restart Odoo container =="
	docker restart $(ODOO_CONTAINER)

ps:
	@echo "== docker ps (table) =="
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	@echo "== docker-compose logs -f odoo =="
	$(COMPOSE) logs -f odoo

odoo-shell:
	@echo "== docker exec -it $(ODOO_CONTAINER) bash =="
	docker exec -it $(ODOO_CONTAINER) bash

# ================== 数据库重置 ==================
db-reset:
	@echo "== Reset database $(DB_NAME) =="
	- docker stop $(ODOO_CONTAINER)
	- docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres \
		-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB_NAME)' AND pid <> pg_backend_pid();"
	- docker exec $(DB_CONTAINER) dropdb -U $(DB_USER) $(DB_NAME)
	- docker exec $(DB_CONTAINER) createdb -U $(DB_USER) $(DB_NAME)
	- docker start $(ODOO_CONTAINER)
	- docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-i $(INIT_MODULES) \
		--without-demo=all \
		--stop-after-init
	@echo "== ✔ db-reset done =="

# ================== 模块升级 ==================
upgrade:
	@echo "== Upgrade module $(MODULE) =="
	docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--stop-after-init
	@echo "== ✔ upgrade done =="

upgrade-all:
	@echo "== Upgrade all custom modules =="
	docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(CUSTOM_MODULES) \
		--stop-after-init
	@echo "== ✔ upgrade-all done =="

# ================== 测试（Smoke） ==================
test:
	@echo "== Running tests: module=$(MODULE) tags=$(TEST_TAGS) =="
	$(COMPOSE) run --rm -T odoo \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--no-http \
		--test-enable \
		--test-tags "$(TEST_TAGS)" \
		--stop-after-init
	@echo "== ✔ test done =="

# ================== 数据校验器 ==================
validate:
	@echo "== Running data validator on $(DB_NAME) =="
	$(COMPOSE) run --rm -T \
		--entrypoint python3 odoo \
		/mnt/extra-addons/smart_construction_core/tools/validator/run_validate.py
	@echo "== ✔ validate done =="
