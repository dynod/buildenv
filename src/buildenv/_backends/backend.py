from abc import ABC, abstractmethod
from pathlib import Path

from .._shells.factory import ShellFactory


# Backend base implementation
class EnvBackend(ABC):
    def __init__(self, venv_root: Path):
        # Remember root
        self._venv_root = venv_root

        # Prepare shell
        self._shell = ShellFactory.create(self._venv_root)

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

    def shell(self) -> int:
        """
        Launch an interractive shell from the backend
        """

        # Run interractive shell
        return self._shell.run(None)
