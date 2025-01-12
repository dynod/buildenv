import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union

from jinja2 import Environment

from .._renderers.factory import Keywords, RendererFactory
from .._utils import LOGGER_NAME, contribute_path
from ..completion import CompletionCommand
from ..extension import BuildEnvExtension, BuildEnvRenderer

# Templates folder
_TEMPLATES_ROOT_FOLDER = Path(__file__).parent / "templates"


# Build environment shell abstraction class
class EnvShell(ABC):
    def __init__(self, venv_bin: Path, fake_pip: bool, backend_name: str, extensions: dict[str, BuildEnvExtension], completions: list[CompletionCommand]):
        self._venv_bin = venv_bin
        self._fake_pip = fake_pip
        self._backend_name = backend_name
        self._extensions = extensions
        self._completions = completions
        self._logger = logging.getLogger(LOGGER_NAME)

    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Shell implementation name
        """
        pass

    @property
    @abstractmethod
    def script(self) -> str:  # pragma: no cover
        """
        Shell launch script
        """
        pass

    @property
    def env_level(self) -> int:
        """
        Get current buildenv level

        :return: current buildenv level (0 if not in a buildenv)
        """
        return int(os.getenv("BUILDENV_LEVEL", "0"))

    def get_env(self, tmp_dir: Path) -> dict[str, str]:
        """
        Shell environment map, for both interractive and command modes

        :param tmp_dir: temporary directory where activation scripts will be stored
        :return: environment map
        """

        # Inherit from current env
        env = dict(os.environ)

        # Check buildenv level
        previous_level = self.env_level
        if previous_level > 0:
            self._logger.warning("Spawning a new buildenv!")
            self._logger.warning("Even if this is not forbidden, you may prefer exiting the current shell before launching a new one.")

        # Update environment
        env["BUILDENV_LEVEL"] = str(previous_level + 1)  # Increase buildenv level
        env["VIRTUAL_ENV_SCRIPTS"] = str(tmp_dir)  # Path to temporary activation scripts
        env["VIRTUAL_ENV_PROMPT"] = f"(buildenv{'*' * previous_level}) "  # Buildenv prompt (with * for nested levels)
        if "PYTHONHOME" in env:
            del env["PYTHONHOME"]  # Remove PYTHONHOME to avoid conflicts

        # PATH contributions
        if self._fake_pip:
            contribute_path(env, tmp_dir / "bin")  # temporary bin folder

        return env

    @abstractmethod
    def get_args_interractive(self, tmp_dir: Path) -> list[str]:  # pragma: no cover
        """
        Shell environment map, for interractive mode

        :param tmp_dir: temporary directory where activation scripts will be stored
        :return: arguments to run the shell in interractive mode
        """
        pass

    @abstractmethod
    def get_args_command(self, tmp_dir: Path) -> list[str]:  # pragma: no cover
        """
        Shell environment map, for interractive mode

        :param tmp_dir: temporary directory where activation scripts will be stored
        :return: arguments to run the shell in command mode
        """
        pass

    @abstractmethod
    def generate_activation_scripts(self, tmp_dir: Path, command: Union[str, None]):  # pragma: no cover
        """
        Generate activation scripts in the specified temporary directory

        :param tmp_dir: temporary directory where activation scripts will be stored
        :param command: command to be executed in this shell
        """
        pass

    def run(self, command: Union[str, None]) -> int:
        """
        Run this shell

        :param command: command to be executed; if None or empty, run the shell in interractive mode
        ;return: return code of the shell process (interractive or command mode)
        """

        # Prepare temporary scripts folder
        with TemporaryDirectory() as td:
            # Generate activation files in this directory
            temp_path = Path(td)
            self.generate_activation_scripts(temp_path, command)

            # Generate extensions activation scripts
            self._generate_extensions_scripts(temp_path / "activate")

            # Prepare arguments, depending if a command is specified or not
            args = self.get_args_command(temp_path) if command else self.get_args_interractive(temp_path)

            # Prepare environment
            env = self.get_env(temp_path)

            # Run shell as subprocess, and grab return code
            return subprocess.run(args, env=env, check=False).returncode

    def render(self, template: str, target: Path, executable: bool = False, keywords: Union[Keywords, None] = None):
        """
        Render template to target file

        :param template: Template file to render
        :param target: Target file to be generated
        :param executable: States if target file as to be set as executable
        :param keyword: Map of keywords provided to template
        """

        # Delegate rendering to the renderer factory
        RendererFactory.create(Path("shells") / template, self._backend_name).render(target, executable, keywords)

    # Get completion commands from extensions
    def _get_completion_commands(self) -> list[CompletionCommand]:
        # Iterate on extensions
        completion_commands = list(self._completions)
        for ext_name, extension in self._extensions.items():
            # Get extension contributed completion commands
            try:
                completion_commands += extension.get_completion_commands()
            except Exception as e:
                raise AssertionError(f"Error occurred while getting {ext_name} extension completion commands: {e}") from e
        return completion_commands

    # Generate extensions activation scripts
    def _generate_extensions_scripts(self, tmp_dir: Path):
        # Renderer adapter
        class RenderingAdapter(BuildEnvRenderer):
            def render(slf, environment: Environment, template: str, executable: bool = False, keywords: Union[Keywords, None] = None):  # type: ignore
                # Delegate rendering to the renderer factory
                template_path = Path(template)
                RendererFactory.create(template_path, self._backend_name, environment).render(
                    tmp_dir / template_path.name.replace(".jinja", ""), executable, keywords
                )

        # Iterate on extensions
        renderer = RenderingAdapter()
        for ext_name, extension in self._extensions.items():
            # Generate extension activation scripts (through renderer adapter)
            try:
                extension.generate_activation_scripts(renderer)
            except Exception as e:
                raise AssertionError(f"Error occurred while generating {ext_name} extension activation scripts: {e}") from e

    def _get_pip_stub_wording(self) -> list[str]:
        """
        Get pip stub wording, depending on the backend used

        :return: pip stub wording
        """
        return [f"pip is not available in this environment (powered by {self._backend_name})."] + (
            [
                "You may use one of the following commands, depending on what you want to do:",
                "  uv pip  -- mimics pip behavior",
                "  uv tree -- to dump current project dependencies tree",
                "  uv add  -- to add a package dependency to current project",
            ]
            if self._backend_name == "uv"
            else ["To modify installed packages, please consider updating the requirements.txt file and relaunch this buildenv instead."]
        )
