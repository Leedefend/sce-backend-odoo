# -*- coding: utf-8 -*-
# 在加载新模型定义之前执行：加新列、填默认值、删除旧约束、做数据备份等
from odoo import SUPERUSER_ID, api

def migrate(cr, version):
    # 示例：加列（若存在则忽略）
    cr.execute("""ALTER TABLE app_menu_config ADD COLUMN IF NOT EXISTS scene varchar;""")
    cr.execute("""ALTER TABLE app_menu_config ADD COLUMN IF NOT EXISTS company_id integer;""")
    cr.execute("""ALTER TABLE app_menu_config ADD COLUMN IF NOT EXISTS lang varchar;""")
    cr.execute("""ALTER TABLE app_menu_config ADD COLUMN IF NOT EXISTS action_index jsonb;""")
    cr.execute("""ALTER TABLE app_menu_config ADD COLUMN IF NOT EXISTS etag varchar;""")

    # 默认值
    cr.execute("""UPDATE app_menu_config SET scene='web' WHERE scene IS NULL;""")
    cr.execute("""UPDATE app_menu_config SET lang='zh_CN' WHERE lang IS NULL;""")
    cr.execute("""
        UPDATE app_menu_config a
        SET company_id = sub.id
        FROM (SELECT id FROM res_company ORDER BY id ASC LIMIT 1) AS sub
        WHERE a.company_id IS NULL;
    """)

    # 外键（若不存在）
    cr.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'app_menu_config_company_id_fkey'
      ) THEN
        ALTER TABLE app_menu_config
        ADD CONSTRAINT app_menu_config_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE SET NULL;
      END IF;
    END $$;
    """)

    # 删除旧唯一约束（若存在）
    cr.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'uniq_target_model'
      ) THEN
        ALTER TABLE app_menu_config DROP CONSTRAINT uniq_target_model;
      END IF;
    END $$;
    """)
