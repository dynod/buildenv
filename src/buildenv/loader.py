"""
Python module for loading script.

This module is standalone (i.e. it doesn't have any dependencies out of the raw python SDK)
and is designed to be:

- copied in project root folder
- kept in source control, so that the script is ready to run just after project clone
"""

import os
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from types import SimpleNamespace
from venv import EnvBuilder

VENV_OK = "venvOK"
"""Valid venv tag file"""


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
        return self.context.env_dir

    @property
    def executable(self) -> Path:
        """Path to python executable in environment"""
        return self.root / self.context.bin_name / self.context.python_exe


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
        self.venv_folder = self.read_config("venv_folder", "venv")  # Venv folder name
        self.venv_path = self.project_path / self.venv_folder  # Venv path for current project
        self.requirements_file = self.read_config("requirements", "requirements.txt")  # Requirements file name
        self.build_env_manager = self.read_config("build_env_manager", "buildenv")  # Python module for build env manager

    def read_config(self, name: str, default: str) -> str:
        """
        Read configuration parameter from config file (**buildenv.cfg**).

        Value is read according to the current profile: **[local]** or **[ci]** (if **CI** env var is defined and not empty).
        Note that if a parameter is not defined in **[ci]** profile, it will be defaulted to value in **[local]** profile,
        if any (otherwise provided default will be used).

        :param name: parameter name
        :param default: default value if parameter is not set
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
            return self.config_parser.get("ci", name, fallback=local_value) if self.is_ci else local_value
        else:
            return default

    def find_venv(self) -> Path:
        """
        Find venv folder, in current project folder, or in parent ones

        :return: venv folder path, or None if no venv found
        """

        # Look up to find venv folder (even in parent projects)
        current_path = self.project_path
        go_on = True
        while go_on:
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

    def setup_venv(self) -> EnvContext:
        """
        Prepare python environment builder, and create environment if it doesn't exist yet

        :return: Environment context object
        """

        # Look for venv
        venv_path = self.find_venv()
        missing_venv = venv_path is None

        # Create env builder and remember context
        env_builder = EnvBuilder(
            clear=missing_venv and self.venv_path.is_dir(), symlinks=os.name != "nt", with_pip=True, prompt=self.read_config("prompt", "buildenv")
        )
        context = EnvContext(env_builder.ensure_directories(self.venv_path if missing_venv else venv_path))

        if missing_venv:
            # Setup venv
            print(">> Creating venv...")
            env_builder.clear = False
            env_builder.create(self.venv_path)

            # Install requirements
            print(">> Installing requirements...")
            requirements = ["-r", self.requirements_file] if (self.project_path / self.requirements_file).is_file() else ["buildenv"]
            subprocess.run([str(context.executable), "-m", "pip", "install", "pip"] + requirements + ["--upgrade"], cwd=self.project_path, check=True)

            # If we get here, venv is valid
            print(">> Python venv is ready!")
            (self.venv_path / VENV_OK).touch()

        return context

    def setup(self):
        """
        Prepare python venv if not done yet. Then invoke build env manager.
        """

        # Prepare venv
        context = self.setup_venv()

        # Delegate to build env manager
        subprocess.run([str(context.executable), "-m", self.build_env_manager], cwd=self.project_path, check=True)


# Loading script entry point
if __name__ == "__main__":  # pragma: no cover
    try:
        BuildEnvLoader(Path(__file__).parent).setup()
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
