# smart_core/core/command_registry.py
from ..commands.login import LoginCommand
from ..commands.load_view import LoadViewCommand
from ..commands.load_records import LoadRecordsCommand
from ..commands.load_metadata import LoadMetadataCommand


COMMANDS = {
    "login": LoginCommand,
    "load_model_view": LoadViewCommand,
    "load_model_records": LoadRecordsCommand,
    "load_model_metadata": LoadMetadataCommand,
    
}

def get_command_class(intent_name):
    return COMMANDS.get(intent_name)
