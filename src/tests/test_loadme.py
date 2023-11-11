import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from nmk.utils import is_windows
from pytest_multilog import TestHelper

from buildenv.loadme import BUILDENV_FOLDER, BUILDENV_OK, VENV_OK, LoadMe

# Expected bin folder in venv
BIN_FOLDER = "Scripts" if is_windows() else "bin"

# Python executable name
PYTHON_EXE = "python(.exe)?" if is_windows() else "python"


class TestLoadme(TestHelper):
    @pytest.fixture
    def fake_ci(self):
        # Fake CI environment
        old_ci_value = os.environ["CI"] if "CI" in os.environ else None
        os.environ["CI"] = "true"

        # yield to test
        yield

        # Restore previous environment
        if old_ci_value is not None:
            os.environ["CI"] = old_ci_value
        else:
            del os.environ["CI"]

    @pytest.fixture
    def fake_local(self):
        # Fake local environment
        old_ci_value = os.environ["CI"] if "CI" in os.environ else None
        os.environ["CI"] = ""

        # yield to test
        yield

        # Restore previous environment
        if old_ci_value is not None:
            os.environ["CI"] = old_ci_value
        else:
            del os.environ["CI"]

    def prepare_config(self, name: str):
        # Create buildenv folder, and copy template config file
        buildenv = self.test_folder / BUILDENV_FOLDER
        buildenv.mkdir()
        shutil.copyfile(Path(__file__).parent / "templates" / name, buildenv / "loadme.cfg")

    def test_loadme_class(self):
        # Verify default loadme attributes
        loader = LoadMe(self.test_folder)
        assert loader.project_path == self.test_folder
        assert loader.config_file == self.test_folder / BUILDENV_FOLDER / "loadme.cfg"
        assert loader.config_parser is None
        assert loader.venv_folder == "venv"
        assert loader.venv_path == self.test_folder / "venv"
        assert loader.requirements_file == "requirements.txt"
        assert loader.build_env_manager == "buildenv"

    def test_loadme_local_config(self, fake_local):
        # Populate a config file with some local profile values
        self.prepare_config("loadme-local.cfg")
        loader = LoadMe(self.test_folder)
        assert loader.config_parser is not None
        assert loader.venv_folder == "MyVenv"
        assert loader.build_env_manager == "buildenv"
        assert loader.requirements_file == "requirements.txt"

    def test_loadme_ci_config(self, fake_ci):
        # Populate a config file with some ci profile values
        self.prepare_config("loadme-ci.cfg")
        loader = LoadMe(self.test_folder)
        assert loader.config_parser is not None
        assert loader.venv_folder == "MyCiVenv"
        assert loader.build_env_manager == "buildenv-foo"
        assert loader.requirements_file == "requirements.txt"

    def test_loadme_find_real_venv(self):
        # Test for current project venv detection
        loader = LoadMe(self.test_folder)
        v = loader.find_venv()
        assert v == Path(__file__).parent.parent.parent / "venv"
        assert v.is_dir()

    def test_loadme_find_parent_venv(self, monkeypatch):
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
        loader = LoadMe(level3)
        v = loader.find_venv()
        assert v == level1_venv

    def test_loadme_find_parent_venv_unknown(self, monkeypatch):
        # Patch subprocess to fake git answer --> returns parent path and rc 0
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 0, str(cwd).encode()))

        # Can't find venv from fake path
        loader = LoadMe(Path(("Z:" if is_windows() else "") + "/some/unknown/path"))
        v = loader.find_venv()
        assert v is None

    def test_loadme_find_venv_git_error(self, monkeypatch):
        # Patch subprocess to fake git answer --> returns rc 1
        monkeypatch.setattr(subprocess, "run", lambda args, capture_output, cwd, check: subprocess.CompletedProcess(args, 1, str(cwd).encode()))

        # Prepare fake venv
        fake_venv = self.test_folder / "venv"
        fake_venv.mkdir()
        (fake_venv / VENV_OK).touch()

        # Find venv when project path is not a git folder
        loader = LoadMe(self.test_folder)
        v = loader.find_venv()
        assert v == fake_venv

    def check_venv_creation(self, monkeypatch, requirements: str):
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

        # Create venv
        loader = LoadMe(self.test_folder)
        c = loader.setup_venv()
        assert c.root == self.test_folder / "venv"
        created_exe = self.test_folder / "venv" / BIN_FOLDER / PYTHON_EXE
        assert c.executable == created_exe

        # Check used commands
        for received, expected in zip(
            received_commands,
            [
                "git rev-parse --show-toplevel",
                f"{created_exe} -I?m ensurepip --upgrade --default-pip",
                f"{created_exe} -m pip install pip " + requirements + " --upgrade",
            ],
        ):
            p = re.compile(expected)
            assert p.match(received) is not None

    def test_setup_venv_create_empty(self, monkeypatch):
        # Check with empty folder
        self.check_venv_creation(monkeypatch, "buildenv")

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
        self.check_venv_creation(monkeypatch, "-r requirements.txt")

    def test_setup_venv_projet_path(self):
        # Check with current project venv
        loader = LoadMe(self.test_folder)
        c = loader.setup_venv()
        assert c.executable == Path(__file__).parent.parent.parent / "venv" / BIN_FOLDER / PYTHON_EXE
        assert not (self.test_folder / "venv").is_dir()

    def test_setup_no_manager(self, monkeypatch):
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
        (fake_venv / BUILDENV_OK).touch()

        # Setup (should do nothing)
        loader = LoadMe(self.test_folder)
        loader.setup()

        # Check used commands
        assert received_commands == ["git rev-parse --show-toplevel"]

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
        loader = LoadMe(self.test_folder)
        loader.setup()

        # Check used commands
        assert received_commands == [
            "git rev-parse --show-toplevel",
            f"{self.test_folder/'venv'/BIN_FOLDER/PYTHON_EXE} -m buildenv",
        ]
