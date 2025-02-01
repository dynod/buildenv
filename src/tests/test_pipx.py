from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv2._backends.factory import EnvBackendFactory
from buildenv2._backends.pipx import EnvBackend, PipXBackend
from buildenv2._shells.bash import BashShell
from tests.commons2 import WithBash, WithPipxVenv, WithToolsProject


class TestPipxBash(WithPipxVenv, WithBash, WithToolsProject):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        return EnvBackendFactory.create(project)

    def test_pipx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, PipXBackend)
        assert isinstance(backend._shell, BashShell)
