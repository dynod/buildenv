import subprocess
from pathlib import Path

import pytest

from buildenv.backends.factory import EnvBackend, EnvBackendFactory

from .commons2 import FakeBash, WithUvVenv


class TestMisc(WithUvVenv, FakeBash):
    @pytest.fixture
    def backend(self, fake_venv: Path, monkeypatch: pytest.MonkeyPatch) -> EnvBackend:
        monkeypatch.setenv("PYTHONHOME", str(fake_venv))
        return EnvBackendFactory.detect(fake_venv, verbose_subprocess=False)

    def test_command(self, patch_run_process: None, backend: EnvBackend):
        # Test command execution, with fake PYTHONHOME env
        rc = backend.run("echo Hello")
        assert rc == 0

    def test_non_verbose_subprocess(self, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Fake subprocess
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout="stdout content\n", stderr="stderr content\n"),  # type: ignore
        )

        # Test non-verbose subprocess
        backend.subprocess(["--help"])
        self.check_logs(">> stdout:")

    def test_venv_root(self, backend: EnvBackend, fake_venv: Path):
        # Check venv root property
        assert backend.venv_root == fake_venv

    def test_project_path(self, backend: EnvBackend, fake_venv: Path):
        # Check project path property
        assert backend.project_path == fake_venv
