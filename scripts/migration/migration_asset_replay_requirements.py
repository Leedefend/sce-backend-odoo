"""Shared replay artifact requirements for migration asset packaging."""

from __future__ import annotations


EXTRA_REQUIRED_REPLAY_ARTIFACTS = {
    # Variable/function-based one-click dependencies that are required for
    # packaged replay but are not discoverable by the legacy direct regex.
    "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv",
    "artifacts/migration/fresh_db_replay_manifest_v1.json",
    "artifacts/migration/project_member_neutral_34_write_result_v1.json",
}

BASELINE_EXCLUDED_REQUIRED_ARTIFACTS = {
    # Default-off privacy lanes. These are intentionally not shipped in the
    # baseline package because they may contain sensitive personal data.
    "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_personnel_movement_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv",
    # Default-off recovery lanes backed by old downstream snapshots.
    "artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv",
    "artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv",
    "artifacts/migration/history_project_lifecycle_continuity_payload_v1.csv",
    # Deprecated recovery lanes skipped when authoritative XML assets exist.
    "artifacts/migration/contract_12_row_write_authorization_packet_v1.json",
    "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv",
    "artifacts/migration/contract_partner_source_57_design_rows_v1.csv",
    "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv",
    "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv",
    "artifacts/migration/history_contract_direction_defer_recovery_payload_v1.csv",
    "artifacts/migration/history_contract_partner_recovery_payload_v1.csv",
    "artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv",
    "artifacts/migration/history_partner_master_direction_defer_replay_payload_v1.csv",
    "artifacts/migration/history_partner_master_targeted_replay_payload_v1.csv",
    "artifacts/migration/history_receipt_parent_recovery_adapter_result_v1.json",
    "artifacts/migration/history_receipt_parent_recovery_payload_v1.csv",
    "artifacts/migration/history_receipt_partner_targeted_replay_payload_v1.csv",
}
