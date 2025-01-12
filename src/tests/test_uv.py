import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv2._backends.factory import EnvBackendFactory
from buildenv2._backends.uv import EnvBackend, UvProjectBackend
from buildenv2._shells.bash import BashShell
from buildenv2._shells.cmd import CmdShell
from tests.commons2 import WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithPythonProject, WithUnknownShell, WithUvVenv


class WithUv(WithUvVenv, WithPythonProject):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project)
        assert backend.venv_name == ".venv"
        assert not backend.use_requirements
        yield backend

    @pytest.fixture
    def expected_lockfile(self) -> str:
        return "uv.lock"

    @pytest.fixture
    def expected_upgrade_cmd(self, backend: EnvBackend) -> list[str]:
        return ["uv", "sync", "--upgrade"]

    @pytest.fixture
    def expected_project_install_editable_cmd(self, backend: EnvBackend) -> list[str]:
        return ["uv", "sync"]

    @pytest.fixture
    def expected_project_install_non_editable_cmd(self, backend: EnvBackend) -> list[str]:
        return ["uv", "sync", "--no-editable"]


class TestUvBash(WithUv, WithBash):
    def test_uv_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, UvProjectBackend)
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
        assert install_cmd_args == ["uv", "add", "--dev", "requests"]


class TestUvCmd(WithUv, WithCmd):
    def test_uv_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, UvProjectBackend)
        assert isinstance(backend.shell_instance, CmdShell)


class TestUvUnknownShell(WithUvVenv, WithUnknownShell):
    def test_backend(self):
        with pytest.raises(RuntimeError, match="Unable to detect the running shell"):
            EnvBackendFactory.detect(self.test_folder)


# Updated env for uv tests
UV_UPDATED_ENV = {"BUILDENV_UV_ARGS": "--no-cache"}  # Force re-creating venv from scratch

# Extra files to be installed
UV_EXTRA_FILES = [Path(__file__).parent / "templates" / "pyproject.toml"]


class TestFunctionalUvBash(WithFunctionalBash):
    def test_real_life(self, bash: str, wheel_path: Path):
        escaped_wheel_path = str(wheel_path).replace("\\", "\\\\")  # For Windows
        self.run_real_life_version(
            "uv",
            [bash],
            "buildenv.sh",
            wheel_path,
            UV_UPDATED_ENV,
            expect_requirements=False,
            expect_venv=True,
            extra_files=UV_EXTRA_FILES,
            patches={"pyproject.toml": {"buildenv2": f"buildenv2@{escaped_wheel_path}"}},
        )


class TestFunctionalUvCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str, wheel_path: Path):
        escaped_wheel_path = str(wheel_path).replace("\\", "\\\\")  # For Windows
        self.run_real_life_version(
            "uv",
            [cmd, "/c"],
            "buildenv.cmd",
            wheel_path,
            UV_UPDATED_ENV,
            expect_requirements=False,
            expect_venv=True,
            extra_files=UV_EXTRA_FILES,
            patches={"pyproject.toml": {"buildenv2": f"buildenv2@{escaped_wheel_path}"}},
        )
