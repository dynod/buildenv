import importlib.metadata
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from jinja2 import Environment, FileSystemLoader

from buildenv.__main__ import buildenv
from buildenv._backends.factory import EnvBackendFactory
from buildenv._backends.uv import EnvBackend
from buildenv.extension import BuildEnvExtension, BuildEnvRenderer
from tests.commons2 import FakeBash, WithToolsProject, WithUvVenv


class TestExtension(FakeBash):
    def test_extension_bad_class(self, monkeypatch: MonkeyPatch):
        # Fake extension class
        class FakeExtension:
            pass

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Prepare backend to trigger extension loading
        with pytest.raises(AssertionError, match="Failed to load foo extension: foo extension class is not extending buildenv.BuildEnvExtension"):
            EnvBackendFactory.create("uvx", self.test_folder)

    def test_extension_unknown_ref(self, monkeypatch: MonkeyPatch):
        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                raise ValueError("some error")

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Prepare backend to trigger extension loading
        with pytest.raises(AssertionError, match="Failed to load foo extension: some error"):
            EnvBackendFactory.create("uvx", self.test_folder)

    def test_extension_init_failed(self, monkeypatch: MonkeyPatch):
        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def init(self, force: bool):
                # Something went bad
                raise RuntimeError("some init error")

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Prepare backend to trigger extension loading
        b = EnvBackendFactory.create("uvx", self.test_folder)
        with pytest.raises(AssertionError, match="Error occurred while calling foo extension init: some init error"):
            b.init()

    def test_extension_get_completion_commands_failed(self, monkeypatch: MonkeyPatch):
        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def init(self, force: bool):
                # Nothing to fo
                pass

            def get_completion_commands(self):
                # Something went bad
                raise RuntimeError("some completion error")

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Prepare backend to trigger extension loading
        with pytest.raises(AssertionError, match="Error occurred while getting foo extension completion commands: some completion error"):
            b = EnvBackendFactory.create("uvx", self.test_folder)
            b.run("foo")

    def test_extension_generate_activation_scripts_failed(self, monkeypatch: MonkeyPatch):
        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def init(self, force: bool):
                # Nothing to fo
                pass

            def generate_activation_scripts(self, renderer: BuildEnvRenderer):
                # Something went bad
                raise RuntimeError("some generation error")

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Prepare backend to trigger extension loading
        with pytest.raises(AssertionError, match="Error occurred while generating foo extension activation scripts: some generation error"):
            b = EnvBackendFactory.create("uvx", self.test_folder)
            b.run("foo")


class TestExtensionDefault(WithUvVenv, FakeBash):
    @pytest.fixture
    def backend(self, monkeypatch: MonkeyPatch):
        ext_init_called = False
        ext_init_force = None

        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def init(self, force: bool):
                # Remember if init was called and with which force value
                nonlocal ext_init_called
                nonlocal ext_init_force
                ext_init_called = True
                ext_init_force = force

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        # Yield to test
        yield EnvBackendFactory.create("uvx", self.test_folder)

        # Check that the extension was loaded and init was called
        assert ext_init_called
        assert ext_init_force is False

    def test_extension_default(self, backend: EnvBackend, patch_run_process: None):
        # Prepare backend and call init
        backend.run("echo Hello")

    def test_extension_default_cli(self, backend: EnvBackend, patch_run_process: None):
        # Test interractive shell (CLI)
        rc = buildenv(["run", "echo", "Hello"])
        assert rc == 0


class TestExtensionGeneration(WithUvVenv, WithToolsProject, FakeBash):
    @pytest.fixture
    def backend(self, project: Path, monkeypatch: MonkeyPatch) -> EnvBackend:
        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def init(self, force: bool):
                pass

            def generate_activation_scripts(self, renderer: BuildEnvRenderer):
                # Generate some scripts
                renderer.render(Environment(loader=FileSystemLoader(Path(__file__).parent / "templates")), "some_script.sh.jinja")

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda **kwargs: [FakeEntryPoint()])  # type: ignore

        return EnvBackendFactory.detect(project)

    def get_extra_expected_files(self) -> list[str]:
        # Add expected files to the list
        return ["activate/some_script.sh"]

    def test_extension_script_generation(self, backend: EnvBackend, tmp_dir: Path, patch_run_process: None):
        # Run command to generate activation scripts
        backend.run("echo Hello")

        # Check that the script was generated
        generated_script = tmp_dir / "activate" / "some_script.sh"
        assert generated_script.is_file()
        assert "# Some extension generated script" in generated_script.read_text()

    def test_no_ext(self, backend: EnvBackend, tmp_dir: Path):
        # Run command to generate activation scripts, ignoring all extensions
        backend.init(no_ext=True)

        # Check that the script was not generated
        generated_script = tmp_dir / "activate" / "some_script.sh"
        assert not generated_script.is_file()

    def test_skip_ext(self, backend: EnvBackend, tmp_dir: Path):
        # Run command to generate activation scripts, ignoring the extension
        backend.init(skip_ext=["foo"])

        # Check that the script was not generated
        generated_script = tmp_dir / "activate" / "some_script.sh"
        assert not generated_script.is_file()
