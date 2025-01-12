import os
from pathlib import Path
from typing import Union

from .backend import EnvBackendWithRequirements, MutableEnvBackend


# Legacy pip-style backend
class LegacyPipBackend(EnvBackendWithRequirements, MutableEnvBackend):
    NAME = "pip"

    @property
    def name(self):
        return LegacyPipBackend.NAME

    @property
    def command(self) -> str:
        return "python"

    @property
    def install_url(self):
        return "https://www.python.org/"

    @property
    def venv_name(self) -> str:
        return "venv"

    def has_pip(self):
        # Pip has pip, obviously
        return True

    @property
    def _pip_args(self) -> list[str]:
        return [arg for arg in os.getenv("BUILDENV_PIP_ARGS", "").split(" ") if arg]

    def subprocess(
        self, args: list[str], check: bool = True, cwd: Union[Path, None] = None, env: Union[dict[str, str], None] = None, verbose: Union[bool, None] = None
    ):
        # Systematically add pip args to pip subprocess
        return super().subprocess([str(self._venv_bin / self.command), "-m", "pip"] + args + self._pip_args, check, cwd, env, verbose)

    def _delegate_add_packages(self, packages: list[str]):
        # Delegate to pip
        self.subprocess(["install", *packages], check=True)

    def _delegate_upgrade(self, full: bool = True, only_deps: bool = False) -> int:
        # Delegate to pip
        return self.subprocess(["install", "-r", "requirements.txt"] + (["--upgrade", "--upgrade-strategy=eager"] if full else []), check=False).returncode
