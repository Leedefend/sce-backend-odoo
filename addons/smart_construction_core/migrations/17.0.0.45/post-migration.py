# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        UPDATE project_project AS project
           SET project_category_id = category.id,
               write_date = NOW()
          FROM sc_dictionary AS category
         WHERE project.project_category_id IS NULL
           AND category.type = 'project_category'
           AND category.active IS TRUE
           AND category.code = CASE project.operation_strategy
                WHEN 'direct' THEN 'PROJECT_CATEGORY_DIRECT'
                WHEN 'joint' THEN 'PROJECT_CATEGORY_JOINT'
                ELSE NULL
           END
        """
    )
