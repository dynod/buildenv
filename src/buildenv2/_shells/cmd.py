from pathlib import Path

from ..completion import CompletionCommand
from ..extension import BuildEnvExtension
from .shell import EnvShell


# Windows cmd shell implementation
class CmdShell(EnvShell):
    def __init__(self, venv_bin: Path, fake_pip: bool, backend_name: str, extensions: dict[str, BuildEnvExtension], completions: list[CompletionCommand]):
        super().__init__(venv_bin, fake_pip, backend_name, extensions, completions)
        self._shell_path = "cmd"

    @property
    def name(self) -> str:
        return "cmd"

    @property
    def script(self) -> str:
        return "buildenv.cmd"

    def get_args_interractive(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "/k", str(tmp_dir / "shell.cmd")]

    def get_args_command(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "/c", str(tmp_dir / "command.cmd")]

    def generate_activation_scripts(self, tmp_dir: Path, command: str | None):
        # Root files
        self.render("cmd/activate.cmd.jinja", tmp_dir / "activate.cmd")  # Main activation file
        if command:
            self.render("cmd/command.cmd.jinja", tmp_dir / "command.cmd", keywords={"command": command})  # Command execution file
        else:
            self.render("cmd/shell.cmd.jinja", tmp_dir / "shell.cmd")  # Shell activation file

        # Activation scripts
        self.render("cmd/activate_readme.cmd.jinja", tmp_dir / "activate" / "readme.cmd")

        # Generate fake pip if required
        if self._fake_pip:
            self.render("cmd/pip.cmd.jinja", tmp_dir / "bin" / "pip.cmd", executable=True, keywords={"pip_help": self._get_pip_stub_wording()})
