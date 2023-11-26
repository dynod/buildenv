import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from nmk.utils import is_windows

from buildenv._internal.parser import RCHolder
from buildenv.loader import BuildEnvLoader
from buildenv.manager import BUILDENV_OK, BuildEnvManager
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
    ):
        received_commands = []

        def fake_subprocess(args, cwd=None, **kwargs):
            received_commands.append(" ".join(args))
            if args[0] == "git":
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
                assert not f.is_file()

            # Call manager method
            getattr(m, method)(options)

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
        self.check_manager(monkeypatch, "init", False, True)

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
