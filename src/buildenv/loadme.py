import os
import shutil
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path

# Build env sub-folder in project
BUILDENV_FOLDER = ".buildenv"

# Valid venv tag file
VENV_OK = "venvOK"

# Valid buildenv tag file
BUILDENV_OK = "buildenvOK"


class LoadMe:
    """
    **loadme** wrapper to BuildEnvManager

    :param project_path: Path to project root directory
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path  # Path to current project
        self.buildenv_path = project_path / BUILDENV_FOLDER  # Path to buildenv subfolder
        self.config_file = self.buildenv_path / "loadme.cfg"  # Path to config file (in project folder)
        self.config_parser = None  # Config parser object (lazy init)
        self.is_ci = "CI" in os.environ and len(os.environ["CI"]) > 0  # Check if running in CI
        self.venv_folder = self.read_config("venv_folder", "venv")  # venv folder name
        self.venv_path = self.project_path / self.venv_folder  # default venv path for current project
        self.requirements_file = self.read_config("requirements", "requirements.txt")  # requirements file name
        self.is_windows = "nt" in os.name  # Check if running on Windows
        self.bin_folder = "Scripts" if self.is_windows else "bin"  # Binary folder in venv
        self.build_env_manager = self.read_config("build_env_manager", "buildenv")  # Python module for build env manager

    def read_config(self, name: str, default: str) -> str:
        """
        Read configuration parameter from config file

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
            if self.is_ci:
                # From [ci] profile, if any
                return self.config_parser.get("ci", name, fallback=self.config_parser.get("local", name, fallback=default))
            else:
                # From [default] profile, is any
                return self.config_parser.get("local", name, fallback=default)
        else:
            return default

    def find_venv(self) -> Path:
        """
        Find venv folder, incurrent project folder, or in parent ones

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
                if (candidate_path / self.venv_folder / VENV_OK).is_file():
                    # Venv found!
                    return candidate_path / self.venv_folder

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

    def setup_venv_python(self) -> Path:
        """
        Check for python executable in venv; create venv if not done yet

        :return: Path to python executable in venv
        """

        # Look for venv
        venv_path = self.find_venv()
        if venv_path is None:
            # No venv yet: create it in current project folder
            if self.venv_path.is_dir():
                print(">> Cleaning existing (corrupted?) venv folder...")
                shutil.rmtree(self.venv_path)

            # Setup venv
            print(">> Creating venv folder...")
            subprocess.run([sys.executable, "-m", "venv", self.venv_folder], cwd=self.project_path, check=True)

            # Upgrade pip
            print(">> Upgrading pip...")
            venv_python = self.venv_path / self.bin_folder / "python"
            subprocess.run([str(venv_python), "-m", "pip", "install", "pip", "wheel", "--upgrade"], cwd=self.project_path, check=True)

            # Install requirements
            print(">> Installing requirements...")
            requirements = ["-r", self.requirements_file] if (self.project_path / self.requirements_file).is_file() else ["buildenv"]
            subprocess.run([str(venv_python), "-m", "pip", "install"] + requirements, cwd=self.project_path, check=True)

            # If we get here, venv is valid
            print(">> Python venv is ready!")
        else:
            venv_python = venv_path / self.bin_folder / "python"

        return venv_python

    def setup(self) -> int:
        """
        Prepare python venv if not done yet. Then invoke build env manager if not done yet.
        """

        # Prepare python venv
        venv_python = self.setup_venv_python()

        # Needs to invoke build env manager?
        if not (venv_python.parent.parent / BUILDENV_OK).is_file():
            # Delegate to build env manager
            print(">> Loading buildenv manager...")
            subprocess.run([str(venv_python), "-m", self.build_env_manager], cwd=self.project_path, check=True)


# Load me script entry point
if __name__ == "__main__":  # pragma: no cover
    sys.exit(LoadMe(Path(__file__).parent).setup())
