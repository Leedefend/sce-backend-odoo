-- tools/sql/noiseoff.sql
-- 目标：开发/演示环境降噪（cron/server action），可审计、可回滚（配套 noiseon.sql）

-- 0) 审计表（记录被改动的 cron）
CREATE TABLE IF NOT EXISTS sc_noise_audit_cron (
  audit_id      bigserial PRIMARY KEY,
  audited_at    timestamp without time zone NOT NULL DEFAULT now(),
  dbname        text NOT NULL DEFAULT current_database(),
  cron_id       int NOT NULL,
  cron_name     text,
  old_active    boolean,
  new_active    boolean
);

-- 1) 找出高噪音 cron（按名称匹配）
WITH target AS (
  SELECT id, cron_name, active
  FROM ir_cron
  WHERE (
       cron_name ILIKE 'Mail:%'
    OR cron_name ILIKE 'Notification:%'
    OR cron_name ILIKE 'Discuss:%'
    OR cron_name ILIKE 'SMS:%'
    OR cron_name ILIKE 'Snailmail:%'
    OR cron_name ILIKE 'Partner Autocomplete:%'
    OR cron_name ILIKE 'Send invoices automatically%'
    OR cron_name ILIKE 'Project:%rating%'
    OR cron_name ILIKE 'Procurement:%'
    OR cron_name ILIKE 'Purchase reminder%'
    OR cron_name ILIKE '%Tier%'
    OR cron_name ILIKE '%Unregistered Users%'
  )
)
INSERT INTO sc_noise_audit_cron (cron_id, cron_name, old_active, new_active)
SELECT id, cron_name, active, false
FROM target
WHERE active IS DISTINCT FROM false;

-- 2) 关闭这些 cron（仅作用于本次批次）
UPDATE ir_cron
SET active = false
WHERE id IN (
  SELECT cron_id FROM sc_noise_audit_cron
  WHERE audited_at >= now() - interval '5 minutes'
);

-- 3) 将可能报错的 server action（未注册用户提醒）置为 pass
UPDATE ir_act_server
SET code = 'pass'
WHERE state = 'code'
  AND code ILIKE '%send_unregistered_user_reminder%';

-- 4) 输出：本次关闭的 cron 清单（便于审计）
SELECT cron_id AS id, cron_name, old_active, new_active, audited_at
FROM sc_noise_audit_cron
WHERE audited_at >= now() - interval '5 minutes'
ORDER BY cron_id;
