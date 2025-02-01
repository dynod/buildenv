import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from pytest_multilog import TestHelper

import buildenv2._shells.shell as buildenv_shell
from buildenv2._backends.backend import EnvBackend


class WithVenv(TestHelper):
    @pytest.fixture(autouse=True)
    def fake_venv(self, monkeypatch: pytest.MonkeyPatch, logs) -> Generator[Path, Any, Any]:
        # Fake python executable
        venv_bin = self.test_folder / "fake_venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(sys, "executable", str(venv_bin / "python"))

        # Fake venv properties
        venv_root = venv_bin.parent
        venv_cfg = venv_root / "pyvenv.cfg"
        venv_cfg.touch()

        yield venv_root

    @pytest.fixture
    def tmp_dir(self, monkeypatch: pytest.MonkeyPatch, logs) -> Generator[Path, Any, Any]:
        # Fake temporary directory handling
        tmp_dir = self.test_folder / "tmp"
        tmp_dir.mkdir()

        class FakeTempDir:
            def __enter__(self):
                return tmp_dir

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        # Patch temporary folder creation
        monkeypatch.setattr(buildenv_shell, "TemporaryDirectory", FakeTempDir)

        yield tmp_dir


class WithToolsProject(TestHelper):
    @pytest.fixture(autouse=True)
    def project(self) -> Generator[Path, Any, Any]:
        # Fake tools project
        tools_project = self.test_folder / "tools_project"
        tools_project.mkdir(parents=True, exist_ok=True)
        yield tools_project


class WithPythonProject(TestHelper):
    @pytest.fixture(autouse=True)
    def project(self) -> Generator[Path, Any, Any]:
        # Test folder is a python project
        yield self.test_folder


class WithUvVenv(WithVenv):
    @pytest.fixture(autouse=True)
    def with_uv(self, fake_venv: Path):
        # Fake uv property
        with (fake_venv / "pyvenv.cfg").open("w") as f:
            f.write("uv = xxx\n")


class WithPipxVenv(WithVenv):
    @pytest.fixture(autouse=True)
    def with_pipx(self, fake_venv: Path):
        # Fake pipx metadata
        (fake_venv / "pipx_metadata.json").touch()


class WithBash(TestHelper):
    @pytest.fixture(autouse=True)
    def with_bash(self):
        old_shell = os.getenv("SHELL", None)
        os.environ["SHELL"] = "/bin/bash"
        yield
        if old_shell is not None:
            os.environ["SHELL"] = old_shell
        else:
            del os.environ["SHELL"]

    def test_shell(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Check shell name
        assert backend._shell.name == "bash"

        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess | None = None

        def _remember_cp(args, **kwargs):
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0)
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))

        # Test interractive shell
        rc = backend.shell()
        assert rc == 0

        # Verify subprocess.run call
        assert cp.args == ["/bin/bash", "--rcfile", str(tmp_dir / "shell.sh")]

        # Verify generated files
        assert len(list(filter(lambda f: f.is_file(), tmp_dir.rglob("*")))) == 4
        for f in ["activate.sh", "shell.sh", "activate/completion.sh", "bin/pip"]:
            assert (tmp_dir / f).is_file()

    def test_command(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess | None = None

        def _remember_cp(args, **kwargs):
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0)
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))

        # Test command execution through shell
        rc = backend.run("echo Hello")
        assert rc == 0

        # Verify subprocess.run call
        assert cp.args == ["/bin/bash", "-c", str(tmp_dir / "command.sh")]

        # Verify generated files
        assert len(list(filter(lambda f: f.is_file(), tmp_dir.rglob("*")))) == 4
        for f in ["activate.sh", "command.sh", "activate/completion.sh", "bin/pip"]:
            assert (tmp_dir / f).is_file()

        # Check command is in generated file
        with (tmp_dir / "command.sh").open() as f:
            assert "echo Hello" in f.read().splitlines()
