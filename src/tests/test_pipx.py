import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv._shells.bash import BashShell
from buildenv._shells.cmd import CmdShell
from buildenv.backends import EnvBackend, EnvBackendFactory
from buildenv.backends._pipx import PipXBackend
from tests.commons2 import WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithPipxVenv, WithToolsProject


class WithPipx(WithPipxVenv, WithToolsProject):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project)
        assert backend.venv_name == ""
        assert backend.use_requirements
        yield backend


class TestPipxBash(WithPipx, WithBash):
    def test_pipx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, PipXBackend)
        assert isinstance(backend.shell_instance, BashShell)


class TestPipxCmd(WithPipx, WithCmd):
    def test_pipx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, PipXBackend)
        assert isinstance(backend.shell_instance, CmdShell)


# Updated env for pipx tests
PIPX_UPDATED_ENV = {"BUILDENV_PIPX_ARGS": "--no-cache"}  # Force re-creating venv from scratch


class TestFunctionalPipxBash(WithFunctionalBash):
    def test_real_life(self, bash: str, wheel_path: Path):
        if "CI" in os.environ:
            pytest.skip(reason="Works locally but not on CI... need to investigate")

        self.run_real_life_version("pipx", [bash], "buildenv.sh", wheel_path, PIPX_UPDATED_ENV)


class TestFunctionalPipxCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str, wheel_path: Path):
        if "CI" in os.environ:
            pytest.skip(reason="Works locally but not on CI... need to investigate")

        self.run_real_life_version("pipx", [cmd, "/c"], "buildenv.cmd", wheel_path, PIPX_UPDATED_ENV)
