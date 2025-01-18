import os

from .shell import EnvShell


# Bash shell implementation
class BashShell(EnvShell):
    def __init__(self):
        self._shell_path = os.getenv("SHELL")

    @property
    def name(self) -> str:
        return "bash"

    def get_args_interractive(self) -> list[str]:
        return [self._shell_path]

    def get_args_command(self, command: str) -> list[str]:
        return [self._shell_path, "-c", command]
