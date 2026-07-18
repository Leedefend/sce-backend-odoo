USER_DATA_REPORT_PATH ?= /tmp/user-data-production-boundary.json
USER_DATA_PLAN_PATH ?= /tmp/user-data-demo-removal-plan.json

.PHONY: verify.user_data.production_boundary verify.user_data.role_boundary user_data.demo_impact_report user_data.demo_removal.plan user_data.demo_removal.apply verify.user_data.post_demo_removal demo.ownership_cleanup.report demo.ownership_cleanup.apply

verify.user_data.production_boundary:
	@python3 scripts/verify/user_data_production_boundary_guard.py

verify.user_data.role_boundary: verify.user_data.production_boundary
	@USER_DATA_ROLE_REPORT_PATH=$(USER_DATA_REPORT_PATH) \
		$(MAKE) --no-print-directory odoo.shell.exec < scripts/user_data/user_role_boundary_audit.py

user_data.demo_impact_report: verify.user_data.production_boundary
	@USER_DATA_ACTION=impact USER_DATA_REPORT_PATH=$(USER_DATA_REPORT_PATH) \
		$(MAKE) --no-print-directory odoo.shell.exec < scripts/user_data/user_data_production_boundary.py

user_data.demo_removal.plan: verify.user_data.production_boundary
	@USER_DATA_ACTION=plan USER_DATA_REPORT_PATH=$(USER_DATA_REPORT_PATH) USER_DATA_PLAN_PATH=$(USER_DATA_PLAN_PATH) \
		$(MAKE) --no-print-directory odoo.shell.exec < scripts/user_data/user_data_production_boundary.py

user_data.demo_removal.apply: verify.user_data.production_boundary
	@USER_DATA_ACTION=apply USER_DATA_REPORT_PATH=$(USER_DATA_REPORT_PATH) USER_DATA_PLAN_PATH=$(USER_DATA_PLAN_PATH) \
		$(MAKE) --no-print-directory odoo.shell.exec < scripts/user_data/user_data_production_boundary.py

verify.user_data.post_demo_removal: verify.user_data.production_boundary
	@USER_DATA_ACTION=verify USER_DATA_REPORT_PATH=$(USER_DATA_REPORT_PATH) \
		$(MAKE) --no-print-directory odoo.shell.exec < scripts/user_data/user_data_production_boundary.py

demo.ownership_cleanup.report: guard.prod.forbid check-compose-project check-compose-env
	@DEMO_OWNERSHIP_ACTION=report $(MAKE) --no-print-directory odoo.shell.exec < scripts/ops/demo_ownership_cleanup.py

demo.ownership_cleanup.apply: guard.prod.forbid check-compose-project check-compose-env
	@DEMO_OWNERSHIP_ACTION=apply $(MAKE) --no-print-directory odoo.shell.exec < scripts/ops/demo_ownership_cleanup.py
