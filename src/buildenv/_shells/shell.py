import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory

from jinja2 import Template

# Templates folder
_TEMPLATES_ROOT_FOLDER = Path(__file__).parent / "templates"


# Build environment shell abstraction class
class EnvShell(ABC):
    def __init__(self, venv_root: Path):
        self._venv_root = venv_root
        self._logger = logging.getLogger(type(self).__name__)

    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Shell implementation name
        """
        pass

    def get_env(self, tmp_dir: Path) -> dict[str, str]:
        """
        Shell environment map, for both interractive and command modes

        :param tmp_dir: temporary directory where activation scripts will be stored
        :return: environment map
        """

        # Inherit from current env
        env = dict(os.environ)

        # Update environment
        env["VIRTUAL_ENV_SCRIPTS"] = str(tmp_dir)  # Path to activation scripts
        env["VIRTUAL_ENV"] = str(self._venv_root)  # Path to virtual env root
        env["VIRTUAL_ENV_PROMPT"] = "buildenv"  # Buildenv prompt

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
    def get_args_command(self, tmp_dir: Path, command: str) -> list[str]:  # pragma: no cover
        """
        Shell environment map, for interractive mode

        :param tmp_dir: temporary directory where activation scripts will be stored
        :param command: command to be executed in this shell
        :return: arguments to run the shell in command mode
        """
        pass

    @abstractmethod
    def generate_activation_scripts(self, tmp_dir: Path):  # pragma: no cover
        """
        Generate activation scripts in the specified temporary directory

        :param tmp_dir: temporary directory where activation scripts will be stored
        """
        pass

    def run(self, command: str) -> int:
        """
        Run this shell

        :param command: command to be executed; if None or empty, run the shell in interractive mode
        ;return: return code of the shell process (interractive or command mode)
        """

        # Prepare temporary scripts folder
        with TemporaryDirectory() as td:
            # Generate activation files in this directory
            temp_path = Path(td)
            self.generate_activation_scripts(temp_path)

            # Prepare arguments, depending if a command is specified or not
            args = self.get_args_command(temp_path, command) if command else self.get_args_interractive(temp_path)

            # Prepare environment
            env = self.get_env(temp_path)

            # Run shell as subprocess, and grab return code
            return subprocess.run(args, env=env, check=False).returncode

    @property
    @abstractmethod
    def header(self) -> str:  # pragma: no cover
        """
        Header string for this shell
        """
        pass

    @property
    @abstractmethod
    def new_line(self) -> str:  # pragma: no cover
        """
        New line string for this shell
        """
        pass

    @property
    @abstractmethod
    def comment_prefix(self) -> str:  # pragma: no cover
        """
        Comment prefix string for this shell
        """
        pass

    def render(self, template: Path | str, target: Path, executable: bool = False, keywords: dict[str, str] = None):
        """
        Render template template to target file

        :param template: Path to template file
        :param target: Target file to be generated
        :param executable: States if target file as to be set as executable
        :param keyword: Map of keywords provided to template
        """

        # Build keywords map
        all_keywords = {}
        if keywords is not None:
            all_keywords.update(keywords)

        # Build fragments list
        fragments = [
            template if (isinstance(template, Path) and template.is_absolute()) else (_TEMPLATES_ROOT_FOLDER / template),
        ]

        # Known type: handle header and comments
        all_keywords.update(
            {
                "header": self.header,
                "comment": self.comment_prefix,
            }
        )

        # Add warning header
        fragments.insert(0, _TEMPLATES_ROOT_FOLDER / "warning.jinja")

        # Iterate on fragments
        generated_content = ""
        for fragment in fragments:
            # Load template
            with fragment.open() as f:
                t = Template(f.read())
                generated_content += t.render(all_keywords)
                generated_content += "\n\n"

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Generate target
        with target.open("w", newline=self.new_line) as f:
            f.write(generated_content)
