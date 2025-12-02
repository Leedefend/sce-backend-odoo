# ============================================================
# Smart Construction Backend — Makefile
# 后端工程化命令统一入口
# ============================================================

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
PROJECT       := sc-backend-odoo
ODDO_CONTAINER := sc-odoo
DB_CONTAINER   := sc-db
COMPOSE        := docker-compose
DB_NAME        := sc_odoo
DB_USER        := odoo

# ------------------------------------------------------------
# 基础命令
# ------------------------------------------------------------

help:
	@echo ""
	@echo "🚀 Smart Construction Backend Makefile"
	@echo ""
	@echo "可用命令："
	@echo "  make up             - 启动所有服务"
	@echo "  make down           - 停止所有服务"
	@echo "  make restart        - 重启所有服务"
	@echo "  make logs           - 查看 Odoo 日志"
	@echo "  make odoo-shell     - 进入 Odoo shell"
	@echo "  make db-shell       - 进入 PostgreSQL"
	@echo "  make ps             - 查看容器状态"
	@echo "  make upgrade MODULE=xxx    - 升级指定模块"
	@echo "  make dump           - 导出数据库"
	@echo "  make restore FILE=xxx.dump - 导入数据库"
	@echo ""

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

ps:
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	docker logs -f $(ODDO_CONTAINER)

# ------------------------------------------------------------
# Odoo 相关
# ------------------------------------------------------------

odoo-shell:
	docker exec -it $(ODDO_CONTAINER) odoo shell -c /etc/odoo/odoo.conf -d $(DB_NAME)

upgrade:
	docker exec -it $(ODDO_CONTAINER) odoo -c /etc/odoo/odoo.conf -d $(DB_NAME) -u $(MODULE)

# ------------------------------------------------------------
# 数据库命令
# ------------------------------------------------------------

db-shell:
	docker exec -it $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME)

dump:
	@mkdir -p backup
	docker exec $(DB_CONTAINER) pg_dump -U $(DB_USER) $(DB_NAME) -Fc > backup/$(DB_NAME)_$$(date +%Y%m%d_%H%M%S).dump
	@echo "🎉 数据库已备份到 backup/ 目录。"

restore:
ifdef FILE
	docker exec -i $(DB_CONTAINER) pg_restore -U $(DB_USER) -d $(DB_NAME) < $(FILE)
	@echo "♻️ 已从 $(FILE) 恢复数据库。"
else
	@echo "❌ 需要指定 FILE，例如： make restore FILE=backup/sc_odoo_xxx.dump"
endif
