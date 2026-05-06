# smart_core/core/command_registry.py
from .source_authority import build_source_authority_contract

COMMANDS = {}

SOURCE_KIND = "legacy_command_registry_projection"
SOURCE_AUTHORITIES = ("smart_core.commands",)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        legacy_compatibility=True,
    )

try:
    from ..commands.login import LoginCommand
    from ..commands.load_view import LoadViewCommand
    from ..commands.load_records import LoadRecordsCommand
    from ..commands.load_metadata import LoadMetadataCommand

    COMMANDS.update({
        "login": LoginCommand,
        "load_model_view": LoadViewCommand,
        "load_model_records": LoadRecordsCommand,
        "load_model_metadata": LoadMetadataCommand,
    })
except Exception:
    # commands 包可选，缺失时保持空注册表
    COMMANDS = {}

def get_command_class(intent_name):
    return COMMANDS.get(intent_name)
