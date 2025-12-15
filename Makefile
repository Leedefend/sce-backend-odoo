# ================== 基本配置 ==================
COMPOSE        := docker-compose
DB_NAME        := sc_odoo
DB_USER        := odoo
DB_CONTAINER   := sc-db
ODOO_CONTAINER := sc-odoo
INIT_MODULES   := base

# 默认要升级的模块（可在命令行用 MODULE=xxx 覆盖）
MODULE ?= smart_construction_core
TEST_TAGS ?= sc_smoke

# 自定义模块集合（升级全部时使用）
CUSTOM_MODULES := smart_construction_core smart_construction_demo

# ================== 基础操作 ==================
.PHONY: up down restart restart-odoo ps logs odoo-shell db-reset upgrade upgrade-all test validate

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

# 仅重启 Odoo 服务（开发期高频操作）
restart-odoo:
	@echo "== restart Odoo service only: $(ODOO_CONTAINER) =="
	docker restart $(ODOO_CONTAINER)

# 查看容器简表
ps:
	@echo "== docker ps (table) =="
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看 Odoo 日志（注意：compose 的 service 名通常是 odoo，不是 sc-odoo）
logs:
	@echo "== docker-compose logs -f odoo =="
	$(COMPOSE) logs -f odoo

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

# ================== 模块升级（开发期高频操作） ==================

# 升级指定模块（使用 MODULE 变量，带默认值）
# 示例：
#   make upgrade
#   make upgrade MODULE=smart_construction_demo
upgrade:
	@echo "== Upgrading module: $(MODULE) on database: $(DB_NAME) =="
	docker exec $(ODOO_CONTAINER) \
		odoo -c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--stop-after-init
	@echo "== ✔ Upgrade done =="

# 升级所有自定义模块
# 示例：
#   make upgrade-all
upgrade-all:
	@echo "== Upgrading all custom modules: $(CUSTOM_MODULES) =="
	docker exec $(ODOO_CONTAINER) \
		odoo -c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(CUSTOM_MODULES) \
		--stop-after-init
	@echo "== ✔ All modules upgraded =="

# ================== 测试与校验（Phase3.5 当前步骤） ==================

# 运行测试基线（默认 smoke）
# 示例：
#   make test
#   make test TEST_TAGS=sc_smoke
#   make test TEST_TAGS=/   # 全量（不建议日常）
test:
	@echo "== Running tests for module: $(MODULE) (tags: $(TEST_TAGS)) on database: $(DB_NAME) =="
	$(COMPOSE) run --rm -T odoo \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--no-http \
		--test-enable \
		--test-tags "$(TEST_TAGS)" \
		--stop-after-init
	@echo "== ✔ Test run done =="

# 数据校验器（Data Validator）
# 直接用 python 构造 registry/env 调用，避免 stdin/odoo shell/stop-after-init 时序问题
# 示例：
#   make validate
#   make validate DB_NAME=sc_odoo
validate:
	@echo "== Validating data on database: $(DB_NAME) =="
	$(COMPOSE) run --rm -T --entrypoint python3 odoo \
		/mnt/extra-addons/smart_construction_core/tools/validator/run_validate.py
	@echo "== ✔ Validate done =="
