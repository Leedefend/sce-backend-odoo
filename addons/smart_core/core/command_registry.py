# smart_core/core/command_registry.py
COMMANDS = {}

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
