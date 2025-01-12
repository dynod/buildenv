from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from jinja2 import Environment

from .completion import CompletionCommand


@dataclass
class BuildEnvInfo:
    """
    BuildEnv information holding object, used to give some context to extensions.
    """

    venv_bin: Path
    """Path to the virtual environment binary directory (i.e. the one with all installed scripts and executables)"""

    project_root: Union[Path, None]
    """Path to the project root directory, if any (None otherwise)"""


class BuildEnvRenderer(ABC):
    """
    Rendering interface for buildenv extensions
    """

    @abstractmethod
    def render(self, environment: Environment, template: str, executable: bool = False, keywords: Union[dict[str, str], None] = None):  # pragma: no cover
        """
        Render extension activation script from template

        :param environment: Jinja2 environment to use for rendering
        :param template: Template file to render (relative to provided environment)
        :param executable: States if target file as to be set as executable
        :param keyword: Map of keywords provided to template
        """
        pass


class BuildEnvExtension(ABC):
    """
    Base class for **buildenv** extensions, to be contributed through "buildenv_init" entry point

    :param info: BuildEnvInfo object holding information about the build environment
    """

    def __init__(self, info: BuildEnvInfo):
        self.info = info
        pass

    @abstractmethod
    def init(self, force: bool):  # pragma: no cover
        """
        Method called by buildenv backend when initializing environment.

        The extension is supposed to perform some build logic initialization (once for all). This method will always be called by buildenv;
        the extension must decide by itself if it needs to perform some action or not.

        The self.info attribute can be used to access to buildenv information.

        :param force: Tells the extension if the **--force** argument was used on the **buildenv init** command line.
        """
        pass

    def get_completion_commands(self) -> list[CompletionCommand]:
        """
        Method called by buildenv backend to get the list of commands to be completed.

        The extension can use this method to provide its own completion commands.

        :return: List of commands to be completed
        """

        # Default implementation: no command to be completed
        return []

    def generate_activation_scripts(self, renderer: BuildEnvRenderer):  # NOQA: B027
        """
        Method called by buildenv backend when generating activation scripts.

        The extension can use this method to generate its own activation scripts in the provided temporary directory.
        The default implementation does nothing.

        :param renderer: Rendering interface to use for generating activation scripts
        """

        # Default implementation: do nothing
        pass
