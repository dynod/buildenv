import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pkg_resources
from nmk.utils import is_windows

from buildenv import BuildEnvExtension, BuildEnvLoader, BuildEnvManager
from buildenv._internal.parser import RCHolder
from buildenv.manager import BUILDENV_OK
from tests.commons import VENV_BIN, BuildEnvTestHelper

# Default (empty) namespace
DEFAULT_OPTIONS = Namespace()


class TestBuildEnvManager(BuildEnvTestHelper):
    def test_attributes(self):
        # Test manager attributes
        m = BuildEnvManager(self.test_folder)
        assert m.project_path == self.test_folder
        assert m.venv_path == Path(sys.executable).parent.parent
        assert m.venv_bin_path == Path(sys.executable).parent
        assert (self.test_folder / m.renderer.relative_venv_bin_path).resolve() == Path(sys.executable).parent
        assert m.project_script_path == self.test_folder / ".buildenv"
        assert m.is_windows == is_windows()

    def check_manager(
        self,
        monkeypatch,
        method: str,
        with_windows: bool = False,
        with_git_files: bool = False,
        expect_files: bool = True,
        options: Namespace = DEFAULT_OPTIONS,
        git_update_index_rc: int = 1,
        check_files: bool = True,
    ):
        received_commands = []

        def fake_subprocess(args, cwd=None, **kwargs):
            received_commands.append(" ".join(args))
            if args[0] == "git":
                if args[1] == "update-index":
                    return subprocess.CompletedProcess(args, git_update_index_rc, "".encode())
                return subprocess.CompletedProcess(args, 1, "".encode())
            return subprocess.CompletedProcess(args, 0, "".encode())

        # Patch subprocess:
        # - to fake git answer --> returns rc 1
        # - to accept other commands --> returns rc 0
        monkeypatch.setattr(subprocess, "run", fake_subprocess)

        # Fake git files
        if with_git_files:
            (self.test_folder / ".gitignore").touch()
            (self.test_folder / ".gitattributes").touch()

        # Fake venv
        loader = BuildEnvLoader(self.test_folder)
        loader.setup([])
        assert (self.test_folder / "venv" / "venvOK").is_file()

        # Prepare file paths
        activate_sh = self.test_folder / ".buildenv" / "activate.sh"
        activate_cmd = self.test_folder / ".buildenv" / "activate.cmd"

        # List generated file + verify they don't exist yet
        m = BuildEnvManager(self.test_folder, self.test_folder / "venv" / VENV_BIN)
        m.is_windows = with_windows  # Force windows files behavior
        generated_buildenv_files = [
            self.test_folder / "venv" / BUILDENV_OK,
            self.test_folder / "venv" / VENV_BIN / "activate.d" / "01_set_prompt.sh",
            self.test_folder / "venv" / VENV_BIN / "activate.d" / "02_completion.sh",
        ]
        generated_files = (
            generated_buildenv_files
            + [
                self.test_folder / "buildenv-loader.py",
                self.test_folder / "buildenv.sh",
                self.test_folder / "buildenv.cmd",
                activate_sh,
                self.test_folder / ".buildenv" / "shell.sh",
            ]
            + ([activate_cmd, self.test_folder / ".buildenv" / "shell.cmd"] if with_windows else [])
            + (
                [
                    self.test_folder / ".gitignore",
                    self.test_folder / ".gitattributes",
                ]
                if not with_git_files
                else []
            )
        )
        missing_files = [] if with_windows else [activate_cmd, self.test_folder / ".buildenv" / "shell.cmd"]

        # Loop to verify some files are created again even with buildenvOK
        for i in range(2):
            # Check files are missing
            for f in generated_files + missing_files:
                assert not check_files or not f.is_file()

            # Call manager method
            getattr(m, method)(options)

            # Stop here if not required to check files
            if not check_files:
                return

            # Verify generated + missing files
            for f in generated_files:
                if expect_files:
                    assert f.is_file()
                else:
                    assert not f.is_file()
            for f in missing_files:
                assert not f.is_file()

            if expect_files:
                # Verify relative venv path
                assert m.renderer.relative_venv_bin_path == Path("venv") / VENV_BIN

                # Verify activate.sh file content
                with activate_sh.open() as f:
                    lines = [line.strip("\r\n") for line in f.readlines()]
                assert f"source venv/{VENV_BIN}/activate" in lines

                # Verify activate.cmd file content
                if activate_cmd.is_file():
                    with activate_cmd.open() as f:
                        lines = [line.strip("\r\n") for line in f.readlines()]
                    assert f"venv\\{VENV_BIN}\\activate.bat" in lines

            # First loop: clean before loop
            if i == 0:
                for p_to_remove in generated_buildenv_files:
                    generated_files.remove(p_to_remove)
                if expect_files:
                    for f in generated_files:
                        f.unlink()

    def test_init_windows(self, monkeypatch):
        self.check_manager(monkeypatch, "init", True, False)

    def test_init_linux(self, monkeypatch):
        self.check_manager(monkeypatch, "init", False, True, git_update_index_rc=0)

    def test_init_invalid_venv(self):
        venv_bin = self.test_folder / "venv" / "fakeBin"
        m = BuildEnvManager(self.test_folder, venv_bin)

        # Try to init with a fake venv: give up as it was not created by loader
        m.init()

        self.check_logs("venv wasn't created by buildenv; can't work on activation scripts")

    def test_init_parent_venv(self):
        venv_bin = self.test_folder / "venv" / "fakeBin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        prj = self.test_folder / "venv" / "project"
        prj.mkdir(parents=True, exist_ok=True)
        m = BuildEnvManager(prj, venv_bin)

        # Try to init with a fake venv: give up as it was not created by loader
        m.init()

        self.check_logs("Can't update a parent project buildenv; please update buildenv")

    def test_shell_refused_no_loader(self, monkeypatch, fake_no_venv):
        try:
            self.check_manager(monkeypatch, "shell", expect_files=False, options=Namespace(from_loader=None))
        except AssertionError as e:
            assert str(e).startswith("Can't use shell command")

    def test_shell_refused_from_venv(self, monkeypatch, fake_venv):
        try:
            self.check_manager(monkeypatch, "shell", expect_files=False, options=Namespace(from_loader="xxx"))
        except AssertionError as e:
            assert str(e).startswith("Already running in build environment shell")

    def test_shell_from_loader(self, monkeypatch, fake_no_venv):
        try:
            self.check_manager(monkeypatch, "shell", options=Namespace(from_loader="xxx"))
        except RCHolder as e:
            assert e.rc == 100

    def test_extension(self, monkeypatch):
        init_passed = False

        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def get_version(self) -> str:
                return "1.2.3"

            def init(self, force: bool):
                nonlocal init_passed
                init_passed = True

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(pkg_resources, "iter_entry_points", lambda _name: [FakeEntryPoint()])

        # Trigger init
        self.check_manager(monkeypatch, "init")

        # Check we gone through init method
        assert init_passed
        v_file = self.test_folder / "venv" / "fooOK"
        assert v_file.is_file()

        # Trigger init again
        init_passed = False
        self.check_manager(monkeypatch, "init", check_files=False)
        assert not init_passed

        # Trigger init again with force
        init_passed = False
        self.check_manager(monkeypatch, "init", check_files=False, options=Namespace(force=True))
        assert init_passed

        # Fake version in persisted file
        with v_file.open("w") as f:
            f.write("0.0.0")

        # Trigger init again with bad version
        init_passed = False
        self.check_manager(monkeypatch, "init", check_files=False)
        assert init_passed

        # Verify that, even after N init, generated activation files are still the same
        venv_activate = self.test_folder / "venv" / VENV_BIN / "activate.d"
        activate_files = [f.name for f in filter(lambda f: f.is_file(), venv_activate.glob("*"))]
        expected_files = ["00_activate.sh", "01_set_prompt.sh", "02_completion.sh"]
        if is_windows():
            expected_files += ["00_activate.bat"]
        assert len(expected_files) == len(activate_files)

    def test_extension_bad_class(self, monkeypatch):
        # Fake extension class
        class FakeExtension:
            pass

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(pkg_resources, "iter_entry_points", lambda _name: [FakeEntryPoint()])

        # Trigger init
        try:
            self.check_manager(monkeypatch, "init")
            raise AssertionError("Shouldn't get here")
        except AssertionError as e:
            assert str(e) == "Failed to load foo extension: foo extension class is not extending buildenv.BuildEnvExtension"

    def test_extension_unknown_ref(self, monkeypatch):
        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                raise ValueError("some error")

        # Patch entry points iteration
        monkeypatch.setattr(pkg_resources, "iter_entry_points", lambda _name: [FakeEntryPoint()])

        # Trigger init
        try:
            self.check_manager(monkeypatch, "init")
            raise AssertionError("Shouldn't get here")
        except AssertionError as e:
            assert str(e) == "Failed to load foo extension: some error"

    def test_extension_failed_init(self, monkeypatch):
        # Fake extension class
        class FakeExtension(BuildEnvExtension):
            def get_version(self) -> str:
                return "1.2.3"

            def init(self, force: bool):
                raise ValueError("init error")

        # Fake entry point class
        class FakeEntryPoint:
            name = "foo"

            def load(self):
                return FakeExtension

        # Patch entry points iteration
        monkeypatch.setattr(pkg_resources, "iter_entry_points", lambda _name: [FakeEntryPoint()])

        # Trigger init
        try:
            self.check_manager(monkeypatch, "init")
            raise AssertionError("Shouldn't get here")
        except AssertionError as e:
            assert str(e) == "Failed to execute foo extension init: init error"
