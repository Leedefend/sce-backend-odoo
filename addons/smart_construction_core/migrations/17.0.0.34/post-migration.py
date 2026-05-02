# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Mark analysis report route replacement in upgraded databases."""
    cr.execute(
        """
        INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
        VALUES ('sc.professionalization.v17_0_0_34.done', '1', 1, NOW(), 1, NOW())
        ON CONFLICT (key) DO UPDATE
           SET value = EXCLUDED.value,
               write_uid = EXCLUDED.write_uid,
               write_date = EXCLUDED.write_date
        """
    )
