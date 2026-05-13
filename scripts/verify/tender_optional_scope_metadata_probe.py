# -*- coding: utf-8 -*-
"""Rollback-only Odoo shell probe for tender optional scope metadata."""


def _env():
    return globals()["env"]


def _assert_field(model, name, field_type, required=False):
    field = model._fields.get(name)
    if not field:
        raise AssertionError("Missing field %s.%s" % (model._name, name))
    if field.type != field_type:
        raise AssertionError("%s.%s type expected %s got %s" % (model._name, name, field_type, field.type))
    if bool(field.required) != required:
        raise AssertionError("%s.%s required expected %s got %s" % (model._name, name, required, field.required))


def main():
    env = _env()
    Tender = env["tender.bid"].sudo()
    Project = env["project.project"].sudo()

    _assert_field(Tender, "project_id", "many2one", required=True)
    _assert_field(Tender, "business_scope_key", "char")
    _assert_field(Tender, "business_direction", "selection")
    _assert_field(Tender, "carrier_type", "char")
    _assert_field(Tender, "carrier_model", "char")
    _assert_field(Tender, "carrier_res_id", "integer")

    env.cr.execute(
        """
        SELECT is_nullable
          FROM information_schema.columns
         WHERE table_name = 'tender_bid'
           AND column_name = 'project_id'
        """
    )
    project_nullable_row = env.cr.fetchone()
    if not project_nullable_row or project_nullable_row[0] != "NO":
        raise AssertionError("tender_bid.project_id must remain NOT NULL")

    expected_columns = {
        "business_scope_key",
        "business_direction",
        "carrier_type",
        "carrier_model",
        "carrier_res_id",
    }
    env.cr.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'tender_bid'
           AND column_name = ANY(%s)
        """,
        (list(expected_columns),),
    )
    actual_columns = {row[0] for row in env.cr.fetchall()}
    missing_columns = sorted(expected_columns - actual_columns)
    if missing_columns:
        raise AssertionError("tender_bid missing optional scope columns: %s" % ", ".join(missing_columns))

    view = env.ref("smart_construction_core.view_tender_bid_form")
    arch = view.arch_db or ""
    if 'name="platform_scope_metadata"' not in arch:
        raise AssertionError("tender.bid form missing platform_scope_metadata page")
    for field_name in expected_columns:
        if 'name="%s"' % field_name not in arch:
            raise AssertionError("tender.bid form missing optional scope field %s" % field_name)

    project = Project.create({"name": "Tender Optional Scope Probe"})
    bid = Tender.create({"tender_name": "Tender Optional Scope Probe", "project_id": project.id})
    assert bid.project_id == project, bid.project_id
    assert not bid.business_scope_key, bid.business_scope_key
    assert not bid.business_direction, bid.business_direction
    assert not bid.carrier_type, bid.carrier_type
    assert not bid.carrier_model, bid.carrier_model
    assert bid.carrier_res_id == 0, bid.carrier_res_id

    bid.write(
        {
            "business_scope_key": "income:tender-probe",
            "business_direction": "income",
            "carrier_type": "project",
            "carrier_model": "project.project",
            "carrier_res_id": project.id,
        }
    )
    assert bid.project_id == project, bid.project_id
    assert bid.business_scope_key == "income:tender-probe", bid.business_scope_key
    assert bid.business_direction == "income", bid.business_direction
    assert bid.carrier_type == "project", bid.carrier_type
    assert bid.carrier_model == "project.project", bid.carrier_model
    assert bid.carrier_res_id == project.id, bid.carrier_res_id

    env.cr.rollback()
    print(
        "TENDER_OPTIONAL_SCOPE_METADATA_PROBE=PASS model=tender.bid project_required=1 optional_scope_fields=5"
    )


main()
