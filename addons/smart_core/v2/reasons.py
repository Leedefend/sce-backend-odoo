REASON_INTENT_NOT_FOUND = "INTENT_NOT_FOUND"
REASON_PERMISSION_DENIED = "PERMISSION_DENIED"
REASON_VALIDATION_FAILED = "VALIDATION_FAILED"
REASON_DISPATCH_FAILED = "DISPATCH_FAILED"


def build_error(reason_code: str, message: str) -> dict:
    return {
        "code": str(reason_code or "UNKNOWN_ERROR"),
        "message": str(message or ""),
        "reason_code": str(reason_code or "UNKNOWN_ERROR"),
    }
