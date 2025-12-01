# -*- coding: utf-8 -*-
# 在新模型定义加载之后执行：建新唯一约束、索引、数据修复等
from odoo import SUPERUSER_ID, api

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
