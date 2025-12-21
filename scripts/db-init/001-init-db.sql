-- Create database sc_odoo if it does not exist.
-- This runs only on first init of the data volume.

SELECT 'CREATE DATABASE sc_odoo'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sc_odoo')\gexec
