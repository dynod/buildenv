import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv._shells.bash import BashShell
from buildenv._shells.cmd import CmdShell
from buildenv.backends._uv import EnvBackend, UvProjectBackend
from buildenv.backends.factory import EnvBackendFactory
from tests.commons2 import TEMPLATES, WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithPythonProject, WithUvVenv


class WithUv(WithUvVenv, WithPythonProject):
    @pytest.fixture
    def backend(self, project: Path, shell_name: str) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project, shell_name=shell_name)
        assert backend.venv_name == ".venv"
        assert not backend.use_requirements
        yield backend

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


# Updated env for uv tests
UV_UPDATED_ENV = {"BUILDENV_UV_ARGS": "--no-cache"}  # Force re-creating venv from scratch

# Extra files to be installed
UV_EXTRA_FILES = [TEMPLATES / "pyproject.toml"]


class TestFunctionalUvBash(WithFunctionalBash):
    def test_real_life(self, bash: str):
        self.run_real_life_version(
            "uv",
            [bash],
            "buildenv.sh",
            UV_UPDATED_ENV,
            expect_requirements=False,
            expect_venv=".venv",
            extra_files=UV_EXTRA_FILES,
        )


class TestFunctionalUvCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str):
        self.run_real_life_version(
            "uv",
            [cmd, "/c"],
            "buildenv.cmd",
            UV_UPDATED_ENV,
            expect_requirements=False,
            expect_venv=".venv",
            extra_files=UV_EXTRA_FILES,
        )
