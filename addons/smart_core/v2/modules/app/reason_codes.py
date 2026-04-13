APP_REASON_OK = ""
APP_REASON_APP_KEY_MISSING = "APP_KEY_MISSING"
APP_REASON_WORKSPACE_WORK_PARTIAL = "WORKSPACE_WORK_PARTIAL"

APP_REASON_CODE_SET = {
    APP_REASON_OK,
    APP_REASON_APP_KEY_MISSING,
    APP_REASON_WORKSPACE_WORK_PARTIAL,
}


def normalize_reason_code(value: str) -> str:
    reason_code = str(value or "")
    if reason_code in APP_REASON_CODE_SET:
        return reason_code
    return APP_REASON_APP_KEY_MISSING
