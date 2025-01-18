import logging
import os

from .._internal.utils import is_windows
from .bash import BashShell
from .cmd import CmdShell
from .shell import EnvShell

_LOGGER = logging.getLogger(__name__)


# Shell detection factory
class ShellFactory:
    @staticmethod
    def create() -> EnvShell:
        """
        Detect shell implementation from environment and OS

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
        return shell_class()
