from pathlib import Path

from ..completion import CompletionCommand
from ..extension import BuildEnvExtension
from .bash import BashShell
from .cmd import CmdShell
from .shell import EnvShell

KNOWN_SHELLS = {shell_cls.NAME: shell_cls for shell_cls in (BashShell, CmdShell)}
"""Map of known shell implementations"""


# Shell detection factory
class ShellFactory:
    @staticmethod
    def create(
        name: str, venv_bin: Path, fake_pip: bool, backend_name: str, extensions: dict[str, BuildEnvExtension], completions: list[CompletionCommand]
    ) -> EnvShell:
        """
        Detect shell implementation from environment and OS

        :param name: shell name to use
        :param venv_bin: path to virtual env bin folder
        :param fake_pip: True if pip command shall be faked
        :param backend_name: name of the backend
        :param extensions: dict of contributed extensions
        :param completions: list of completion commands
        :return: detected shell implementation instance
        """

        # Prepare to create shell instance
        shell_class = None

        # Known/supported shell?
        assert name in KNOWN_SHELLS, f"Unknown shell: {name}"
        shell_class = KNOWN_SHELLS[name]
        shell_class.check_supported()

        # Return shell instance
        return shell_class(venv_bin, fake_pip, backend_name, extensions, completions)
