import importlib.metadata
from pathlib import Path

import pytest

from buildenv.__main__ import buildenv
from buildenv.extension import BuildEnvProjectTemplate, BuildEnvRenderer
from tests.commons2 import WithUvxVenv


# Fake template class
class FakeTemplate(BuildEnvProjectTemplate):
    def generate_project_files(self, renderer: BuildEnvRenderer, packages: list[str], extra_templates: list[BuildEnvProjectTemplate]) -> None:
        # Just touch some files directly in the project folder
        assert self.info.project_root is not None
        (self.info.project_root / f"{self.name}.txt").touch()

    @property
    def generated_files(self) -> set[Path]:
        return super().generated_files | set([Path("requirements.txt")])


# Fake entry point class
class FakeEntryPoint:
    name = "my_template"

    def load(self):
        return FakeTemplate


class TestExtension(WithUvxVenv):
    def _patch_entry_points(self, monkeypatch: pytest.MonkeyPatch):
        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda group, **kwargs: [FakeEntryPoint()] if group == "buildenv_template" else [])  # type: ignore

    def test_list(self, monkeypatch: pytest.MonkeyPatch):
        # Patch entry points iteration
        self._patch_entry_points(monkeypatch)

        # List templates and check output
        rc = buildenv(["install", "--list-templates"])
        assert rc == 0
        self.check_logs(["Available project templates:", " - my_template"])

    def test_unknown(self, monkeypatch: pytest.MonkeyPatch):
        # Patch entry points iteration
        self._patch_entry_points(monkeypatch)

        # List templates and check output
        rc = buildenv(["install", "--template", "unknown"])
        assert rc == 1
        self.check_logs("Unknown project template 'unknown'")

    def test_install(self, monkeypatch: pytest.MonkeyPatch):
        # Patch entry points iteration
        self._patch_entry_points(monkeypatch)

        # Install with template and check generated files
        rc = buildenv(["install", "--template", "my_template", "--project", str(self.test_folder)])
        assert rc == 0
        assert (self.test_folder / "my_template.txt").is_file()
        assert not (self.test_folder / "requirements.txt").exists()
