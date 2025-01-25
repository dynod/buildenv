from abc import ABC, abstractmethod
from pathlib import Path

from .._shells.factory import ShellFactory


# Backend base implementation
class EnvBackend(ABC):
    def __init__(self, venv_bin: Path):
        # Remember venv bin path
        self._venv_bin = venv_bin

        # Prepare shell
        self._shell = ShellFactory.create(self._venv_bin, not self.is_mutable() or not self.has_pip(), self.name)

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

    @abstractmethod
    def has_pip(self) -> bool:  # pragma: no cover
        """
        State if this backend includes pip tool

        :return: True if environment includes pip
        """
        pass

    def shell(self) -> int:
        """
        Launch an interractive shell from the backend

        :return: shell exit code
        """

        # Run interractive shell
        return self._shell.run(None)

    def run(self, command: str) -> int:
        """
        Run command in the backend shell

        :param command: command to be executed
        :return: command exit code
        """

        # Run command in shell
        return self._shell.run(command)
