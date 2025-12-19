-- tools/sql/noiseon.sql
-- 目标：恢复最近一次 noiseoff 关闭的 cron（按审计表回滚）

WITH last_batch AS (
  SELECT audited_at
  FROM sc_noise_audit_cron
  WHERE dbname = current_database()
  ORDER BY audited_at DESC
  LIMIT 1
),
targets AS (
  SELECT a.cron_id, a.old_active
  FROM sc_noise_audit_cron a
  JOIN last_batch b ON a.audited_at = b.audited_at
)
UPDATE ir_cron c
SET active = t.old_active
FROM targets t
WHERE c.id = t.cron_id;

-- 输出恢复结果（最近一批）
SELECT c.id, c.cron_name, c.active
FROM ir_cron c
WHERE c.id IN (
    SELECT cron_id FROM sc_noise_audit_cron
    WHERE audited_at = (SELECT audited_at FROM sc_noise_audit_cron ORDER BY audited_at DESC LIMIT 1)
)
ORDER BY c.id;
