# -*- coding: utf-8 -*-
# 在新模型定义加载之后执行：建新唯一约束、索引、数据修复等
from odoo import SUPERUSER_ID, api

SOURCE_KIND = "smart_core_schema_post_migration"
SOURCE_AUTHORITIES = ("postgres_schema", "app_menu_config", "app_view_config")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": False,
        "rebuildable": False,
        "write_proxy": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "schema_migration_only": True,
    }


def migrate(cr, version):
    # 新唯一约束
    cr.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'uniq_dim'
      ) THEN
        ALTER TABLE app_menu_config
        ADD CONSTRAINT uniq_dim
        UNIQUE (target_model, scene, company_id, lang);
      END IF;
    END $$;
    """)

    # 组合索引
    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_menu_cfg_dim
        ON app_menu_config (scene, target_model, company_id, lang);
    """)

    cr.execute("""
    UPDATE app_view_config
       SET projection_scope = CONCAT('generic:', model, ':', view_type)
     WHERE projection_scope IS NULL OR projection_scope = '';
    """)

    cr.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'app_view_config'
          AND constraint_name = 'uniq_projection_scope'
      ) THEN
        ALTER TABLE app_view_config
        ADD CONSTRAINT uniq_projection_scope UNIQUE (projection_scope);
      END IF;
    END $$;
    """)

    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_view_config_projection_scope
        ON app_view_config (projection_scope);
    """)
    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_view_config_action_view
        ON app_view_config (model, view_type, action_id, source_view_id);
    """)
