import json
import subprocess
from pathlib import Path

import pytest

from buildenv._backends.factory import EnvBackend, EnvBackendFactory

from .commons2 import WithVenv


class TestMisc(WithVenv):
    @pytest.fixture
    def backend(self, fake_venv: Path) -> EnvBackend:
        return EnvBackendFactory.detect(fake_venv, verbose_subprocess=False)

    @pytest.fixture
    def lockfile(self, fake_venv: Path) -> Path:
        return fake_venv / "requirements.lock"

    def dump_fake_old_packages(self, backend: EnvBackend, packages: dict[str, str]) -> Path:
        packages_path = self.test_folder / "._buildenv_old_packages.json"
        if not packages:
            packages = backend.installed_packages
        packages_path.write_text(json.dumps(packages))
        return packages_path

    def test_no_updates(self, backend: EnvBackend, lockfile: Path):
        # Give a try with no updates
        jp = self.dump_fake_old_packages(backend, {})
        backend.init(no_ext=True, show_updates_from=jp)
        self.check_logs("All packages are already up to date.")

        # No lock file
        assert not lockfile.is_file()

    def test_with_updates(self, backend: EnvBackend, lockfile: Path):
        # Give a try with fake legacy versions
        jp = self.dump_fake_old_packages(backend, {"some-unknown-pkg": "1.0.0", "argcomplete": "1.0.0"})
        backend.init(no_ext=True, show_updates_from=jp)
        self.check_logs(
            [
                "some-unknown-pkg              removed (was 1.0.0)",
                "argcomplete                   updated (from 1.0.0 to ",
                "Jinja2                        added (",
            ]
        )

        # No lock file
        assert not lockfile.is_file()

    def test_locked_update(self, backend: EnvBackend, lockfile: Path):
        # Fake lockfile
        lockfile.write_text("some-unknown-pkg==1.0.0\nargcomplete==1.0.0\n")

        # Give a try with no updates
        jp = self.dump_fake_old_packages(backend, {})
        backend.init(no_ext=True, show_updates_from=jp)
        self.check_logs(f"Refresh {lockfile.name} file...")

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
