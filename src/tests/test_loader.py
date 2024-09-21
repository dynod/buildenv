import re
import subprocess
from pathlib import Path
from typing import List

import pytest
from nmk.utils import is_windows

from buildenv.loader import VENV_OK, BuildEnvLoader
from tests.commons import BuildEnvTestHelper

# Expected bin folder in venv
BIN_FOLDER = "Scripts" if is_windows() else "bin"

# Python executable name
PYTHON_EXE = "python(.exe)?" if is_windows() else "python[0-9.]*"


class TestBuildEnvLoader(BuildEnvTestHelper):
    def test_loader_class(self):
        # Verify default attributes
        loader = BuildEnvLoader(self.test_folder)
        assert loader.project_path == self.test_folder
        assert loader.config_file == self.test_folder / "buildenv.cfg"
        assert loader.config_parser is None
        assert loader.venv_folder == "venv"
        assert loader.venv_path == self.test_folder / "venv"
        assert loader.requirements_file_pattern == "requirements*.txt"

    def test_loader_local_config(self, fake_local):
        # Populate a config file with some local profile values
        self.prepare_config("buildenv-local.cfg")
        loader = BuildEnvLoader(self.test_folder)
        assert loader.config_parser is not None
        assert loader.venv_folder == "MyVenv"
        assert loader.requirements_file_pattern == "requirements*.txt"

    def test_loader_ci_config(self, fake_ci):
        # Populate a config file with some ci profile values
        self.prepare_config("buildenv-ci.cfg")
        loader = BuildEnvLoader(self.test_folder)
        assert loader.config_parser is not None
        assert loader.venv_folder == "MyCiVenv"
        assert loader.requirements_file_pattern == "foo.txt"

    def test_loader_missing_env(self):
        # Populate a config file with env reference
        self.prepare_config("buildenv-env.cfg")
        try:
            BuildEnvLoader(self.test_folder).setup_venv()
            raise AssertionError("Should not getting here")
        except AssertionError as e:
            assert "Environment variable 'SOME_USER_ENV_VAR' not found" in str(e)

    @pytest.fixture
    def fake_env(self):
        # Fake local environment
        old_value = self.set_env("SOME_USER_ENV_VAR", "johnsmith")

        # yield to test
        yield

        # Restore previous environment
        self.restore_env("SOME_USER_ENV_VAR", old_value)

    def test_loader_with_env(self, fake_env):
        # Populate a config file with env reference
        self.prepare_config("buildenv-env.cfg")
        loader = BuildEnvLoader(self.test_folder)
        assert loader.pip_args == "--require-virtualenv --extra-index-url http://johnsmith@foo.org"

    def test_loader_find_real_venv(self):
        # Test for current project venv detection
        loader = BuildEnvLoader(self.test_folder)
        v = loader.find_venv()
        assert v == Path(__file__).parent.parent.parent / "venv"
        assert v.is_dir()

    def test_loader_find_parent_venv(self, monkeypatch):
        # Patch subprocess to fake git answer --> returns parent path and rc 0
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 0, str(cwd).encode()))

        # Prepare 3 folders level in test folder
        level1 = self.test_folder / "level1"
        level1.mkdir()
        level1_venv = level1 / "venv"
        level1_venv.mkdir()
        (level1_venv / VENV_OK).touch()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()

        # Test for venv detection with fake parent repo path
        loader = BuildEnvLoader(level3)
        v = loader.find_venv()
        assert v == level1_venv

    def test_loader_find_parent_venv_unknown(self, monkeypatch):
        # Patch subprocess to fake git answer --> returns parent path and rc 0
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 0, str(cwd).encode()))

        # Can't find venv from fake path
        loader = BuildEnvLoader(Path(("Z:" if is_windows() else "") + "/some/unknown/path"))
        v = loader.find_venv()
        assert v is None

    def test_loader_find_venv_git_error(self, monkeypatch):
        # Patch subprocess to fake git answer --> returns rc 1
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 1, str(cwd).encode()))

        # Prepare fake venv
        fake_venv = self.test_folder / "venv"
        fake_venv.mkdir()
        (fake_venv / VENV_OK).touch()

        # Find venv when project path is not a git folder
        loader = BuildEnvLoader(self.test_folder)
        v = loader.find_venv()
        assert v == fake_venv

    def check_strings(self, received_list: List[str], expected_list: List[str]):
        # Check used commands
        for received, expected in zip(
            received_list if isinstance(received_list, list) else [received_list],
            expected_list if isinstance(expected_list, list) else [expected_list],
        ):
            assert re.compile("^" + expected + "$").match(received) is not None, f"{expected!r} doesn't match {received!r}"

    def wrap_exe(self, exe: str) -> str:
        return exe.replace("/", "\\\\" if is_windows() else "/")

    @property
    def venv_exe(self) -> str:
        return self.wrap_exe((self.test_folder / "venv" / BIN_FOLDER / PYTHON_EXE).as_posix())

    def check_venv_creation(self, monkeypatch, requirements: bool, pip_args: bool):
        received_commands = []

        def fake_subprocess(args, cwd=None, **kwargs):
            received_commands.append(" ".join(args))
            if args[0] == "git":
                return subprocess.CompletedProcess(args, 1, str(cwd).encode())
            return subprocess.CompletedProcess(args, 0, "".encode())

        # Patch subprocess:
        # - to fake git answer --> returns rc 1
        # - to accept other commands --> returns rc 0
        monkeypatch.setattr(subprocess, "run", fake_subprocess)

        # Check venv doesn't exist yet
        assert not (self.test_folder / "venv" / "venvOK").is_file()

        # Add config file for pip args
        extra_pip_params = "--require-virtualenv"
        if pip_args:
            self.prepare_config("buildenv-pip-args.cfg")
            extra_pip_params += " --no-color --no-cache-dir"

        # Create venv
        loader = BuildEnvLoader(self.test_folder)
        c = loader.setup_venv()
        assert c.root == self.test_folder / "venv"
        self.check_strings(str(c.executable), self.venv_exe)

        # Check used commands
        expected_commands = (
            [
                "git rev-parse --show-toplevel",
                f"{self.venv_exe} -I?m ensurepip --upgrade --default-pip",
                f"{self.venv_exe} -m pip install --upgrade pip wheel setuptools buildenv {extra_pip_params}",
            ]
            + [f"{self.venv_exe} -m pip install --requirement=requirements.txt {extra_pip_params}"]
            if requirements
            else []
        )
        self.check_strings(received_commands, expected_commands)

        # Check venv is marked as created
        assert (self.test_folder / "venv" / "venvOK").is_file()

        # Check created venv files
        assert (self.test_folder / "venv" / BIN_FOLDER / ("activate.bat" if is_windows() else "activate")).is_file()
        assert (self.test_folder / "venv" / BIN_FOLDER / "activate.d" / ("00_activate.bat" if is_windows() else "00_activate.sh")).is_file()

    def test_setup_venv_create_empty(self, monkeypatch):
        # Check with empty folder
        self.check_venv_creation(monkeypatch, False, True)

    def test_setup_venv_create_with_clean(self, monkeypatch):
        # Prepare venv folder with dummy content
        fake_venv = self.test_folder / "venv"
        fake_venv.mkdir()
        fake_file = fake_venv / "fake_file"
        fake_file.touch()
        assert fake_file.is_file()

        # Also put a requirements file
        (self.test_folder / "requirements.txt").touch()

        # Check with existing (but corrupted) venv folder
        self.check_venv_creation(monkeypatch, True, False)

    def test_setup_venv_project_path(self):
        # Check with current project venv
        loader = BuildEnvLoader(self.test_folder)
        c = loader.setup_venv()
        self.check_strings(str(c.executable), self.wrap_exe((Path(__file__).parent.parent.parent / "venv" / BIN_FOLDER / PYTHON_EXE).as_posix()))
        assert not (self.test_folder / "venv").is_dir()

    def test_setup_with_manager(self, monkeypatch):
        received_commands = []

        def fake_subprocess(args, capture_output=True, cwd=None, check=False):
            received_commands.append(" ".join(args))
            return subprocess.CompletedProcess(args, 0, str(cwd).encode())

        # Patch subprocess to fake all commands
        monkeypatch.setattr(subprocess, "run", fake_subprocess)

        # Fake build env OK state
        fake_venv = self.test_folder / "venv"
        fake_venv.mkdir()
        (fake_venv / VENV_OK).touch()

        # Setup (should do nothing)
        loader = BuildEnvLoader(self.test_folder)
        loader.setup([])

        # Check used commands
        self.check_strings(
            received_commands,
            [
                "git rev-parse --show-toplevel",
                f"{self.venv_exe} -m buildenv",
            ],
        )

    def test_generated_files_parent_custom_venv(self, monkeypatch):
        # Prepare fake parent venv
        parent_venv = self.test_folder / "MyVenv"
        parent_venv.mkdir()
        (parent_venv / VENV_OK).touch()
        self.prepare_config("buildenv-local.cfg")

        # Prepare child project
        project = self.test_folder / "subproject"
        project.mkdir()

        # Patch subprocess to fake git answer --> returns current path and rc 0
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 0, str(cwd).encode()))

        # Launch loader script
        loader = BuildEnvLoader(project)
        assert loader.find_venv() == parent_venv
