# Diagnostic Scripts

These scripts support menu root and DB resolution diagnostics. They are intended for DEV usage.

## Scripts

- `scripts/diag/check-root-menu.py`
Usage: `python scripts/diag/check-root-menu.py --db <db_name> [--xmlid module.menu_xmlid]`

- `scripts/diag/nav_root_db_check.sh`
Usage: `make diag.nav_root DB_NAME=<db_name> ROOT_XMLID=<module.menu_xmlid> LOGIN=<login> [LANG_OVERRIDE=en_US]`

- `scripts/diag/test-default-menu.py`
Usage: `python scripts/diag/test-default-menu.py`

- `scripts/diag/test-frontend-changes.sh`
Usage: `scripts/diag/test-frontend-changes.sh`

- `scripts/diag/test-menu-issue.sh`
Usage: `scripts/diag/test-menu-issue.sh`

## Notes

- These scripts may assume a local dev environment and specific container names.
- Adjust DB name and endpoints as needed for your environment.
