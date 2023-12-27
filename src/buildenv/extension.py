from abc import ABC, abstractmethod


class BuildEnvExtension(ABC):
    """
    Base class for **buildenv** extensions, to be contributed through "buildenv_init" entry point

    :param manager: BuildEnvManager instance
    :type manager: BuildEnvManager
    """

    def __init__(self, manager):
        self.manager = manager
        pass

    @abstractmethod
    def init(self, force: bool):  # pragma: no cover
        """
        Method called by manager when delegating its own "init" method to extensions.

        Extensions are supposed:

        * to perform some build logic initialization (once for all)
        * to contribute to activation scripts (loaded each time the buildenv is activated)

        The self.manager attribute can be used to access to the manager instance.

        :param force: Tells the extension if the **--force** argument was used on the **buildenv init** command line.
        """
        pass

    @abstractmethod
    def get_version(self) -> str:  # pragma: no cover
        """
        Method called by manager to know extension version.

        This version is used by manager to be compared to version used last time the init was done.
        If it differs, previous activation scripts are deleted, and init method is called again.

        :return: Extension version string
        """
        pass
