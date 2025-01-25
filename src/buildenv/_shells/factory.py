import logging
import os
from pathlib import Path

from .._internal.utils import is_windows
from .bash import BashShell
from .cmd import CmdShell
from .shell import EnvShell

_LOGGER = logging.getLogger(__name__)


# Shell detection factory
class ShellFactory:
    @staticmethod
    def create(venv_bin: Path, fake_pip: bool, backend_name: str) -> EnvShell:
        """
        Detect shell implementation from environment and OS

        :param venv_bin: path to virtual env bin folder
        :param fake_pip: True if pip command shall be faked
        :param backend_name: name of the backend
        :return: detected shell implementation instance
        """

        # Prepare to create shell instance
        shell_class = None

        # SHELL env var?
        if os.getenv("SHELL"):
            # Linux-style (assuming bash) shell detected
            shell_class = BashShell

        # Running on Windows
        elif is_windows():
            shell_class = CmdShell

        # Default: well, don't know...
        else:
            raise RuntimeError("Unable to detect the running shell")

        # Return shell instance
        return shell_class(venv_bin, fake_pip, backend_name)
