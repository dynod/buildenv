from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from buildenv2._backends.factory import EnvBackendFactory
from buildenv2._backends.uv import EnvBackend, UvProjectBackend
from buildenv2._shells.bash import BashShell
from tests.commons2 import WithBash, WithPythonProject, WithUvVenv


class TestUvBash(WithUvVenv, WithBash, WithPythonProject):
    @pytest.fixture
    def backend(self, project: Path) -> Generator[EnvBackend, Any, Any]:
        return EnvBackendFactory.create(project)

    def test_uv_backend(self, backend: EnvBackend):
        # Create backend
        assert isinstance(backend, UvProjectBackend)
        assert isinstance(backend._shell, BashShell)
