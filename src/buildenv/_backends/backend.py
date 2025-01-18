import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


# Backend base implementation
class EnvBackend(ABC):
    def __init__(self, venv_root: Path):
        self._venv_root = venv_root

    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Environment backend implementation name
        """
        pass

    @abstractmethod
    def is_mutable(self) -> bool:  # pragma: no cover
        """
        State if this backend supports installed packages update once created

        :return: True if environment is mutable
        """
        pass

    def shell(self):
        """
        Launch an interractive shell from the backend
        """

        # Get current shell
        shell = os.environ.get("SHELL", None)
        assert shell is not None, "SHELL env var is not defined"

        # Prepare updated environment
        shell_env = dict(os.environ)
        shell_env["VIRTUAL_ENV_PROMPT"] = "buildenv"  # Buildenv prompt
        shell_env["VIRTUAL_ENV"] = str(self._venv_root)  # Venv root folder
        shell_env["PS1"] = f"(buildenv) {shell_env['PS1']}"  # Updated prompt

        # Launch shell process
        subprocess.run([shell], env=shell_env, check=False)
