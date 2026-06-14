# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        WITH ids AS (
            SELECT
                id,
                name,
                regexp_replace(url, '^legacy-file-id://', '') AS legacy_key
              FROM ir_attachment
             WHERE url LIKE 'legacy-file-id://%'
        ),
        picked AS (
            SELECT DISTINCT ON (ids.id)
                ids.id,
                i.file_name,
                COALESCE(NULLIF(i.preview_path, ''), NULLIF(i.file_path, '')) AS path
              FROM ids
              JOIN sc_legacy_file_index i
                ON i.active
               AND (
                    i.legacy_file_id = ids.legacy_key
                 OR i.legacy_file_key = ids.legacy_key
                 OR i.bill_id = ids.legacy_key
               )
             WHERE COALESCE(NULLIF(i.preview_path, ''), NULLIF(i.file_path, '')) IS NOT NULL
             ORDER BY ids.id, i.upload_time DESC NULLS LAST, i.id DESC
        )
        UPDATE ir_attachment a
           SET url = 'legacy-file://' || ltrim(p.path, '/'),
               name = CASE
                    WHEN a.name IS NULL OR a.name = '' OR a.name LIKE 'legacy attachment %'
                    THEN COALESCE(NULLIF(p.file_name, ''), a.name)
                    ELSE a.name
               END,
               write_date = NOW()
          FROM picked p
         WHERE a.id = p.id
        """
    )
