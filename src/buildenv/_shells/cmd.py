from .shell import EnvShell


# Windows cmd shell implementation
class CmdShell(EnvShell):
    def __init__(self):
        self._shell_path = "cmd"

    @property
    def name(self) -> str:
        return "cmd"

    def get_args_interractive(self) -> list[str]:
        return [self._shell_path]

    def get_args_command(self, command: str) -> list[str]:
        return [self._shell_path, "/c", command]
