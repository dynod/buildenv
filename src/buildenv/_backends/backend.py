from abc import ABC, abstractmethod


# Backend interface
class EnvBackend(ABC):
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
