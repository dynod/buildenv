import subprocess
import sys
from pathlib import Path

from nmk.utils import is_windows

from buildenv.__main__ import BuildEnvManager
from buildenv.loadme import LoadMe
from tests.commons import BuildEnvTestHelper

# Venv bin directory
VENV_BIN = "Scripts" if is_windows() else "bin"


class TestBuildEnvManager(BuildEnvTestHelper):
    def test_attributes(self):
        # Test manager attributes
        m = BuildEnvManager(self.test_folder)
        assert m.project_path == self.test_folder
        assert m.venv_path == Path(sys.executable).parent.parent
        assert m.venv_bin_path == Path(sys.executable).parent
        assert (self.test_folder / m.relative_venv_bin_path).resolve() == Path(sys.executable).parent
        assert m.project_script_path == self.test_folder / ".loadme"
        assert m.is_windows == is_windows()

    def check_generated_files(self, with_windows: bool, with_git_files: bool, monkeypatch):
        def fake_subprocess(args, cwd=None, **kwargs):
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
        loader = LoadMe(self.test_folder)
        loader.setup()
        assert (self.test_folder / "venv" / "venvOK").is_file()

        # Prepare file paths
        activate_sh = self.test_folder / ".loadme" / "activate.sh"
        activate_cmd = self.test_folder / ".loadme" / "activate.cmd"

        # List generated file + verify they don't exist yet
        m = BuildEnvManager(self.test_folder, self.test_folder / "venv" / VENV_BIN)
        m.is_windows = with_windows  # Force windows files behavior
        generated_files = [
            self.test_folder / "venv" / "buildenvOK",
            self.test_folder / "loadme.py",
            self.test_folder / "loadme.sh",
            self.test_folder / "loadme.cmd",
            activate_sh,
        ] + ([activate_cmd] if with_windows else [])
        missing_files = [] if with_windows else [activate_cmd]
        for f in generated_files + missing_files:
            assert not f.is_file()

        # Call manager setup
        m.setup()

        # Verify generated + missing files
        for f in generated_files:
            assert f.is_file()
        for f in missing_files:
            assert not f.is_file()

        # Verify relative venv path
        assert m.relative_venv_bin_path == Path("venv") / VENV_BIN

        # Verify activate.sh file content
        with activate_sh.open() as f:
            lines = [line.strip("\r\n") for line in f.readlines()]
        assert f"source venv/{VENV_BIN}/activate" in lines

        # Verify activate.cmd file content
        if activate_cmd.is_file():
            with activate_cmd.open() as f:
                lines = [line.strip("\r\n") for line in f.readlines()]
            assert f"venv\\{VENV_BIN}\\activate.bat" in lines

    def test_generated_files_windows(self, monkeypatch):
        self.check_generated_files(True, False, monkeypatch)

    def test_generated_files_linux(self, monkeypatch):
        self.check_generated_files(False, True, monkeypatch)
