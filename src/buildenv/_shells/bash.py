import shutil
from pathlib import Path

from .._utils import contribute_path, is_windows, to_linux_path
from ..completion import CompletionCommand
from ..extension import BuildEnvExtension
from .shell import EnvShell


# Bash shell implementation
class BashShell(EnvShell):
    NAME = "bash"

    @classmethod
    def check_supported(cls):
        # Check if bash shell is supported in the current environment by trying to detect its path
        cls._detect_shell_path()

    @classmethod
    def _detect_shell_path(cls) -> str:
        # Detect shell path
        if is_windows():  # pragma: no cover -- for local tests on Linux
            git_path = shutil.which("git")
            assert git_path is not None, "Git executable not found when trying to detect bash path"
            parent_path = Path(git_path).parent.parent
            if parent_path.name == "mingw64":
                # One more level up
                parent_path = parent_path.parent
            bash_path = parent_path / "usr" / "bin" / "bash.exe"
        else:  # pragma: no cover -- for local tests on Windows
            bash_path = shutil.which("bash")
            assert bash_path is not None, "Bash shell not found on path"
            bash_path = Path(bash_path)
        assert bash_path.is_file(), f"Invalid bash path: {bash_path}"
        return str(bash_path)

    def __init__(self, venv_bin: Path, fake_pip: bool, backend_name: str, extensions: dict[str, BuildEnvExtension], completions: list[CompletionCommand]):
        super().__init__(venv_bin, fake_pip, backend_name, extensions, completions)

        # Detect shell path
        self._shell_path: str = self._detect_shell_path()

    @property
    def name(self) -> str:
        return BashShell.NAME

    @property
    def script(self) -> str:
        return "./buildenv.sh"

    def get_args_interractive(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "--rcfile", to_linux_path(tmp_dir / "shell.sh")]

    def get_args_command(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "-c", to_linux_path(tmp_dir / "command.sh")]

    def generate_activation_scripts(self, tmp_dir: Path, command: str | None):
        # Root files
        self.render("bash/activate.sh.jinja", tmp_dir / "activate.sh")  # Main activation file
        if command:
            self.render("bash/command.sh.jinja", tmp_dir / "command.sh", keywords={"command": command}, executable=True)  # Command execution file
        else:
            self.render("bash/shell.sh.jinja", tmp_dir / "shell.sh")  # Shell activation file

        # Activation scripts
        self.render("bash/activate_readme.sh.jinja", tmp_dir / "activate" / "readme.sh")
        self.render(
            "bash/completion.sh.jinja",
            tmp_dir / "activate" / "completion.sh",
            keywords={"commands": [c.get_command() for c in self._get_completion_commands()], "has_pip": not self._fake_pip},
        )

        # Generate fake pip if required
        if self._fake_pip:
            self.render("bash/pip.sh.jinja", tmp_dir / "bin" / "pip", executable=True, keywords={"pip_help": self._get_pip_stub_wording()})

    def get_env(self, tmp_dir: Path) -> dict[str, str]:
        # Super call
        env = super().get_env(tmp_dir)

        if is_windows():  # pragma: no cover -- for local tests on Linux
            # On Windows, contribute some extra paths that may not be present when spawned from non git bash shell (e.g. cmd or powershell)
            root_mingw = Path(self._shell_path).parent.parent.parent
            contribute_path(env, Path(env["USERPROFILE"]) / "bin")
            contribute_path(env, root_mingw / "usr" / "bin")
            contribute_path(env, root_mingw / "mingw64" / "bin")

            # Also add some env var
            env["MSYSTEM"] = "MINGW64"
        return env
