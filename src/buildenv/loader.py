"""
Python module for loading script.

This module is standalone (i.e. it doesn't have any dependencies out of the raw python SDK)
and is designed to be:

- copied in project root folder
- kept in source control, so that the script is ready to run just after project clone
"""

import os
import re
import shutil
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from types import SimpleNamespace
from typing import List, Union
from venv import EnvBuilder

VENV_OK = "venvOK"
"""Valid venv tag file"""

NEWLINE_PER_TYPE = {".sh": "\n", ".cmd": "\r\n", ".bat": "\r\n"}
"""Map of newline styles per file extension"""

# Regular expression pattern for environment variable reference in config file
_ENV_VAR_PATTERN = re.compile("\\$\\{([a-zA-Z0-9_]+)\\}")


def to_linux_path(path: Path) -> str:
    """
    Turn provided path to a Linux style path.
    On Windows, this means turning drive "X:\" to "/x/" format (git-bash style path)

    :param path: Path to be converted
    :return: Converted path, in Linux style
    """
    return f"/{path.drive[0].lower()}/{path.as_posix()[3:]}" if len(path.drive) else path.as_posix()


def to_windows_path(path: Path) -> str:
    """
    Turn provided path to a Windows style path.

    :param path: Path to be converted
    :return: Converted path, in Windows style
    """
    return str(path).replace("/", "\\")


class EnvContext:
    """
    Simple context class for a build env, providing some utility properties

    :param context: Environment context object, returned by EnvBuilder
    """

    def __init__(self, context: SimpleNamespace):
        self.context = context

    @property
    def root(self) -> Path:
        """Path to environment root folder"""
        return self.context.env_dir if isinstance(self.context.env_dir, Path) else Path(self.context.env_dir)

    @property
    def bin_folder(self) -> Path:
        """Path to bin folder in environment"""
        return self.root / self.context.bin_name

    @property
    def executable(self) -> Path:
        """Path to python executable in environment"""
        return self.bin_folder / self.context.python_exe

    @property
    def activation_scripts_folder(self) -> Path:
        """Path to activation scripts folder in environment"""
        return self.bin_folder / "activate.d"


class _MyEnvBuilder(EnvBuilder):
    """Custom env builder class used to customize venv loading scripts"""

    def post_setup(self, context: SimpleNamespace):
        """Custom scripts setup"""

        # Prepare activation scripts folder
        e = EnvContext(context)
        d = e.activation_scripts_folder
        d.mkdir(parents=True, exist_ok=True)

        # Prepare activation loop, per supported script extension
        activation_loop = {
            ".sh": f"for i in {to_linux_path(d)}/*.sh; do source $i; done",
            ".bat": f"@echo off\nfor /f %%i in ('dir /b /o:n {to_windows_path(d)}\\*.bat') do (\n    call {to_windows_path(d)}\\%%i\n)",
        }

        # Iterate on supported and existing activation scripts
        for original_script in filter(lambda s: s.is_file(), [e.bin_folder / s for s in ["activate", "activate.bat"]]):
            # Move to activation folder
            dest_script = d / ("00_" + original_script.name + ("" if len(original_script.suffix) else ".sh"))
            shutil.move(original_script, dest_script)

            # Generate new root activation script, iterating on all scripts in activation folder
            with original_script.open("w", newline=NEWLINE_PER_TYPE[dest_script.suffix]) as f:
                f.write(activation_loop[dest_script.suffix] + NEWLINE_PER_TYPE[dest_script.suffix])


