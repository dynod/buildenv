from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv2._backends.factory import EnvBackendFactory
from buildenv2._backends.uv import EnvBackend, UvxBackend
from buildenv2._shells.bash import BashShell
from buildenv2._shells.cmd import CmdShell
from tests.commons2 import WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithToolsProject, WithUvVenv


class WithUvx(WithUvVenv, WithToolsProject):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project)
        assert backend.venv_name == ""
        assert backend.use_requirements
        yield backend


class TestUvxBash(WithUvx, WithBash):
    def test_uvx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, UvxBackend)
        assert isinstance(backend.shell_instance, BashShell)


class TestUvxCmd(WithUvx, WithCmd):
    def test_uvx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, UvxBackend)
        assert isinstance(backend.shell_instance, CmdShell)


# Updated env for uvx tests
UVX_UPDATED_ENV = {"BUILDENV_UVX_ARGS": "--no-cache"}  # Force re-creating venv from scratch


class TestFunctionalUvxBash(WithFunctionalBash):
    def test_real_life(self, bash: str, wheel_path: Path):
        self.run_real_life_version("uvx", [bash], "buildenv.sh", wheel_path, UVX_UPDATED_ENV)


class TestFunctionalUvxCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str, wheel_path: Path):
        self.run_real_life_version("uvx", [cmd, "/c"], "buildenv.cmd", wheel_path, UVX_UPDATED_ENV)
