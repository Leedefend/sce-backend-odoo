def migrate(cr, version):
    cr.execute(
        "INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) "
        "VALUES ('sc.migration_failure_fixture.marker', 'must_rollback', 1, 1, now(), now()) "
        "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, write_date=now()"
    )
    raise RuntimeError("intentional migration failure for transaction rollback verification")
