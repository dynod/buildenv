from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv._shells.bash import BashShell
from buildenv._shells.cmd import CmdShell
from buildenv.backends import EnvBackend, EnvBackendFactory
from buildenv.backends._pipx import PipXBackend
from tests.commons2 import WithBash, WithCmd, WithPipxVenv, WithToolsProject


class WithPipx(WithPipxVenv, WithToolsProject):
    @pytest.fixture
    def backend(self, project: Path, shell_name: str) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project, shell_name=shell_name)
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
