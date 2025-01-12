import os
import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv2._backends.backend import EnvBackend
from buildenv2._backends.factory import EnvBackendFactory
from buildenv2._backends.pip import LegacyPipBackend
from buildenv2._shells.bash import BashShell
from buildenv2._shells.cmd import CmdShell
from tests.commons2 import WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithPythonProject, WithVenv


class PipExpectedCommands(WithPythonProject):
    @pytest.fixture
    def expected_upgrade_cmd(self, backend: EnvBackend) -> list[str]:
        return [str(backend._venv_bin / backend.command), "-m", "pip", "install", "-r", "requirements.txt", "--upgrade", "--upgrade-strategy=eager"]  # type: ignore

    @pytest.fixture
    def expected_project_install_editable_cmd(self, backend: EnvBackend) -> list[str]:
        return [str(backend._venv_bin / backend.command), "-m", "pip", "install", "-e", ".", "--no-deps", "--no-build-isolation"]  # type: ignore

    @pytest.fixture
    def expected_project_install_non_editable_cmd(self, backend: EnvBackend) -> list[str]:
        return [str(backend._venv_bin / backend.command), "-m", "pip", "install", "foo.whl", "--no-deps", "--force-reinstall"]  # type: ignore


class WithPip(WithVenv, PipExpectedCommands):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project)
        assert backend.venv_name == "venv"
        assert backend.use_requirements
        yield backend


class TestPipBash(WithPip, WithBash):
    def test_pip_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, LegacyPipBackend)
        assert isinstance(backend.shell_instance, BashShell)

    def test_add_packages(self, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        install_cmd_args: list[str] = []

        def fake_run(args: list[str], **kwargs: dict[str, str]):
            # Remember command arguments
            nonlocal install_cmd_args
            install_cmd_args.extend(args)
            return subprocess.CompletedProcess[str](args, 0, stdout="", stderr="")

        # Mock subprocess.run to simulate package installation
        monkeypatch.setattr(subprocess, "run", fake_run)

        # Add packages
        backend.add_packages(["requests"])

        # Check command arguments
        assert install_cmd_args == [str(backend._venv_bin / "python"), "-m", "pip", "install", "requests"]  # pyright: ignore[reportPrivateUsage]


class TestPipCmd(WithPip, WithCmd):
    def test_pip_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, LegacyPipBackend)
        assert isinstance(backend.shell_instance, CmdShell)


class TestPipAlreadyLoaded(WithVenv, WithBash, PipExpectedCommands):
    @pytest.fixture
    def backend(self, project: Path, fake_venv: Path) -> Generator[EnvBackend, Any, Any]:
        # Fake python home + PATH
        old_python_home = os.getenv("PYTHONHOME", None)
        os.environ["PYTHONHOME"] = str(fake_venv)
        old_path = os.getenv("PATH")
        assert old_path is not None, "PATH must be set"
        os.environ["PATH"] = f"{old_path}{os.pathsep}{fake_venv / 'bin'}"

        # Create backend
        yield EnvBackendFactory.detect(project)

        # Restore python home + PATH
        if old_python_home is None:
            del os.environ["PYTHONHOME"]
        else:
            os.environ["PYTHONHOME"] = old_python_home
        os.environ["PATH"] = old_path

    def test_pip_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, LegacyPipBackend)
        assert isinstance(backend.shell_instance, BashShell)


# Install script patch
INSTALL_PATCH = {"pip install buildenv2": "pip install"}


class TestFunctionalPipBash(WithFunctionalBash):
    def test_real_life(self, bash: str, wheel_path: Path):
        # Delegate test
        self.run_real_life_version("pip", [bash], "buildenv.sh", wheel_path, patches={"buildenv.sh": INSTALL_PATCH}, expect_venv=True)


class TestFunctionalPipCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str, wheel_path: Path):
        # Delegate test
        self.run_real_life_version("pip", [cmd, "/c"], "buildenv.cmd", wheel_path, patches={"buildenv.cmd": INSTALL_PATCH}, expect_venv=True)
