from pathlib import Path

from .shell import EnvShell


# Windows cmd shell implementation
class CmdShell(EnvShell):
    def __init__(self, venv_bin: Path, fake_pip: bool, backend_name: str):
        super().__init__(venv_bin, fake_pip, backend_name)
        self._shell_path = "cmd"

    @property
    def name(self) -> str:
        return "cmd"

    def get_args_interractive(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path]

    def get_args_command(self, tmp_dir: Path, command: str) -> list[str]:
        return [self._shell_path, "/c", command]

    def generate_activation_scripts(self, tmp_dir: Path):
        pass

    @property
    def header(self) -> str:
        return "@ECHO OFF\n"

    @property
    def new_line(self) -> str:
        return "\r\n"

    @property
    def comment_prefix(self) -> str:
        return ":: "
