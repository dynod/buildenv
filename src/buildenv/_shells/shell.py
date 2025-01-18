import os
import subprocess
from abc import ABC, abstractmethod
from tempfile import TemporaryDirectory


# Build environment shell abstraction class
class EnvShell(ABC):
    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Shell implementation name
        """
        pass

    @property
    def env(self) -> dict[str, str]:  # pragma: no cover
        """
        Shell environment map, for both interractive and command modes
        """
        return dict(os.environ)

    @abstractmethod
    def get_args_interractive(self) -> list[str]:  # pragma: no cover
        """
        Shell environment map, for interractive mode
        """
        pass

    @abstractmethod
    def get_args_command(self, command: str) -> list[str]:  # pragma: no cover
        """
        Shell environment map, for interractive mode

        :param command: command to be executed in this shell
        """
        pass

    def run(self, command: str) -> int:
        """
        Run this shell

        :param command: command to be executed; if None or empty, run the shell in interractive mode
        """

        # Prepare environment
        env = self.env

        # Prepare temporary scripts folder
        with TemporaryDirectory() as td:
            # Generate activation files in this directory

            # Prepare arguments, depending if a command is specified or not
            args = self.get_args_command(command) if command else self.get_args_interractive()

            # Run shell as subprocess, and grab return code
            return subprocess.run(args, env=env, check=False).returncode
