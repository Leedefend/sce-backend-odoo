\set ON_ERROR_STOP on

-- Runs only inside disposable restored databases. It marks deterministic,
-- relationship-bearing history records as demo-owned to reproduce the unsafe
-- ownership shape without writing the daily-development source database.
CREATE TEMP TABLE migration_safety_users AS
SELECT id
FROM (
    (SELECT user_id AS id FROM project_project WHERE user_id > 2 ORDER BY user_id LIMIT 4)
    UNION
    (SELECT manager_id AS id FROM project_project WHERE manager_id > 2 ORDER BY manager_id LIMIT 4)
    UNION
    (SELECT u.id FROM res_users u JOIN mail_followers f ON f.partner_id = u.partner_id
      WHERE u.id > 2 ORDER BY u.id LIMIT 4)
    UNION
    (SELECT approved_by AS id FROM project_material_plan WHERE approved_by > 2 ORDER BY approved_by LIMIT 4)
    UNION
    (SELECT approver_id AS id FROM sc_plan_report WHERE approver_id > 2 ORDER BY approver_id LIMIT 4)
    UNION
    (SELECT approved_by AS id FROM sc_plan_version WHERE approved_by > 2 ORDER BY approved_by LIMIT 4)
    UNION
    (SELECT approved_by_user_id AS id FROM sc_release_action WHERE approved_by_user_id > 2 ORDER BY approved_by_user_id LIMIT 4)
) candidates
WHERE id IS NOT NULL
ORDER BY id
LIMIT 24;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM migration_safety_users) THEN
        RAISE EXCEPTION 'daily-development snapshot has no relationship-bearing user fixture candidates';
    END IF;
END $$;

INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
SELECT 'smart_construction_demo', 'migration_safety_user_' || u.id, 'res.users', u.id, TRUE
FROM migration_safety_users u
ON CONFLICT (module, name) DO UPDATE
SET model = EXCLUDED.model, res_id = EXCLUDED.res_id, noupdate = TRUE;

INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
SELECT 'smart_construction_demo', 'migration_safety_partner_' || p.id, 'res.partner', p.id, TRUE
FROM res_partner p
JOIN res_users u ON u.partner_id = p.id
JOIN migration_safety_users sample ON sample.id = u.id
ON CONFLICT (module, name) DO UPDATE
SET model = EXCLUDED.model, res_id = EXCLUDED.res_id, noupdate = TRUE;

INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
SELECT 'smart_construction_demo', 'migration_safety_project_' || p.id, 'project.project', p.id, TRUE
FROM project_project p
WHERE p.user_id IN (SELECT id FROM migration_safety_users)
   OR p.manager_id IN (SELECT id FROM migration_safety_users)
ON CONFLICT (module, name) DO UPDATE
SET model = EXCLUDED.model, res_id = EXCLUDED.res_id, noupdate = TRUE;

INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
SELECT DISTINCT 'smart_construction_demo', 'migration_safety_company_' || c.id, 'res.company', c.id, TRUE
FROM res_company c
JOIN res_company_users_rel rel ON rel.cid = c.id
JOIN migration_safety_users sample ON sample.id = rel.user_id
ON CONFLICT (module, name) DO UPDATE
SET model = EXCLUDED.model, res_id = EXCLUDED.res_id, noupdate = TRUE;

-- Execute both safety migrations in the disposable clone.
UPDATE ir_module_module
SET latest_version = '17.0.0.1.0'
WHERE name = 'smart_construction_seed' AND state = 'installed';
