import importlib.metadata
import logging
from pathlib import Path
from typing import Any

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

        # Also logs extra template names
        logging.debug(f"Loaded extra templates: {[t.name for t in extra_templates]}")

    @property
    def generated_files(self) -> set[Path]:
        return super().generated_files | set([Path(".gitattributes")])

    @property
    def auto_extra(self) -> bool:
        return super().auto_extra or True


# Fake entry point class
class FakeEntryPoint:
    name = "my_template"

    def load(self):
        return FakeTemplate


# Fake template class with weight
class WeightedFakeTemplate(FakeTemplate):
    @property
    def weight(self):
        return 100

    @property
    def auto_extra(self) -> bool:
        return False


# Fake entry point class for weighted template
class WeightedFakeEntryPoint:
    name = "my_other_template"

    def load(self):
        return WeightedFakeTemplate


# Fake entry point class for weighted template
class SameWeightedFakeEntryPoint:
    name = "my_yet_other_template"

    def load(self):
        return WeightedFakeTemplate


class WithExtensionTest(WithUvxVenv):
    @pytest.fixture
    def project(self) -> Path:
        return self.test_folder

    @pytest.fixture(autouse=True)
    def patch_entry_points(self, monkeypatch: pytest.MonkeyPatch, entry_points: list[Any], fake_git_parent: None):
        # Patch entry points iteration
        monkeypatch.setattr(
            importlib.metadata,
            "entry_points",
            lambda group, **kwargs: entry_points if group == "buildenv_template" else [],  # type: ignore
        )


class TestExtension(WithExtensionTest):
    @pytest.fixture
    def entry_points(self) -> list[Any]:
        return [FakeEntryPoint()]

    def test_list(self):  # List templates and check output
        rc = buildenv(["install", "--list-templates"])
        assert rc == 0
        self.check_logs(["Available project templates", " - my_template"])

    def test_unknown(self):  # List templates and check output
        rc = buildenv(["install", "--template", "unknown"])
        assert rc == 1
        self.check_logs("Unknown project template 'unknown'")

    def test_install_with_main(self):  # Install with template and check generated files
        rc = buildenv(["install", "--template", "my_template", "--project", str(self.test_folder)])
        assert rc == 0
        assert (self.test_folder / "my_template.txt").is_file()
        assert not (self.test_folder / ".gitattributes").exists()

    def test_install_with_no_default(self):  # Install with no default (i.e. no template)
        rc = buildenv(["install", "--project", str(self.test_folder)])
        assert rc == 0
        assert not (self.test_folder / "my_template.txt").exists()
        assert (self.test_folder / ".gitattributes").is_file()
        self.check_logs("No default project template")


class TestSingleWeightedExtension(WithExtensionTest):
    @pytest.fixture
    def entry_points(self) -> list[Any]:
        return [WeightedFakeEntryPoint(), FakeEntryPoint()]

    def test_install_with_default(self):
        rc = buildenv(["install", "--project", str(self.test_folder)])
        assert rc == 0
        assert (self.test_folder / "my_other_template.txt").is_file()
        assert not (self.test_folder / "my_template.txt").exists()
        assert not (self.test_folder / ".gitattributes").exists()
        self.check_logs(["Main template: my_other_template", "Extra templates: my_template", "Loaded extra templates: ['my_template']"])

    def test_install_without_extra(self):
        rc = buildenv(
            [
                "install",
                "--project",
                str(self.test_folder),
                "--extra-template",
                "my_template",
                "--extra-template",
                "my_template",
                "--extra-template",
                "my_other_template",
                "--ignore-template",
                "my_template",
                "--ignore-template",
                "my_template",
            ]
        )
        assert rc == 0
        assert (self.test_folder / "my_other_template.txt").is_file()
        assert not (self.test_folder / "my_template.txt").exists()
        assert not (self.test_folder / ".gitattributes").exists()
        self.check_logs(["Main template: my_other_template", "Extra templates:  -", "Loaded extra templates: [] -"])


class TestSameWeightedExtension(WithExtensionTest):
    @pytest.fixture
    def entry_points(self) -> list[Any]:
        return [WeightedFakeEntryPoint(), SameWeightedFakeEntryPoint()]

    def test_install_with_multiple_default(self):
        rc = buildenv(["install", "--project", str(self.test_folder)])
        assert rc == 1
        self.check_logs("Please choose among the available default main templates:")

    def test_install_with_main(self):
        rc = buildenv(["install", "--template", "my_yet_other_template", "--project", str(self.test_folder)])
        assert rc == 0
        assert (self.test_folder / "my_yet_other_template.txt").is_file()
        assert not (self.test_folder / ".gitattributes").exists()