class BuildEnvLoader:
    """
    Wrapper to **buildenv** manager

    This wrapper mainly creates python venv (if not done yet) before delegating setup to :class:`buildenv.manager.BuildEnvManager`.
    Also provides configuration file (**buildenv.cfg**) reading facility.

    :param project_path: Path to project root directory
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path  # Path to current project
        self.config_file = self.project_path / "buildenv.cfg"  # Path to config file (in project folder)
        self.config_parser = None  # Config parser object (lazy init)
        self.is_ci = "CI" in os.environ and len(os.environ["CI"]) > 0  # Check if running in CI
        self.venv_folder = self.read_config("venvFolder", "venv")  # Venv folder name
        self.venv_path = self.project_path / self.venv_folder  # Venv path for current project
        self.requirements_file = self.read_config("requirements", "requirements.txt")  # Requirements file name
        self.prompt = self.read_config("prompt", "buildenv")  # Prompt for buildenv
        self.look_up = self.read_config("lookUp", "true").lower() not in ["false", "0", ""]  # Look up for git root folder

    def read_config(self, name: str, default: str, resolve: bool = False) -> str:
        """
        Read configuration parameter from config file (**buildenv.cfg**).

        Value is read according to the current profile: **[local]** or **[ci]** (if **CI** env var is defined and not empty).
        Note that if a parameter is not defined in **[ci]** profile, it will be defaulted to value in **[local]** profile,
        if any (otherwise provided default will be used).

        :param name: parameter name
        :param default: default value if parameter is not set
        :param resolve: resolve environment variables used in parameter value
        :return: parameter value
        """

        # Load config file if any
        if self.config_parser is None and self.config_file.is_file():
            self.config_parser = ConfigParser()
            with self.config_file.open("r") as f:
                self.config_parser.read_file(f.readlines())

        # Read config
        if self.config_parser is not None:
            local_value = self.config_parser.get("local", name, fallback=default)
            value = self.config_parser.get("ci", name, fallback=local_value) if self.is_ci else local_value

            # Resolve env vars if required
            go_on = True
            while resolve and go_on:
                # Look for pattern
                m = _ENV_VAR_PATTERN.search(value)
                go_on = m is not None
                if go_on:
                    # Check for value
                    var_name = m.group(1)
                    assert var_name in os.environ, f"Environment variable '{var_name}' not found while reading '{name}' config parameter value"

                    # Replace value
                    value = value[0 : m.start()] + os.environ[var_name] + value[m.end() :]

            return value
        else:
            return default

    def find_venv(self) -> Union[Path, None]:
        """
        Find venv folder, in current project folder, or in parent ones

        :return: venv folder path, or None if no venv found
        """

        # Look up (unless disabled by config) to find venv folder (even in parent projects)
        current_path = self.project_path
        go_on = True
        while self.look_up and go_on:
            # Ask git
            cp = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, cwd=current_path, check=False)
            if cp.returncode == 0:
                # Git root folder found: check for venv
                candidate_path = Path(cp.stdout.decode().splitlines()[0].strip())
                candidate_loader = BuildEnvLoader(candidate_path)
                if (candidate_loader.venv_path / VENV_OK).is_file():
                    # Venv found!
                    return candidate_loader.venv_path

                # Otherwise, try parent folder
                if len(candidate_path.parts) > 1:
                    current_path = candidate_path.parent
                    continue

            # Don't loop anymore
            go_on = False

        # Last try: maybe current project is not a git folder yet
        if (self.venv_path / VENV_OK).is_file():
            # Venv found!
            return self.venv_path

        # Can't find any valid venv
        return None

    @property
    def pip_args(self) -> str:
        """
        Additional arguments for "pip install" commands, read from **buildenv.cfg** project config file.
        """
        return self.read_config("pipInstallArgs", "", resolve=True)

    def setup_venv(self, with_venv: Path = None) -> EnvContext:
        """
        Prepare python environment builder, and create environment if it doesn't exist yet

        :param with_venv: Existing venv path (typically used for testing purpose)
        :return: Environment context object
        """

        # Look for venv
        venv_path = with_venv if with_venv is not None and with_venv.is_dir() else self.find_venv()
        missing_venv = venv_path is None

        # Create env builder and remember context
        env_builder = _MyEnvBuilder(clear=missing_venv and self.venv_path.is_dir(), symlinks=os.name != "nt", with_pip=True, prompt=self.prompt)
        context = EnvContext(env_builder.ensure_directories(self.venv_path if missing_venv else venv_path))

        if missing_venv:
            # Prepare pip install extra args, if any
            pip_args = self.pip_args
            pip_args = pip_args.split(" ") if len(pip_args) else []

            # Setup venv
            print(">> Creating venv...")
            env_builder.clear = False
            env_builder.create(self.venv_path)

            # Install requirements
            print(">> Installing requirements...")
            subprocess.run(
                [str(context.executable), "-m", "pip", "install", "pip", "wheel", "buildenv", "--upgrade"] + pip_args, cwd=self.project_path, check=True
            )
            if (self.project_path / self.requirements_file).is_file():
                subprocess.run([str(context.executable), "-m", "pip", "install", "-r", self.requirements_file] + pip_args, cwd=self.project_path, check=True)

            # If we get here, venv is valid
            print(">> Python venv is ready!")
            (self.venv_path / VENV_OK).touch()

        return context

    def setup(self, args: List[str]) -> int:
        """
        Prepare python venv if not done yet. Then invoke build env manager.

        :returns: Forwarded **buildenv** command return code
        """

        # Prepare venv
        context = self.setup_venv()

        # Delegate to build env manager
        return subprocess.run([str(context.executable), "-m", "buildenv"] + args, cwd=self.project_path, check=False).returncode


# Loading script entry point
if __name__ == "__main__":  # pragma: no cover
    try:
        sys.exit(BuildEnvLoader(Path(__file__).parent).setup(sys.argv[1:]))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
